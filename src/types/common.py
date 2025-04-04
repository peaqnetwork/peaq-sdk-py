"""commonly shared objects across the sdk"""
# python native imports
from enum import Enum
from typing import Optional
from dataclasses import dataclass


# 3rd party imports
from substrateinterface import SubstrateInterface
from substrateinterface.keypair import Keypair


class ChainType(Enum):
    EVM = "evm"
    SUBSTRATE = "substrate"
    
@dataclass
class SDKMetadata:
    chain_type: Optional[ChainType]
    base_url: str
    pair: Optional[Keypair]
    
class ExtrinsicExecutionError(Exception):
    """Raised when an extrinsic fails to execute successfully on the blockchain."""
    pass