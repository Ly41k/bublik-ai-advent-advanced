import csv
import html
from pathlib import Path
from .core import *
from .owner import check_flags

def source_templates(rows,lineage,sources):
    """Populate factual bindings only; all human rights decisions stay blank."""
    by={l['sample_id']:l for l in lineage};out=[]
    for s in sources:
        ref=s['source_ref'];linked=[r for r in rows if ref in by[r['sample_id']]['all_source_refs']]
        out.append({**s,'source_candidate_commitment':digest(linked),'linked_rows_count':len(linked),
                    'primary_rows_count':sum(r['source_ref']==ref for r in linked),'actor_kind':'',
                    'source_claim':'','underlying_material':'','claim_scope':'','rights_attester_id':'',
                    'source_version':s.get('revision/content_hash',''),
                    'evidence_ref':'','decision_by':'','decision_time':'','privacy_review_status':'PENDING',
                    'permitted_local_training':None,'permitted_derivative_use':None,'permitted_publication':'unreviewed'})
    return out

def flagged_review_template(rows):
    return {'schema':'d7-r2-flagged-review-v1','frame_commitment':digest(rows),
            'actor_kind':'','actor_id':'','timestamp':'','declared_ambiguous_ids':[],
            'record_resolutions':[],'duplicate_resolutions':[],
            'machine_flags':duplicate_flags(rows),
            'meaning':'No 240 human approvals. Empty flags are not human attestation of universal correctness.'}

def admit(rows,lineage,sources,human,cross):
    validate_rows(rows,{'train':200,'valid':40})
    need(len(lineage)==240 and {l['sample_id'] for l in lineage}=={r['sample_id'] for r in rows},'LINEAGE_COVERAGE')
    by={l['sample_id']:l for l in lineage};src={s['source_ref']:s for s in sources}
    need(len(src)==len(sources),'DUPLICATE_SOURCE_REF')
    all_refs={ref for l in lineage for ref in l['all_source_refs']}
    need(set(src)==all_refs,'SOURCE_COVERAGE')
    for ref,s in src.items():
        linked=[r for r in rows if ref in by[r['sample_id']]['all_source_refs']]
        need(s.get('source_candidate_commitment')==digest(linked)
             and s.get('linked_rows_count')==len(linked)
             and s.get('primary_rows_count')==sum(r['source_ref']==ref for r in linked),'SOURCE_CANDIDATE_BINDING')
        need(s.get('actor_kind')=='human' and s.get('rights_attester_id') and s.get('evidence_ref')
             and s.get('decision_by') and s.get('decision_time') and s.get('source_claim')
             and s.get('underlying_material') and s.get('claim_scope')=='ALL_BOUND_LINKED_ROWS' and s.get('source_version')
             and s.get('permitted_local_training') is True and s.get('permitted_derivative_use') is True
             and s.get('privacy_review_status')=='PASS'
             and s.get('permitted_publication') in ('allowed','denied','unreviewed'),'SOURCE_RIGHTS_HOLD')
    for r in rows:
        l=by[r['sample_id']]
        need(l['family_id']==r['family_id'] and r['source_ref'] in l['all_source_refs'],'LINEAGE_BINDING')
    need(human.get('schema')=='d7-r2-flagged-review-v1' and human.get('frame_commitment')==digest(rows),'FLAG_FRAME_BINDING')
    ambiguous=human.get('declared_ambiguous_ids',[])
    need(len(ambiguous)==len(set(ambiguous)) and set(ambiguous)<={r['sample_id'] for r in rows},'AMBIGUOUS_IDS')
    decisions=human.get('record_resolutions',[])
    need(len(decisions)==len({d['sample_id'] for d in decisions}),'ADJUDICATION_DUPLICATE')
    dd={d['sample_id']:d for d in decisions}
    need(set(dd)==set(ambiguous),'ADJUDICATION_COVERAGE')
    if ambiguous:
        need(human.get('actor_kind')=='human' and human.get('actor_id') and human.get('timestamp'),'ADJUDICATION_HUMAN')
        rr={r['sample_id']:r for r in rows}
        for sid,d in dd.items():
            need(d.get('candidate_revision')==digest(rr[sid]) and d.get('decision')=='PASS'
                 and d.get('label')==rr[sid]['label'] and d.get('rationale'),'ADJUDICATION_HOLD')
    check_flags(rows,human.get('duplicate_resolutions',[]))
    need(cross.get('status')=='PASS' and cross.get('candidate_commitment')==digest(rows)
         and cross.get('eval_freeze_commitment') and not cross.get('excluded_train_valid_ids'),'CROSS_SPLIT_HOLD')
    return [{**r,'review_status':'validated'} for r in rows]


