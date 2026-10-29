"""Future explicit owner-local file operations; never invoked on real data by Work.

Operational human consent, NOT a signed/native security system. Standard Python only.
R2 codec is derived from the supplied owner-generator source; real state remains owner-local.
"""
import csv
import io
import os
import stat
import secrets
import struct
import zipfile
from pathlib import Path, PurePosixPath
from .core import *

def private_path(p, directory=False):
    p=Path(p)
    need(p.is_absolute(), 'OWNER_ABSOLUTE_LOCAL_PATH_REQUIRED')
    # No folder discovery, crawling, ACL/xattr changes or system-wide custody claims.
    for a in [p,*p.parents]:
        need(not a.is_symlink(),'OWNER_SYMLINK')
    st=p.stat()
    need(st.st_uid==os.getuid() and not st.st_mode & 0o077,'OWNER_PERMISSIONS')
    need(stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode),'OWNER_TYPE')
    if not directory:need(st.st_nlink==1,'OWNER_HARDLINK')
    return p

def gate(consent_path, output, scope, release_hash, inputs):
    """Consume one explicit scoped human consent BEFORE eval/model access. No self-grant flag.

    A locally editable human form is not cryptographic authorization. Control must review
    exact release and inputs and the owner must accept the documented residual boundary.
    """
    output=private_path(output,True)
    c=read_json(private_path(consent_path))
    need(c.get('scope')==scope and scope in ('PRIVATE_FREEZE','A_B','TRAIN','C'),'CONSENT_SCOPE')
    need(c.get('release_sha256')==release_hash and c.get('input_commitment')==digest(inputs),'CONSENT_BINDING')
    for k in ('control_review_ref','owner_actor','consent_id','timestamp'):
        need(isinstance(c.get(k),str) and len(c[k])>=3,'CONSENT_INCOMPLETE')
    need(re.fullmatch('[A-Za-z0-9_-]{8,80}',c['consent_id']) is not None,'CONSENT_ID')
    need(c.get('human_confirmed') is True and c.get('private_local_no_shared_or_sync') is True
         and c.get('residual_risk_accepted') is True,'CONSENT_HOLD')
    # Across scopes use one persistent owner-chosen output root; failure consumes permission too.
    save_new(output/('USED_'+c['consent_id']+'.json'), {'scope':scope,'consent_id':c['consent_id']})
    return output

def _file(root,name):
    need(isinstance(name,str) and name==Path(name).name and name not in ('.','..'),'LAYOUT_NAME')
    return private_path(root/name)

