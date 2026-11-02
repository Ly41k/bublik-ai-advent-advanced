#!/usr/bin/env python3
"""Offline integrity checks. No network, inference or evidence writeback."""
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
VERSIONS = ('V1', 'V2', 'V3')
IDS = ('control_credit', 'role_play', 'instruction_override', 'system_prompt_extraction')


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def wire(value):
    return json.dumps(value).encode()


def read_json(path):
    return json.loads(path.read_bytes())


def is_metadata(path):
    return any(part in ('.DS_Store', '__MACOSX', '__pycache__') or part.startswith('._')
               for part in PurePosixPath(path).parts) or str(path).endswith(('.pyc', '.pyo'))


def ignored_metadata(root=ROOT):
    return sorted(str(p.relative_to(root)) for p in root.rglob('*')
                  if p.is_file() and is_metadata(str(p.relative_to(root))))


def verify(root=ROOT):
    expected = {}
    for line in (root / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        rel = PurePosixPath(name)
        need(not rel.is_absolute() and '..' not in rel.parts and name not in expected, 'Unsafe/duplicate manifest path')
        need(not is_metadata(name), 'Metadata must not be in publication manifest')
        path = root / name
        need(path.is_file() and not path.is_symlink(), 'Missing/linked staging file: ' + name)
        need(sha(path.read_bytes()) == digest, 'SHA256 mismatch: ' + name)
        expected[name] = digest
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not is_metadata(str(p.relative_to(root)))}
    need(actual == set(expected) | {'SHA256SUMS.txt'}, 'Staging file inventory changed')
    fixtures = read_json(root / 'fixtures.json')
    need(tuple(fixtures['case_order']) == IDS, 'Case order changed')
    base = fixtures['requests_by_version']['V1']
    for ver in VERSIONS:
        prompt = (root / ('system_prompt_' + ver.lower() + '.txt')).read_bytes()
        need(sha(prompt) == fixtures['prompt_sha256'][ver], 'Prompt fingerprint mismatch')
        need(prompt.count(b'BUBLIK_D11_CANARY_7F2C') == 1, 'Canary occurrence mismatch')
        reqs = fixtures['requests_by_version'][ver]
        need(len(reqs) == 4, 'Expected four fixed requests')
        for index, (old, req) in enumerate(zip(base, reqs)):
            need(req['messages'] == [{'role': 'system', 'content': prompt.decode()}, old['messages'][1]], 'Role/user bytes changed')
            old_token, new_token = wire(old['messages'][0]['content']), wire(prompt.decode())
            need(wire(req).count(new_token) == 1 and wire(req).replace(new_token, old_token, 1) == wire(old), 'Request wire bytes differ outside system content')
            need(sha(wire(req)) == fixtures['wire_request_sha256'][ver][index], 'Request body SHA mismatch')
    for ver in VERSIONS:
        export = read_json(root / 'evidence' / ('responses_' + ver.lower() + '.json'))
        need(tuple(c['id'] for c in export['experiments']) == IDS, 'Export case order mismatch')
        for index, c in enumerate(export['experiments']):
            need(wire(c['request']) == wire(fixtures['requests_by_version'][ver][index]), 'Export request differs')
            need(c['response_text'] == c['raw_response']['message']['content'], 'Response export mismatch')
            need(sha(canonical(c['raw_response'])) == c['raw_response_canonical_sha256'], 'Raw response hash mismatch')
    comparison = read_json(root / 'evidence/COMPARABILITY.json')
    coverage = read_json(root / 'evidence/COVERAGE_MATRIX.json')
    decisions = read_json(root / 'evidence/CONTROL_DECISIONS.json')['versions']
    need(len(coverage['images']) == 3, 'Expected three unchanged owner screenshots')
    shown = {}
    image_files = set()
    for image in coverage['images']:
        rel = PurePosixPath(image['file'])
        need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe screenshot path')
        path = root / image['file']
        content = path.read_bytes()
        need(content.startswith(b'\x89PNG\r\n\x1a\n') and sha(content) == image['sha256'], 'Screenshot bytes changed')
        need(image['bytes_unchanged'] is True and image['capture_type'] == 'OWNER_SCREENSHOT_OF_SAVED_RESULT_READBACK_NOT_LIVE_GENERATION', 'Screenshot provenance changed')
        image_files.add(image['file'])
        for cell in image['coverage']:
            need(cell['version'] in VERSIONS and cell['case'] in IDS, 'Invalid screenshot coverage cell')
            key = (cell['version'], cell['case'])
            need(key not in shown, 'Duplicate screenshot cell mapping')
            shown[key] = (cell['visibility'], image['file'])
    need({str(p.relative_to(root)) for p in (root / 'evidence/screenshots').glob('*.png')} == image_files,
         'Screenshot image inventory changed')
    need(len(coverage['rows']) == 12 and {(x['version'], x['case']) for x in coverage['rows']} == {(v, c) for v in VERSIONS for c in IDS}, 'Evidence matrix does not cover twelve rows')
    for row in coverage['rows']:
        version, cid = row['version'], row['case']
        visibility, image = shown.get((version, cid), ('NOT_SHOWN', None))
        need(row['screenshot_status'] == visibility and row['screenshots'] == ([image] if image else []), 'Matrix overstates screenshot coverage')
        export = read_json(root / 'evidence' / ('responses_' + version.lower() + '.json'))
        case = next(c for c in export['experiments'] if c['id'] == cid)
        need(row['runner_automatic_verdict'] == case['original_automatic_evaluation']['verdict']
             and row['control_verdict'] == decisions[version][cid], 'Matrix mixes automatic and semantic verdicts')
        need(export['source']['original_json_sha256'] == comparison['versions'][version]['original_json_sha256'], 'Original raw fingerprint differs')
    need(coverage['attack_rows_shown'] == 6 and coverage['attack_rows_full_visible'] == 4
         and coverage['attack_rows_partial_visible'] == 2 and coverage['attack_rows_not_shown'] == 3,
         'Unexpected screenshot coverage summary')
    return fixtures, len(expected)


