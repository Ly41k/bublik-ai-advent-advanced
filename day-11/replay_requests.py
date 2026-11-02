#!/usr/bin/env python3
"""Future optional reproduction. Default: offline plan. Historical evidence never rewritten."""
import argparse
import json
import platform
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode = True
from verify import ROOT, VERSIONS, canonical, need, sha, verify, wire


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_a, **_kw):
        raise ValueError('Redirect prohibited')


def api(route, body=None):
    need(route in ('/api/version', '/api/tags', '/api/show', '/api/chat'), 'Endpoint prohibited')
    req = urllib.request.Request('http://127.0.0.1:11434' + route,
        data=None if body is None else wire(body), headers={'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=180 if route == '/api/chat' else 10) as r:
        result = json.load(r)
    need(isinstance(result, dict) and not result.get('error'), 'Invalid/error local API response')
    return result


def preflight(f):
    host = dict(system=platform.system(), machine=platform.machine(), python=platform.python_version())
    need(host == f['host'], 'Host/Python differs from frozen protocol')
    version = api('/api/version')
    need(version.get('version') == f['ollama_version'], 'Ollama version differs')
    tags = api('/api/tags')
    entries = [x for x in tags.get('models', []) if x.get('name') == f['model']]
    need(len(entries) == 1 and entries[0].get('digest') == f['model_digest'], 'Local tag/digest missing or differs; no pull allowed')
    show = api('/api/show', {'model': f['model']})
    need(not show.get('remote_host') and not show.get('remote_model'), 'Remote model refused')
    need(sha(canonical({k:show.get(k) for k in f['show_stable_fields']})) == f['show_stable_sha256'], 'Model template/defaults differ')
    return dict(host=host, version=version, tags=tags, show=show)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', choices=VERSIONS, required=True)
    p.add_argument('--execute-local', action='store_true')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    f, _ = verify()
    if not a.execute_local:
        print(json.dumps({'mode':'OFFLINE_PLAN', 'version':a.version, 'new_inference':'NOT_RUN',
            'case_order':f['case_order'], 'wire_sha256':f['wire_request_sha256'][a.version]}, indent=2))
        return 0
    need(a.out is not None, 'A new --out directory is required')
    out = a.out.resolve()
    need(not out.is_relative_to(ROOT) and not out.is_relative_to(ROOT.parent / 'audit'), 'Output cannot be inside staging or original audit evidence')
    need(not out.exists(), 'Output exists; never overwrite previous results')
    out.mkdir(parents=True)
    result = {'kind':'NEW_REPLAY_NOT_HISTORICAL', 'version':a.version,
        'created_at':datetime.now(timezone.utc).isoformat(), 'semantic_verdict':'NOT_ADJUDICATED', 'experiments':[]}
    try:
        for case_id, request in zip(f['case_order'], f['requests_by_version'][a.version]):
            verify()
            case = {'id':case_id, 'request':request, 'request_wire_sha256':sha(wire(request))}
            result['experiments'].append(case)
            case['preflight_before'] = preflight(f)
            start = time.perf_counter()
            case['raw_response'] = api('/api/chat', request)
            case['wall_seconds'] = time.perf_counter() - start
            raw = case['raw_response']
            need(raw.get('done') is True and raw.get('model') == f['model']
                and raw.get('message', {}).get('role') == 'assistant'
                and isinstance(raw['message'].get('content'), str)
                and bool(raw['message']['content'].strip()), 'Incomplete/wrong-model reply')
            case['preflight_after'] = preflight(f)
            (out / 'replay_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        verify()
    except Exception as exc:
        result['error'] = dict(type=type(exc).__name__, message=str(exc))
    (out / 'replay_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('BLOCKED' if 'error' in result else 'Saved NEW replay; no historical verdict changed')
    return 2 if 'error' in result else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        sys.exit(2)
