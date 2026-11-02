#!/usr/bin/env python3
"""Readback of saved evidence only. No Ollama, network or image generation."""
import argparse
import json
import math
import sys
import textwrap
from pathlib import Path
sys.dont_write_bytecode = True
from verify import IDS, VERSIONS, ROOT, read_json, saved_case


def safe(value):
    return ''.join(c if c in '\n\t' or (ord(c) >= 32 and not 127 <= ord(c) <= 159) else '\\u%04x' % ord(c) for c in value)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', choices=VERSIONS, required=True)
    p.add_argument('--case', choices=IDS, required=True)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--lines', type=int, default=22)
    p.add_argument('--width', type=int, default=100)
    p.add_argument('--raw-json', action='store_true')
    p.add_argument('--v2-json', type=Path)
    a = p.parse_args()
    if a.lines < 5 or a.width < 40:
        p.error('Use lines >=5 and width >=40')
    case, origin_sha, provenance = saved_case(a.version, a.case, a.v2_json)
    f = read_json(ROOT / 'fixtures.json')
    controls = read_json(ROOT / 'evidence/CONTROL_DECISIONS.json')['versions']
    auto = case.get('original_automatic_evaluation', case.get('evaluation'))
    text = json.dumps(case['raw_response'], ensure_ascii=False, indent=2) if a.raw_json else case['response_text']
    wrapped = []
    for line in safe(text).split('\n'):
        wrapped.extend(textwrap.wrap(line, a.width, replace_whitespace=False, drop_whitespace=False) or [''])
    pages = max(1, math.ceil(len(wrapped) / a.lines))
    if not 1 <= a.page <= pages:
        p.error('Page must be between 1 and ' + str(pages))
    print('SAVED RESULT READBACK — NO MODEL RUN')
    print(a.version + ' / ' + a.case + ' / page ' + str(a.page) + '/' + str(pages))
    print(provenance)
    print('Original JSON SHA256: ' + origin_sha)
    print('Model: ' + f['model'] + ' / Ollama ' + f['ollama_version'])
    print('Digest: ' + f['model_digest'])
    print('Control verdict: ' + controls[a.version][a.case] + ' | historical automatic: ' + str(auto.get('verdict')))
    print('USER:')
    print('\n'.join(textwrap.wrap(safe(case['user_prompt']), a.width)))
    print('FULL RAW JSON, PAGINATED:' if a.raw_json else 'MODEL RESPONSE, PAGINATED:')
    print('\n'.join(wrapped[(a.page - 1) * a.lines:a.page * a.lines]))
    if a.page < pages:
        print('CONTINUES: capture remaining pages; do not omit continuation after refusal.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        sys.exit(2)
