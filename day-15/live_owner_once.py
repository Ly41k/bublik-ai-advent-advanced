#!/usr/bin/env python3
"""Optional owner-only one-shot LIVE attack, with no TCP listener and no auto retry.

NOT part of MOCK smoke; LIVE is never enabled by default.
Every allowed attack case has a single durable reservation per extracted package.
"""
from __future__ import annotations
import argparse
import asyncio
import getpass
import json
import os
from pathlib import Path
import sys
import hashlib

CASE_NAMES = (
    'C1_control', 'A1_direct', 'A2_indirect', 'A3_review_bypass',
    'A4_plain_secret', 'A4_base64_secret', 'A4_split_secret',
    'A4_double_base64_secret', 'A4_comment_secret',
)
HERE = Path(__file__).resolve().parent
PRIVATE = HERE / '.private' / 'live-owner'


def terminate(message: str, code: int = 2) -> None:
    print('STOP=' + message)
    raise SystemExit(code)


def reserve(case_name: str, payload_bytes: bytes) -> Path:
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE, 0o700)
    ledger = PRIVATE / ('reserved-' + case_name + '.json')
    try:
        with ledger.open('x', encoding='utf-8') as f:
            json.dump({'event':'RESERVED_BEFORE_REQUEST','case':case_name,
                       'payload_sha256':hashlib.sha256(payload_bytes).hexdigest(),
                       'retries_allowed':0},f,sort_keys=True)
            f.write('\n')
            f.flush(); os.fsync(f.fileno())
    except FileExistsError:
        terminate('ONE_SHOT_ALREADY_RESERVED_NO_RETRY')
    return ledger


async def invoke(req: dict) -> dict:
    # The application is imported ONLY after explicit key/opt-in configuration.
    import httpx
    from redteam_api import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app,client=('127.0.0.1',8345)),
                                 base_url='http://127.0.0.1',timeout=50) as client:
        response = await client.post('/v1/redteam/run', json=req)
    return {'transport_status':response.status_code, 'body':response.json()}


def main() -> int:
    parser=argparse.ArgumentParser(description='One explicitly approved LIVE case; never starts a TCP listener')
    parser.add_argument('--case', choices=CASE_NAMES, required=True)
    args=parser.parse_args()
    os.umask(0o077)
    filename=HERE/'attack_cases'/(args.case+'.json')
    if filename.is_symlink() or not filename.is_file() or filename.stat().st_size>4096:
        terminate('CASE_FILE_INVALID')
    data=filename.read_bytes()
    try:
        req=json.loads(data)
    except (json.JSONDecodeError,UnicodeDecodeError):
        terminate('CASE_JSON_INVALID')
    if type(req) is not dict:
        terminate('CASE_JSON_NOT_OBJECT')
    if (args.case.startswith('A4_') and req.get('attack_id')!='A4') or (
            not args.case.startswith('A4_') and req.get('attack_id')!=args.case.split('_')[0]):
        terminate('CASE_ID_MISMATCH')
    if os.environ.get('OPENAI_API_KEY'):
        terminate('OPENAI_API_KEY_ALREADY_IN_ENV_UNSET_FIRST')
    for key in ('OPENAI_PROJECT_ID','OPENAI_ORG_ID','OPENAI_CUSTOM_HEADERS','OPENAI_ADMIN_KEY','OPENAI_WEBHOOK_SECRET'):
        if os.environ.get(key):
            terminate('UNEXPECTED_ACCOUNT_OVERRIDE_'+key)
    if (PRIVATE/('reserved-'+args.case+'.json')).exists():
        terminate('ONE_SHOT_ALREADY_RESERVED_NO_RETRY')
    print('DAY15_G2_OWNER_ONLY_LIVE_CASE='+args.case)
    print('BIND=IN_PROCESS_ASGI_NO_TCP_LISTENER')
    print('MAX_GATEWAY_CALLS='+('2' if req['attack_id'] in ('A1','A2','C1') else '1'))
    print('OWNER_CONSENT_CEILING_USD=0.01')
    print('PROVIDER_ACCOUNT_HARD_CAP=NOT_PROVEN')
    print('AUTO_RETRY=false')
    print('KOTLIN_EXECUTION=DISABLED')
    print('CASE_SHA256='+hashlib.sha256(data).hexdigest())
    try:
        with open('/dev/tty','r') as tty:
            print('Type RUN to authorize one live case: ',end='',flush=True)
            approved=tty.readline().strip()
    except OSError:
        terminate('NO_INTERACTIVE_TTY')
    if approved!='RUN':
        terminate('OWNER_DECLINED',0)
    try:
        secret=getpass.getpass('OpenAI API key (hidden): ')
    except (OSError,EOFError):
        terminate('KEY_INPUT_FAILED')
    if not secret.startswith('sk-'):
        terminate('INVALID_KEY')
    ledger=reserve(args.case,data)
    os.environ.update({'OPENAI_API_KEY':secret,'BUBLIK_D15_LIVE_OWNER_OPT_IN':'YES',
                       'GATEWAY_PROVIDER':'openai','LIVE_ENABLED':'true',
                       'GATEWAY_AUDIT_PATH':str(PRIVATE/('audit-'+args.case+'.jsonl'))})
    os.environ.pop('BUBLIK_D15_ALLOW_KOTLIN',None)
    secret=None
    report={'case':args.case,'payload_sha256':hashlib.sha256(data).hexdigest(),
            'purpose':'single-owner-controlled-day15-live', 'result':'OUTCOME_UNKNOWN'}
    try:
        received=asyncio.run(invoke(req))
        body=received['body']
        report.update({'transport_status':received['transport_status'],'result':body})
        print('TRANSPORT_HTTP='+str(received['transport_status']))
        print('GATEWAY_HTTP='+str(body.get('gateway_http_status')))
        print('ORIGIN='+str(body.get('origin')))
        print('FINDING='+str(body.get('finding')))
        if body.get('reviewer_severities'):
            print('REVIEWER_SEVERITIES='+json.dumps(body['reviewer_severities'],sort_keys=True))
        print('COST_ESTIMATE_USD='+str(body.get('gateway_cost_usd_estimate')))
        print('LIVE_CASE=RESPONSE_RECEIVED')
    except Exception as exc:
        report['result']='STOP_'+type(exc).__name__+'_UNKNOWN_PROVIDER_OUTCOME'
        print('LIVE_CASE=STOP_NO_RETRY')
        print('PROVIDER_OUTCOME=UNKNOWN_POSSIBLY_BILLED')
    finally:
        os.environ.pop('OPENAI_API_KEY',None)
        report_path=PRIVATE/('result-'+args.case+'.json')
        with report_path.open('x',encoding='utf-8') as f:
            json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2)
            f.write('\n')
        print('PRIVATE_RESULT='+str(report_path))
        print('API_KEY_SHARED=false')
        print('GIT_WRITES=NONE')
    return 0 if report['result']!='OUTCOME_UNKNOWN' and not str(report['result']).startswith('STOP_') else 2

if __name__=='__main__':
    raise SystemExit(main())
