"""objects used in the main sdk initializer"""
# python native imports
from dataclasses import dataclass
from typing import Optional

# local imports
from peaq_sdk.types.common import ChainType


@dataclass
class CreateInstanceOptions:
    base_url: str
    chain_type: Optional[ChainType]
    seed: Optional[str]
