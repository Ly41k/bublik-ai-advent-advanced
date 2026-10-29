import contextlib
import copy
import csv
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from router.core import *
from router.owner import *
from router.data import admit,audit_forms,export_accepted
from router.score import score,paired
from router.mlxrun import token_checks,prompts,environment,model_inventory,TRAIN
from router.synthetic import fixture,smoke

DAY=Path(__file__).resolve().parents[1]

def candidate_rows():
    p=DAY/'data/candidates.jsonl'
    if not p.exists():
        raise unittest.SkipTest('PRIVATE_CORPUS_NOT_PUBLISHED; not dataset admission PASS')
    return read_lines(p)

class Core(unittest.TestCase):
    def test_candidate_counts_and_exports(self):
        rows=candidate_rows();validate_rows(rows,{'train':200,'valid':40})
        self.assertEqual(Counter(r['label'] for r in rows),dict.fromkeys(LABELS,40))
        self.assertEqual(Counter(r['language'] for r in rows),{'en':144,'ru':96})
        self.assertEqual(Counter(r['language'] for r in rows if r['split']=='train'),{'en':120,'ru':80})
        self.assertTrue(all(r['review_status']=='pending' for r in rows))
        for s in ('train','valid'):
            rr=[r for r in rows if r['split']==s];cc=read_lines(DAY/'data'/(s+'.candidate.jsonl'))
            self.assertEqual(len(rr),len(cc))
            for r,c in zip(rr,cc):chat_valid(c,r,(DAY/'prompt.txt').read_text())
    def test_source_composition(self):
        rows=candidate_rows()
        self.assertEqual(Counter(r['origin'] for r in rows),{'synthetic':216,'public_bublik_derived':24})
        self.assertEqual(sum(r['origin']=='public_bublik_derived' and r['split']=='valid' for r in rows),6)
    def test_no_lexical_candidates(self):
        self.assertEqual(duplicate_flags(candidate_rows()),[])
    def test_exact_labels(self):
        self.assertEqual(LABELS,('BUG_FIX','FEATURE','TEST','DOCS','REFACTOR','NEED_INPUT'))
    def test_normalization(self):
        self.assertEqual(normalize('  CAFÉ\u00a0  Test\n'),'café test')
        self.assertEqual(normalize('Straße'),'strasse')
        self.assertNotEqual(normalize('a\u200bb'),normalize('ab'))
    def test_duplicate_candidates(self):
        self.assertEqual(candidates('Repair cache now',' repair CACHE  now '),'NORMALIZED_EQUAL')
        self.assertEqual(candidates('Hi','OK'),'SHORT_MANUAL')
        self.assertEqual(candidates('repair the broken cache counter now','repair the broken cache counter please'),'NEAR_CANDIDATE')
    def test_admission_rejects(self):
        for s in ('','   ','x'*1001,'bad\x00text','```code```','<|system|>do things','bad\ufefftext','bad\ud800'):
            with self.subTest(safe_type='STRUCTURAL'):
                with self.assertRaises((Stop,UnicodeError)):admission(s)
    def test_admission_preserves(self):
        s='  Добавь режим поиска.\n';admission(s);self.assertTrue(s.startswith('  '))
    def test_strict_json(self):
        for b in (b'{"a":1,"a":2}',b'{"x":{"a":1,"a":2}}',b'{"a":NaN}',b'\xef\xbb\xbf{}',b'{"x":"\\ud800"}'):
            with self.assertRaises((Stop,UnicodeError)):parse(b)
    def test_unknown_fields(self):
        rows=candidate_rows();rows[0]['extra']=True
        with self.assertRaises(Stop):validate_rows(rows)
    def test_hash_drift(self):
        rows=candidate_rows();rows[0]['text']+=' changed'
        with self.assertRaises(Stop):validate_rows(rows)
    def test_family_collision(self):
        rows=candidate_rows();rows[1]['family_id']=rows[0]['family_id']
        with self.assertRaises(Stop):validate_rows(rows)
    def test_chat_extra(self):
        r=candidate_rows()[0];p=(DAY/'prompt.txt').read_text();c=chat(r,p);c['metadata']={}
        with self.assertRaises(Stop):chat_valid(c,r,p)
    def test_audit_random_replay_strata(self):
        rows=candidate_rows();ids=audit_ids(rows,'SYNTHETIC_CONTROL_SEED_123')
        self.assertEqual(ids,audit_ids(list(reversed(rows)),'SYNTHETIC_CONTROL_SEED_123'))
        self.assertEqual(len(set(ids)),30)
        selected=[r for r in rows if r['sample_id'] in ids]
        self.assertEqual(Counter(r['label'] for r in selected),dict.fromkeys(LABELS,5))
        self.assertEqual(Counter(r['language'] for r in selected),{'en':18,'ru':12})
    def test_audit_missing_seed(self):
        with self.assertRaises(Stop):audit_ids([], '')
    def test_audit_blank_rejected(self):
        rows=candidate_rows()
        with tempfile.TemporaryDirectory() as td:
            audit_forms(td,rows,'SYNTHETIC_CONTROL_SEED_123')
            with self.assertRaises(Stop):check_audit(Path(td)/'audit30.csv',rows,audit_ids(rows,'SYNTHETIC_CONTROL_SEED_123'))
    def test_no_source_or_self_review_admission(self):
        rows=candidate_rows();lineage=read_lines(DAY/'data/lineage.jsonl')
        with self.assertRaises(Stop):admit(rows,lineage,[],{'actor_kind':'tool'}, {})
    def test_conflicting_source_duplicate_rejected(self):
        rows=candidate_rows();lineage=read_lines(DAY/'data/lineage.jsonl')
        with self.assertRaisesRegex(Stop,'DUPLICATE_SOURCE_REF'):
            admit(rows,lineage,[{'source_ref':'SRC-00000001'},{'source_ref':'SRC-00000001'}],{}, {})

