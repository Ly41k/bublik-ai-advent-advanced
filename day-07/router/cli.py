import contextlib
import csv
import io
import json
import os
import sys
from pathlib import Path
from .core import *

DAY=Path(__file__).resolve().parents[1]
ROOT=DAY.parent

class Discard:
    def write(self,s):return len(s)
    def flush(self):pass

def offline_check():
    rows=read_lines(DAY/'data/candidates.jsonl');validate_rows(rows,{'train':200,'valid':40})
    prompt=(DAY/'prompt.txt').read_text()
    for split in ('train','valid'):
        cc=read_lines(DAY/'data'/(split+'.candidate.jsonl'));rr=[r for r in rows if r['split']==split]
        need(len(cc)==len(rr),'CANDIDATE_EXPORT_COUNT')
        for c,r in zip(cc,rr):chat_valid(c,r,prompt)
    flags=duplicate_flags(rows)
    need(not any(f['kind']=='NORMALIZED_EQUAL' for f in flags),'DUPLICATE')
    return {'status':'OFFLINE_STRUCTURAL_CHECKS_COMPLETE_WITH_HOLD','candidates':240,'train':200,'valid':40,
            'accepted':0,'duplicate_candidates':len(flags),'pairs_checked':28680,
            'human_review':'AUDIT30_AND_FLAGGED_ONLY_PENDING','individual_240_approvals_required':False,'cross_split_eval':'NOT_RUN','A_B_C':'NOT_RUN','training':'NOT_RUN',
            'unicode':ud.unidata_version}

def train_review_template(output):
    output=Path(output);output.mkdir(mode=0o700)
    rows=read_lines(DAY/'data/candidates.jsonl')
    from .data import flagged_review_template,source_templates
    save_new(output/'train_review.BLANK.json',flagged_review_template(rows))
    save_new(output/'source_attestations.BLANK.json',source_templates(rows,
        read_lines(DAY/'data/lineage.jsonl'),read_json(DAY/'data/sources.PENDING.json')))
    import html
    with (output/'train_review.html').open('x',encoding='utf-8') as f:
        f.write('<!doctype html><meta charset="utf-8"><style>pre{white-space:pre-wrap}</style><h1>240 machine-checked candidates: human adjudication of flags and random audit30 only</h1>'+''.join(
            '<section><h2>'+r['sample_id']+' / '+r['label']+' / '+r['language']+'</h2><pre>'+html.escape(r['text'])+'</pre></section>' for r in rows))
    return {'status':'SOURCE_ATTESTATION_AND_FLAG_ADJUDICATION_PENDING','machine_checked':240,'individual_240_approvals_required':False}

def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    os.umask(0o077)
    # Suppress every third-party print/warning/traceback, including model output strings.
    # Only a small final JSON status is printed. Detailed predictions stay private.
    try:
        with contextlib.redirect_stdout(Discard()),contextlib.redirect_stderr(Discard()):
            need(bool(argv),'COMMAND_REQUIRED')
            if argv==['check']:result=offline_check()
            elif argv==['synthetic-smoke']:
                from .synthetic import smoke
                result=smoke()
            elif len(argv)==2 and argv[0]=='prepare-train-review':result=train_review_template(argv[1])
            elif len(argv)==3 and argv[0]=='audit-draw':
                from .data import draw_audit
                from .owner import private_path
                result=draw_audit(argv[1],read_json(private_path(argv[2])))
            elif len(argv)==3 and argv[0]=='consent-draft':
                from .workflow import code_release
                from .owner import private_path
                q=read_json(private_path(argv[1]));out=Path(argv[2])
                need(str(out)==q.get('consent'),'CONSENT_OUTPUT_BINDING')
                need(q.get('scope') in ('PRIVATE_FREEZE','A_B','TRAIN','C'),'CONSENT_SCOPE')
                private_path(out.parent,True)
                save_new(out,{'scope':q['scope'],'release_sha256':code_release(ROOT),
                    'input_commitment':digest({k:v for k,v in q.items() if k!='consent'}),
                    'control_review_ref':'','owner_actor':'','consent_id':'','timestamp':'',
                    'human_confirmed':None,'private_local_no_shared_or_sync':None,'residual_risk_accepted':None})
                result={'status':'HUMAN_CONSENT_PENDING','authorization':'NOT_GRANTED'}
            elif len(argv)==2 and argv[0]=='owner':
                # No scope flags, no implicit grant. Current task runs NO real owner command.
                from .workflow import run_owner,dataset_owner
                from .owner import private_path
                q=read_json(private_path(argv[1]))
                if q.get('operation')=='DATASET_CHECK':
                    need(q.get('scope')=='PRIVATE_FREEZE' and Path(q.get('release_root',''))==ROOT,'RELEASE_ROOT')
                    result=dataset_owner(q)
                else:result=run_owner(argv[1],ROOT)
            else:raise Stop('COMMAND_NOT_ALLOWED')
        print(json.dumps(result,ensure_ascii=True,allow_nan=False))
        return 0
    except Stop as e:
        # All Stop strings are static source-code literals; never interpolate file data.
        code=e.args[0] if e.args else 'STOP_WITH_HOLD'
        print(json.dumps({'status':'STOP_WITH_HOLD','code':code}))
        return 2
    except BaseException:
        print('{"status":"STOP_WITH_HOLD","code":"UNCLASSIFIED_SAFE_STOP"}')
        return 2
