#!/usr/bin/env python3
"""One HTTP Base/q4 evaluation, optional FP16 fallback, load-failure test and rollback."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener

from prepare_model import (DEFAULT_ROOT, LABELS, SMOKE_TEXT, canonical, day9_context, inventory,
                           load_registry, need, objsha, read, sha, versions, write_new)


class Client:
    def __init__(self, port):
        need(1 <= port <= 65535, 'INVALID_PORT')
        self.url = f'http://127.0.0.1:{port}'
        self.opener = build_opener(ProxyHandler({}))

    def call(self, route, body=None):
        data = None if body is None else canonical(body).encode()
        request = Request(self.url + route, data=data, method='GET' if body is None else 'POST',
                          headers={'Content-Type': 'application/json'})
        started = time.perf_counter()
        try:
            with self.opener.open(request, timeout=120) as response:
                status, raw = response.status, response.read()
        except HTTPError as exc:
            status, raw = exc.code, exc.read()
        return status, json.loads(raw), time.perf_counter() - started


def stats(records):
    if len(records) != 32:
        return {'complete32': False, 'attempted': len(records), 'accuracy': None}
    matrix = {gold: {p: 0 for p in (*LABELS, 'INVALID')} for gold in LABELS}
    correct = 0
    for row in records:
        out = row['response']
        raw = out.get('raw')
        prediction = raw if (row['http_status'] == 200 and raw in LABELS
                             and out.get('finish_reason') == 'stop') else 'INVALID'
        matrix[row['gold']][prediction] += 1
        correct += prediction == row['gold']
    scores = []
    for label in LABELS:
        tp = matrix[label][label]
        fp = sum(matrix[g][label] for g in LABELS if g != label)
        fn = sum(matrix[label].values()) - tp
        scores.append(0 if 2 * tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn))
    http = sorted(r['http_seconds'] for r in records)
    generation = sorted(r['response']['generation_seconds'] for r in records if r['http_status'] == 200)
    memories = [r['response']['memory'] for r in records if r['http_status'] == 200]
    metal = {}
    for label in ('active_bytes', 'cache_bytes', 'peak_bytes'):
        values = [m.get('metal', {}).get(label) for m in memories]
        values = [v for v in values if v is not None]
        metal[label] = max(values) if values else None
    return {'complete32': True, 'attempted': 32, 'correct': correct, 'accuracy': correct / 32,
            'invalid': sum(matrix[g]['INVALID'] for g in LABELS), 'macro_f1': statistics.mean(scores),
            'confusion': matrix, 'http_median_seconds': statistics.median(http),
            'http_p95_seconds': http[math.ceil(.95 * len(http)) - 1],
            'server_generation_median_seconds': statistics.median(generation) if generation else None,
            'server_generation_p95_seconds': generation[math.ceil(.95 * len(generation)) - 1] if generation else None,
            'max_sampled_rss_bytes': max((m['rss_bytes'] for m in memories), default=None),
            'process_lifetime_high_water_rss_bytes': max((m['process_high_water_rss_bytes'] for m in memories), default=None),
            'metal_max_observed_bytes': metal}


def paired(base, tuned):
    need([r['id'] for r in base] == [r['id'] for r in tuned], 'PAIRED_ID_MISMATCH')
    counts = Counter()
    for b, t in zip(base, tuned):
        def correct(row):
            out = row['response']
            return row['http_status'] == 200 and out.get('raw') == row['gold'] and out.get('finish_reason') == 'stop'
        bc, tc = correct(b), correct(t)
        counts['both_correct' if bc and tc else 'base_only' if bc else 'tuned_only' if tc else 'both_wrong'] += 1
    return {k: counts[k] for k in ('both_correct', 'base_only', 'tuned_only', 'both_wrong')}


def atomic_selection(path, value):
    need(not path.exists(), 'SELECTION_ALREADY_EXISTS')
    temp = path.with_suffix('.pending')
    write_new(temp, value)
    os.replace(temp, path)


def render_report(result):
    lines = ['# Бублик — Day 10', '', f"Status: **{result['status']}**.",
             '', 'Один локальный запуск; frozen final32 из Day9. API/training/Git writes: 0.',
             f"Versions: `{canonical(result['versions'])}`.",
             f"Registry SHA256: `{result['registry_sha256']}`.", '',
             '| Arm | Correct /32 | Accuracy | Macro-F1 | Invalid | HTTP median / p95, ms | Load, s | Logical disk, MiB | RSS max sampled, MiB |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm, metric in result['metrics'].items():
        if not metric['complete32']:
            lines.append(f'| {arm} | PARTIAL {metric["attempted"]}/32 | UNKNOWN | — | — | — | — | — | — |')
            continue
        switch = result['switches'][arm]['last_switch']
        lines.append(f"| {arm} | {metric['correct']}/32 | {metric['accuracy']:.2%} | {metric['macro_f1']:.6f} | {metric['invalid']} | "
            f"{1000*metric['http_median_seconds']:.3f} / {1000*metric['http_p95_seconds']:.3f} | "
            f"{switch['load_seconds']:.6f} | {result['models'][arm]['disk']['logical_bytes']/2**20:.2f} | "
            f"{metric['max_sampled_rss_bytes']/2**20:.2f} |")
    lines.extend(['', f"Selected tuned version: **{result.get('selected', 'NOT_SELECTED')}**.",
        f"4-bit acceptance: >=24/32. Outcome: `{result.get('q4_decision', 'NOT_RUN')}`.",
        'FP16 evaluates only after q4 quality failure; q4 evidence is retained. No parameter search or retraining.',
        f"Load-failure preservation test: `{canonical(result.get('load_failure', {'status':'NOT_RUN'}))}`.",
        f"Rollback: `{canonical(result.get('rollback', {'status':'NOT_RUN'}))}`.",
        f"Day9 preservation: `{result.get('day9_preserved', False)}`.", '',
        'Model versions: ' + ', '.join(f"{k}=`{v['version']}`" for k, v in result['models'].items()),
        'Preparation times: ' + canonical(result['preparation']), '',
        'Release: keep immutable model directories with recorded inventories and REGISTRY.sha256; verify hashes, load and one-token readiness smoke before committing the active reference. '
        'After this benchmark, SELECTION.json binds the accepted q4 or FP16 variant to this registry. '
        'POST /model {"model":"tuned"}, then GET /health and POST /classify.',
        'Rollback: POST /model {"model":"base"}; verify active=base, same PID and instance_id, then classify. '
        'Failed candidate load leaves the previous Python model reference active. The benchmark ends with Base active.', '',
        'Load time includes weight materialization and synchronize; hash validation and one-token readiness forward are recorded separately. '
        'HTTP time includes serialization, localhost HTTP, inference and process-memory sampling; server generation time excludes the memory probe. '
        'p95 is nearest rank over32 attempts. No hidden warmups: each load has an explicitly counted one-token technical smoke outside final32. '
        'First final32 request includes remaining cold-kernel effects.',
        'RSS sampling is not an exact instantaneous peak. Process high-water RSS and MLX peak are cumulative for the service lifetime, '
        'including overlap while switching models; active/cache memory are reported separately. Disk allocation may share APFS blocks. '
        'Base and tuned-q4 have different weight precision, so their resource difference is not attributable solely to LoRA.',
        'The known final32 is a deployment regression set, not a new independent production-quality estimate. '
        'Historical Day9 tuned+adapter=26/32 is retained as reference; Base=2/32. No model is trained or chosen by a new training run.',
        'Private request IDs/labels/raw responses remain in PRIVATE_RECORDS.jsonl; no datasets, prompts, adapter or model weights are included in the Control report.',
        '', '**STOP_FOR_CONTROL_REVIEW**'])
    if result.get('error'):
        lines.insert(3, 'Failure: `' + result['error'] + '`. Partial evidence is retained; no retry was performed.')
    return '\n'.join(lines) + '\n'


def benchmark(args):
    os.umask(0o077)
    root = args.root.expanduser().resolve()
    runtime = versions()
    registry, digest = load_registry(root / 'REGISTRY.json')
    output = root / 'benchmark-r1'
    need(not output.exists(), 'BENCHMARK_ALREADY_EXISTS_NO_RETRY')
    output.mkdir(mode=0o700)
    write_new(output / 'STARTED.json', {'status': 'STARTED', 'registry_sha256': digest})
    result = {'status': 'STARTED', 'schema': 'bublik-day10-http-benchmark-r1', 'versions': runtime,
        'service_dependencies': registry['service_dependencies'], 'registry_sha256': digest,
        'threshold_correct_of32': 24, 'metrics': {}, 'switches': {},
        'models': {k: {'version': v['version'], 'disk': v['disk'], 'inventory_sha256': objsha(v['inventory'])}
                   for k, v in registry['models'].items() if k != 'load-error-fixture'},
        'preparation': registry['preparation'], 'training': 'NOT_RUN', 'api_calls': 0, 'git_writes': 0,
        'day9_reference': {'base_correct': 2, 'tuned_adapter_correct': 26, 'n': 32},
        'implementation_sha256': registry['implementation_sha256']}
    client = Client(args.port)
    records = {}
    identity = None
    c = None
    def same(out):
        need(out['registry_sha256'] == digest and (out['pid'], out['instance_id']) == identity,
             'SERVICE_PID_INSTANCE_OR_REGISTRY_CHANGED')
    def call_ok(route, body=None):
        code, value, elapsed = client.call(route, body)
        need(code == 200, 'HTTP_FAILURE:' + route + ':' + str(code))
        same(value)
        return value, elapsed
    try:
        _, c = day9_context(registry['day9_paths'])
        need(c['task'] == registry['task'] and c['messages'][0][0]['content'] == registry['system_prompt'],
             'DAY9_TASK_OR_SYSTEM_PROMPT_DRIFT')
        status, health, _ = client.call('/health')
        need(status == 200 and health['ready'] and health['registry_sha256'] == digest,
             'SERVICE_NOT_READY_OR_WRONG_RELEASE')
        need(health['load_failure_test_enabled'], 'START_SERVICE_WITH_ENABLE_LOAD_FAILURE_TEST')
        identity = health['pid'], health['instance_id']
        result['service_identity'] = {'pid': identity[0], 'instance_id': identity[1]}
        gold = {r['id']: r['label'] for r in c['gold']}
        def arm(name):
            switched, _ = call_ok('/model', {'model': 'base'} if name == 'base' else {'model': 'tuned', 'version': name})
            need(switched['active'] == name, 'WRONG_ACTIVE_ARM')
            result['switches'][name] = switched
            records[name] = []
            for i, (row, messages) in enumerate(zip(c['rows'], c['messages'])):
                body = {'text': messages[1]['content']}
                # A reservation is persisted BEFORE attempting HTTP, with no text/gold leak.
                with (output / 'PRIVATE_RECORDS.jsonl').open('a') as f:
                    f.write(canonical({'event': 'reserved', 'arm': name, 'id': row['id'],
                                       'request_sha256': objsha(body)}) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
                sent = time.perf_counter()
                try:
                    code, response, elapsed = client.call('/classify', body)
                except Exception as exc:
                    code, response, elapsed = 0, {'error': type(exc).__name__}, time.perf_counter() - sent
                rec = {'event': 'response', 'arm': name, 'id': row['id'], 'gold': gold[row['id']],
                       'http_status': code, 'response': response, 'http_seconds': elapsed}
                records[name].append(rec)
                with (output / 'PRIVATE_RECORDS.jsonl').open('a') as f:
                    f.write(canonical(rec) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
                need(code == 200, 'CLASSIFY_TECHNICAL_FAILURE_PARTIAL_NO_RETRY')
                same(response)
                need(response['active'] == name, 'ARM_CHANGED_DURING_BENCHMARK')
                need(response['prompt_serialization_sha256'] == registry['final32_serialization_sha256'][i]
                     == c['local_meta']['prompt_serialization_sha256'][i], 'FROZEN_PROMPT_SERIALIZATION_CHANGED')
            result['metrics'][name] = stats(records[name])
        arm('base')
        base_probe, _ = call_ok('/classify', {'text': SMOKE_TEXT})
        arm('q4')
        selected = 'q4'
        if result['metrics']['q4']['correct'] < 24:
            result['q4_decision'] = 'FAIL_BELOW24_USE_FP16_NO_Q4_RETRY'
            arm('fp16')
            selected = 'fp16'
            need(result['metrics']['fp16']['correct'] >= 24, 'FP16_ALSO_BELOW24_STOP')
        else:
            result['q4_decision'] = 'PASS_AT_LEAST24'
        result['selected'] = selected
        result['paired_base_selected'] = paired(records['base'], records[selected])
        # Use the SAME real request on the active working model before/after an
        # actual MLX load from the fixed missing-weights fixture. No final32 score retry.
        check_text = SMOKE_TEXT
        before, _ = call_ok('/classify', {'text': check_text})
        code, failure, elapsed = client.call('/model', {'model': 'tuned', 'version': 'load-error-fixture'})
        need(code == 503 and failure['detail']['error'] == 'FileNotFoundError', 'EXPECTED_REAL_MISSING_WEIGHTS_LOAD_FAILURE')
        same(failure['detail'])
        after, _ = call_ok('/classify', {'text': check_text})
        need(before['model_version'] == after['model_version'] and before['active'] == after['active'] == selected
             and before['raw'] == after['raw'] and before['finish_reason'] == after['finish_reason'],
             'WORKING_MODEL_NOT_PRESERVED_AFTER_LOAD_FAILURE')
        result['load_failure'] = {'status': 'PASS_REAL_LOADER_FILE_NOT_FOUND',
            'same_model_version': True, 'same_prediction': True, 'same_pid_instance': True,
            'failure_seconds': elapsed, 'http_status': code}
        result['diagnostic_classify_calls_excluded_from32'] = 4
        atomic_selection(root / 'SELECTION.json', {'selected': selected, 'registry_sha256': digest,
            'correct_of32': result['metrics'][selected]['correct'], 'minimum_required': 24})
        result['status'] = 'BENCHMARK_COMPLETE_STOP_FOR_CONTROL_REVIEW'
    except Exception as exc:
        result['status'] = 'STOP_FOR_CONTROL_REVIEW'
        result['error'] = type(exc).__name__ + ':' + str(exc)
    finally:
        for name, values in records.items():
            result['metrics'][name] = stats(values)
        if identity is not None:
            try:
                rolled, elapsed = call_ok('/model', {'model': 'base'})
                health, _ = call_ok('/health')
                need(rolled['active'] == health['active'] == 'base', 'ROLLBACK_NOT_BASE')
                prediction, _ = call_ok('/classify', {'text': SMOKE_TEXT})
                need(prediction['active'] == 'base', 'ROLLBACK_CLASSIFY_NOT_BASE')
                if 'base_probe' in locals():
                    need(prediction['raw'] == base_probe['raw']
                         and prediction['finish_reason'] == base_probe['finish_reason'],
                         'ROLLBACK_BASE_PREDICTION_DIFFERS')
                result['rollback'] = {'status': 'PASS', 'active': 'base', 'pid': health['pid'],
                    'instance_id': health['instance_id'], 'same_pid_instance': True,
                    'classify_confirmed': True, 'switch_wall_seconds_http': elapsed,
                    'load': rolled['last_switch']}
            except Exception as exc:
                result['rollback'] = {'status': 'FAIL', 'error_type': type(exc).__name__}
                result['status'] = 'STOP_FOR_CONTROL_REVIEW'
        try:
            _, after_context = day9_context(registry['day9_paths'])
            result['day9_preserved'] = after_context['task'] == registry['task']
            need(result['day9_preserved'], 'DAY9_CHANGED')
        except Exception as exc:
            result['day9_preserved'] = False
            result['status'] = 'STOP_FOR_CONTROL_REVIEW'
            result['preservation_error_type'] = type(exc).__name__
        write_new(output / 'CONTROL_EVIDENCE.json', result)
        (output / 'REPORT.md').write_text(render_report(result))
        write_new(output / 'EVIDENCE_SHA256.json', {'files': inventory(output)})
    return result, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--port', type=int, default=8010)
    args = parser.parse_args()
    try:
        result, output = benchmark(args)
        print(canonical({'status': result['status'], 'selected': result.get('selected'),
            'correct_of32': {k: v.get('correct') for k, v in result['metrics'].items()},
            'rollback': result.get('rollback', {}).get('status'),
            'day9_preserved': result['day9_preserved'], 'evidence_directory': str(output),
            'control_evidence_sha256': sha(output / 'CONTROL_EVIDENCE.json'),
            'report_sha256': sha(output / 'REPORT.md'), 'next': 'STOP_FOR_CONTROL_REVIEW'}))
        return 0 if result['status'] == 'BENCHMARK_COMPLETE_STOP_FOR_CONTROL_REVIEW' else 2
    except Exception as exc:
        print(canonical({'status': 'STOP_FOR_CONTROL_REVIEW', 'error_type': type(exc).__name__, 'reason': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
