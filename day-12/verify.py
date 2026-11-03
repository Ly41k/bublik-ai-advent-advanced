"""Offline input/plan integrity admission. Never contacts a model or a network."""
import json
from pathlib import Path
from agent import ROOT, build_request, load_json, sha
from defenses import MODES


def verify(root=ROOT):
    manifest = load_json(root / 'fixtures' / 'SHA256SUMS.json')
    expected_files = {'cases.json', 'references.json', 'email_attack.html', 'email_clean.html',
        'document_attack.html', 'document_clean.html', 'web_attack.md', 'web_clean.md'}
    if set(manifest) != expected_files:
        raise ValueError('Fixture manifest inventory mismatch')
    for name, digest in manifest.items():
        path = root / 'fixtures' / name
        if path.is_symlink() or sha(path.read_bytes()) != digest:
            raise ValueError('Fixture drift: ' + name)
    actual = {p.name for p in (root / 'fixtures').iterdir() if p.is_file()}
    if actual != expected_files | {'SHA256SUMS.json'}:
        raise ValueError('Unexpected fixture files')
    lock = load_json(root / 'INPUT_LOCK.json')
    if set(lock) != {'FIXTURE_CONTRACT.json', 'RUN_MATRIX.csv', 'fixtures/SHA256SUMS.json'}:
        raise ValueError('Input lock inventory mismatch')
    for name, digest in lock.items():
        path = root / name
        if name not in {'FIXTURE_CONTRACT.json', 'RUN_MATRIX.csv', 'fixtures/SHA256SUMS.json'} or path.is_symlink() or sha(path.read_bytes()) != digest:
            raise ValueError('Input lock mismatch: ' + name)
    contract = load_json(root / 'FIXTURE_CONTRACT.json')
    config = load_json(root / 'fixtures' / 'cases.json')
    if config['_model'] != contract['model'] or config['_options'] != contract['model_options']:
        raise ValueError('Model configuration drift')
    for case in contract['cases']:
        if config[case['id']]['task'] != case['task']:
            raise ValueError('Original task drift')
    from runner import rows
    matrix = rows(root)
    case_types = {c['id']: c['source_type'] for c in contract['cases']}
    expected = {(case, mode, 'attack') for case in case_types for mode in MODES}
    expected |= {(case, mode, 'clean_control') for case in case_types for mode in ('BASELINE', 'ALL')}
    found, ids, stable = set(), set(), {}
    for row in matrix:
        key = (row['case'], row['mode'], row['run_type'])
        expected_id = row['case'] + ('_CONTROL' if row['run_type'] == 'clean_control' else '') + '_' + row['mode']
        stage = 'G2' if row['mode'] == 'BASELINE' else 'G5'
        if (key in found or row['id'] in ids or key not in expected or row['id'] != expected_id
                or row['source'] != case_types[row['case']] or row['owner_stage'] != stage
                or row['expected_state'] != 'NOT_RUN'):
            raise ValueError('Invalid matrix row')
        found.add(key)
        ids.add(row['id'])
        item = build_request(row, root)
        stable_key = row['case'], row['run_type']
        hashes = item['source_sha256'], item['task_sha256']
        if stable_key in stable and stable[stable_key] != hashes:
            raise ValueError('Source/task changed across defense modes')
        stable[stable_key] = hashes
    if len(matrix) != 21 or found != expected:
        raise ValueError('21-row matrix mismatch')
    return {'status': 'PASS', 'fixture_files_verified': len(manifest),
            'planned_observations': len(matrix), 'live_observations': 'NOT_RUN',
            'network_calls': 0, 'source_task_stability': 'PASS'}


def verify_evidence(directory):
    """Read-only verification for one finished observation directory."""
    directory = Path(directory)
    manifest = load_json(directory / 'manifest.json')
    listed = manifest['files']
    if {p.name for p in directory.iterdir()} != set(listed) | {'manifest.json'}:
        raise ValueError('Evidence inventory mismatch')
    for name, info in listed.items():
        if Path(name).name != name:
            raise ValueError('Unsafe evidence entry')
        path = directory / name
        if path.is_symlink():
            raise ValueError('Evidence symlink')
        data = path.read_bytes()
        if sha(data) != info['sha256'] or len(data) != info['size_bytes']:
            raise ValueError('Evidence hash/size mismatch')
    result = load_json(directory / 'result.json')
    if result.get('synthetic') and (result['observation_status'] != 'NOT_RUN'
                                  or result['pipeline_verdict'] != 'NOT_RUN'
                                  or result['result_origin'] != 'SYNTHETIC_TEST_ONLY'):
        raise ValueError('Synthetic result mislabelled')
    for artifact, key in [('source.bin', 'source_sha256'), ('request.json', 'request_sha256'),
                          ('raw-response.json', 'raw_response_sha256')]:
        if key in result and sha((directory / artifact).read_bytes()) != result[key]:
            raise ValueError('Evidence provenance mismatch: ' + key)
    final_path = directory / 'final-answer.txt'
    final = result.get('final_exposed_answer')
    if (final is None and final_path.exists()) or (final is not None and
            (not final_path.exists() or final_path.read_bytes() != final.encode('utf-8'))):
        raise ValueError('Evidence final-answer mismatch')
    return {'status': 'PASS', 'files_verified': len(listed)}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
