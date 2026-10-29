"""Structural fixtures only. Every apparent human decision is a TEST DOUBLE.
Nothing here creates real review evidence, real permissions or an ML result.
"""
import hashlib
import random
import tempfile
import zipfile
from pathlib import Path
from .core import *
from .owner import private_eval,verify_seven,freeze_new,gate,cross_split
from .score import summary

def fixture(directory):
    from .owner import ROLES,REVIEW_FIELDS,eval_review_template
    import csv,io
    directory=Path(directory);directory.chmod(0o700);rr=[];gold=[];metadata=[];review=[]
    for li,label in enumerate(LABELS):
        for j in range(10):
            i=li*10+j;sid=f'D7-{i+90000000:08d}'
            words=' '.join(sha(('fixture-'+str(i)+'-'+str(k)).encode())[:10] for k in range(8))
            text='SYNTHETIC STRUCTURAL ONLY '+words;lang='en' if j<6 else 'ru'
            rr.append({'sample_id':sid,'text':text});gold.append({'sample_id':sid,'label':label,'label_policy_version':'labels-v1.1'})
            metadata.append({'sample_id':sid,'origin':'synthetic','generator_model':'SYNTHETIC_TEST_MODEL','seed':i,
                'attempt_number':1,'language_proposed':lang,'domain_proposed':'general_dev',
                'family_id_provisional':f'FAM-{i+90000000:08d}','review_status':'pending','split_proposed':'eval',
                'rights_ref':'PENDING','lineage_ref':'PENDING','text_sha256':sha(text.encode())})
            review.append({'sample_id':sid,'language':lang,'domain':'general_dev','text':text,'proposed_label':label,
                'review_decision':'','final_label':'','reviewer':'','reviewed_at':'','review_comment':''})
    provenance={'schema':'g2a-owner-local-draft-r1','model':'SYNTHETIC_TEST_MODEL','model_digest':'SYNTHETIC_TEST_DIGEST',
        'owner_review':'NOT_RUN','reviewed_count':0,'rights':'NOT_ADMITTED','freeze':'NOT_CREATED','prompt_and_inference':'HOLD',
        'generation_options':{'temperature':0.75,'top_p':0.90,'num_predict':180},'generation_mode':'localhost_ollama_only'}
    def csvbytes(rows):
        buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(REVIEW_FIELDS),lineterminator='\n')
        w.writeheader();w.writerows(rows);return buf.getvalue().encode()
    normalized=[{**r,'review_decision':'PASS','final_label':r['proposed_label'],'reviewer':'SYNTHETIC_TEST_DOUBLE',
                 'reviewed_at':'2000-01-01T00:00:00Z'} for r in review]
    roles=dict(ROLES)
    data={'inputs':b''.join(encoded(r)+b'\n' for r in rr),'gold':b''.join(encoded(g)+b'\n' for g in gold),
        'provenance':encoded(provenance)+b'\n','lineage':b''.join(encoded(m)+b'\n' for m in metadata),
        'blank_review':csvbytes(review),'normalized_review':csvbytes(normalized)}
    five=[roles[k] for k in ('inputs','gold','provenance','lineage','blank_review')]
    data['manifest']=''.join(sha(data[k])+'  '+roles[k]+'\n' for k in ('inputs','gold','provenance','lineage','blank_review')).encode()
    for role,b in data.items():
        p=directory/roles[role];p.write_bytes(b);p.chmod(0o600)
    backup=directory/'SYNTHETIC_backup.zip'
    with zipfile.ZipFile(backup,'w') as z:
        for role,b in data.items():z.writestr(roles[role],b)
    backup.chmod(0o600)
    descriptor={'contract_status':'OWNER_GENERATOR_CODEC_R2','roles':roles,'historical_five':five,
        'backup_zip':str(backup),'owner_independent_backup_sha256':sha(backup.read_bytes()),'zip_prefix':''}
    human=eval_review_template(data)
    human.update(SYNTHETIC_TEST_DOUBLE_NOT_HUMAN_EVIDENCE=True,actor_kind='human',actor_id='SYNTHETIC_TEST_DOUBLE',
        timestamp='2000-01-01T00:00:00Z',global_scenario_family_scan_complete=True,
        related_pairs_review_complete=True,language_content_review_complete=True,generation_lineage_rationale='SYNTHETIC_TEST_DOUBLE_ONLY')
    for h,m in zip(human['records'],metadata):
        h.update(language=m['language_proposed'],family_id=m['family_id_provisional'],semantic_family='PASS',language_review='PASS')
    human['source_resolutions'][0].update(decision='PASS',actor_kind='human',rights_attester_id='SYNTHETIC_TEST_DOUBLE',
        evidence_ref='SYNTHETIC_TEST_DOUBLE',source_claim='SYNTHETIC_TEST_DOUBLE',underlying_material='SYNTHETIC_TEST_DOUBLE',
        permitted_local_eval=True,permitted_derivative_use=True)
    return descriptor,human,data

