"""One minimal future owner workflow. No command performs an automatic next stage."""
from pathlib import Path
from .core import *
from .owner import gate,private_path,verify_seven,private_eval,cross_split,freeze_new,eval_review_template,decode_owner_files,cross_review_template
from .data import admit,export_accepted
from .score import score,summary

def code_release(root):
    manifest=Path(root)/'SHA256SUMS.txt'
    for line in manifest.read_text().splitlines():
        h,name=line.split(None,1)
        p=Path(name)
        need(not p.is_absolute() and '..' not in p.parts,'RELEASE_PATH')
        need(sha((Path(root)/p).read_bytes())==h,'RELEASE_HASH')
    return sha(manifest.read_bytes())

def _eval(q):
    files,hashes=verify_seven(q['eval_root'],read_json(private_path(q['seven_descriptor'])))
    human=read_json(private_path(q['eval_human_review']))
    rows=private_eval(files,human)
    return files,hashes,rows,human

def _frozen(q):
    files,hashes,rows,human=_eval(q)
    freeze=read_json(private_path(q['freeze_file']))
    need(freeze['file_hashes']=={k:sha(v) for k,v in files.items()} and freeze['ordered_records']==rows,'FREEZE_DRIFT')
    need(freeze['review_commitment']==digest(human),'FROZEN_REVIEW_DRIFT')
    ledger=private_path(Path(q['freeze_file']).parent/'EVAL_REVIEW_LEDGER.private.jsonl')
    need(sha(ledger.read_bytes())==freeze['review_ledger_sha256'],'FROZEN_REVIEW_LEDGER_DRIFT')
    return files,rows,freeze

def _accepted(q,prompt,day):
    directory=private_path(q['accepted_dir'],True)
    rows=read_lines(private_path(directory/'accepted.jsonl'))
    validate_rows(rows,{'train':200,'valid':40})
    need(all(r['review_status']=='validated' for r in rows),'ACCEPTED_ROWS')
    proof=read_json(private_path(directory/'ADMISSION.private.json'))
    originals=read_lines(day/'data/candidates.jsonl')
    expected=admit(originals,read_lines(day/'data/lineage.jsonl'),proof['sources'],proof['human'],proof['cross'])
    need(rows==expected,'DATASET_REVISION_OR_ADMISSION_DRIFT')
    files={}
    for s in ('train','valid'):
        p=private_path(directory/'training-data'/(s+'.jsonl'))
        rr=[r for r in rows if r['split']==s];cc=read_lines(p)
        need(len(cc)==len(rr),'CHAT_COUNT')
        for c,r in zip(cc,rr):chat_valid(c,r,prompt)
        files[s]=sha(p.read_bytes())
    seed_commit=read_json(private_path(directory/'audit_seed.private.json'))
    frame=read_json(private_path(directory/'audit_frame.json'))
    need(seed_commit['frame_commitment']==digest(rows) and seed_commit['seed']==frame['seed'],'AUDIT_SEED_DRIFT')
    need(frame['frame_commitment']==digest(rows) and frame['ids']==audit_ids(rows,frame['seed']),'AUDIT_FRAME_DRIFT')
    check_audit(private_path(directory/'audit30.csv'),rows,frame['ids'])
    return rows,{'rows':digest(rows),'files':files,'prompt':sha(prompt.encode()),
                'admission':digest(proof),'audit_csv':sha((directory/'audit30.csv').read_bytes()),
                'eval_commitment':proof['cross']['eval_freeze_commitment']}

