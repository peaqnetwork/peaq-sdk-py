"""commonly shared objects across the sdk"""
# python native imports
from enum import Enum
from typing import Optional
from dataclasses import dataclass


# 3rd party imports
from substrateinterface import SubstrateInterface
from substrateinterface.keypair import Keypair
from eth_account import Account


class ChainType(Enum):
    EVM = "evm"
    SUBSTRATE = "substrate"

@dataclass
class TransactionResult:
    extrinsic_hash: str
    block_hash: str
    fee: int

@dataclass
class SDKMetadata:
    chain_type: Optional[ChainType]
    base_url: str
    pair: Optional[Keypair | Account]
    
class PrecompileAddresses(str, Enum):
    STORAGE = "0x0000000000000000000000000000000000000801"

# Used for Substrate calls
class CallModule(str, Enum):
    PEAQ_STORAGE = 'PeaqStorage'
    # Add more modules as needed

class EvmTransaction():
    to: str
    data: str

    
class ExtrinsicExecutionError(Exception):
    """Raised when an extrinsic fails to execute successfully on the blockchain."""
    pass

class SeedError(Exception):
    """Raised when there is no seed set for the write operation."""
    pass