def audit_forms(output,rows,seed):
    output=Path(output);ids=audit_ids(rows,seed);by={r['sample_id']:r for r in rows}
    fields=['sample_id','revision','decision','actor_kind','actor_id','timestamp','notes']
    with (output/'audit30.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for sid in ids:w.writerow({'sample_id':sid,'revision':digest(by[sid])})
    sections=[]
    for sid in ids:
        r=by[sid]
        sections.append('<section><h2>'+html.escape(sid)+'</h2><p>'+html.escape(r['label'])+' / '+r['language']+'</p><pre>'+html.escape(r['text'])+'</pre></section>')
    with (output/'audit30.html').open('x',encoding='utf-8') as f:
        f.write('<!doctype html><meta charset="utf-8"><title>Owner audit 30</title><style>pre{white-space:pre-wrap}section{border-bottom:1px solid #aaa;padding:1em}</style><h1>Human decisions remain blank</h1>'+''.join(sections))
    save_new(output/'audit_frame.json',{'frame_commitment':digest(rows),'seed':seed,'ids':ids,
                                      'status':'HUMAN_REVIEW_PENDING','draws':1})

def export_accepted(output,rows,prompt,seed=None):
    output=Path(output);output.mkdir(mode=0o700)
    save_new(output/'accepted.jsonl',rows,True)
    data=output/'training-data';data.mkdir(mode=0o700)
    for split in ('train','valid'):
        save_new(data/(split+'.jsonl'),[chat(r,prompt) for r in rows if r['split']==split],True)
    save_new(output/'frame.fixed.json',{'frame_commitment':digest(rows),
        'train_sha256':sha((data/'train.jsonl').read_bytes()),'valid_sha256':sha((data/'valid.jsonl').read_bytes())})
    if seed is not None:audit_forms(output,rows,seed)
    return {'rows_commitment':digest(rows),'train_sha256':sha((data/'train.jsonl').read_bytes()),
            'valid_sha256':sha((data/'valid.jsonl').read_bytes()),'prompt_sha256':sha(prompt.encode()),
            'status':'HUMAN_AUDIT30_PENDING','accepted_rows':240}

def draw_audit(output,authorization):
    import secrets
    from .owner import private_path
    output=private_path(output,True)
    rows=read_lines(private_path(output/'accepted.jsonl'))
    validate_rows(rows,{'train':200,'valid':40})
    fixed=read_json(private_path(output/'frame.fixed.json'))
    need(fixed['frame_commitment']==digest(rows),'AUDIT_FIXED_FRAME')
    for split in ('train','valid'):
        need(fixed[split+'_sha256']==sha(private_path(output/'training-data'/(split+'.jsonl')).read_bytes()),'AUDIT_FIXED_EXPORT')
    need(not any((output/n).exists() for n in ('audit_seed.private.json','audit_frame.json','audit30.csv','audit30.html')),'AUDIT_ALREADY_DRAWN')
    need(authorization.get('frame_commitment')==digest(rows) and authorization.get('control_authorization_ref'), 'AUDIT_SEED_AUTHORIZATION')
    source=authorization.get('seed_source')
    if source=='OWNER_CSPRNG':
        need(authorization.get('owner_rng_authorized') is True,'OWNER_RNG_NOT_AUTHORIZED')
        seed=secrets.token_hex(32)
    else:
        need(source=='CONTROL_PROVIDED','AUDIT_SEED_SOURCE')
        seed=authorization.get('seed')
        need(isinstance(seed,str) and len(seed)>=16 and not seed.startswith('PREVIEW'),'AUDIT_CONTROL_SEED')
    # Frame already fixed. Commit unpredictable seed BEFORE drawing or displaying selected IDs.
    save_new(output/'audit_seed.private.json',{'frame_commitment':digest(rows),'seed':seed,
        'seed_source':source,'authorization_commitment':digest(authorization)})
    audit_forms(output,rows,seed)
    return {'status':'HUMAN_AUDIT30_PENDING','n':30,'seed_committed_before_draw':True}
