"""Load local Neon/dotenv files into os.environ without logging values.

Order: `.env` then `.env.local` (local wins). Existing process env is never overwritten.
Safe for API/worker boot when `neon deploy` / `neon env pull` wrote `.env.local`.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env_files(*paths: str | Path, override: bool = False) -> list[str]:
    """Parse KEY=VALUE lines; returns list of file paths that were read."""
    loaded: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            if override or key not in os.environ:
                os.environ[key] = value
        loaded.append(str(path.resolve()))
    return loaded


def load_default_env(root: str | Path | None = None) -> list[str]:
    """Load repo-root `.env` then `.env.local` (Neon CLI default pull target)."""
    base = Path(root) if root is not None else Path.cwd()
    return load_env_files(base / ".env", base / ".env.local", override=False)
