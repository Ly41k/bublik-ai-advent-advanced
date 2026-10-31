#!/usr/bin/env python3
"""One offline Day9 checkpoint150 fusion and one MLX affine4 conversion."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import gc
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path('artifacts/day10').absolute()
LABELS = ('BUG', 'FEATURE', 'DOCS', 'NEED_INFO')
SMOKE_TEXT = 'Technical readiness check: add an export button.'
GENERATION = {'seed_per_request': 9001, 'max_new_tokens': 64, 'max_context': 2048, 'temperature': 0}
PINS = {'mlx': '0.32.4', 'mlx-lm': '0.32.2', 'transformers': '5.21.0', 'huggingface_hub': '1.33.0'}
ADAPTER_SHA = '14156cc4f94d9b2baa9d1a3fd8dc18e71b92aad64f7621489e6a807a40fff8bc'
G5_SHA = '7a153f17ee8d2acbbc76c38f68406b7b9aac1408f874fca04aeb477b2ebd9375'


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def objsha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(canonical(value) + '\n')
        f.flush()
        os.fsync(f.fileno())


def inventory(folder):
    folder = Path(folder)
    return {p.relative_to(folder).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def disk_size(folder):
    files = [p for p in Path(folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    seen = set()
    allocated = 0
    for p in files:
        s = p.stat()
        key = (s.st_dev, s.st_ino)
        if key not in seen:
            allocated += s.st_blocks * 512
            seen.add(key)
    return {'logical_bytes': sum(p.stat().st_size for p in files),
            'allocated_bytes_unique_inodes': allocated, 'files': len(files)}


def versions(require_mac=True):
    if require_mac:
        need(sys.platform == 'darwin' and platform.machine() == 'arm64', 'OWNER_APPLE_SILICON_MAC_REQUIRED')
        need(platform.python_version() == '3.13.3', 'PYTHON_PIN_MISMATCH')
    actual = {k: metadata.version(k) for k in PINS}
    need(actual == PINS, 'MLX_PACKAGE_PINS_CHANGED')
    return {'python': platform.python_version(), **actual}


@contextmanager
def offline():
    """Block outbound IP/DNS during model work; loopback HTTP remains outside this context."""
    originals = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo
    before = {k: os.environ.get(k) for k in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY')}
    def connect(sock, *a, **k):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise PermissionError('OUTBOUND_NETWORK_FORBIDDEN')
        return originals[0](sock, *a, **k)
    def connect_ex(sock, *a, **k):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise PermissionError('OUTBOUND_NETWORK_FORBIDDEN')
        return originals[1](sock, *a, **k)
    def dns(*a, **k):
        raise PermissionError('DNS_FORBIDDEN')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = connect, connect_ex, dns
    try:
        yield
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = originals
        for key, value in before.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def day9_context(paths):
    """Reuse authenticated Day9 verification. No exports, training or captures."""
    required = {'g5_path', 'recovery_source', 'tokenizer_source', 'source',
                'g2_source', 'r70_source', 'diagnostic_source', 'owner_source',
                'derived', 'audit', 'split', 'training', 'model'}
    need(isinstance(paths, dict) and set(paths) == required, 'EXPLICIT_DAY9_PATHS_REQUIRED')
    need(all(isinstance(v, str) and Path(v).expanduser().is_absolute() for v in paths.values()),
         'DAY9_PATHS_MUST_BE_ABSOLUTE')
    resolved = {key: str(Path(value).expanduser().absolute()) for key, value in paths.items()}
    g5_path = Path(resolved['g5_path']).resolve()
    need(sha(g5_path.parent / 'SOURCE_MANIFEST.json') == G5_SHA, 'G5_MANIFEST_CHANGED')
    sys.path.insert(0, str(g5_path.parent))
    spec = importlib.util.spec_from_file_location('d10_existing_g5', g5_path)
    g5 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g5)
    args = SimpleNamespace(**{key: value for key, value in resolved.items() if key != 'g5_path'})
    with offline():
        context = g5.context(args)
        g5.native_check(context, args)
    need(len(context['messages']) == 32, 'FINAL32_NOT_32')
    for messages in context['messages']:
        need([m['role'] for m in messages] == ['system', 'user'], 'DAY9_MESSAGE_CONTRACT')
        need(messages[0] == context['messages'][0][0], 'VARIABLE_SYSTEM_PROMPT_NOT_SUPPORTED')
    return g5, context


def source_identity():
    return {name: sha(HERE / name) for name in
            ('prepare_model.py', 'service.py', 'benchmark.py', 'README.md')}


def memory(mx=None):
    import resource
    ps = subprocess.run(['ps', '-o', 'rss=', '-p', str(os.getpid())],
                        check=True, capture_output=True, text=True)
    result = {'rss_bytes': int(ps.stdout.strip()) * 1024,
              'process_high_water_rss_bytes': int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
              * (1 if sys.platform == 'darwin' else 1024), 'metal': {}}
    if mx is not None:
        for label in ('active', 'cache', 'peak'):
            method = getattr(mx, 'get_' + label + '_memory', None)
            if method is None:
                method = getattr(getattr(mx, 'metal', None), 'get_' + label + '_memory', None)
            try:
                result['metal'][label + '_bytes'] = int(method()) if method else None
            except (RuntimeError, AttributeError):
                result['metal'][label + '_bytes'] = None
    return result


def install_service_deps(root):
    """Freeze every installed distribution so pip cannot update the ML stack."""
    before = {d.metadata['Name'].lower(): d.version for d in metadata.distributions()
              if d.metadata['Name']}
    constraints = root / 'installed.constraints.txt'
    constraints.write_text(''.join(f'{name}=={version}\n' for name, version in sorted(before.items())))
    command = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
               '--constraint', str(constraints), 'fastapi==0.121.0', 'uvicorn==0.38.0']
    with (root / 'dependency-install.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    after = {d.metadata['Name'].lower(): d.version for d in metadata.distributions()
             if d.metadata['Name']}
    need(all(after.get(k) == v for k, v in before.items()), 'EXISTING_DEPENDENCY_CHANGED_STOP')
    need(result.returncode == 0, 'DEPENDENCY_INSTALL_FAILED_SEE_LOCAL_LOG')
    return {name: metadata.version(name) for name in ('fastapi', 'uvicorn', 'pydantic')}


def validate_model_spec(spec):
    path = Path(spec['path'])
    need(path.is_absolute() and path.is_dir(), 'MODEL_DIRECTORY_MISSING')
    need(inventory(path) == spec['inventory'], 'RELEASE_MODEL_BYTES_CHANGED')
    return path


def load_registry(path):
    path = Path(path).expanduser().resolve()
    digest = path.with_name('REGISTRY.sha256').read_text().strip()
    need(sha(path) == digest, 'REGISTRY_SHA_MISMATCH')
    r = read(path)
    need(r['schema'] == 'bublik-day10-r1' and r['generation'] == GENERATION, 'REGISTRY_CONTRACT')
    need(r['implementation_sha256'] == source_identity(), 'IMPLEMENTATION_CHANGED_AFTER_PREPARATION')
    return r, digest


def prepare(args):
    os.umask(0o077)
    runtime = versions()
    root = args.root.expanduser().absolute()
    need(not root.exists() and not root.is_symlink(), 'DAY10_OUTPUT_EXISTS_NO_OVERWRITE')
    need(root.parent.is_dir() and not root.parent.is_symlink(), 'PRIVATE_PARENT_MISSING')
    root.mkdir(mode=0o700)
    args.created_output = True
    write_new(root / 'STARTED.json', {'status': 'PREPARATION_STARTED', 'versions': runtime,
                                     'implementation_sha256': source_identity()})
    deps = install_service_deps(root) if args.install_service_deps else {
        k: metadata.version(k) for k in ('fastapi', 'uvicorn', 'pydantic')}
    need(versions() == runtime, 'STACK_CHANGED_AFTER_DEPENDENCIES')
    started = time.perf_counter()
    day9_paths = read(args.paths)
    g5, c = day9_context(day9_paths)
    before_task = c['task']
    models = root / 'models'
    models.mkdir(mode=0o700)
    fp16 = models / 'tuned-step150-fp16-v1'
    q4 = models / 'tuned-step150-affine4-g64-v1'
    with offline():
        import mlx.core as mx
        from mlx.utils import tree_map, tree_unflatten
        from mlx_lm.utils import load, save
        from mlx_lm.convert import convert
        fusion_started = time.perf_counter()
        model, tokenizer, config = load(str(c['model']), adapter_path=str(c['adapter']),
            return_config=True, lazy=False, trust_remote_code=False,
            tokenizer_config={'local_files_only': True, 'trust_remote_code': False})
        fused = [(name, module.fuse(dequantize=True)) for name, module in model.named_modules()
                 if hasattr(module, 'fuse')]
        need(len(fused) == 16, 'EXPECTED_16_Q_V_LORA_MODULES')
        model.update_modules(tree_unflatten(fused))
        model.update(tree_map(lambda value: value.astype(mx.float16)
                     if mx.issubdtype(value.dtype, mx.floating) else value, model.parameters()))
        need(not any(hasattr(module, 'fuse') for _, module in model.named_modules()), 'ADAPTER_NOT_FULLY_FUSED')
        config.pop('quantization', None)
        config.pop('quantization_config', None)
        config['torch_dtype'] = 'float16'
        config['dtype'] = 'float16'
        mx.eval(model.parameters())
        mx.synchronize()
        smoke_messages = [{'role': 'system', 'content': c['messages'][0][0]['content']},
                          {'role': 'user', 'content': SMOKE_TEXT}]
        smoke_prompt_sha = hashlib.sha256(tokenizer.apply_chat_template(
            smoke_messages, tokenize=False, add_generation_prompt=True).encode()).hexdigest()
        save(fp16, c['model'], model, tokenizer, config, donate_model=False)
        mx.synchronize()
        fusion_seconds = time.perf_counter() - fusion_started
        del fused, model, tokenizer
        gc.collect()
        mx.clear_cache()
        quant_started = time.perf_counter()
        convert(hf_path=str(fp16), mlx_path=str(q4), quantize=True,
                q_bits=4, q_group_size=64, q_mode='affine', dtype='float16', trust_remote_code=False)
        mx.synchronize()
        quant_seconds = time.perf_counter() - quant_started
        qconfig = read(q4 / 'config.json')
        quant = qconfig.get('quantization', qconfig.get('quantization_config', {}))
        need(quant.get('bits') == 4 and quant.get('group_size') == 64
             and quant.get('mode', 'affine') == 'affine', 'QUANTIZATION_NOT_AFFINE4_G64')
    # A fixed, intentionally incomplete local fixture exercises the REAL loader's
    # missing-safetensors exception. It is not a model or a second q4 candidate.
    broken = root / 'load-error-fixture'
    broken.mkdir(mode=0o700)
    write_new(broken / 'config.json', read(fp16 / 'config.json'))
    specs = {}
    for name, path in [('base', c['model']), ('q4', q4), ('fp16', fp16), ('load-error-fixture', broken)]:
        inv = inventory(path)
        specs[name] = {'path': str(path), 'version': name + '-' + objsha(inv)[:16],
                       'inventory': inv, 'disk': disk_size(path)}
    need(specs['base']['inventory'] == c['training_provenance']['model_inventory'], 'BASE_CHANGED_AFTER_PREPARATION')
    c['drift']()
    need(c['task'] == before_task, 'DAY9_TASK_CHANGED')
    registry = {'schema': 'bublik-day10-r1', 'models': specs, 'generation': GENERATION,
        'system_prompt': c['messages'][0][0]['content'], 'task': c['task'],
        'smoke_prompt_sha256': smoke_prompt_sha,
        'day9_paths': day9_paths, 'day9_adapter_sha256': ADAPTER_SHA,
        'versions': runtime, 'service_dependencies': deps,
        'implementation_sha256': source_identity(),
        'final32_serialization_sha256': c['local_meta']['prompt_serialization_sha256'],
        'preparation': {'fusion_seconds': fusion_seconds, 'quantization_seconds': quant_seconds,
                        'total_seconds': time.perf_counter() - started,
                        'quality': 'NOT_RUN_USE_BENCHMARK', 'day9_preserved': True}}
    write_new(root / 'REGISTRY.json', registry)
    (root / 'REGISTRY.sha256').write_text(sha(root / 'REGISTRY.json') + '\n')
    write_new(root / 'PREPARATION.json', {'status': 'MODELS_PREPARED_QUALITY_NOT_RUN',
        'registry_sha256': sha(root / 'REGISTRY.json'), 'versions': runtime,
        'timing': registry['preparation'], 'model_disk': {k: v['disk'] for k, v in specs.items()}})
    return {'status': 'MODELS_PREPARED_QUALITY_NOT_RUN', 'root': str(root),
            'registry_sha256': sha(root / 'REGISTRY.json'), 'training': 'NOT_RUN', 'api_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--paths', type=Path, required=True, help='Private JSON mapping of explicit absolute Day9 paths')
    parser.add_argument('--install-service-deps', action='store_true')
    args = parser.parse_args()
    try:
        print(canonical(prepare(args)))
        return 0
    except Exception as exc:
        result = {'status': 'STOP_FOR_CONTROL_REVIEW', 'action': 'prepare',
                  'error_type': type(exc).__name__, 'reason': str(exc)}
        root = args.root.expanduser().absolute()
        if getattr(args, 'created_output', False) and not (root / 'FAILURE.json').exists():
            write_new(root / 'FAILURE.json', result)
        print(canonical(result))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