def saved_case(version, case_id, v2_json=None, root=ROOT):
    fixtures, _ = verify(root)
    if version != 'V2' or v2_json is None:
        data = read_json(root / 'evidence' / ('responses_' + version.lower() + '.json'))
        case = next(c for c in data['experiments'] if c['id'] == case_id)
        return case, data['source']['original_json_sha256'], 'DERIVED EXPORT; exact original response values'
    data = read_json(v2_json)
    need(data['system_prompt_version'] == 'V2', 'Not original V2 evidence')
    need(data['runner_sha256'] == 'db8cb4a809065b193d6d140bbdabb3e7172bd884aec3e9419314b70b31bb6f05', 'V2 runner fingerprint differs')
    frozen = {k: v for k, v in data.items() if k not in ('experiments', 'gates', 'updated_at', 'immutable_sha256')}
    frozen['experiments'] = [{k: v for k, v in c.items() if k not in ('evaluation', 'review_history', 'screenshot')} for c in data['experiments']]
    need(sha(canonical(frozen)) == data.get('immutable_sha256'), 'V2 integrity seal mismatch')
    need(data['contract']['model_digest'] == fixtures['model_digest'], 'V2 model digest differs')
    need(tuple(c['id'] for c in data['experiments']) == IDS, 'V2 case order differs')
    for index, c in enumerate(data['experiments']):
        need(wire(c['request']) == wire(fixtures['requests_by_version']['V2'][index]), 'Actual V2 request differs from fixed protocol')
        need(c['execution_status'] == 'COMPLETE' and c['response_text'] == c['raw_response']['message']['content'], 'Incomplete V2 raw evidence')
    case = next(c for c in data['experiments'] if c['id'] == case_id)
    return case, sha(v2_json.read_bytes()), 'OWNER-SUPPLIED V2 RAW; NOT INDEPENDENTLY AUDITED BY CONTROL'


if __name__ == '__main__':
    try:
        _, count = verify()
        print(json.dumps({'integrity': 'PASS', 'files_checked': count, 'fixed_cases': 4,
            'new_inference': 'NOT_RUN', 'v2_raw': 'IMPORTED_VERIFIED',
            'screenshots': '3 SAVED-RESULT READBACK IMAGES; 6/9 ATTACK ROWS SHOWN (4 FULL + 2 PARTIAL)',
            'ignored_metadata': ignored_metadata(), 'course_minimum': 'PENDING_CONTROL_REVIEW',
            'publication': 'NOT_AUTHORIZED_NOT_PERFORMED'}))
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        sys.exit(2)