def verify_seven(root, descriptor):
    root=private_path(root,True)
    need(descriptor.get('contract_status')=='OWNER_GENERATOR_CODEC_R2', 'INPUT_CONTRACT_HOLD')
    roles=descriptor.get('roles',{})
    need(roles==ROLES,'SEVEN_ROLES')
    files={role:_file(root,name).read_bytes() for role,name in roles.items()}
    need(set(descriptor.get('historical_five',[]))==set(roles.values())-{roles['manifest'],roles['normalized_review']},'HISTORICAL_FIVE')
    mf={}
    for line in files['manifest'].decode('utf-8').splitlines():
        h,name=line.split(None,1);name=name.strip().removeprefix('*')
        need(name not in mf and re.fullmatch('[a-f0-9]{64}',h) is not None,'HISTORICAL_MANIFEST')
        mf[name]=h
    need(set(mf)==set(descriptor['historical_five']),'MANIFEST_5_OF_5')
    for role,name in roles.items():
        if name in mf:need(sha(files[role])==mf[name],'HISTORICAL_HASH')
    backup=private_path(descriptor['backup_zip'])
    raw=backup.read_bytes()
    need(len(raw)<=64_000_000,'ZIP_TOTAL_LIMIT')
    need(sha(raw)==descriptor['owner_independent_backup_sha256'],'BACKUP_SHA')
    prefix=descriptor.get('zip_prefix','')
    need(not prefix or (prefix.endswith('/') and prefix.count('/')==1 and prefix[:-1] not in ('.','..')),'ZIP_PREFIX')
    required={prefix+name for name in roles.values()}
    allowed_sidecars={'__MACOSX/'+prefix+'._'+name for name in roles.values()}
    if prefix:allowed_sidecars.add('__MACOSX/._'+prefix[:-1])
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist();names=[e.filename for e in entries]
        need(len(names)==len(set(names)) and len(names)<=24,'ZIP_COUNTS')
        need(all(e.file_size<=8_000_000 and not e.flag_bits & 1 for e in entries)
             and sum(e.file_size for e in entries)<=32_000_000,'ZIP_LIMIT')
        need(z.testzip() is None,'ZIP_CRC')
        need(required<=set(names),'SNAPSHOT_SEVEN')
        for e in entries:
            name=e.filename
            need(not e.flag_bits & 1 and e.file_size<=8_000_000,'ZIP_LIMIT')
            if name in required:
                need(z.read(e)==files[next(k for k,v in roles.items() if prefix+v==name)],'SNAPSHOT_BYTE_BINDING')
            elif e.is_dir():
                need(name in {prefix,'__MACOSX/','__MACOSX/'+prefix} and e.file_size==0,'ZIP_DIRECTORY')
            else:
                need(name in allowed_sidecars and e.file_size<=65536,'ZIP_UNKNOWN')
                b=z.read(e)
                need(len(b)>=26 and struct.unpack('>II',b[:8])==(0x00051607,0x00020000),'ZIP_APPLEDOUBLE')
                n=struct.unpack('>H',b[24:26])[0]
                need(n<=16 and len(b)>=26+12*n,'ZIP_APPLEDOUBLE_TABLE')
                bounds=[];kinds=set()
                for i in range(n):
                    kind,offset,size=struct.unpack('>III',b[26+12*i:38+12*i])
                    need(kind not in kinds and offset>=26+12*n and offset+size<=len(b),'ZIP_APPLEDOUBLE_RANGE')
                    kinds.add(kind);bounds.append((offset,offset+size))
                need(all(a[1]<=b[0] for a,b in zip(sorted(bounds),sorted(bounds)[1:])),'ZIP_APPLEDOUBLE_OVERLAP')
    return files,{roles[k]:sha(v) for k,v in files.items()}

ROLES = {'inputs':'EVAL_INPUTS_CANDIDATES.jsonl','gold':'EVAL_GOLD_PROPOSALS.jsonl',
         'provenance':'PROVENANCE_PRIVATE.json','lineage':'PROVISIONAL_METADATA.jsonl',
         'blank_review':'REVIEW60_TO_FILL_PRIVATE.csv','normalized_review':'REVIEW60_NORMALIZED_PRIVATE.csv',
         'manifest':'DRAFT_SHA256SUMS.txt'}
PROVENANCE_FIELDS=set('schema model model_digest owner_review reviewed_count rights freeze prompt_and_inference generation_options generation_mode'.split())
META_FIELDS=set('sample_id origin generator_model seed attempt_number language_proposed domain_proposed family_id_provisional review_status split_proposed rights_ref lineage_ref text_sha256'.split())
REVIEW_FIELDS=('sample_id','language','domain','text','proposed_label','review_decision','final_label','reviewer','reviewed_at','review_comment')

def _csv(blob):
    reader=csv.DictReader(io.StringIO(blob.decode('utf-8-sig'),newline=''))
    fields=reader.fieldnames or []
    need(fields and len(fields)==len(set(fields)),'REVIEW_CSV_HEADER')
    records=list(reader)
    need(all(None not in r and all(v is not None for v in r.values()) for r in records),'REVIEW_CSV_WIDTH')
    return fields,records