def run_owner(request_path,root):
    q=read_json(private_path(request_path));scope=q.get('scope')
    release=code_release(root)
    bound={k:v for k,v in q.items() if k!='consent'}
    output=gate(q['consent'],q['output_root'],scope,release,bound)
    day=Path(root)/'day-07';prompt=(day/'prompt.txt').read_text()
    if scope=='PRIVATE_FREEZE' and q.get('operation')=='EVAL_REVIEW_TEMPLATE':
        files,hashes=verify_seven(q['eval_root'],read_json(private_path(q['seven_descriptor'])))
        import html
        inputs,gold,_,_=decode_owner_files(files)
        h=eval_review_template(files)
        sections=['<section><h2>'+html.escape(r['sample_id'])+' / existing owner-reviewed gold '+html.escape(g['label'])+
                  '</h2><pre>'+html.escape(r['text'])+'</pre></section>' for r,g in zip(inputs,gold)]
        save_new(output/'eval_review.BLANK.private.json',h)
        with (output/'eval_review.private.html').open('x',encoding='utf-8') as f:
            f.write('<!doctype html><meta charset="utf-8"><style>pre{white-space:pre-wrap}</style><h1>PRIVATE: human decisions blank</h1>'+''.join(sections))
        return {'status':'HUMAN_EVAL_REVIEW_PENDING'}
    if scope=='PRIVATE_FREEZE' and q.get('operation')=='CROSS_REVIEW_TEMPLATE':
        _,eval_rows,freeze=_frozen(q)
        rows=read_lines(day/'data/candidates.jsonl')
        save_new(output/'cross_review.BLANK.private.json',cross_review_template(rows,eval_rows))
        return {'status':'HUMAN_CROSS_REVIEW_PENDING'}
    if scope=='PRIVATE_FREEZE':
        need(q.get('operation')=='FREEZE','PRIVATE_FREEZE_OPERATION')
        files,_,rows,human=_eval(q)
        receipt=freeze_new(output,files,rows,human)
        save_new(output/'freeze.safe.json',receipt)
        return {'status':'OWNER_ATTESTED_PRIVATE_FREEZE','scope':scope}
    need(q.get('operation')==scope,'UNSUPPORTED_OPERATION')
    if scope in ('A_B','C'):
        _,eval_rows,freeze=_frozen(q)
    rows,data=_accepted(q,prompt,day)
    from . import mlxrun as ml
    tok,runtime=ml.prepare(q['local_model'],rows,prompt)  # tokenizer checks before model load
    model_evidence=read_json(private_path(q['model_snapshot_attestation']))
    need(model_evidence.get('model_id')==MODEL and model_evidence.get('revision')==REVISION
         and model_evidence.get('files')==runtime['files'] and model_evidence.get('source_evidence_ref')
         and model_evidence.get('actor_kind')=='human' and model_evidence.get('actor_id')
         and model_evidence.get('local_snapshot_verified') is True,'MODEL_REVISION_ATTESTATION_HOLD')
    runtime['model_identity_evidence']='OWNER_ATTESTED_LOCAL_SNAPSHOT'
    if scope=='A_B':
        need(data['eval_commitment']==digest(freeze),'CROSS_EVAL_FREEZE_DRIFT')
        # ALL tokenized eval inputs checked before either model forward pass.
        ml.prompts(tok,eval_rows,prompt,'A');ml.prompts(tok,eval_rows,prompt,'B')
        lock={'release':release,'data':data,'runtime':runtime,'eval_commitment':digest(freeze)}
        save_new(output/'experiment_lock.private.json',lock)
        for arm in ('A','B'):
            pred,meta=ml.evaluate(q['local_model'],eval_rows,prompt,arm,prediction_path=output/(arm+'.partial.private.jsonl'))
            result={'arm':arm,'lock_commitment':digest(lock),'predictions':pred,'metadata':meta,'metrics':score(eval_rows,pred)}
            save_new(output/(arm+'.private.json'),result)
        b=read_json(output/'B.private.json')
        save_new(output/'AB_COMPLETE.private.json',{'lock_commitment':digest(lock),
                 'A_sha256':sha((output/'A.private.json').read_bytes()),'B_sha256':sha((output/'B.private.json').read_bytes()),
                 'low_headroom':b['metrics']['correct']>=54})
        save_new(output/'AB.safe.json',{'schema':'d7-safe-ab-v1','A':read_json(output/'A.private.json')['metrics'],
                 'B':b['metrics'],'experiment_status':'BASELINE_AB_COMPLETE','training_status':'NOT_RUN'})
        return {'status':'BASELINE_AB_COMPLETE','scope':scope}
    lock=read_json(private_path(q['experiment_lock']))
    ab=read_json(private_path(q['ab_complete']))
    need(ab['lock_commitment']==digest(lock) and lock['release']==release and lock['data']==data
         and lock['runtime']==runtime,'PRETRAIN_OR_RUNTIME_DRIFT')
    for arm in ('A','B'):
        need(sha(private_path(Path(q['ab_complete']).parent/(arm+'.private.json')).read_bytes())==ab[arm+'_sha256'],'BASELINE_DRIFT')
    if scope=='TRAIN':
        need(not ab['low_headroom'] or q.get('low_headroom_control_ref'),'LOW_HEADROOM_CONTROL_HOLD')
        result=ml.train_once(q['local_model'],rows,prompt,output/'day7-fresh-adapter',tok)
        result['lock_commitment']=digest(lock)
        save_new(output/'TRAIN_COMPLETE.private.json',result)
        return {'status':'TRAIN_COMPLETE','scope':scope}
    need(scope=='C','SCOPE')
    need(lock['eval_commitment']==digest(freeze),'EVAL_DRIFT')
    tr=read_json(private_path(q['train_complete']));adapter=private_path(q['adapter_dir'],True)
    need(tr['status']=='TRAIN_COMPLETE' and tr['lock_commitment']==digest(lock),'TRAIN_NOT_COMPLETE')
    need(sha(private_path(adapter/'adapters.safetensors').read_bytes())==tr['adapter_sha256'] and
         sha(private_path(adapter/'adapter_config.json').read_bytes())==tr['adapter_config_sha256'],'ADAPTER_DRIFT')
    ml.prompts(tok,eval_rows,prompt,'C')
    pred,meta=ml.evaluate(q['local_model'],eval_rows,prompt,'C',adapter,prediction_path=output/'C.partial.private.jsonl')
    save_new(output/'C.private.json',{'predictions':pred,'metadata':meta,'lock_commitment':digest(lock)})
    base=Path(q['ab_complete']).parent
    a=read_json(private_path(base/'A.private.json'));b=read_json(private_path(base/'B.private.json'))
    safe=summary(eval_rows,a['predictions'],b['predictions'],pred)
    safe['training']={k:tr[k] for k in ('status','iterations','passes','runtime_seconds','losses','adapter_reload',
                                     'adapter_sha256','adapter_config_sha256')}
    safe['runtime']={arm:report['metadata'] for arm,report in [('A',a),('B',b),('C',{'metadata':meta})]}
    safe['experiment_status']='COMPLETE';safe['publication']='REQUIRES_CONTROL_APPROVAL'
    save_new(output/'ABC.safe.json',safe)
    return {'status':safe['B_C']['result'],'scope':scope}

