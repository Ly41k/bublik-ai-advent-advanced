#!/usr/bin/env python3
"""Local sequential FastAPI classifier; candidate load commits only after smoke."""
import argparse
from contextlib import asynccontextmanager
import gc
import hashlib
import os
from pathlib import Path
import threading
import time
from typing import Literal, Optional
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from prepare_model import (DEFAULT_ROOT, GENERATION, LABELS, SMOKE_TEXT, canonical, load_registry,
                           memory, need, offline, read, sha, validate_model_spec, versions)

class ClassifyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=1, max_length=16000)


class ModelRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    model: Literal['base', 'tuned']
    version: Optional[Literal['q4', 'fp16', 'load-error-fixture']] = None


class MLXBackend:
    def __init__(self, path, system_prompt, generation):
        self.system_prompt = system_prompt
        self.generation = generation
        started = time.perf_counter()
        with offline():
            import mlx.core as mx
            from mlx_lm import load, stream_generate
            from mlx_lm.sample_utils import make_sampler
            self.mx, self.stream_generate, self.make_sampler = mx, stream_generate, make_sampler
            self.model, self.tokenizer = load(str(path), adapter_path=None, lazy=False,
                trust_remote_code=False, tokenizer_config={'local_files_only': True, 'trust_remote_code': False})
            mx.eval(self.model.parameters())
            mx.synchronize()
        self.load_seconds = time.perf_counter() - started

    def render(self, text):
        messages = [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': text}]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        need(isinstance(prompt, str) and bool(prompt), 'INVALID_CHAT_TEMPLATE')
        return prompt

    def infer(self, text, max_tokens=None):
        started = time.perf_counter()
        limit = self.generation['max_new_tokens'] if max_tokens is None else max_tokens
        with offline():
            prompt = self.render(text)
            bos = self.tokenizer.bos_token
            token_count = len(self.tokenizer.encode(prompt, add_special_tokens=bos is None or not prompt.startswith(bos)))
            need(token_count + limit <= self.generation['max_context'], 'CONTEXT_LIMIT_EXCEEDED')
            self.mx.random.seed(self.generation['seed_per_request'])
            parts, last = [], None
            # Every call creates a fresh generator and KV cache; no prompt_cache is passed.
            for chunk in self.stream_generate(self.model, self.tokenizer, prompt=prompt,
                    max_tokens=limit, sampler=self.make_sampler(temp=0)):
                parts.append(chunk.text)
                last = chunk
            self.mx.synchronize()
            need(last is not None, 'EMPTY_GENERATION')
            raw = ''.join(parts)
            valid = raw in LABELS and last.finish_reason == 'stop'
            return {'raw': raw, 'label': raw if valid else None, 'valid': valid,
                    'finish_reason': last.finish_reason,
                    'usage': {'input_tokens': last.prompt_tokens, 'output_tokens': last.generation_tokens},
                    'prompt_serialization_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'generation_seconds': time.perf_counter() - started}

    def smoke(self):
        # Explicit one-token readiness forward, outside final32 and its measured latency.
        return self.infer(SMOKE_TEXT, max_tokens=1)

    def resources(self):
        return memory(self.mx)

    def close(self):
        del self.model, self.tokenizer
        gc.collect()
        self.mx.clear_cache()


class Manager:
    def __init__(self, registry, registry_sha, root, enable_load_failure_test=False,
                 backend_factory=MLXBackend, verify_spec=validate_model_spec):
        self.registry, self.registry_sha = registry, registry_sha
        self.root = Path(root)
        self.factory, self.verify_spec = backend_factory, verify_spec
        self.lock = threading.RLock()
        self.backend = None
        self.active = None
        self.last_switch = None
        self.preferred = 'q4'
        self.pid = os.getpid()
        self.instance = uuid.uuid4().hex
        self.enable_load_failure_test = enable_load_failure_test
        selection = self.root / 'SELECTION.json'
        if selection.exists():
            selected = read(selection)
            need(selected['registry_sha256'] == registry_sha and selected['selected'] in ('q4', 'fp16'),
                 'INVALID_PERSISTED_SELECTION')
            self.preferred = selected['selected']

    def identity(self):
        return {'pid': self.pid, 'instance_id': self.instance, 'active': self.active,
                'model_version': None if self.active is None else self.registry['models'][self.active]['version'],
                'registry_sha256': self.registry_sha}

    def health(self):
        with self.lock:
            return {**self.identity(), 'ready': self.backend is not None,
                    'preferred_tuned': self.preferred,
                    'memory': memory() if self.backend is None else self.backend.resources(),
                    'last_switch': self.last_switch,
                    'generation': GENERATION, 'load_failure_test_enabled': self.enable_load_failure_test}

    def switch(self, model, version=None):
        with self.lock:
            need(model in ('base', 'tuned'), 'UNKNOWN_MODEL')
            need(model != 'base' or version is None, 'BASE_HAS_NO_VERSION_OPTION')
            key = 'base' if model == 'base' else (version or self.preferred)
            need(key in self.registry['models'], 'UNKNOWN_MODEL_VERSION')
            need(key != 'load-error-fixture' or self.enable_load_failure_test, 'LOAD_FAILURE_TEST_DISABLED')
            if key == self.active:
                return {**self.health(), 'changed': False}
            started = time.perf_counter()
            candidate = None
            before = self.identity()
            try:
                checked = time.perf_counter()
                path = self.verify_spec(self.registry['models'][key])
                validation_seconds = time.perf_counter() - checked
                candidate = self.factory(path, self.registry['system_prompt'], GENERATION)
                double_memory = candidate.resources()
                smoke_started = time.perf_counter()
                smoke = candidate.smoke()
                need(smoke['prompt_serialization_sha256'] == self.registry['smoke_prompt_sha256'],
                     'CANDIDATE_CHAT_TEMPLATE_CHANGED')
                need(smoke['usage']['output_tokens'] >= 1, 'CANDIDATE_SMOKE_FAILED')
                readiness_seconds = time.perf_counter() - smoke_started
                double_memory_after_smoke = candidate.resources()
            except Exception:
                if candidate is not None:
                    candidate.close()
                # Commit has not happened: the old working object is still active.
                need(self.identity() == before, 'ACTIVE_MODEL_CHANGED_ON_LOAD_FAILURE')
                raise
            previous = self.backend
            self.backend, self.active = candidate, key
            if key in ('q4', 'fp16'):
                self.preferred = key
            cleanup_error = None
            if previous is not None:
                try:
                    previous.close()
                except Exception as exc:
                    cleanup_error = type(exc).__name__
            self.last_switch = {'to': key, 'from': before['active'],
                'validation_seconds': validation_seconds, 'load_seconds': candidate.load_seconds,
                'readiness_smoke_seconds': readiness_seconds, 'readiness_generated_tokens': smoke['usage']['output_tokens'],
                'switch_wall_seconds': time.perf_counter() - started,
                'memory_both_models_loaded': double_memory,
                'memory_both_after_smoke': double_memory_after_smoke,
                'memory_after_release': candidate.resources(), 'cleanup_error': cleanup_error}
            return {**self.health(), 'changed': True}

    def classify(self, text):
        with self.lock:
            need(self.backend is not None, 'NO_ACTIVE_MODEL')
            result = self.backend.infer(text)
            return {**result, **self.identity(), 'memory': self.backend.resources()}


def create_app(manager):
    @asynccontextmanager
    async def lifespan(app):
        manager.switch('base')
        yield
        if manager.backend is not None:
            manager.backend.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    # Synchronous MLX calls run on this single event-loop thread. No await inside
    # an operation; the RLock also protects direct calls and future thread use.
    @app.get('/health')
    async def health():
        return manager.health()

    @app.post('/classify')
    async def classify(body: ClassifyRequest):
        try:
            return manager.classify(body.text)
        except Exception as exc:
            raise HTTPException(503, detail={'error': type(exc).__name__, **manager.identity()}) from exc

    @app.post('/model')
    async def model(body: ModelRequest):
        try:
            return manager.switch(body.model, body.version)
        except Exception as exc:
            raise HTTPException(503, detail={'error': type(exc).__name__,
                'previous_preserved': manager.backend is not None, **manager.identity()}) from exc
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--port', type=int, default=8010)
    parser.add_argument('--enable-load-failure-test', action='store_true')
    args = parser.parse_args()
    try:
        versions()
        registry, digest = load_registry(args.root / 'REGISTRY.json')
        manager = Manager(registry, digest, args.root, args.enable_load_failure_test)
        import uvicorn
        uvicorn.run(create_app(manager), host='127.0.0.1', port=args.port,
                    workers=1, reload=False, access_log=False, log_level='warning',
                    loop='asyncio', http='h11', ws='none')
        return 0
    except Exception as exc:
        print(canonical({'status': 'STOP_FOR_CONTROL_REVIEW', 'action': 'service',
                         'error_type': type(exc).__name__, 'reason': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
