"""E1: evaluate frozen acceptance on captured code; no model methods permitted."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LAUNCHER_SHA = '65dbff56253a94c1698b118d3afd691dbf6c558cdb60187fcf9539b7c81f5b42'
ACCEPTANCE_SHA = '1d085031c337416f77e87af09af51c7503c53d98f84a335e16b0c71ea735054f'


def sha(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError('INPUT_MISSING_OR_LINKED')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(work: Path, tests: Path) -> list[str]:
    return [str(work / '.venv/bin/python'), '-m', 'pytest', '-vv',
            '-c', str(work / 'pyproject.toml'), '--rootdir', str(tests),
            '--confcutdir', str(tests), '-p', 'no:cacheprovider',
            '-o', 'addopts=--strict-config --strict-markers', str(tests / 'test_status_contract.py')]


def outcome(value: dict) -> bool:
    stdout = value.get('stdout', '')
    return (type(value.get('exitCode')) is int and value['exitCode'] == 0
            and isinstance(stdout, str)
            and re.search(r'\bcollected 17 items\b', stdout) is not None
            and re.search(r'\b17 passed\b', stdout) is not None
            and len(re.findall(r'\bPASSED\b', stdout)) == 17)


def load_launcher():
    manifest = json.loads((HERE / 'manifest.json').read_bytes())
    for name, expected in manifest['files'].items():
        if Path(name).name != name or sha(HERE / name) != expected:
            raise ValueError('E1_PACKAGE_CHANGED')
    if sha(ROOT / 'gate3/launcher-r1.0.2/launcher-manifest.json') != LAUNCHER_SHA:
        raise ValueError('LAUNCHER_MANIFEST_CHANGED')
    sys.path.insert(0, str(ROOT / 'gate3/launcher-r1.0.2'))
    spec = importlib.util.spec_from_file_location('e1_accepted_launcher', ROOT / 'gate3/launcher-r1.0.2/launcher.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.package()
    return m


def unchanged(m, g, lab: Path, variant: str, work: Path, captured: dict, metadata: dict) -> None:
    m.require(set(g.workspace_files(work)) == {n for n, value in captured.items() if value != 'DELETED'}, 'CAPTURE_FILE_SET_CHANGED')
    for name, value in captured.items():
        path = work / name
        if value == 'DELETED':
            m.require(not path.exists() and not path.is_symlink(), 'DELETED_CAPTURE_FILE_REAPPEARED')
        else:
            m.require(isinstance(value, str) and not path.is_symlink() and g.digest(path) == value, 'CODE_CHANGED_AFTER_CAPTURE')
    g.verify_lab(lab, variant, allow_generated=True, allow_rules_v2=variant == 'v2')
    m.require(m.e.sha(m.encoded(g.venv_snapshot(work / '.venv'))) == metadata['venv_sha256'], 'VENV_CHANGED_AFTER_CAPTURE')


def execute(m, lab: Path, variant: str, cli: str) -> dict:
    _, p, g = m.package()
    m.require(lab.is_absolute() and lab.is_dir() and not lab.is_symlink(), 'LAB_UNAVAILABLE')
    base = lab / 'evidence' / variant
    for name in ('run', 'capture', 'evaluation-logs'):
        g.verify_map(base / name, m.read(base / name / 'manifest.json'))
    metadata = m.read(base / 'run/metadata.json')
    m.require(metadata.get('status') == 'CAPTURED_PENDING_EVALUATION'
              and metadata.get('generation_invocations') == 1 and metadata.get('exit_code') == 0
              and metadata.get('protected_inputs_after_capture') == 'PASS'
              and metadata.get('capture', {}).get('complete') is True
              and metadata.get('native_trace', {}).get('complete') is True
              and metadata.get('launcher_manifest_sha256') == LAUNCHER_SHA, 'COMPLETE_ORIGINAL_GENERATION_REQUIRED')
    work = g.verify_lab(lab, variant, allow_generated=True, allow_rules_v2=variant == 'v2')
    captured = m.read(base / 'capture/files.json')
    m.require(not m.read(base / 'capture/omissions.json'), 'INCOMPLETE_CAPTURE')
    unchanged(m, g, lab, variant, work, captured, metadata)
    tests = lab / 'control/acceptance'
    m.require(sha(tests / 'test_status_contract.py') == ACCEPTANCE_SHA
              and g.acceptance_count(tests / 'test_status_contract.py') == 17, 'FROZEN_ACCEPTANCE_CHANGED')
    plan = m.read(lab / 'launcher-r1.0.2' / variant / 'plan.json')
    initial = m.read(base / 'initial-inputs.json')
    m.require(sha(lab / 'launcher-r1.0.2' / variant / 'plan.json') == metadata['plan_sha256'], 'ORIGINAL_PLAN_CHANGED')
    policy = p.candidate_policy(lab, variant, [n for n in initial['baseline'] if not n.startswith('src/')] + list(initial['overlay']))
    m.require(p.policy_fingerprint(policy, lab, variant) == plan['r1_variant']['policy_sha256'], 'R1_POLICY_DRIFT')
    m.require(g.digest(Path(cli).resolve()) == plan['codex_binary_sha256']
              and g.run([cli, '--version']).stdout.strip() == b'codex-cli 0.163.0', 'CODEX_BINARY_DRIFT')
    folder = base / 'acceptance-root-v1.0.0'
    folder.mkdir(mode=0o700)  # Existing original evaluations are preserved.
    wire = None
    report = {'status': 'BLOCKED', 'variant': variant, 'generation_invocations_by_evaluator': 0,
              'turn_start_requests': 0, 'thread_start_requests': 0,
              'model_isolation_proof': False, 'permission_profile': p.PROFILE,
              'policy_sha256': plan['r1_variant']['policy_sha256'],
              'original_run_manifest_sha256': sha(base / 'run/manifest.json'),
              'original_evaluation_sha256': sha(base / 'evaluation.json'),
              'acceptance_sha256': ACCEPTANCE_SHA, 'tool_manifest_sha256': sha(HERE / 'manifest.json'),
              'command': command(work, tests), 'test_changes': False, 'permission_changes': False}
    try:
        request = {'command': command(work, tests), 'cwd': str(work), 'permissionProfile': p.PROFILE, 'timeoutMs': 120000}
        wire = m.Wire(cli, work, g.environment(lab, variant), policy, p, folder, [request])
        wire.initialize()
        config = wire.request('config/read', {'cwd': str(work), 'includeLayers': True})
        m.require(g.runtime_config(config['config'], work) == plan['r1_variant']['effective_config'], 'EFFECTIVE_CONFIG_DRIFT')
        m.require(p.profiles(wire, work), 'PROFILE_UNAVAILABLE')
        result = wire.request('command/exec', request)
        m.e.write_json(folder / 'acceptance.json', result)
        report.update(status='PASS' if outcome(result) else 'FAIL', pytest_exit_code=result.get('exitCode'),
                      cases_passed=17 if outcome(result) else None)
    except BaseException as error:
        code = str(error) if type(error).__name__ == 'Blocked' else 'E1_EXECUTION_ERROR'
        report.update(status='BLOCKED', error_code=code if re.fullmatch(r'[A-Z0-9_]+', code) else 'E1_EXECUTION_ERROR')
    finally:
        if wire is not None:
            m.close(wire, report)
            report['requests_sent'] = dict(wire.sent)
            if wire.attempted.get('turn/start') or wire.attempted.get('thread/start'):
                report.update(status='BLOCKED', error_code='UNEXPECTED_MODEL_METHOD')
        try:
            unchanged(m, g, lab, variant, work, captured, metadata)
            m.require(sha(tests / 'test_status_contract.py') == ACCEPTANCE_SHA, 'FROZEN_ACCEPTANCE_CHANGED')
            g.verify_map(base / 'run', m.read(base / 'run/manifest.json'))
            g.verify_map(base / 'capture', m.read(base / 'capture/manifest.json'))
            report['capture_and_protected_inputs_after_evaluation'] = 'PASS'
        except BaseException:
            report.update(status='BLOCKED', error_code='INPUT_OR_CAPTURE_CHANGED')
        m.e.write_json(folder / 'report.json', report)
        m.e.seal(folder)
    return {k: report.get(k) for k in ('status', 'cases_passed', 'pytest_exit_code', 'generation_invocations_by_evaluator', 'error_code')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--lab', type=Path)
    parser.add_argument('--variant', choices=('v1', 'v2'))
    args = parser.parse_args()
    try:
        m = load_launcher()
        if args.verify:
            print(json.dumps({'status': 'PASS', 'generation_invocations': 0}))
            return 0
        m.require(args.lab is not None and args.variant is not None, 'MISSING_REQUIRED_INPUT')
        m.require(platform.system() == 'Darwin' and platform.python_version() == '3.13.3', 'MAC_PYTHON_REQUIRED')
        cli = shutil.which('codex')
        m.require(cli is not None, 'CODEX_NOT_FOUND')
        result = execute(m, args.lab, args.variant, str(Path(cli).resolve()))
        folder = args.lab / 'evidence' / args.variant / 'acceptance-root-v1.0.0'
        target = folder.parent / (folder.name + '.zip')
        entries = []
        for path in sorted(folder.iterdir()):
            m.require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1
                      and not m.e.forbidden(path.name), 'UNSAFE_E1_EVIDENCE')
            data = path.read_bytes()
            m.require(not m.e.secret(data), 'SECRET_SIGNATURE_IN_E1_EVIDENCE')
            entries.append((path.name, data))
        with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in entries:
                archive.writestr('acceptance-root-v1.0.0/' + name, data)
        result['evidence_zip'] = str(target)
        result['evidence_zip_sha256'] = sha(target)
        print(json.dumps(result))
        return int(result['status'] != 'PASS')
    except BaseException as error:
        code = str(error) if re.fullmatch(r'[A-Z0-9_]+', str(error)) else 'E1_INPUT_OR_CAPABILITY_ERROR'
        print(json.dumps({'status': 'BLOCKED', 'error_code': code, 'generation_invocations_by_evaluator': 0}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