def decode_owner_files(files):
    """Exact generator serialization. No inference, conversion or modification of originals."""
    inputs=[parse(l) for l in files['inputs'].splitlines()]
    gold=[parse(l) for l in files['gold'].splitlines()]
    need(len(inputs)==len(gold)==60,'EVAL_60')
    need(all(set(r)=={'sample_id','text'} for r in inputs),'EVAL_INPUT_SCHEMA')
    need(all(set(g)=={'sample_id','label','label_policy_version'} for g in gold),'EVAL_GOLD_SCHEMA')
    ids=[r['sample_id'] for r in inputs]
    need(len(set(ids))==60 and [g['sample_id'] for g in gold]==ids,'EVAL_IDS')
    need(all(re.fullmatch(r'D7-\d{8}',sid) for sid in ids),'EVAL_ID_SCHEMA')
    provenance=parse(files['provenance'])
    need(isinstance(provenance,dict) and set(provenance)==PROVENANCE_FIELDS,'PROVENANCE_OBJECT_CODEC')
    need(provenance['schema']=='g2a-owner-local-draft-r1' and isinstance(provenance['model'],str)
         and provenance['model'] and isinstance(provenance['model_digest'],str) and provenance['model_digest'], 'GENERATOR_IDENTITY')
    need(provenance['owner_review']=='NOT_RUN' and provenance['reviewed_count']==0
         and provenance['rights']=='NOT_ADMITTED' and provenance['freeze']=='NOT_CREATED'
         and provenance['prompt_and_inference']=='HOLD' and provenance['generation_mode']=='localhost_ollama_only'
         and provenance['generation_options']=={'temperature':0.75,'top_p':0.90,'num_predict':180},'GENERATOR_EVIDENCE')
    metadata=[parse(l) for l in files['lineage'].splitlines()]
    need(len(metadata)==60 and [m['sample_id'] for m in metadata]==ids,'PROVISIONAL_ID_BINDING')
    for r,g,m in zip(inputs,gold,metadata):
        admission(r['text'])
        need(g['label'] in LABELS and g['label_policy_version']=='labels-v1.1','EVAL_LABEL')
        need(set(m)==META_FIELDS and m['origin']=='synthetic' and m['generator_model']==provenance['model'], 'PROVISIONAL_FIELDS')
        need(type(m['seed']) is int and 0<=m['seed']<2**31 and type(m['attempt_number']) is int and 1<=m['attempt_number']<=3,'PROVISIONAL_GENERATION')
        need(m['language_proposed'] in ('en','ru') and m['domain_proposed'] in DOMAINS
             and re.fullmatch(r'FAM-\d{8}',m['family_id_provisional']) is not None,'PROVISIONAL_PROPOSALS')
        need(m['review_status']=='pending' and m['split_proposed']=='eval'
             and m['rights_ref']=='PENDING' and m['lineage_ref']=='PENDING','PROVISIONAL_NOT_ADMITTED')
        need(m['text_sha256']==sha(r['text'].encode()),'PROVISIONAL_TEXT_BINDING')
    fields,blank=_csv(files['blank_review'])
    need(tuple(fields)==REVIEW_FIELDS and len(blank)==60 and [r['sample_id'] for r in blank]==ids,'ORIGINAL_BLANK_SCHEMA')
    for b,r,g,m in zip(blank,inputs,gold,metadata):
        need(b['text']==r['text'] and b['proposed_label']==g['label'] and b['language']==m['language_proposed']
             and b['domain']==m['domain_proposed'] and all(b[k]=='' for k in ('review_decision','final_label','reviewer','reviewed_at','review_comment')),'ORIGINAL_BLANK_BINDING')
    # Reuse existing human gold decisions; do NOT ask for new 60 labels or synthesize them.
    fields,review=_csv(files['normalized_review'])
    required={'sample_id','review_decision','final_label','reviewer','reviewed_at','proposed_label'}
    need(required<=set(fields) and len(review)==60 and len({r['sample_id'] for r in review})==60
         and {r['sample_id'] for r in review}==set(ids),'HISTORICAL_REVIEW60_SCHEMA')
    reviewed={r['sample_id']:r for r in review}
    for r,g in zip(inputs,gold):
        h=reviewed[r['sample_id']]
        need(h['review_decision'].strip()=='PASS' and h['proposed_label'].strip()==h['final_label'].strip()==g['label']
             and h['reviewer'].strip() and h['reviewed_at'].strip(),'HISTORICAL_REVIEW60_HOLD')
        if 'text' in h:need(h['text']==r['text'],'HISTORICAL_REVIEW_TEXT')
    return inputs,gold,provenance,metadata

