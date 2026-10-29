"""R2 structural fixtures; all human/grant positives here are explicit TEST DOUBLES."""
import copy,csv,io,json,os,struct,tempfile,types,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from router.core import *
from router.owner import *
from router.data import *
from router.synthetic import fixture

ROOT=Path(__file__).resolve().parents[2]

def fake_train():
    rows=[];lineage=[]
    for i in range(240):
        text='SYNTHETIC TRAIN FIXTURE '+' '.join(sha(f'R2-fixture-{i}-{j}'.encode())[:12] for j in range(8))
        sid=f'D7-{70000000+i:08d}';fam=f'FAM-{70000000+i:08d}';ref='SRC-00000002' if i%10==0 else 'SRC-00000001'
        r=dict(schema_version='d7-record-v1.1',sample_id=sid,text=text,label=LABELS[i//40],language='en' if i%40<24 else 'ru',
          domain='general_dev',origin='public_bublik_derived' if i%10==0 else 'synthetic',source_ref=ref,family_id=fam,
          split='valid' if i%6==0 else 'train',label_policy_version='labels-v1.1',review_status='pending',
          text_sha256=sha(text.encode()),fingerprint_sha256=sha(normalize(text).encode()),lineage_ref=sid,review_ref=sid,rights_ref=ref)
        rows.append(r);lineage.append({'sample_id':sid,'family_id':fam,'all_source_refs':list(dict.fromkeys(['SRC-00000001',ref]))})
    return rows,lineage

def fake_sources(rows,lineage):
    src=source_templates(rows,lineage,[{'source_ref':r} for r in ('SRC-00000001','SRC-00000002')])
    for s in src:s.update(actor_kind='human',rights_attester_id='SYNTHETIC_TEST_DOUBLE',evidence_ref='SYNTHETIC_TEST_DOUBLE',
        decision_by='SYNTHETIC_TEST_DOUBLE',decision_time='2000-01-01T00:00:00Z',source_version='SYNTHETIC_TEST_VERSION',
        source_claim='SYNTHETIC_TEST_DOUBLE',underlying_material='SYNTHETIC_TEST_DOUBLE',claim_scope='ALL_BOUND_LINKED_ROWS',
        permitted_local_training=True,permitted_derivative_use=True,privacy_review_status='PASS',permitted_publication='denied')
    return src

class CodecR2(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='R2_SYNTHETIC_ONLY_');self.p=Path(self.t.name).resolve()
        self.desc,self.human,self.files=fixture(self.p)
    def tearDown(self):self.t.cleanup()
    def test_source_generator_actual_serializer_compatible_without_network(self):
        # Read PUBLIC SOURCE bytes only, then inject the generation function. No Ollama/model calls.
        if not (ROOT/'reference/BUBLIK-D7-G2A-OWNER-LOCAL-KIT-R1.zip').exists():
            self.skipTest('PUBLIC_REFERENCE_NOT_PUBLISHED; not codec admission PASS')
        with zipfile.ZipFile(ROOT/'reference/BUBLIK-D7-G2A-OWNER-LOCAL-KIT-R1.zip') as z:
            source=z.read(next(n for n in z.namelist() if n.endswith('/owner_local_eval_draft.py')))
        mod=types.ModuleType('SYNTHETIC_REFERENCE_SOURCE')
        exec(compile(source,'public_owner_generator_reference.py','exec'),mod.__dict__)
        def fake(model,label,lang,domain,recent,seed):
            return 'SYNTHETIC REFERENCE FIXTURE '+' '.join(sha(f'ref-{len(recent)}-{i}'.encode())[:10] for i in range(8))
        with patch.object(mod,'http_json',side_effect=AssertionError('NETWORK_FORBIDDEN')):
            a,b,c,d=mod.build_rows(fake,'SYNTHETIC_TEST_MODEL')
            out=self.p/'generator_output'
            with patch.object(mod,'ensure_private_dir',side_effect=lambda p:p.mkdir(mode=0o700)):
                mod.save_draft(out,a,b,c,d,'SYNTHETIC_TEST_MODEL','SYNTHETIC_TEST_DIGEST')
        roles=dict(ROLES);data={k:(out/n).read_bytes() for k,n in roles.items() if k!='normalized_review'}
        normalized=[{**r,'review_decision':'PASS','final_label':r['proposed_label'],
            'reviewer':'SYNTHETIC_TEST_DOUBLE','reviewed_at':'2000-01-01T00:00:00Z'} for r in c]
        data['normalized_review']=mod.csvbytes(normalized)
        inputs,gold,prov,meta=decode_owner_files(data)
        self.assertEqual(len(inputs),60);self.assertIsInstance(prov,dict)
        self.assertTrue(all(m['rights_ref']==m['lineage_ref']=='PENDING' for m in meta))
    def test_template_never_repeats_gold_approval(self):
        h=eval_review_template(self.files)
        self.assertTrue(all('gold_review' not in r and 'label' not in r for r in h['records']))
        self.assertTrue(all(r['family_id']==r['language']==r['semantic_family']=='' for r in h['records']))
        self.assertIsNone(h['source_resolutions'][0]['permitted_local_eval'])
        self.assertFalse('all_pairs_semantic_review_complete' in h)
    def test_list_provenance_rejected(self):
        f=copy.deepcopy(self.files);f['provenance']=encoded([parse(f['provenance'])])
        with self.assertRaises(Stop):decode_owner_files(f)
    def test_provisional_not_authoritative(self):
        _,_,prov,meta=decode_owner_files(self.files)
        self.assertNotIn('source_ref',prov);self.assertNotIn('all_source_refs',meta[0])
        with self.assertRaises(Stop):private_eval(self.files,eval_review_template(self.files))
    def test_fake_pending_to_pass_in_original_rejected(self):
        f=copy.deepcopy(self.files);mm=[parse(l) for l in f['lineage'].splitlines()];mm[0]['rights_ref']='PASS'
        f['lineage']=b''.join(encoded(m)+b'\n' for m in mm)
        with self.assertRaises(Stop):decode_owner_files(f)
    def test_metadata_model_mismatch(self):
        f=copy.deepcopy(self.files);mm=[parse(l) for l in f['lineage'].splitlines()];mm[0]['generator_model']='OTHER'
        f['lineage']=b''.join(encoded(m)+b'\n' for m in mm)
        with self.assertRaises(Stop):decode_owner_files(f)
    def test_metadata_text_hash_drift(self):
        f=copy.deepcopy(self.files);mm=[parse(l) for l in f['lineage'].splitlines()];mm[0]['text_sha256']='0'*64
        f['lineage']=b''.join(encoded(m)+b'\n' for m in mm)
        with self.assertRaises(Stop):decode_owner_files(f)
    def test_historical_gold_reused_not_independently_claimed(self):
        self.assertEqual(len(private_eval(self.files,self.human)),60)
        self.assertNotIn('gold_review_verified',self.human)
        self.assertNotIn('gold_review',self.human['records'][0])
    def test_history_incomplete_or_correction_stops(self):
        for replacement in (b'CORRECT',b'REJECT',b'ADJUDICATION_REQUIRED'):
            f=copy.deepcopy(self.files);f['normalized_review']=f['normalized_review'].replace(b'PASS',replacement,1)
            with self.assertRaises(Stop):decode_owner_files(f)
    def test_history_duplicate_header(self):
        f=copy.deepcopy(self.files);f['normalized_review']=b'sample_id,sample_id\nX,X\n'
        with self.assertRaises(Stop):decode_owner_files(f)
    def test_duplicate_provisional_ids_do_not_grant_final_family(self):
        h=copy.deepcopy(self.human);h['records'][0]['family_id']=''
        with self.assertRaises(Stop):private_eval(self.files,h)
    def test_ledger_is_new_and_hash_bound(self):
        from router.workflow import _frozen
        rows=private_eval(self.files,self.human);freeze_new(self.p,self.files,rows,self.human)
        save_new(self.p/'descriptor.json',self.desc);save_new(self.p/'human.json',self.human)
        q={'eval_root':str(self.p),'seven_descriptor':str(self.p/'descriptor.json'),'eval_human_review':str(self.p/'human.json'),
           'freeze_file':str(self.p/'EVAL_FREEZE.private.json')}
        _frozen(q)
        with (self.p/'EVAL_REVIEW_LEDGER.private.jsonl').open('ab') as f:f.write(b'\n')
        with self.assertRaisesRegex(Stop,'FROZEN_REVIEW_LEDGER_DRIFT'):_frozen(q)
    def _zip(self,sidecar=None,payload=None):
        prefix='eval-draft-SYNTHETIC/'
        backup=Path(self.desc['backup_zip'])
        with zipfile.ZipFile(backup,'w') as z:
            z.writestr(prefix,b'');z.writestr('__MACOSX/',b'');z.writestr('__MACOSX/'+prefix,b'')
            for role,b in self.files.items():
                z.writestr(prefix+ROLES[role],b)
                z.writestr('__MACOSX/'+prefix+'._'+ROLES[role],struct.pack('>II',0x00051607,0x00020000)+b'\0'*18)
            z.writestr(sidecar or '__MACOSX/._eval-draft-SYNTHETIC',payload if payload is not None else struct.pack('>II',0x00051607,0x00020000)+b'\0'*18)
        self.desc.update(zip_prefix=prefix,owner_independent_backup_sha256=sha(backup.read_bytes()))
    def test_root_and_seven_appledouble(self):
        self._zip();files,_=verify_seven(self.p,self.desc);self.assertEqual(files,self.files)
    def test_wrong_root_sidecar(self):
        self._zip(sidecar='__MACOSX/._other-root')
        with self.assertRaises(Stop):verify_seven(self.p,self.desc)
    def test_appledouble_v1_rejected(self):
        self._zip(payload=struct.pack('>II',0x00051607,0x00010000)+b'\0'*18)
        with self.assertRaises(Stop):verify_seven(self.p,self.desc)
    def test_appledouble_range_rejected(self):
        self._zip(payload=struct.pack('>II',0x00051607,0x00020000)+b'\0'*16+struct.pack('>HIII',1,9,1,10))
        with self.assertRaises(Stop):verify_seven(self.p,self.desc)
    def test_appledouble_oversize_rejected(self):
        self._zip(payload=b'X'*65537)
        with self.assertRaises(Stop):verify_seven(self.p,self.desc)
    def test_duplicate_zip_entry_rejected(self):
        self._zip();p=Path(self.desc['backup_zip'])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(p,'a') as z:z.writestr('eval-draft-SYNTHETIC/'+ROLES['inputs'],self.files['inputs'])
        self.desc['owner_independent_backup_sha256']=sha(p.read_bytes())
        with self.assertRaises(Stop):verify_seven(self.p,self.desc)

class AdmissionR2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows,cls.lineage=fake_train()
    def setUp(self):
        self.sources=fake_sources(self.rows,self.lineage);self.h=flagged_review_template(self.rows)
        self.cross={'status':'PASS','candidate_commitment':digest(self.rows),'eval_freeze_commitment':'SYNTHETIC_TEST_DOUBLE','excluded_train_valid_ids':[]}
    def test_no_240_signoffs_required_on_structural_fixtures(self):
        out=admit(self.rows,self.lineage,self.sources,self.h,self.cross)
        self.assertEqual(len(out),240);self.assertEqual(self.h['record_resolutions'],[])
        self.assertEqual(self.h['actor_kind'],'')
    def test_two_sources_once_each_not240(self):
        self.assertEqual(len(self.sources),2)
        self.assertEqual([s['linked_rows_count'] for s in self.sources],[240,24])
        self.assertEqual(Counter(r['source_ref'] for r in self.rows),{'SRC-00000001':216,'SRC-00000002':24})
        self.sources[1]['permitted_local_training']=None
        with self.assertRaises(Stop):admit(self.rows,self.lineage,self.sources,self.h,self.cross)
    def test_conditional_method_is_not_rights(self):
        blank=source_templates(self.rows,self.lineage,[{'source_ref':s['source_ref']} for s in self.sources])
        self.assertTrue(all(s['permitted_local_training'] is None for s in blank))
        with self.assertRaises(Stop):admit(self.rows,self.lineage,blank,self.h,self.cross)
    def test_source_commitment_drift(self):
        self.sources[0]['source_candidate_commitment']='0'*64
        with self.assertRaises(Stop):admit(self.rows,self.lineage,self.sources,self.h,self.cross)
    def test_declared_ambiguity_needs_human(self):
        self.h['declared_ambiguous_ids']=[self.rows[0]['sample_id']]
        with self.assertRaises(Stop):admit(self.rows,self.lineage,self.sources,self.h,self.cross)
    def test_resolved_ambiguity_not_240_reviews(self):
        r=self.rows[0];self.h.update(actor_kind='human',actor_id='SYNTHETIC_TEST_DOUBLE',timestamp='2000-01-01T00:00:00Z')
        self.h['declared_ambiguous_ids']=[r['sample_id']]
        self.h['record_resolutions']=[{'sample_id':r['sample_id'],'candidate_revision':digest(r),'decision':'PASS','label':r['label'],'rationale':'SYNTHETIC_TEST_DOUBLE'}]
        self.assertEqual(len(admit(self.rows,self.lineage,self.sources,self.h,self.cross)),240)
    def test_correct_does_not_auto_relabel(self):
        r=self.rows[0];self.h.update(actor_kind='human',actor_id='SYNTHETIC_TEST_DOUBLE',timestamp='2000-01-01')
        self.h['declared_ambiguous_ids']=[r['sample_id']]
        self.h['record_resolutions']=[{'sample_id':r['sample_id'],'candidate_revision':digest(r),'decision':'CORRECT','label':'TEST','rationale':'SYNTHETIC_TEST_DOUBLE'}]
        with self.assertRaises(Stop):admit(self.rows,self.lineage,self.sources,self.h,self.cross)
    def test_cross_global_scan_and_related_pairs_required(self):
        t=[{'sample_id':'D7-55555555','text':'SYNTHETIC one distinct text structure here','family_id':'FAM-55555555'}]
        e=[{'sample_id':'D7-99999999','text':'Completely independent synthetic fixture with other tokens','family_id':'FAM-99999999'}]
        h={'comparison_commitment':digest({'train':t,'eval':e}),'actor_kind':'human','actor_id':'SYNTHETIC_TEST_DOUBLE','timestamp':'2000-01-01',
           'global_scenario_family_scan_complete':True,'related_pairs_review_complete':True,'exclude_train_ids':[]}
        self.assertEqual(cross_split(t,e,h)['status'],'PASS')
        h['related_pairs_review_complete']=False
        self.assertEqual(cross_split(t,e,h)['status'],'HOLD')
    def test_near_flag_requires_bound_distinct_decision(self):
        t=[{'sample_id':'D7-55555555','text':'SYNTHETIC fixture cache loader alpha test case','family_id':'FAM-55555555'}]
        e=[{'sample_id':'D7-99999999','text':'SYNTHETIC fixture cache loader beta test case','family_id':'FAM-99999999'}]
        h=cross_review_template(t,e)
        self.assertEqual(len(h['pair_resolutions']),1)
        h.update(actor_kind='human',actor_id='SYNTHETIC_TEST_DOUBLE',timestamp='2000-01-01',
                 global_scenario_family_scan_complete=True,related_pairs_review_complete=True)
        self.assertEqual(cross_split(t,e,h)['status'],'HOLD')
        h['pair_resolutions'][0].update(decision='DISTINCT',rationale='SYNTHETIC_TEST_DOUBLE')
        self.assertEqual(cross_split(t,e,h)['status'],'PASS')
        h['pair_resolutions'][0]['pair_commitment']='0'*64
        self.assertEqual(cross_split(t,e,h)['status'],'HOLD')
    def test_exact_cannot_be_waived(self):
        t=[{'sample_id':'D7-55555555','text':'SYNTHETIC identical fixture text','family_id':'FAM-55555555'}]
        e=[{**t[0],'sample_id':'D7-99999999','family_id':'FAM-99999999'}]
        h=cross_review_template(t,e)
        h.update(actor_kind='human',actor_id='SYNTHETIC_TEST_DOUBLE',timestamp='2000-01-01',
                 global_scenario_family_scan_complete=True,related_pairs_review_complete=True)
        h['pair_resolutions'][0].update(decision='DISTINCT',rationale='SYNTHETIC_TEST_DOUBLE')
        self.assertEqual(cross_split(t,e,h)['excluded_train_valid_ids'],['D7-55555555'])

class SeedR2(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='R2_AUDIT_STRUCTURAL_');self.p=Path(self.t.name).resolve()/'accepted'
        rows,_=fake_train();self.rows=[{**r,'review_status':'validated'} for r in rows]
        export_accepted(self.p,self.rows,'SYNTHETIC PROMPT')
        self.a={'frame_commitment':digest(self.rows),'control_authorization_ref':'SYNTHETIC_TEST_DOUBLE',
                'seed_source':'OWNER_CSPRNG','owner_rng_authorized':True}
    def tearDown(self):self.t.cleanup()
    def test_seed_only_after_fixed_frame_then_blank30(self):
        self.assertFalse((self.p/'audit30.csv').exists())
        with patch('secrets.token_hex',return_value='a'*64):draw_audit(self.p,self.a)
        committed=read_json(self.p/'audit_seed.private.json');frame=read_json(self.p/'audit_frame.json')
        self.assertEqual(committed['seed'],frame['seed']);self.assertEqual(len(frame['ids']),30)
        with (self.p/'audit30.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        self.assertTrue(all(r['decision']==r['actor_kind']=='' for r in rows))
        with self.assertRaises(Stop):check_audit(self.p/'audit30.csv',self.rows,frame['ids'])
    def test_rng_not_authorized(self):
        self.a['owner_rng_authorized']=None
        with self.assertRaises(Stop):draw_audit(self.p,self.a)
    def test_frame_mismatch_before_rng(self):
        self.a['frame_commitment']='0'*64
        with patch('secrets.token_hex') as rng:
            with self.assertRaises(Stop):draw_audit(self.p,self.a)
            rng.assert_not_called()
    def test_no_redraw_after_seed(self):
        draw_audit(self.p,self.a)
        with patch('secrets.token_hex') as rng:
            with self.assertRaises(Stop):draw_audit(self.p,self.a)
            rng.assert_not_called()
    def test_control_seed(self):
        self.a.update(seed_source='CONTROL_PROVIDED',seed='SYNTHETIC_CONTROL_SEED_NOT_REAL')
        draw_audit(self.p,self.a)
        self.assertEqual(read_json(self.p/'audit_seed.private.json')['seed_source'],'CONTROL_PROVIDED')
    def test_preview_seed_is_not_actual_audit(self):
        self.a.update(seed_source='CONTROL_PROVIDED',seed='PREVIEW_ONLY_NOT_CONTROL_RANDOM_SEED')
        with self.assertRaises(Stop):draw_audit(self.p,self.a)
    def test_modified_export_stops_before_draw(self):
        (self.p/'training-data/train.jsonl').write_bytes(b'SYNTHETIC_CORRUPT')
        with self.assertRaises(Stop):draw_audit(self.p,self.a)