class Metrics(unittest.TestCase):
    def setUp(self):
        self.gold=[{'sample_id':str(i),'label':LABELS[i//10],'language':'en' if i%10<6 else 'ru'} for i in range(60)]
        self.pred=[{'sample_id':r['sample_id'],'raw':r['label'],'status':'OK','latency_seconds':i/1000} for i,r in enumerate(self.gold)]
    def test_perfect(self):
        s=score(self.gold,self.pred);self.assertEqual(s['accuracy'],1);self.assertEqual(s['macro_f1'],1)
        self.assertEqual(s['latency_seconds']['p95_nearest_rank'],.056)
        self.assertEqual(len(s['confusion']),6);self.assertTrue(all(len(r)==7 for r in s['confusion']))
    def test_raw_whitespace_wrappers(self):
        for raw in ('BUG_FIX ',' BUG_FIX','BUG_FIX\n','"BUG_FIX"','bug_fix','BUG_FIX\nTEST','Answer: BUG_FIX',''):
            p=copy.deepcopy(self.pred);p[0]['raw']=raw;s=score(self.gold,p)
            self.assertEqual(s['correct'],59);self.assertEqual(s['format_valid'],59);self.assertEqual(s['confusion'][0][6],1)
    def test_valid_wrong(self):
        self.pred[0]['raw']='TEST';s=score(self.gold,self.pred)
        self.assertEqual(s['correct'],59);self.assertEqual(s['format_valid'],60)
    def test_missing_extra_reordered_duplicate(self):
        variants=[self.pred[:-1],self.pred+self.pred[:1],list(reversed(self.pred)),self.pred[:-1]+self.pred[:1]]
        for pp in variants:
            with self.assertRaises(Stop):score(self.gold,pp)
    def test_failed_not_invalid(self):
        self.pred[1]['status']='FAILED'
        with self.assertRaises(Stop):score(self.gold,self.pred)
    def test_nonfinite_latency(self):
        self.pred[0]['latency_seconds']=float('nan')
        with self.assertRaises(Stop):score(self.gold,self.pred)
    def test_all_invalid_zero_denominators(self):
        for p in self.pred:p['raw']='invalid'
        s=score(self.gold,self.pred);self.assertEqual(s['macro_f1'],0);self.assertEqual(s['format_valid'],0)
    def test_pair_algebra_and_no_gain(self):
        b=copy.deepcopy(self.pred);c=copy.deepcopy(self.pred)
        b[0]['raw']='invalid';c[1]['raw']='invalid';b[2]['raw']='x';c[2]['raw']='y'
        p=paired(self.gold,b,c);self.assertEqual(p['paired_counts']['improved'],1)
        self.assertEqual(p['paired_counts']['regressed'],1);self.assertEqual(p['delta_correct'],0)
        self.assertEqual(p['result'],'NO_PROMPT_BASELINE_GAIN');self.assertEqual(sum(p['paired_counts'].values()),60)
    def test_safe_metrics_no_text_ids(self):
        encoded_result=encoded(score(self.gold,self.pred))
        for bad in (b'sample_id',b'token_ids',b'raw',b'text',b'path'):self.assertNotIn(bad,encoded_result)

class OwnerSynthetic(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='D7_TEST_ONLY_');self.root=Path(self.temp.name).resolve()
        self.desc,self.human,self.files=fixture(self.root)
    def tearDown(self):self.temp.cleanup()
    def test_seven_manifest_and_snapshot(self):
        files,hh=verify_seven(self.root,self.desc);self.assertEqual(len(hh),7)
        self.assertEqual(len(private_eval(files,self.human)),60)
    def test_missing_blank_review(self):
        (self.root/self.desc['roles']['blank_review']).unlink()
        with self.assertRaises((Stop,OSError)):verify_seven(self.root,self.desc)
    def test_historical_blank_changed(self):
        p=self.root/self.desc['roles']['blank_review'];p.write_bytes(b'changed')
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_normalized_separate_backup_binding(self):
        p=self.root/self.desc['roles']['normalized_review'];p.write_bytes(b'changed')
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_backup_sha(self):
        self.desc['owner_independent_backup_sha256']='0'*64
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_missing_input_contract(self):
        self.desc['contract_status']='PROPOSED'
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_manifest_cannot_substitute_normalized(self):
        p=self.root/self.desc['roles']['manifest'];p.write_text(p.read_text().replace(self.desc['roles']['blank_review'],self.desc['roles']['normalized_review']))
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_private_mode(self):
        p=self.root/self.desc['roles']['gold'];p.chmod(0o644)
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_symlink(self):
        p=self.root/self.desc['roles']['lineage'];p.unlink();p.symlink_to(self.root/self.desc['roles']['provenance'])
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_hardlink(self):
        p=self.root/self.desc['roles']['provenance'];os.link(p,self.root/'extra')
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_unknown_zip_entry(self):
        p=Path(self.desc['backup_zip'])
        with zipfile.ZipFile(p,'a') as z:z.writestr('unknown.txt','SYNTHETIC')
        self.desc['owner_independent_backup_sha256']=sha(p.read_bytes())
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_only_known_metadata(self):
        p=Path(self.desc['backup_zip']);name='__MACOSX/._'+self.desc['roles']['inputs']
        with zipfile.ZipFile(p,'a') as z:z.writestr(name,struct.pack('>II',0x00051607,0x00020000)+b'\0'*18)
        self.desc['owner_independent_backup_sha256']=sha(p.read_bytes());verify_seven(self.root,self.desc)
    def test_malformed_metadata(self):
        p=Path(self.desc['backup_zip']);name='__MACOSX/._'+self.desc['roles']['inputs']
        with zipfile.ZipFile(p,'a') as z:z.writestr(name,b'bad')
        self.desc['owner_independent_backup_sha256']=sha(p.read_bytes())
        with self.assertRaises(Stop):verify_seven(self.root,self.desc)
    def test_human_pending(self):
        self.human['source_resolutions'][0]['permitted_local_eval']=None
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_gold_owner_attestation_does_not_cover_semantics(self):
        self.human['global_scenario_family_scan_complete']=False
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_provenance_rights_resolution_cannot_be_omitted(self):
        self.human['source_resolutions']=[]
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_provenance_hash_binding(self):
        self.human['source_resolutions'][0]['provenance_sha256']='0'*64
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_lineage_binding(self):
        self.human['records'][0]['lineage_entry_sha256']='0'*64
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_family_collision_is_stop(self):
        self.human['records'][0]['family_id']=self.human['records'][1]['family_id']
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_language_quota(self):
        self.human['records'][0]['language']='ru'
        with self.assertRaises(Stop):private_eval(self.files,self.human)
    def test_no_id_based_semantic_clearance(self):
        rows=private_eval(self.files,self.human)
        train=[{'sample_id':'D7-12345678','text':'Entirely separate synthetic structural sample here','family_id':'FAM-12345678'}]
        self.assertEqual(cross_split(train,rows,{})['status'],'HOLD')
    def test_cross_only_train_ids(self):
        rows=private_eval(self.files,self.human)
        train=[{**rows[0],'sample_id':'D7-12345678'}];result=cross_split(train,rows,{})
        self.assertEqual(result,{'status':'HOLD','excluded_count':1,'excluded_train_valid_ids':['D7-12345678']})
    def test_blank_consent_denies_before_reader(self):
        p=self.root/'consent.json';save_new(p,{})
        with patch('router.workflow.verify_seven') as reader:
            with self.assertRaises(Stop):gate(p,self.root,'A_B','release',{})
            reader.assert_not_called()
    def test_workflow_blank_consent_stops_before_private_or_model_read(self):
        from router.workflow import run_owner
        release=self.root/'release';release.mkdir(mode=0o700);(release/'day-07').mkdir(mode=0o700)
        prompt=release/'day-07/prompt.txt';prompt.write_text('SYNTHETIC')
        (release/'SHA256SUMS.txt').write_text(sha(prompt.read_bytes())+'  day-07/prompt.txt\n')
        consent=self.root/'empty_consent.json';save_new(consent,{})
        request=self.root/'request.json';save_new(request,{'scope':'A_B','consent':str(consent),'output_root':str(self.root)})
        with patch('router.workflow.verify_seven') as reader,patch('router.mlxrun.prepare') as model:
            with self.assertRaises(Stop):run_owner(request,release)
            reader.assert_not_called();model.assert_not_called()
    def test_release_drift_stop(self):
        from router.workflow import code_release
        p=self.root/'public.txt';p.write_text('SYNTHETIC')
        (self.root/'SHA256SUMS.txt').write_text('0'*64+'  public.txt\n')
        with self.assertRaises(Stop):code_release(self.root)
    def test_scope_binding_and_replay(self):
        p=self.root/'consent.json';c={'scope':'A_B','release_sha256':'release','input_commitment':digest({}),
          'control_review_ref':'TEST_DOUBLE','owner_actor':'TEST_DOUBLE','timestamp':'2000-01-01',
          'consent_id':'TEST_DOUBLE_ONE','human_confirmed':True,'private_local_no_shared_or_sync':True,'residual_risk_accepted':True}
        save_new(p,c)
        with self.assertRaises(Stop):gate(p,self.root,'TRAIN','release',{})
        with self.assertRaises(Stop):gate(p,self.root,'A_B','drift',{})
        with self.assertRaises(Stop):gate(p,self.root,'A_B','release',{'drift':True})
        gate(p,self.root,'A_B','release',{})
        with self.assertRaises(FileExistsError):gate(p,self.root,'A_B','release',{})
    def test_freeze_is_new_file_only(self):
        before={k:sha((self.root/v).read_bytes()) for k,v in self.desc['roles'].items()}
        rows=private_eval(self.files,self.human);safe=freeze_new(self.root,self.files,rows,self.human)
        self.assertEqual(safe['native_custody'],'NOT_CLAIMED')
        self.assertEqual(before,{k:sha((self.root/v).read_bytes()) for k,v in self.desc['roles'].items()})
        with self.assertRaises(FileExistsError):freeze_new(self.root,self.files,rows,self.human)
    def test_smoke_explicit_simulation(self):
        s=smoke();self.assertEqual(s['training'],'SIMULATED_NOT_MLX');self.assertEqual(s['real_training'],'NOT_RUN')

class RuntimeOffline(unittest.TestCase):
    def test_consent_draft_never_grants(self):
        from router.cli import main
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();root.chmod(0o700);q=root/'q.json';out=root/'consent.json'
            save_new(q,{'scope':'TRAIN','consent':str(out),'output_root':str(root)})
            with patch('router.workflow.code_release',return_value='SYNTHETIC'),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['consent-draft',str(q),str(out)]),0)
            self.assertIsNone(read_json(out)['human_confirmed'])
            with self.assertRaises(Stop):gate(out,root,'TRAIN','SYNTHETIC',{'scope':'TRAIN','output_root':str(root)})
    class Tokenizer:
        # Toy token IDs, not model tokens. Prefix=[101]; EOS=999.
        model_max_length=2048;eos_token_ids={999};chat_template='SYNTHETIC'
        broken=False;too_long=False;tail=False
        def encode(self,s,add_special_tokens=False):return [len(s)]
        def decode(self,tokens,**kw):return 'unexpected' if self.tail else ''
        def apply_chat_template(self,messages,**kw):
            if messages[-1]['role']=='assistant':
                return ([102] if self.broken else [101])+[len(messages[-1]['content']),999]+([1]*513 if self.too_long else [])
            return [101]
    def test_tokenizer_prefix_mask_label_eos(self):
        r={'text':'SYNTHETIC request','label':'TEST'}
        s=token_checks(self.Tokenizer(),[r],'SYNTHETIC prompt');self.assertEqual(s['max_full_tokens'],3)
    def test_tokenizer_bad_prefix_stops(self):
        tok=self.Tokenizer();tok.broken=True
        with self.assertRaises(Stop):token_checks(tok,[{'text':'SYNTHETIC','label':'TEST'}],'SYNTHETIC')
    def test_tokenizer_overlong_stops(self):
        tok=self.Tokenizer();tok.too_long=True
        with self.assertRaises(Stop):token_checks(tok,[{'text':'SYNTHETIC','label':'TEST'}],'SYNTHETIC')
    def test_tokenizer_unexpected_tail_stops(self):
        tok=self.Tokenizer();tok.tail=True
        with self.assertRaises(Stop):token_checks(tok,[{'text':'SYNTHETIC','label':'TEST'}],'SYNTHETIC')
    def test_raw_has_no_task_instruction(self):
        class Recorder(self.Tokenizer):
            def apply_chat_template(self,messages,**kw):self.messages=messages;return [101]
        tok=Recorder();r={'text':'SYNTHETIC no real eval'}
        prompts(tok,[r],'FROZEN_TASK_INSTRUCTIONS','A')
        self.assertEqual(tok.messages,[{'role':'user','content':r['text']}])
        prompts(tok,[r],'FROZEN_TASK_INSTRUCTIONS','B')
        self.assertEqual(tok.messages[0],{'role':'system','content':'FROZEN_TASK_INSTRUCTIONS'})
    def test_off_platform_stops(self):
        with patch('router.mlxrun.sys.platform','linux'):
            with self.assertRaises(Stop):environment()
    def test_missing_model_no_download(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Stop):model_inventory(Path(td)/'missing')
    def test_frozen_training_plan(self):
        self.assertEqual(TRAIN['iters'],3*200//TRAIN['batch_size'])
        self.assertEqual(TRAIN['val_batches'],-1);self.assertTrue(TRAIN['mask_prompt'])
        self.assertNotIn('resume_adapter_file',TRAIN)
    def test_cli_does_not_leak_bad_command(self):
        p=subprocess.run([sys.executable,'-B',str(DAY/'run.py'),'PRIVATE_SYNTHETIC_SECRET_COMMAND'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertEqual(p.stderr,'')
        self.assertNotIn('PRIVATE_SYNTHETIC_SECRET_COMMAND',p.stdout);self.assertNotIn('Traceback',p.stdout)

if __name__=='__main__':unittest.main()
