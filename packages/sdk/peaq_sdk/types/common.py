"""commonly shared objects across the sdk"""
# python native imports
from enum import Enum
from typing import Optional
from dataclasses import dataclass


# 3rd party imports
from substrateinterface import SubstrateInterface
from substrateinterface.keypair import Keypair
from substrateinterface.base import GenericCall
from eth_account import Account
from web3.types import TxParams


class ChainType(Enum):
    EVM = "evm"
    SUBSTRATE = "substrate"

# Used for EVM calls
class PrecompileAddresses(str, Enum):
    DID = "0x0000000000000000000000000000000000000800"
    STORAGE = "0x0000000000000000000000000000000000000801"
    RBAC = "0x0000000000000000000000000000000000000802"
    IERC20 = "0x0000000000000000000000000000000000000809"

# Used for Substrate calls
class CallModule(str, Enum):
    PEAQ_DID = 'PeaqDid'
    PEAQ_STORAGE = 'PeaqStorage'
    PEAQ_RBAC = 'PeaqRbac'
    
    # Add more modules as needed
@dataclass
class SDKMetadata:
    chain_type: Optional[ChainType]
    base_url: str
    pair: Optional[Keypair | Account]
    machine_station: bool
# EVM Transaction type - using Web3.py native TxParams (equivalent to SubstrateInterface's GenericCall)

@dataclass
class WrittenTransactionResult():
    message: str
    receipt: dict  # Backwards compatibility with dict

@dataclass
class BuiltEvmTransactionResult():
    message: str
    tx: TxParams

@dataclass
class BuiltCallTransactionResult():
    message: str
    call: GenericCall
    
class ExtrinsicExecutionError(Exception):
    """Raised when an extrinsic fails to execute successfully on the blockchain."""
    pass

class SeedError(Exception):
    """Raised when there is no seed set for the write operation."""
    pass

class BaseUrlError(Exception):
    """Raised when an incorrect Base Url is set."""
    pass