"""Static checks for the sanitized publication; no ML or external dependencies."""
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWLIST = {'README.md', 'REPRODUCIBILITY.md', 'RESULTS.json', 'loss_curve.png',
             'verify_publication.py', 'tests/test_publication.py', 'MANIFEST.sha256.json'}
CHART_SHA = 'db9181d7a2a069076203e8dfe144f57e754c0c2f33de594b9eb6323318f02067'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def validate_metrics(m):
    setup = m['setup']
    require(setup['primary_eval_items'] == 40 and setup['dimensions'] ==
            {'FORMAT': 8, 'STYLE': 8, 'KNOWLEDGE': 12, 'OOD': 12}, 'EVAL_DENOMINATORS')
    require((setup['train_examples'], setup['valid_examples'], setup['fictional_facts']) == (96, 20, 6), 'SETUP_COUNTS')
    expected = {'Base': (1, 0, 0, 0, 1), 'Base+Prompt': (1, 0, 0, 0, 1),
                'TunedBest': (11, 5, 3, 1, 2), 'TunedLate': (11, 5, 3, 1, 2)}
    require(set(m['strict_40']) == set(expected), 'STRICT_ARMS')
    for arm, values in expected.items():
        r = m['strict_40'][arm]
        require(r['n'] == 40 and tuple(r[k] for k in ('correct', 'FORMAT', 'STYLE', 'KNOWLEDGE', 'OOD')) == values, 'STRICT_METRICS')
        require(sum(r[k] for k in setup['dimensions']) == r['correct'], 'STRICT_ARITHMETIC')
    d = m['tuned_details']
    require((d['json_shape_valid'], d['json_shape_n'], d['wrong_target_format']) == (8, 8, 3), 'JSON_SHAPE_VS_CONTENT')
    require((d['knowledge_direct_correct'], d['knowledge_direct_n'], d['knowledge_paraphrase_correct'], d['knowledge_paraphrase_n']) == (1, 6, 0, 6), 'WEAK_FACT_RECALL')
    pair = m['paired_base_tuned']
    require(pair == {'gains': 11, 'losses': 1, 'both_wrong': 28, 'both_correct': 0, 'delta_percentage_points': 25}, 'PAIRED_COUNTS')
    require((pair['gains'] - pair['losses']) / 40 * 100 == 25, 'PAIRED_DELTA')
    ood = m['ood']; secondary = ood['secondary_content_review']
    require((ood['n'], ood['strict_base_correct'], ood['strict_tuned_correct'], ood['strict_paired_regressions']) == (12, 1, 2, 1), 'STRICT_OOD')
    require(ood['owner_adjudication'] == 'PENDING', 'OWNER_SIGNOFF_NOT_PROVIDED')
    require(secondary['kind'] == 'POST_HOC_MANUAL_CONTROL_ADJUDICATION_NOT_FROZEN_BENCHMARK', 'SECONDARY_LABEL')
    require(tuple(secondary[k] for k in ('base_correct', 'tuned_correct', 'semantic_losses', 'semantic_gains', 'both_correct', 'both_incorrect')) == (9, 3, 7, 1, 2, 2), 'SECONDARY_OOD')
    require(sum(secondary[k] for k in ('semantic_losses', 'semantic_gains', 'both_correct', 'both_incorrect')) == 12, 'SECONDARY_PAIRS')
    f = m['base_facts_knowledge_only']
    require((f['n'], f['strict_correct'], f['secondary_content_correct'], f['actual_rag']) == (12, 0, 9, False), 'CONTEXT_NOT_RAG')
    require(f['secondary_status'] == 'POST_HOC_CONTENT_INSPECTION_NOT_FROZEN_SCORE', 'CONTEXT_CONTENT_CAVEAT')
    loss = m['loss']
    require(loss['steps'] == [25, 50, 75, 100, 125, 150], 'LOSS_STEPS')
    require(loss['train'] == [2.1253, .9489, .6156, .4604, .2884, .2708] and
            loss['valid'] == [1.4303, .8935, .5985, .4604, .4220, .3011], 'LOSS_VALUES')
    require(all(a > b for a, b in zip(loss['valid'], loss['valid'][1:])), 'VALID_DESCENT')
    require(loss['overfit_signal'] == loss['turning_point'] == 'NOT_OBSERVED', 'NO_INVENTED_OVERFIT')
    cp = m['checkpoints']
    require(cp['saved_steps'] == [50, 100, 150] and cp['best_step'] == cp['late_step'] == 150 and
            cp['same_adapter'] is True and cp['distinct_best_late_comparison'] is False and
            cp['best_late_raw_identical_items'] == 40, 'BEST_EQUALS_LATE')
    cost = m['measurements']
    require(cost['training_routine_seconds'] == 82.29 and cost['adapter_bytes_each'] == 822576 and
            cost['base_weight_bytes'] == 723674815, 'TIME_DISK_MEASUREMENTS')
    require(cost['median_generation_seconds'] == {'Base': .1645, 'Base+Prompt': .2029, 'TunedBest': .1581}, 'LATENCY_VALUES')
    require(cost['prompt_tokens_40'] == {'Base': 1778, 'Base+Prompt': 7658, 'TunedBest': 7658} and
            cost['output_tokens_40'] == {'Base': 1042, 'Base+Prompt': 1549, 'TunedBest': 360}, 'TOKEN_VALUES')
    require(all(cost[k] == 'NOT_MEASURED' for k in ('monetary_cost', 'power', 'peak_ram', 'monetary_savings')) and
            cost['end_to_end_speedup'] == 'NOT_ESTABLISHED', 'COST_SPEED_CAVEAT')
    require(m['scoring']['secondary_review_replaces_primary'] is False and
            not any(m['limits'].values()), 'PRIVACY_REPRODUCTION_LIMITS')