def smoke_components():
    with tempfile.TemporaryDirectory(prefix='D7_SYNTHETIC_ONLY_') as td:
        root=Path(td);root.chmod(0o700)
        desc,human,files=fixture(root)
        verified,_=verify_seven(root,desc);rows=private_eval(verified,human)
        safe=freeze_new(root,verified,rows,human)
        p=root/'SYNTHETIC_consent.json'
        save_new(p,{'scope':'A_B','release_sha256':'TEST_ONLY','input_commitment':digest({'fixture':'SYNTHETIC'}),
           'control_review_ref':'SYNTHETIC_TEST_DOUBLE','owner_actor':'SYNTHETIC_TEST_DOUBLE','consent_id':'SYNTHETIC_ONCE',
           'timestamp':'2000-01-01T00:00:00Z','human_confirmed':True,'private_local_no_shared_or_sync':True,'residual_risk_accepted':True})
        gate(p,root,'A_B','TEST_ONLY',{'fixture':'SYNTHETIC'})
        # Model simulation, NEVER calls MLX or a model or a real adapter.
        def predictions(arm):
            return [{'sample_id':r['sample_id'],'raw':r['label'] if i<{'A':10,'B':30,'C':40}[arm] else 'INVALID SYNTHETIC',
                     'status':'OK','latency_seconds':0.001} for i,r in enumerate(rows)]
        artifact=root/'SYNTHETIC.adapter.json';save_new(artifact,{'SYNTHETIC_NOT_MLX':[1,2,3]})
        need(read_json(artifact)=={'SYNTHETIC_NOT_MLX':[1,2,3]},'SYNTHETIC_SAVE_RELOAD')
        metrics=summary(rows,*[predictions(x) for x in ('A','B','C')])
        return {'status':'SYNTHETIC_END_TO_END_COMPLETE_WITH_HOLD','fixture':'SYNTHETIC_STRUCTURAL_ONLY',
                'seven_file_manifest':'5_OF_5_SYNTHETIC','snapshot_binding':'SEVEN_SYNTHETIC_MATCH',
                'review':'SYNTHETIC_TEST_DOUBLE_NOT_REAL','freeze':'SIMULATED_NOT_REAL',
                'training':'SIMULATED_NOT_MLX','adapter':'SIMULATED_NOT_MLX','A_B_C':'SIMULATED_NOT_ML_RESULTS',
                'counts_simulated':[metrics[x]['correct'] for x in ('A','B','C')],
                'real_owner_operations':'NOT_RUN','real_eval':'NOT_READ','real_training':'NOT_RUN'}

