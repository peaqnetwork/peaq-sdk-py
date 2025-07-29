"""
Transaction-related types and enums for the PEAQ SDK.
Defines confirmation modes, transaction status, callback types, and transaction options.
"""

from enum import Enum
from typing import Optional, Union, Protocol, runtime_checkable
from dataclasses import dataclass, asdict

class TransactionStatus(Enum):
    """
    Status events emitted during transaction lifecycle.
    """
    BROADCAST = 'BROADCAST'      # Transaction has been broadcast to the network
    IN_BLOCK = 'IN_BLOCK'        # Transaction has been included in a block  
    FINALIZED = 'FINALIZED'      # Transaction has been finalized (GRANDPA finality)

class ConfirmationMode(Enum):
    """
    Different confirmation modes for transaction handling.
    """
    FAST = 'FAST'        # Resolves after first successful block inclusion
    CUSTOM = 'CUSTOM'    # Waits for user-defined number of confirmations
    FINAL = 'FINAL'      # Waits until Polkadot-style GRANDPA finality

@dataclass
class TransactionStatusCallback:
    """
    Status update data sent to callback functions during transaction processing.
    """
    status: TransactionStatus
    confirmation_mode: ConfirmationMode
    total_confirmations: int
    hash: str
    receipt: Optional[dict] = None
    nonce: Optional[int] = None
    
    def to_dict(self, clean_fn=None) -> dict:
        """
        Convert to a dictionary. Optionally clean with a provided function.
        """
        raw_dict = asdict(self)
        return clean_fn(raw_dict) if clean_fn else raw_dict

@runtime_checkable
class StatusCallback(Protocol):
    """
    Protocol for transaction status callback functions.
    """
    def __call__(self, status_update: TransactionStatusCallback) -> None:
        """
        Called with status updates during transaction processing.
        
        Args:
            status_update: Current transaction status information
        """
        ...

@dataclass 
class TransactionOptions:
    """
    Options for customizing transaction behavior and gas parameters.
    
    Custom gas and fee parameters:
    - gasLimit: Manual gas limit. If omitted, SDK estimates gas.
    - maxFeePerGas: Cap on total fee per gas unit (baseFee + priorityFee) 
    - maxPriorityFeePerGas: Miner tip per gas unit
    
    WARNING: Overriding gas parameters is for advanced users only.
    Improper values may cause transactions to fail, overpay, or stall.
    """
    mode: Optional[ConfirmationMode] = None
    confirmations: Optional[int] = None
    gas_limit: Optional[int] = None
    max_fee_per_gas: Optional[int] = None  
    max_priority_fee_per_gas: Optional[int] = None
    
    def __post_init__(self):
        """Validate transaction options after initialization."""
        # Set default mode if not provided
        if self.mode is None:
            self.mode = ConfirmationMode.FAST
            
        if self.mode == ConfirmationMode.CUSTOM and self.confirmations is None:
            raise ValueError("confirmations must be set when using ConfirmationMode.CUSTOM")
        
        if self.mode == ConfirmationMode.CUSTOM and (self.confirmations is None or self.confirmations < 1):
            raise ValueError("confirmations must be a positive integer for CUSTOM mode")

@dataclass
class EvmTransactionResult:
    """
    Result returned from EVM transaction execution.
    """
    tx_hash: str
    receipt: dict
    confirmation_mode: ConfirmationMode
    total_confirmations: int
    
@dataclass  
class SubstrateTransactionResult:
    """
    Result returned from Substrate transaction execution.
    """
    tx_hash: str
    receipt: dict
    confirmation_mode: ConfirmationMode
    total_confirmations: int

# Type alias for transaction results
TransactionResult = Union[EvmTransactionResult, SubstrateTransactionResult] 