def validate_report(text, m):
    expected_rows = [
        '| Base | **1/40 (2.5%)** | 0/8 | 0/8 | 0/12 | 1/12 |',
        '| Base + good prompt | **1/40 (2.5%)** | 0/8 | 0/8 | 0/12 | 1/12 |',
        '| TunedBest | **11/40 (27.5%)** | 5/8 | 3/8 | 1/12 | 2/12 |',
        '| TunedLate (same step-150 adapter) | **11/40 (27.5%)** | 5/8 | 3/8 | 1/12 | 2/12 |']
    require(all(row in text for row in expected_rows), 'REPORT_TABLE_DRIFT')
    for step, tr, va in zip(m['loss']['steps'], m['loss']['train'], m['loss']['valid']):
        require(f'| {step} | {tr:.4f} | {va:.4f} |' in text, 'REPORT_LOSS_DRIFT')
    required = ('**1/6 direct**', '**0/6 paraphrased**', '**0/12 strict**', '**9/12**', '**3/12**',
                '**7 semantic losses**', '**post-hoc, manual content adjudication by Control**',
                'Owner adjudication of that strict regression remains PENDING',
                '**overfitting was NOT_OBSERVED**', '**Best and Late are identical**',
                '**82.29 seconds**', '**822,576 bytes**', 'NOT_MEASURED', 'not RAG',
                'excludes tokenization and loading', 'different answer lengths', 'not published')
    require(all(phrase in text for phrase in required), 'REPORT_CAVEAT_MISSING')


def check_png(data):
    require(data.startswith(b'\x89PNG\r\n\x1a\n'), 'PNG_SIGNATURE')
    pos, dimensions, metadata = 8, None, []
    while pos < len(data):
        n = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]; payload = data[pos+8:pos+8+n]
        crc = struct.unpack('>I', data[pos+8+n:pos+12+n])[0]
        require(zlib.crc32(kind + payload) & 0xffffffff == crc, 'PNG_CRC')
        if kind == b'IHDR': dimensions = struct.unpack('>II', payload[:8])
        if kind in (b'tEXt', b'iTXt', b'zTXt'): metadata.append(payload.decode('latin1'))
        pos += n + 12
        if kind == b'IEND': break
    require(pos == len(data) and dimensions == (1620, 864), 'PNG_LAYOUT')
    return metadata


def privacy(root):
    patterns = (r'D8-(?:EVAL|TRAIN|VALID|RESERVE)-[0-9]{3}',
                r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', r'gh[pousr]_[A-Za-z0-9]{20,}',
                r'github_pat_[A-Za-z0-9_]{20,}', '/' + 'Users' + r'/[^/\s]+', '/' + 'home' + r'/[^/\s]+')
    for p in root.rglob('*'):
        if not p.is_file(): continue
        text = '\n'.join(check_png(p.read_bytes())) if p.suffix == '.png' else p.read_text()
        require(not any(re.search(pattern, text) for pattern in patterns), 'PRIVATE_OR_SECRET_TEXT')
    forbidden_keys = {'sample_id', 'fact_id', 'gold', 'raw', 'token_ids', 'rendered_prompt_token_ids'}
    def walk(value):
        if isinstance(value, dict):
            require(not forbidden_keys.intersection(value), 'ITEM_LEVEL_DATA')
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(json.loads((root / 'RESULTS.json').read_text()))


def verify(root=ROOT):
    root = Path(root)
    files = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(files == ALLOWLIST, 'UNEXPECTED_OR_MISSING_FILE')
    manifest = json.loads((root / 'MANIFEST.sha256.json').read_text())
    records = {row['path']: row for row in manifest['files']}
    require(len(records) == len(manifest['files']) and set(records) == ALLOWLIST - {'MANIFEST.sha256.json'}, 'MANIFEST_INVENTORY')
    for path, row in records.items():
        data = (root / path).read_bytes()
        require(hashlib.sha256(data).hexdigest() == row['sha256'] and len(data) == row['bytes'], 'MANIFEST_HASH')
    m = json.loads((root / 'RESULTS.json').read_text())
    validate_metrics(m); validate_report((root / 'README.md').read_text(), m)
    require(hashlib.sha256((root / 'loss_curve.png').read_bytes()).hexdigest() == CHART_SHA == m['chart']['sha256'], 'CHART_CHANGED')
    privacy(root)
    return {'status': 'G5_STATIC_CHECK_PASS', 'manifest_matches': len(records),
            'files': len(files), 'chart': 'SUPPLIED_BYTES_UNCHANGED', 'privacy': 'ALLOWLIST_PATTERN_SCAN_PASS_WITH_LIMITS',
            'real_ml_during_preparation': 'NOT_RUN', 'publication': 'HOLD_CONTROL_APPROVAL'}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), sort_keys=True))
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(exc)}))
        raise SystemExit(2)