def smoke():
    """Actual stage orchestrator, fabricated records, mock human forms and fake ML backend.
    Does NOT approve or simulate human decisions on the delivered 240 candidates.
    """
    from unittest.mock import patch
    from .workflow import run_owner,dataset_owner,code_release
    from . import mlxrun as ml
    from .data import source_templates,flagged_review_template,draw_audit
    import csv
    with tempfile.TemporaryDirectory(prefix='D7_SYNTHETIC_E2E_ONLY_') as td:
        root=Path(td).resolve();root.chmod(0o700)
        day=root/'day-07';day.mkdir(mode=0o700);(day/'data').mkdir(mode=0o700)
        (day/'prompt.txt').write_text('SYNTHETIC TEMPLATE ONLY')
        (root/'SHA256SUMS.txt').write_text(sha((day/'prompt.txt').read_bytes())+'  day-07/prompt.txt\n')
        desc,human,files=fixture(root);save_new(root/'descriptor.json',desc);save_new(root/'human.json',human)
        rows=private_eval(files,human)
        base={'output_root':str(root),'eval_root':str(root),'seven_descriptor':str(root/'descriptor.json'),
              'eval_human_review':str(root/'human.json'),'freeze_file':str(root/'EVAL_FREEZE.private.json')}
        counter=0
        def invoke(scope,operation,extra=None,dataset=False):
            nonlocal counter
            counter+=1;q={**base,**(extra or {}),'scope':scope,'operation':operation}
            c={'scope':scope,'release_sha256':code_release(root),'input_commitment':digest(q),
              'control_review_ref':'SYNTHETIC_TEST_DOUBLE','owner_actor':'SYNTHETIC_TEST_DOUBLE',
              'timestamp':'2000-01-01T00:00:00Z','consent_id':f'TEST_DOUBLE_{counter:08d}',
              'human_confirmed':True,'private_local_no_shared_or_sync':True,'residual_risk_accepted':True}
            cp=root/f'consent{counter}.json';save_new(cp,c);q['consent']=str(cp)
            rp=root/f'request{counter}.json';save_new(rp,q)
            return dataset_owner(q) if dataset else run_owner(rp,root)
        invoke('PRIVATE_FREEZE','FREEZE')
        train=[];lineage=[]
        for i in range(240):
            text='SYNTHETIC TRAIN STRUCTURE '+ ' '.join(sha(f'not-real-train-{i}-{j}'.encode())[:12] for j in range(8))
            sid=f'D7-{80000000+i:08d}';fam=f'FAM-{80000000+i:08d}';label=LABELS[i//40]
            r={'schema_version':'d7-record-v1.1','sample_id':sid,'text':text,'label':label,
              'language':'en' if i%40<24 else 'ru','domain':'general_dev','origin':'synthetic',
              'source_ref':'SRC-80000000','family_id':fam,'split':'valid' if i%6==0 else 'train',
              'label_policy_version':'labels-v1.1','review_status':'pending','text_sha256':sha(text.encode()),
              'fingerprint_sha256':sha(normalize(text).encode()),'lineage_ref':sid,'review_ref':sid,'rights_ref':'SRC-80000000'}
            train.append(r);lineage.append({'sample_id':sid,'family_id':fam,'all_source_refs':['SRC-80000000']})
        save_new(day/'data/candidates.jsonl',train,True);save_new(day/'data/lineage.jsonl',lineage,True)
        source=source_templates(train,lineage,[{'source_ref':'SRC-80000000'}])[0]
        source.update(actor_kind='human',rights_attester_id='SYNTHETIC_TEST_DOUBLE',evidence_ref='SYNTHETIC_TEST_DOUBLE',
          decision_by='SYNTHETIC_TEST_DOUBLE',decision_time='2000-01-01T00:00:00Z',source_version='SYNTHETIC_TEST_VERSION',
          source_claim='SYNTHETIC_TEST_DOUBLE',underlying_material='SYNTHETIC_TEST_DOUBLE',claim_scope='ALL_BOUND_LINKED_ROWS',
          permitted_local_training=True,permitted_derivative_use=True,privacy_review_status='PASS')
        save_new(root/'sources.json',[source])
        save_new(root/'train_human.json',flagged_review_template(train))
        save_new(root/'cross_human.json',{'comparison_commitment':digest({'train':train,'eval':rows}),
            'actor_kind':'human','actor_id':'SYNTHETIC_TEST_DOUBLE','timestamp':'2000-01-01T00:00:00Z',
            'global_scenario_family_scan_complete':True,'related_pairs_review_complete':True,'exclude_train_ids':[]})
        invoke('PRIVATE_FREEZE','DATASET_CHECK',{'release_root':str(root),'train_human_review':str(root/'train_human.json'),
            'cross_human_review':str(root/'cross_human.json'),'approved_sources':str(root/'sources.json'),
            'control_audit_seed':'SYNTHETIC_TEST_SEED_000000'},dataset=True)
        accepted=root/'accepted-v1'
        draw_audit(accepted,{'frame_commitment':digest(read_lines(accepted/'accepted.jsonl')),
            'control_authorization_ref':'SYNTHETIC_TEST_DOUBLE','seed_source':'CONTROL_PROVIDED','seed':'SYNTHETIC_TEST_SEED_000000'})
        audit=accepted/'audit30.csv'
        with audit.open(newline='') as f:aa=list(csv.DictReader(f));fields=list(aa[0])
        for a in aa:a.update(decision='PASS',actor_kind='human',actor_id='SYNTHETIC_TEST_DOUBLE',timestamp='2000-01-01T00:00:00Z')
        with audit.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(aa)
        audit.chmod(0o600)
        inventory={'SYNTHETIC_NOT_REAL':'1'*64};runtime={'files':inventory,'SYNTHETIC_TEST_DOUBLE':True}
        save_new(root/'model_attestation.json',{'model_id':MODEL,'revision':REVISION,'files':inventory,
            'source_evidence_ref':'SYNTHETIC_TEST_DOUBLE','actor_kind':'human','actor_id':'SYNTHETIC_TEST_DOUBLE','local_snapshot_verified':True})
        extra={'accepted_dir':str(accepted),'local_model':'SYNTHETIC_NOT_REAL',
            'model_snapshot_attestation':str(root/'model_attestation.json')}
        def fake_eval(model,rr,prompt,arm,adapter=None,prediction_path=None):
            return ([{'sample_id':r['sample_id'],'raw':r['label'] if i<{'A':10,'B':30,'C':40}[arm] else 'SYNTHETIC_INVALID',
                      'status':'OK','latency_seconds':.001} for i,r in enumerate(rr)],{'SYNTHETIC_TEST_DOUBLE':True})
        def fake_train(model,rr,prompt,adapter,tok):
            adapter.mkdir(mode=0o700);save_new(adapter/'adapter_config.json',{'SYNTHETIC_NOT_MLX':True})
            p=adapter/'adapters.safetensors';p.write_bytes(b'SYNTHETIC_NOT_REAL_WEIGHTS');p.chmod(0o600)
            return {'status':'TRAIN_COMPLETE','iterations':150,'passes':3,'runtime_seconds':0.,'losses':{},
                'adapter_reload':'SYNTHETIC_TEST_DOUBLE','adapter_sha256':sha(p.read_bytes()),
                'adapter_config_sha256':sha((adapter/'adapter_config.json').read_bytes())}
        with patch.object(ml,'prepare',return_value=(None,runtime)),patch.object(ml,'prompts',return_value=[[1]]),\
             patch.object(ml,'evaluate',side_effect=fake_eval),patch.object(ml,'train_once',side_effect=fake_train):
            invoke('A_B','A_B',extra)
            extra.update(experiment_lock=str(root/'experiment_lock.private.json'),ab_complete=str(root/'AB_COMPLETE.private.json'))
            invoke('TRAIN','TRAIN',extra)
            extra.update(train_complete=str(root/'TRAIN_COMPLETE.private.json'),adapter_dir=str(root/'day7-fresh-adapter'))
            invoke('C','C',extra)
        metrics=read_json(root/'ABC.safe.json')
        need([metrics[a]['correct'] for a in ('A','B','C')]==[10,30,40],'SYNTHETIC_STAGE_CHAIN')
        return {'status':'SYNTHETIC_END_TO_END_COMPLETE_WITH_HOLD','stages':['FREEZE','DATASET_CHECK','AUDIT30','A_B','TRAIN','C'],
          'fixture':'ALL_RECORDS_AND_HUMANS_ARE_STRUCTURAL_TEST_DOUBLES','training':'SIMULATED_NOT_MLX',
          'freeze':'SIMULATED_NOT_REAL','A_B_C':'SIMULATED_NOT_ML_RESULTS','counts_simulated':[10,30,40],
          'real_training':'NOT_RUN','real_owner_operations':'NOT_RUN','real_eval':'NOT_READ'}
