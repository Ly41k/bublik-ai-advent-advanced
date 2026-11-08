#!/usr/bin/env python3
"""G2: five requests against a locally started MOCK server; never calls OpenAI."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import sys

HERE = Path(__file__).resolve().parent
HOST = 'http://127.0.0.1:8091'
CASES = [
    ('C1', 'C1_control.json', 200, 'NOT_EVALUABLE_MOCK_NO_MODEL_CONCLUSION'),
    ('A1', 'A1_direct.json', 200, 'NOT_EVALUABLE_MOCK_NO_MODEL_CONCLUSION'),
    ('A2', 'A2_indirect.json', 200, 'NOT_EVALUABLE_MOCK_NO_MODEL_CONCLUSION'),
    ('A3', 'A3_review_bypass.json', 200, 'NOT_EVALUABLE_MOCK_NO_MODEL_CONCLUSION'),
    ('A4', 'A4_base64_secret.json', 403, 'INPUT_GUARD_BLOCKED'),
]

def call(path: str, payload: bytes | None = None) -> tuple[int, dict]:
    request = Request(HOST + path, data=payload,
                      headers={'Content-Type':'application/json'} if payload is not None else {},
                      method='POST' if payload is not None else 'GET')
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read(16384))
    except HTTPError as ex:
        return ex.code, json.loads(ex.read(16384))

def main() -> int:
    try:
        status, health = call('/health')
        assert status == 200 and health.get('mode') == 'MOCK'
        assert health.get('status') == 'ok'
        print('DAY15_G2_MOCK_HEALTH=PASS')
        for attack, filename, gw_status, finding in CASES:
            data = (HERE/'attack_cases'/filename).read_bytes()
            status, result = call('/v1/redteam/run', data)
            assert status == 200, (attack, 'transport', status, result)
            assert result.get('attack_id') == attack, (attack, result)
            assert result.get('gateway_http_status') == gw_status, (attack, result)
            assert result.get('finding') == finding, (attack, result)
            assert result.get('is_live_model') is False, (attack, result)
            print(f'{attack}: GATEWAY_HTTP={gw_status}; FINDING={finding}; LIVE=false')
        print('DAY15_G2_PARTNER_MOCK_SMOKE=5_OF_5_PASS')
        print('LLM_LIVE_CALLS=0')
        print('PARTNER_ATTACK_OUTCOMES=NOT_YET_EVALUATED')
        return 0
    except (OSError, ValueError, AssertionError, URLError) as ex:
        print('DAY15_G2_PARTNER_MOCK_SMOKE=STOP')
        print('REASON=' + type(ex).__name__ + ': ' + str(ex)[:320])
        print('NOTE=Fresh MOCK process has a 5-requests/60s limit; never auto-retry.')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
