import os
from typing import Optional

def get_env_vars(key: str, default: Optional[str] = None) -> str:
    """Retrives an environment variable or raises error if not found."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"{key} is required but not set.")
    return value