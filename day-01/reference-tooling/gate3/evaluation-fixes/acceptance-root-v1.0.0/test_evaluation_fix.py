"""Offline E1 guards; pytest/app-server/model are not executed."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_acceptance_e1', HERE / 'evaluate_acceptance.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class Blocked(ValueError):
    pass


def require(value, code):
    if not value:
        raise Blocked(code)


class E1Tests(unittest.TestCase):
    def test_only_frozen_file_with_explicit_collection_boundaries(self):
        work, tests = Path('/lab/workspaces/v1'), Path('/lab/control/acceptance')
        args = f.command(work, tests)
        self.assertEqual(args[args.index('--rootdir') + 1], str(tests))
        self.assertEqual(args[args.index('--confcutdir') + 1], str(tests))
        self.assertEqual(args[args.index('-c') + 1], str(work / 'pyproject.toml'))
        self.assertEqual(args[-1], str(tests / 'test_status_contract.py'))
        self.assertIn('no:cacheprovider', args)
        self.assertIn('addopts=--strict-config --strict-markers', args)

    def test_summary_requires_exit_zero_and_all_17_cases(self):
        output = 'collected 17 items\n' + 'case PASSED\n' * 17 + '17 passed in 0.4s\n'
        self.assertTrue(f.outcome({'exitCode': 0, 'stdout': output}))
        self.assertFalse(f.outcome({'exitCode': 4, 'stdout': output}))
        self.assertFalse(f.outcome({'exitCode': False, 'stdout': output}))
        self.assertFalse(f.outcome({'exitCode': 0, 'stdout': output.replace('17 passed', '16 passed, 1 skipped')}))
        self.assertFalse(f.outcome({'exitCode': 0, 'stdout': '17 passed'}))

    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        lab = Path(temp.name)
        work = lab / 'workspaces/v1'
        work.mkdir(parents=True)
        path = work / 'generated.py'
        path.write_text('unchanged captured source\n')
        snapshot = {'generated.py': f.sha(path)}
        g = SimpleNamespace(workspace_files=lambda p: [x.name for x in p.iterdir() if x.is_file()],
                            digest=f.sha, verify_lab=lambda *a, **k: work, venv_snapshot=lambda p: {})
        m = SimpleNamespace(require=require, encoded=lambda v: b'{}', e=SimpleNamespace(sha=lambda v: hashlib.sha256(v).hexdigest()))
        metadata = {'venv_sha256': hashlib.sha256(b'{}').hexdigest()}
        return m, g, lab, work, snapshot, metadata

    def test_unchanged_capture_is_allowed(self):
        m, g, lab, work, snapshot, metadata = self.fixture()
        f.unchanged(m, g, lab, 'v1', work, snapshot, metadata)

    def test_modified_generated_code_is_blocked(self):
        m, g, lab, work, snapshot, metadata = self.fixture()
        (work / 'generated.py').write_text('manual edit\n')
        with self.assertRaisesRegex(Blocked, 'CODE_CHANGED_AFTER_CAPTURE'):
            f.unchanged(m, g, lab, 'v1', work, snapshot, metadata)

    def test_added_file_is_blocked(self):
        m, g, lab, work, snapshot, metadata = self.fixture()
        (work / 'extra.py').write_text('manual addition\n')
        with self.assertRaisesRegex(Blocked, 'CAPTURE_FILE_SET_CHANGED'):
            f.unchanged(m, g, lab, 'v1', work, snapshot, metadata)

    def test_frozen_test_hash_matches_approved_source(self):
        self.assertEqual(f.sha(f.ROOT / 'gate2/acceptance/test_status_contract.py'), f.ACCEPTANCE_SHA)

    def test_dependency_snapshot_drift_is_blocked(self):
        m, g, lab, work, snapshot, metadata = self.fixture()
        metadata['venv_sha256'] = 'changed'
        with self.assertRaisesRegex(Blocked, 'VENV_CHANGED_AFTER_CAPTURE'):
            f.unchanged(m, g, lab, 'v1', work, snapshot, metadata)


if __name__ == '__main__':
    unittest.main()
