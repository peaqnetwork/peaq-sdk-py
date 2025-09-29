"""
Utility functions for the MSF SDK.
"""
import json, os
from pydantic import ValidationError
from pathlib import Path
from typing import List
from eth_utils import keccak, to_hex

ROOT = Path(__file__).resolve().parent.parent

def parse_options(cls, options: dict, caller: str = "function"):
    try:
        return cls(**options)
    except ValidationError as e:
        missing = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
        if missing:
            raise ValueError(f"{caller}(): missing required field(s): {', '.join(missing)}") from None
        raise
    
def _load_abi(path: str | Path) -> List[dict]:
    p = (ROOT / path).resolve()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
    
def error_selector() -> dict[str, dict]:
    errors_abi = _load_abi("./abi/errors_abi.json")
    def selector_for(entry: dict) -> str:
        types = ",".join(inp["type"] for inp in entry.get("inputs", []))
        sig = f"{entry['name']}({types})"
        return to_hex(keccak(text=sig)[:4])  # 4-byte selector, 0x-prefixed

    return {
        selector_for(entry): entry
        for entry in errors_abi
        if entry.get("type") == "error" and "name" in entry
    }