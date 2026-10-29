import csv
import hashlib
import itertools
import json
import re
import unicodedata as ud
from collections import Counter
from pathlib import Path

LABELS = ('BUG_FIX', 'FEATURE', 'TEST', 'DOCS', 'REFACTOR', 'NEED_INPUT')
DOMAINS = ('android_kotlin_compose', 'python_fastapi', 'agent_tooling',
           'git_ci_build', 'config_docs', 'general_dev')
MODEL = 'mlx-community/SmolLM2-360M-Instruct'
REVISION = '5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7'
SPACE = {9,10,11,12,13,32,133,160,5760,*range(8192,8203),8232,8233,8239,8287,12288}

class Stop(Exception):
    """Only predeclared safe codes may reach the CLI."""

def need(ok, code):
    if not ok:
        raise Stop(code)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def encoded(x):
    return json.dumps(x, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')

def digest(x):
    return sha(encoded(x))

def _pairs(items):
    d = {}
    for k,v in items:
        need(k not in d, 'JSON_DUPLICATE_KEY')
        d[k] = v
    return d

def parse(b):
    need(not b.startswith(b'\xef\xbb\xbf'), 'JSON_BOM')
    x = json.loads(b.decode('utf-8'), object_pairs_hook=_pairs,
                   parse_constant=lambda _: (_ for _ in ()).throw(Stop('JSON_NONFINITE')))
    encoded(x)  # rejects surrogates recursively
    return x

def read_json(p):
    return parse(Path(p).read_bytes())

def read_lines(p):
    b = Path(p).read_bytes()
    need(b.endswith(b'\n') and b and b'\r\n' not in b, 'JSONL_SERIALIZATION')
    return [parse(l) for l in b.splitlines()]

def save_new(p, x, jsonl=False):
    p = Path(p)
    b = b''.join(encoded(r)+b'\n' for r in x) if jsonl else encoded(x)+b'\n'
    with p.open('xb') as f:
        f.write(b)
    p.chmod(0o600)

def normalize(text):
    s = ud.normalize('NFC', text)
    s = ''.join(' ' if ord(c) in SPACE else c for c in s)
    return re.sub(' +', ' ', s).strip(' ').casefold()

def admission(text):
    need(isinstance(text,str) and 1 <= len(text) <= 1000, 'TEXT_LENGTH')
    text.encode('utf-8')
    need(any(ord(c) not in SPACE for c in text), 'TEXT_EMPTY')
    need(not any(ud.category(c) in ('Cs','Cc') and ord(c) not in SPACE for c in text), 'TEXT_CONTROL')
    need('\ufeff' not in text and '```' not in text, 'TEXT_CODE_OR_BOM')
    need(not any(x in text for x in ('<|','[INST]','<<SYS>>')), 'TEXT_ROLE_DELIMITER')
    # Language, private material, code dumps and semantics require actual human review.

def chat(r, prompt):
    return {'messages':[{'role':'system','content':prompt},
                        {'role':'user','content':r['text']},
                        {'role':'assistant','content':r['label']}]}

def chat_valid(c, r, prompt):
    need(c == chat(r,prompt) and list(c) == ['messages'], 'CHAT_MISMATCH')
    need(all(list(m)==['role','content'] for m in c['messages']), 'CHAT_FIELDS')

FIELDS = set('schema_version sample_id text label language domain origin source_ref family_id split label_policy_version review_status text_sha256 fingerprint_sha256 lineage_ref review_ref rights_ref'.split())

def validate_rows(rows, counts=None):
    ids, families = set(), set()
    for r in rows:
        need(set(r)==FIELDS, 'RECORD_FIELDS')
        admission(r['text'])
        need(re.fullmatch(r'D7-\d{8}',r['sample_id']) and r['sample_id'] not in ids, 'RECORD_ID')
        need(re.fullmatch(r'FAM-\d{8}',r['family_id']) and r['family_id'] not in families, 'FAMILY_COLLISION')
        ids.add(r['sample_id']);families.add(r['family_id'])
        need(r['schema_version']=='d7-record-v1.1' and r['label_policy_version']=='labels-v1.1', 'POLICY')
        need(r['label'] in LABELS and r['language'] in ('en','ru') and r['domain'] in DOMAINS, 'RECORD_ENUM')
        need(r['origin'] in ('synthetic','authored','public_bublik_derived'), 'ORIGIN')
        need(r['review_status'] in ('pending','validated','frozen'), 'REVIEW_PENDING_OR_VALID')
        need(r['split'] in ('train','valid','eval'), 'SPLIT')
        need(r['text_sha256']==sha(r['text'].encode()) and
             r['fingerprint_sha256']==sha(normalize(r['text']).encode()), 'RECORD_HASH')
        need(re.fullmatch(r'SRC-\d{8}',r['source_ref']) is not None and
             all(isinstance(r[f],str) and r[f] for f in ('lineage_ref','review_ref','rights_ref')), 'LEDGER_REF')
    if counts is not None:
        need(Counter(r['split'] for r in rows)==Counter(counts), 'SPLIT_COUNTS')

def candidates(a,b):
    a,b = normalize(a),normalize(b)
    if a==b:return 'NORMALIZED_EQUAL'
    tok=lambda x:set(re.findall(r'\w+',x,flags=re.UNICODE))
    if min(len(a),len(b))<5 or min(len(tok(a)),len(tok(b)))<3:return 'SHORT_MANUAL'
    def jac(x,y):return len(x&y)/len(x|y) if x|y else 0
    for n,t in ((3,.70),(5,.65)):
        if jac({a[i:i+n] for i in range(len(a)-n+1)},
               {b[i:i+n] for i in range(len(b)-n+1)})>=t:return 'NEAR_CANDIDATE'
    if jac(tok(a),tok(b))>=.80:return 'NEAR_CANDIDATE'
    if ud.normalize('NFKC',a)==ud.normalize('NFKC',b):return 'COMPATIBILITY_CANDIDATE'
    return None

def duplicate_flags(rows):
    result=[]
    for a,b in itertools.combinations(rows,2):
        kind=candidates(a['text'],b['text'])
        if kind or a['family_id']==b['family_id']:
            result.append({'a':a['sample_id'],'b':b['sample_id'],'kind':kind or 'FAMILY'})
    return result

def audit_ids(rows, seed):
    need(isinstance(seed,str) and len(seed)>=16, 'CONTROL_SEED_REQUIRED')
    result=[]
    for label in LABELS:
        for lang,n in (('en',3),('ru',2)):
            group=[r for r in rows if r['label']==label and r['language']==lang]
            need(len(group)>=n,'AUDIT_STRATUM')
            group.sort(key=lambda r:(sha(('audit-v1\0'+seed+'\0'+r['sample_id']).encode()),r['sample_id']))
            result.extend(r['sample_id'] for r in group[:n])
    return result

def check_audit(path, rows, expected):
    with Path(path).open(newline='',encoding='utf-8') as f:
        rr=list(csv.DictReader(f))
    need(len(rr)==30 and [r['sample_id'] for r in rr]==expected, 'AUDIT_IDS')
    by={r['sample_id']:r for r in rows}
    for r in rr:
        need(r['decision']=='PASS' and r['actor_kind']=='human' and r['actor_id'] and r['timestamp'] and
             r['revision']==digest(by[r['sample_id']]), 'AUDIT_HOLD')
    return {'reviewed':30,'status':'OWNER_REPORTED_AUDIT_PASS'}

def distribution(rows):
    out={}
    for split in ('train','valid'):
        rr=[r for r in rows if r['split']==split]
        out[split]={k:dict(Counter(r[k] for r in rr)) for k in ('label','language','domain','origin','source_ref')}
        out[split]['label_language_domain_origin']=dict(Counter('|'.join(r[k] for k in ('label','language','domain','origin')) for r in rr))
    return out
