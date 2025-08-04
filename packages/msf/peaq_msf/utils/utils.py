"""
Utility functions for the MSF SDK.
"""
from pydantic import ValidationError


def parse_options(cls, options: dict, caller: str = "function"):
    try:
        return cls(**options)
    except ValidationError as e:
        missing = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
        if missing:
            raise ValueError(f"{caller}(): missing required field(s): {', '.join(missing)}") from None
        raise