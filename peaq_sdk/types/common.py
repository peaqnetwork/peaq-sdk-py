"""commonly shared objects across the sdk"""
# python native imports
from enum import Enum
from typing import Optional, List, Union, Dict, Any
from dataclasses import dataclass


# 3rd party imports
from substrateinterface import SubstrateInterface
from substrateinterface.keypair import Keypair
from substrateinterface.base import GenericCall
from eth_account import Account

class ChainType(Enum):
    EVM = "evm"
    SUBSTRATE = "substrate"

class ConfirmationMode(str, Enum):
    """Transaction confirmation modes for different speed/safety tradeoffs"""
    FAST = "fast"           # Return immediately after submission (tx_hash only)
    BALANCED = "balanced"   # Wait for inclusion in block
    SAFE = "safe"          # Wait for inclusion + finalization

class BatchMode(str, Enum):
    """Batch execution modes"""
    SEQUENTIAL = "sequential"   # Execute calls one by one
    PARALLEL = "parallel"      # Submit all calls concurrently  
    ATOMIC = "atomic"          # Use utility.batchAll for atomic execution

@dataclass
class SDKMetadata:
    chain_type: Optional[ChainType]
    base_url: str
    pair: Optional[Keypair | Account]
    
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
    UTILITY = 'Utility'  # For batching operations

class UtilityCallFunction(str, Enum):
    """Utility pallet functions for batching"""
    BATCH = 'batch'
    BATCH_ALL = 'batch_all'
    AS_DERIVATIVE = 'as_derivative'

@dataclass
class TransactionConfig:
    """Configuration for transaction submission"""
    mode: ConfirmationMode = ConfirmationMode.BALANCED
    fee_multiplier: float = 1.0
    max_retries: int = 5
    wait_for_finalization: bool = False
    timeout_seconds: int = 120

@dataclass
class BatchConfig:
    """Configuration for batch transactions"""
    batch_mode: BatchMode = BatchMode.SEQUENTIAL
    transaction_config: TransactionConfig = None
    max_batch_size: int = 100
    
    def __post_init__(self):
        if self.transaction_config is None:
            self.transaction_config = TransactionConfig()

class EvmTransaction():
    to: str
    data: str

@dataclass
class TxReceipt:
    """Unified transaction receipt format"""
    tx_hash: str
    block_hash: Optional[str] = None
    block_number: Optional[int] = None
    success: bool = True
    finalized: bool = False
    events: List[Dict[str, Any]] = None
    fee: Optional[Union[int, str]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []

@dataclass
class BatchReceipt:
    """Receipt for batch transactions"""
    batch_hash: Optional[str] = None
    receipts: List[TxReceipt] = None
    success: bool = True
    failed_at_index: Optional[int] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.receipts is None:
            self.receipts = []

@dataclass
class WrittenTransactionResult():
    message: str
    receipt: Union[TxReceipt, BatchReceipt, dict]  # Backwards compatibility with dict

@dataclass
class BuiltEvmTransactionResult():
    message: str
    tx: EvmTransaction

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

class BatchExecutionError(Exception):
    """Raised when a batch execution fails."""
    pass