def eval_review_template(files):
    inputs,gold,provenance,metadata=decode_owner_files(files)
    return {'schema':'d7-r2-eval-sidecar-v1','files_commitment':digest({k:sha(v) for k,v in files.items()}),
        'historical_gold_review':'OWNER_ATTESTED_NORMALIZED_CSV_60_PASS_NOT_INDEPENDENTLY_REVIEWED',
        'actor_kind':'','actor_id':'','timestamp':'','global_scenario_family_scan_complete':None,
        'related_pairs_review_complete':None,'language_content_review_complete':None,'generation_lineage_rationale':'',
        'records':[{'sample_id':r['sample_id'],'text_sha256':sha(r['text'].encode()),
            'lineage_entry_sha256':digest(m),'language_proposed':m['language_proposed'],
            'family_id_provisional':m['family_id_provisional'],'language':'','family_id':'',
            'semantic_family':'','language_review':''} for r,m in zip(inputs,metadata)],
        'source_resolutions':[{'source_ref':'OWNER_EVAL_GENERATOR','provenance_sha256':digest(provenance),
            'scope':'ALL_60_BOUND_GENERATOR_ROWS','decision':'','actor_kind':'','rights_attester_id':'','evidence_ref':'',
            'source_claim':'','underlying_material':'','permitted_local_eval':None,'permitted_derivative_use':None,
            'permitted_publication':'unreviewed'}],'duplicate_resolutions':[]}

def private_eval(files,human):
    inputs,gold,provenance,metadata=decode_owner_files(files)
    need(human.get('schema')=='d7-r2-eval-sidecar-v1' and
         human.get('files_commitment')==digest({k:sha(v) for k,v in files.items()}),'HUMAN_BINDING')
    need(human.get('actor_kind')=='human' and human.get('actor_id') and human.get('timestamp'),'HUMAN_ATTESTATION')
    need(all(human.get(k) is True for k in ('global_scenario_family_scan_complete','related_pairs_review_complete',
             'language_content_review_complete')) and human.get('generation_lineage_rationale'),'EVAL_REVIEW_HOLD')
    resolutions=human.get('source_resolutions',[])
    need(len(resolutions)==1,'SOURCE_RESOLUTION_SCOPE')
    d=resolutions[0]
    need(d.get('source_ref')=='OWNER_EVAL_GENERATOR' and d.get('scope')=='ALL_60_BOUND_GENERATOR_ROWS'
         and d.get('provenance_sha256')==digest(provenance) and d.get('decision')=='PASS'
         and d.get('actor_kind')=='human' and d.get('rights_attester_id') and d.get('evidence_ref')
         and d.get('source_claim') and d.get('underlying_material') and d.get('permitted_local_eval') is True
         and d.get('permitted_derivative_use') is True and d.get('permitted_publication') in ('allowed','denied','unreviewed'),
         'SOURCE_RIGHTS_RESOLUTION_HOLD')
    decisions=human.get('records',[])
    need(len(decisions)==60 and [h['sample_id'] for h in decisions]==[r['sample_id'] for r in inputs],'HUMAN_ALL_60')
    rows=[]
    for r,g,m,h in zip(inputs,gold,metadata,decisions):
        need(h.get('text_sha256')==sha(r['text'].encode()),'HUMAN_RECORD_BINDING')
        need(h.get('lineage_entry_sha256')==digest(m),'LINEAGE_RESOLUTION_BINDING')
        need(h.get('language') in ('en','ru') and re.fullmatch(r'FAM-\d{8}',h.get('family_id','')) is not None,'EVAL_PROVENANCE')
        need(h.get('semantic_family')=='PASS' and h.get('language_review')=='PASS','EVAL_UNRESOLVED')
        rows.append({**r,'label':g['label'],'language':h['language'],'family_id':h['family_id']})
    need(Counter(r['language'] for r in rows)=={'en':36,'ru':24} and
         Counter(r['label'] for r in rows)==dict.fromkeys(LABELS,10),'EVAL_QUOTAS')
    need(all(Counter(r['language'] for r in rows if r['label']==l)=={'en':6,'ru':4} for l in LABELS),'EVAL_CLASS_LANG')
    need(len({r['family_id'] for r in rows})==60,'EVAL_FAMILY_COLLISION')
    check_flags(rows,human.get('duplicate_resolutions',[]))
    return rows


