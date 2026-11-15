"""Which version of PhysicsMind is running, saved with every piece of feedback.

The label is the release number plus the git commit when git is available, e.g. "0.2.0 · f36985a". Uncommitted
local edits are marked "+ local changes", so feedback from a work-in-progress copy is never mistaken for a release.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import subprocess

from . import __version__

ROOT = Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    try:
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


@lru_cache(maxsize=1)
def app_version() -> str:
    commit = _git("rev-parse", "--short", "HEAD")
    if not commit:
        return __version__
    label = f"{__version__} · {commit}"
    if _git("status", "--porcelain", "--untracked-files=no"):
        label += " + local changes"
    return label