def dataset_owner(q):
    """Explicit future owner command: train/valid + eval comparator, same PRIVATE_FREEZE scope.
    It reads sealed eval only with a separate exact consent bound to operation DATASET_CHECK.
    The existing freeze and all seven source files are read-only.
    """
    root=Path(q['release_root']);release=code_release(root)
    output=gate(q['consent'],q['output_root'],'PRIVATE_FREEZE',release,{k:v for k,v in q.items() if k!='consent'})
    _,eval_rows,freeze=_frozen(q)
    rows=read_lines(root/'day-07/data/candidates.jsonl')
    h=read_json(private_path(q['train_human_review']))
    cross=cross_split(rows,eval_rows,read_json(private_path(q['cross_human_review'])))
    cross.update(candidate_commitment=digest(rows),eval_freeze_commitment=digest(freeze))
    # Safe collision response has ONLY training IDs and HOLD. No eval IDs/scores/hashes/reasons.
    save_new(output/'cross_split.safe.json',{k:cross[k] for k in ('status','excluded_count','excluded_train_valid_ids')})
    need(cross['status']=='PASS','CROSS_SPLIT_HOLD')
    sources=read_json(private_path(q['approved_sources']))
    accepted=admit(rows,read_lines(root/'day-07/data/lineage.jsonl'),sources,h,cross)
    result=export_accepted(output/'accepted-v1',accepted,(root/'day-07/prompt.txt').read_text())
    save_new(output/'accepted-v1/ADMISSION.private.json',{'sources':sources,'human':h,'cross':cross})
    save_new(output/'DATASET_FRAME.private.json',result)
    return {'status':'ACCEPTED_FRAME_FIXED_AUDIT30_PENDING','n':240}
