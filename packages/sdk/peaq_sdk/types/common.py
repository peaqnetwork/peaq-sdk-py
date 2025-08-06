"""commonly shared objects across the sdk"""
# python native imports
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
# Removed dataclass import - using Pydantic BaseModel instead



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

class SDKMetadata(BaseModel):
    """SDK metadata containing chain configuration and authentication"""
    chain_type: Optional[ChainType] = Field(..., description="The blockchain type (EVM or Substrate)")
    base_url: str = Field(..., description="Base URL for the blockchain endpoint")
    pair: Optional[Keypair | Account] = Field(None, description="Optional keypair or account for signing transactions")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow Keypair and Account types
    )
    
# placeholder for now
class WrittenTransactionResult(BaseModel):
    """Result for written transactions with message and receipt"""
    message: str = Field(..., description="Informational message about the transaction")
    receipt: dict = Field(..., description="Transaction receipt data")  # Backwards compatibility with dict


class BuiltEvmTransactionResult(BaseModel):
    """Result for unsigned EVM transactions that need external signing"""
    message: str = Field(..., description="Informational message about the constructed transaction")
    tx: TxParams = Field(..., description="EVM transaction parameters for external signing")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow TxParams type
    )

class BuiltCallTransactionResult(BaseModel):
    """Result for unsigned Substrate calls that need external signing"""
    message: str = Field(..., description="Informational message about the constructed call")
    call: GenericCall = Field(..., description="Substrate call object for external signing")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow GenericCall type
    )
    
class ExtrinsicExecutionError(Exception):
    """Raised when an extrinsic fails to execute successfully on the blockchain."""
    pass

class SeedError(Exception):
    """Raised when there is no seed set for the write operation."""
    pass

class BaseUrlError(Exception):
    """Raised when an incorrect Base Url is set."""
    pass