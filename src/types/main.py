"""objects used in the main sdk initializer"""
# python native imports
from dataclasses import dataclass
from typing import Optional

# local imports
from src.types.common import ChainType


@dataclass
class CreateInstanceOptions:
    base_url: str
    chain_type: Optional[ChainType]
    seed: Optional[str]



# Custom Errors
class ApiError(Exception):
    """Raised when there is an issue establishing the API connection."""
    pass
class BaseUrlError(Exception):
    """Raised when an incorrect Base Url is set."""
    pass