def check_flags(rows,resolutions):
    flags=duplicate_flags(rows)
    decisions={(x['a'],x['b']):x for x in resolutions}
    for f in flags:
        need(f['kind'] not in ('NORMALIZED_EQUAL','FAMILY'),'DUPLICATE_STOP')
        d=decisions.get((f['a'],f['b']),{})
        need(d.get('decision')=='DISTINCT' and d.get('actor_kind')=='human'
             and d.get('actor_id') and d.get('timestamp'),'SEMANTIC_FLAGS_HOLD')

def cross_review_template(train,eval_rows):
    pairs=[]
    for t in train:
        for e in eval_rows:
            kind='FAMILY' if t['family_id']==e['family_id'] else candidates(t['text'],e['text'])
            if kind:
                pairs.append({'train_id':t['sample_id'],'eval_id':e['sample_id'],'kind':kind,
                    'pair_commitment':digest([t,e]),'decision':'','rationale':''})
    return {'comparison_commitment':digest({'train':train,'eval':eval_rows}),
        'actor_kind':'','actor_id':'','timestamp':'','global_scenario_family_scan_complete':None,
        'related_pairs_review_complete':None,'exclude_train_ids':[],'pair_resolutions':pairs}

def cross_split(train,eval_rows,human):
    excluded=set()
    binding=digest({'train':train,'eval':eval_rows})
    reviewed=(human.get('comparison_commitment')==binding and human.get('actor_kind')=='human'
              and human.get('actor_id') and human.get('timestamp') and human.get('global_scenario_family_scan_complete') is True
              and human.get('related_pairs_review_complete') is True)
    resolutions=human.get('pair_resolutions',[])
    keys=[(p['train_id'],p['eval_id']) for p in resolutions]
    need(len(keys)==len(set(keys)),'CROSS_PAIR_DUPLICATE')
    resolved={k:p for k,p in zip(keys,resolutions)}
    for t in train:
        for e in eval_rows:
            kind='FAMILY' if t['family_id']==e['family_id'] else candidates(t['text'],e['text'])
            if not kind:continue
            d=resolved.get((t['sample_id'],e['sample_id']),{})
            # Never waive exact matches or a confirmed family collision. Near flags need
            # an actual, privately bound human DISTINCT decision, not a blanket boolean.
            distinct=(reviewed and kind not in ('FAMILY','NORMALIZED_EQUAL') and
                d.get('pair_commitment')==digest([t,e]) and d.get('decision')=='DISTINCT' and d.get('rationale'))
            if not distinct:excluded.add(t['sample_id'])
    if reviewed:
        extra=human.get('exclude_train_ids',[])
        need(set(extra)<=set(t['sample_id'] for t in train),'CROSS_EXCLUSION_ID')
        excluded.update(extra)
    return {'status':'PASS' if reviewed and not excluded else 'HOLD',
            'excluded_count':len(excluded),'excluded_train_valid_ids':sorted(excluded)}

def freeze_new(output,files,rows,human):
    # Call ONLY after explicit PRIVATE_FREEZE scope, full checks and actual human decisions.
    ledger={'schema':'d7-r2-private-semantic-review-event','human_review':human,
            'review_commitment':digest(human),'previous_event_hash':None}
    save_new(Path(output)/'EVAL_REVIEW_LEDGER.private.jsonl',[ledger],jsonl=True)
    payload={'schema':'d7-private-freeze-v1','nonce':secrets.token_hex(32),
             'file_hashes':{k:sha(v) for k,v in files.items()},'ordered_records':rows,
             'review_commitment':digest(human),'review_ledger_sha256':sha((Path(output)/'EVAL_REVIEW_LEDGER.private.jsonl').read_bytes()),
             'gold_review':'HISTORICAL_OWNER_ATTESTED_60_PASS_NOT_INDEPENDENTLY_REVIEWED',
             'policy':'labels-v1.1','status':'OWNER_ATTESTED_FREEZE_NOT_NATIVE_PROOF'}
    save_new(Path(output)/'EVAL_FREEZE.private.json',payload)
    return {'schema':'d7-safe-freeze-v1','status':'OWNER_ATTESTED_PRIVATE_FREEZE',
            'n':60,'en':36,'ru':24,'per_class':10,'commitment':digest(payload),
            'native_custody':'NOT_CLAIMED','historical_p9r4':'SUSPENDED_HOLD',
            'gold_review':'EXISTING_OWNER_ATTESTED_60_PASS','new_gold_label_decisions_required':False}
