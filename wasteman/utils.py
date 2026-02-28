import os
from typing import Optional

def get_env_vars(key: str, default: Optional[str] = None) -> str:
    """Retrives an environment variable or raises error if not found."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"{key} is required but not set.")
    return value

def parse_sizes_and_prices(sizes_and_prices):
    """We parse this format: x,x,y;x,x,y == w,h,p;w,h,p"""
    return [item.split(",") for item in sizes_and_prices.split(";")]