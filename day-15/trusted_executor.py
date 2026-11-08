"""Run ONLY an exact Day 14 whitelist match in a pinned network-isolated Docker image."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

from trusted_day14_runner import ALLOWED, Halt, kotlin_sources, make_kotlin_script, parse_generated, parse_review

IMAGE = 'gradle:8.14.6-jdk17'
IMAGE_SHA = 'sha256:2f977f0a5b95ade2eabcfcf4840ff4b29fc176c61ee56fd184df038f64b18f9e'
MARKERS = ('T1_GENERATED_KOTLIN_TEST_PASS', 'T2_GENERATED_KOTLIN_TEST_PASS', 'T3_GENERATED_KOTLIN_TEST_PASS', 'ALL_THREE_GENERATED_KOTLIN_CHECKS_PASS')


def trusted_kotlin_check(parts: dict[str, str], docker_socket: str | None = None) -> dict:
    """No arbitrary code, host files, network, root privileges, or Docker image pull."""
    if parts != ALLOWED:
        return {'status': 'BLOCKED_NOT_WHITELISTED'}
    if os.getenv('BUBLIK_D15_ALLOW_KOTLIN') != 'YES':
        return {'status': 'DISABLED_BY_DEFAULT'}
    sock = docker_socket or os.getenv('BUBLIK_D15_DOCKER_SOCKET') or str(Path.home() / '.colima/bublik-d14/docker.sock')
    if not Path(sock).is_socket():
        return {'status': 'STOP_SOCKET_UNAVAILABLE'}
    cmd = ['docker', '--host', f'unix://{sock}']
    try:
        found = subprocess.run(cmd + ['image', 'inspect', '--format', '{{.Id}}', IMAGE], capture_output=True, text=True, timeout=8, check=True)
        if found.stdout.strip() != IMAGE_SHA:
            return {'status': 'STOP_IMAGE_MISMATCH'}
        run = subprocess.run(cmd + [
            'run', '--rm', '-i', '--pull', 'never', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--pids-limit', '64', '--memory', '1g', '--cpus', '1', '--user', '65532:65532',
            '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=64m',
            '--tmpfs', '/work:rw,noexec,nosuid,nodev,size=64m,uid=65532,gid=65532,mode=0700',
            '--entrypoint', '/bin/sh', IMAGE, '-eu', '-s'
        ], input=make_kotlin_script(parts), capture_output=True, text=True, timeout=65, check=False)
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return {'status': 'STOP_DOCKER_FAILURE'}
    output = run.stdout
    if run.returncode != 0 or not all(output.count(m) == 1 for m in MARKERS):
        return {'status': 'STOP_COMPILE_OR_TEST_FAILURE'}
    return {'status': 'PASS', 'tests': list(MARKERS[:-1]), 'network': 'NONE', 'untrusted_code_executed': False}
