import os
from pathlib import Path


def load_env_file(env_path: str = "backend/.env") -> None:
    """Load environment variables from a simple KEY=VALUE file."""
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
