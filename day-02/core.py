"""Small fail-closed primitives shared by the host controller."""

import hashlib
import json
import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_SHA = "3c2ed09a2e5c9e35a70e18b11dfe0a29a675db66"
MODEL = "gpt-6.1-sol"
EFFORT = "medium"
ALLOWED_CHANGES = {"src/bublik/domain/task.py", "tests/test_task_status_invariant.py"}


class Blocked(ValueError):
    """Missing evidence or an unconfirmed permission stops execution."""


def require(condition: object, code: str) -> None:
    if not condition:
        raise Blocked(code)


def encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def no_links(path: Path) -> None:
    require(path.is_absolute(), "ABSOLUTE_PATH_REQUIRED")
    require(not any(p.is_symlink() for p in (path, *path.parents)), "SYMLINK_FORBIDDEN")


def new_json(path: Path, value: object) -> None:
    no_links(path.absolute())
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def inventory(root: Path) -> dict[str, dict[str, object]]:
    """Inventory all regular files/modes; reject links and special files."""
    no_links(root.absolute())
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "SYMLINK_IN_WORKSPACE")
        if path.is_dir():
            result[path.relative_to(root).as_posix()] = {
                "type": "directory",
                "mode": stat.S_IMODE(path.stat().st_mode),
            }
            continue
        require(path.is_file(), "SPECIAL_FILE_IN_WORKSPACE")
        result[path.relative_to(root).as_posix()] = {
            "type": "file",
            "sha256": sha(path.read_bytes()),
            "mode": stat.S_IMODE(path.stat().st_mode),
        }
    return result


def delta(before: dict, after: dict) -> list[str]:
    return sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
