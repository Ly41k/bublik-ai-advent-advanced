"""Offline-first CLI. Future live path is owner gated and numeric-loopback only."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import http.client
import io
import json
import os
from pathlib import Path
import platform
import re
import socket
import time
from datetime import datetime, timezone
from agent import ROOT, build_request, evaluate, load_json, sha
from defenses import canonical_json, strict_json

SCHEMA_VERSION = 'd12-evidence-1'
MAX_RESPONSE = 8 * 1024 * 1024


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def rows(root=ROOT):
    return list(csv.DictReader(io.StringIO((root / 'RUN_MATRIX.csv').read_text(encoding='utf-8'))))


def plan(root=ROOT):
    output = []
    for row in rows(root):
        item = build_request(row, root)
        output.append(dict(row, observation_status='NOT_RUN',
                           source_sha256=item['source_sha256'], task_sha256=item['task_sha256'],
                           request_sha256=sha(item['request_bytes']), system_sha256=item['system_sha256'],
                           sanitized_sha256=item['sanitized_sha256'], defenses=item['defenses']))
    return output


class EvidenceStore:
    """Exclusive new run directory; artifacts are never replaced or appended to.

    Local single-owner integrity, not an OS security boundary against another
    process with write access. No claim of tamper-proof/WORM storage.
    """
    def __init__(self, output, run_id, root=ROOT):
        if not re.fullmatch(r'[A-Z0-9_]+', run_id):
            raise ValueError('Invalid run ID')
        supplied = Path(output)
        if '..' in supplied.parts:
            raise ValueError('Parent traversal forbidden')
        target = supplied if supplied.is_absolute() else root / supplied
        base = root / 'evidence'
        if not target.is_relative_to(base) or target == root:
            raise ValueError('Declared output must be within day-12/evidence/')
        # Check symlinks only INSIDE the trusted workspace's evidence tree.
        # macOS tempfile may use /var/... where /var -> /private/var;
        # checking parents above `base` produces a false positive.
        # Never follow symlinks in base or any user-selected output component.
        component = target
        while True:
            if component.is_symlink():
                raise ValueError('Output symlink forbidden')
            if component == base:
                break
            component = component.parent
        target.mkdir(parents=True, exist_ok=True)
        self.path = target / run_id
        self.path.mkdir(exist_ok=False)
        self.files = {}

    def write(self, name, data):
        if not re.fullmatch(r'[a-z0-9_.-]+', name):
            raise ValueError('Unsafe artifact name')
        if type(data) is not bytes:
            raise TypeError('Artifact must be bytes')
        target = self.path / name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(target, flags, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        self.files[name] = {'sha256': sha(data), 'size_bytes': len(data)}

    def json(self, name, value):
        self.write(name, canonical_json(value))

    def finish(self):
        self.json('manifest.json', {'schema_version': SCHEMA_VERSION, 'files': dict(self.files)})
        for child in self.path.iterdir():
            child.chmod(0o444)
        self.path.chmod(0o555)


class _NumericLoopbackConnection(http.client.HTTPConnection):
    def connect(self):
        # Bypass getaddrinfo, DNS, proxy environment, and hostname resolution.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect(('127.0.0.1', 11434))
        except BaseException:
            self.sock.close()
            raise


class LocalOllama:
    """Not instantiated by offline tests except with mocked network primitives."""
    def __init__(self, *, owner_live, endpoint='http://127.0.0.1:11434', recorder=None):
        if owner_live is not True:
            raise ValueError('Explicit owner live flag required')
        if endpoint not in ('http://127.0.0.1:11434', 'http://localhost:11434'):
            raise ValueError('Only fixed local Ollama endpoint permitted')
        if recorder is None:
            raise ValueError('Request/response evidence recorder required')
        self.recorder, self.counter = recorder, 0

    def call(self, method, path, payload=None):
        if (method, path) not in (('GET', '/api/version'), ('GET', '/api/tags'), ('POST', '/api/chat')):
            raise ValueError('Unsupported Ollama path/method; no model pull/download')
        self.counter += 1
        prefix = f'http-{self.counter:02}'
        body = b'' if payload is None else canonical_json(payload)
        self.recorder.write(prefix + '-request.json', canonical_json({
            'method': method, 'path': path, 'endpoint': '127.0.0.1:11434',
            'body_sha256': sha(body), 'body_utf8': body.decode('utf-8'), 'started_utc': utc_now()}))
        conn = _NumericLoopbackConnection('127.0.0.1', 11434, timeout=120)
        try:
            conn.request(method, path, body=body, headers={'Content-Type': 'application/json', 'Connection': 'close'})
            response = conn.getresponse()
            raw = response.read(MAX_RESPONSE + 1)
            self.recorder.write(prefix + '-response.bin', raw)
            self.recorder.json(prefix + '-response-meta.json', {'status': response.status,
                'headers': response.getheaders(), 'completed_utc': utc_now()})
            if response.status != 200:
                raise ValueError('HTTP error/redirect rejected; no redirect following')
            if len(raw) > MAX_RESPONSE:
                raise ValueError('Response exceeds size bound')
            return raw
        finally:
            conn.close()

    def fingerprint(self, model):
        version = strict_json(self.call('GET', '/api/version').decode('utf-8'))
        tags = strict_json(self.call('GET', '/api/tags').decode('utf-8'))
        matches = [m for m in tags['models'] if m.get('name') == model]
        if len(matches) != 1 or not re.fullmatch(r'[a-f0-9]{64}', matches[0].get('digest', '')):
            raise ValueError('Unverified/ambiguous local model identity')
        if not isinstance(version.get('version'), str) or not version['version']:
            raise ValueError('Missing Ollama version')
        return {'model': model, 'digest': matches[0]['digest'], 'ollama_version': version['version']}

    def generate(self, request):
        return self.call('POST', '/api/chat', request)


def check_admission(admission, row, plan_hash, manifest_hash):
    if admission.get('decision') != 'OWNER_AUTHORIZED' or admission.get('stage') != row['owner_stage']:
        raise ValueError('Missing stage-specific owner authorization')
    if admission.get('model') != 'qwen2.5:7b':
        raise ValueError('Wrong model')
    if not re.fullmatch(r'[a-f0-9]{64}', admission.get('digest', '')) or not admission.get('ollama_version'):
        raise ValueError('Owner must pin verified digest and version')
    if (admission.get('plan_sha256') != plan_hash or admission.get('fixture_manifest_sha256') != manifest_hash
            or row['id'] not in admission.get('allowed_run_ids', [])):
        raise ValueError('Admission drift or run not authorized')
    return {key: admission[key] for key in ('model', 'digest', 'ollama_version')}


def execute(row, output, transport, *, synthetic, root=ROOT, admission=None, store=None):
    """One fresh context; tests pass an inert transport. No renderer or action executor."""
    item = build_request(row, root)
    store = store or EvidenceStore(output, row['id'], root)
    store.write('source.bin', item['source_bytes'])
    store.write('request.json', item['request_bytes'])
    store.json('preparation.json', {key: value for key, value in item.items()
                                  if key not in ('request', 'request_bytes', 'source_bytes')})
    store.json('run-start.json', {'schema_version': SCHEMA_VERSION, 'row': row,
        'started_utc': utc_now(), 'synthetic': synthetic,
        'result_origin': 'SYNTHETIC_TEST_ONLY' if synthetic else 'OWNER_LOCAL_OLLAMA',
        'environment': {'python': sys.version, 'platform': platform.platform()},
        'admission': admission})
    if item['sanitized_text'] is not None:
        store.write('sanitized.txt', item['sanitized_text'].encode('utf-8'))
    started = time.perf_counter()
    try:
        before = None
        if not synthetic:
            if not isinstance(transport, LocalOllama) or admission is None:
                raise ValueError('Only owner-admitted local transport allowed')
            before = transport.fingerprint(item['request']['model'])
            if before != admission:
                raise ValueError('Pre-run model fingerprint mismatch')
        raw = transport.generate(item['request'])
        if type(raw) is not bytes:
            raise TypeError('Transport must return exact response bytes')
        store.write('raw-response.json', raw)
        response = strict_json(raw.decode('utf-8', errors='strict'))
        if response.get('model') != item['request']['model'] or response.get('done') is not True:
            raise ValueError('Model mismatch or incomplete response')
        answer = response['message']['content']
        if not isinstance(answer, str) or not answer.strip() or response['message'].get('role') != 'assistant':
            raise ValueError('Missing assistant content')
        # Any proposed tools are disallowed and never executed.
        if response['message'].get('tool_calls'):
            raise ValueError('Unexpected proposed tool calls; none executed')
        after = transport.fingerprint(item['request']['model']) if not synthetic else None
        if not synthetic and after != admission:
            raise ValueError('Post-run model fingerprint drift')
        result = evaluate(row, answer, root)
        if result['final_exposed_answer'] is not None:
            store.write('final-answer.txt', result['final_exposed_answer'].encode('utf-8'))
        result.update(schema_version=SCHEMA_VERSION, row=row, synthetic=synthetic,
            result_origin='SYNTHETIC_TEST_ONLY' if synthetic else 'OWNER_LOCAL_OLLAMA',
            observation_status='NOT_RUN' if synthetic else 'OBSERVED',
            model_fingerprint_before=before, model_fingerprint_after=after,
            duration_seconds=time.perf_counter() - started,
            source_sha256=item['source_sha256'], task_sha256=item['task_sha256'],
            request_sha256=sha(item['request_bytes']), raw_response_sha256=sha(raw))
        if synthetic:
            result['synthetic_pipeline_verdict'] = result.pop('pipeline_verdict')
            result['pipeline_verdict'] = 'NOT_RUN'
        store.json('result.json', result)
    except Exception as error:
        result = {'schema_version': SCHEMA_VERSION, 'row': row, 'synthetic': synthetic,
            'result_origin': 'SYNTHETIC_TEST_ONLY' if synthetic else 'OWNER_LOCAL_OLLAMA',
            'observation_status': 'NOT_RUN' if synthetic else 'ERROR',
            'pipeline_verdict': 'NOT_RUN' if synthetic else 'INCONCLUSIVE',
            'raw_model_compliance': 'UNKNOWN', 'final_exposed_answer': None,
            'error_type': type(error).__name__, 'error': str(error), 'simulated_actions': []}
        store.json('result.json', result)
    store.finish()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('plan')
    run = sub.add_parser('run')
    run.add_argument('--run-id', required=True)
    run.add_argument('--output', default='evidence/owner')
    run.add_argument('--owner-live', action='store_true')
    run.add_argument('--admission')
    run.add_argument('--endpoint', default='http://127.0.0.1:11434')
    args = parser.parse_args(argv)
    from verify import verify
    verify()
    planned = plan()
    if args.command == 'plan':
        print(json.dumps({'schema_version': SCHEMA_VERSION, 'planned_calls': len(planned),
                          'live_calls_executed': 0, 'rows': planned}, ensure_ascii=False, indent=2))
        return 0
    matches = [r for r in rows() if r['id'] == args.run_id]
    if len(matches) != 1:
        parser.error('Unknown run ID')
    if not args.owner_live:
        print(json.dumps({'status': 'NOT_RUN', 'dry_run': True, 'live_calls_executed': 0,
                          'row': next(r for r in planned if r['id'] == args.run_id)}, ensure_ascii=False))
        return 0
    if not args.admission:
        parser.error('--owner-live requires --admission; G1 does not authorize live runs')
    admission = load_json(Path(args.admission))
    expected = check_admission(admission, matches[0], sha(canonical_json(planned)),
                               sha((ROOT / 'fixtures' / 'SHA256SUMS.json').read_bytes()))
    # Validate endpoint/gate before creating any output. Constructor itself makes no request.
    transport = LocalOllama(owner_live=True, endpoint=args.endpoint, recorder=True)
    store = EvidenceStore(args.output, args.run_id)
    transport.recorder = store
    store.json('owner-admission.json', admission)
    result = execute(matches[0], args.output, transport, synthetic=False, admission=expected, store=store)
    # Do not render or print model-authored content; raw bytes stay in inert evidence files.
    print(json.dumps({'run_id': args.run_id, 'pipeline_verdict': result['pipeline_verdict'],
                      'observation_status': result['observation_status'], 'evidence': str(store.path)}))
    return 0 if result['observation_status'] == 'OBSERVED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
