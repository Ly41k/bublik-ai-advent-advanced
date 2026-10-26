"""Host-only fixed-destination Markdown writer using directory descriptors."""

import os
from pathlib import Path

from core import no_links, require

FORBIDDEN = {"readme.md", "agents.md", "agents.override.md", "skill.md"}


def write_markdown(root: Path, name: str, content: str) -> Path:
    require(
        name == Path(name).name and "/" not in name and "\\" not in name, "DOCUMENT_PATH_FORBIDDEN"
    )
    require(name.lower() not in FORBIDDEN and name.endswith(".md"), "DOCUMENT_NAME_FORBIDDEN")
    require(name not in {".", ".."} and bool(content.strip()), "DOCUMENT_INVALID")
    no_links(root.absolute())
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(
            name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
        )
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(directory)
    return root / name
