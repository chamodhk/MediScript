#!/usr/bin/env python3
"""
Run the MediScript FastAPI backend (development server).

Usage (from repo root or from this directory):
    python run.py
    python backend/run.py

Optional environment variables:
    HOST   — bind address (default: 0.0.0.0)
    PORT   — port (default: 8000)
    RELOAD — set to 0 or false to disable auto-reload (default: on)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent


def main() -> None:
    os.chdir(BACKEND_DIR)

    # backend.* imports need repo root; models.* and core.* need backend on path
    # Note: uvicorn reload can spawn a new process, so we also set PYTHONPATH
    # to make sure imports keep working in the reloader child.
    for path in (str(BACKEND_DIR), str(REPO_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)

    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    preferred_pythonpath = f"{BACKEND_DIR}:{REPO_ROOT}"
    if preferred_pythonpath not in existing_pythonpath.split(":"):
        os.environ["PYTHONPATH"] = (
            f"{preferred_pythonpath}:{existing_pythonpath}" if existing_pythonpath else preferred_pythonpath
        )

    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "1").lower() not in ("0", "false", "no")

    kwargs: dict = {
        "host": host,
        "port": port,
        "reload": reload,
    }
    if reload:
        kwargs["reload_dirs"] = [str(BACKEND_DIR)]

    uvicorn.run("main:app", **kwargs)


if __name__ == "__main__":
    main()
