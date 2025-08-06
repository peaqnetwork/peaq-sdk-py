"""
Transaction-related types and enums for the PEAQ SDK.
Defines confirmation modes, transaction status, callback types, and transaction options.
"""

from enum import Enum
from typing import Optional, Union, Protocol, runtime_checkable, Callable, Awaitable, Any
from pydantic import BaseModel, Field, ConfigDict

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

class TransactionStatusCallback(BaseModel):
    """
    Status update data sent to callback functions during transaction processing.
    """
    status: TransactionStatus
    confirmation_mode: ConfirmationMode
    total_confirmations: int
    hash: str
    receipt: Optional[dict] = None
    nonce: Optional[int] = None

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

class TxOptions(BaseModel):
    """
    Transaction options for customizing transaction behavior and gas parameters.
    Matches TypeScript txOptions interface exactly.
    
    Custom gas and fee parameters:
    - gasLimit: Manual gas limit. If omitted, SDK estimates gas.
    - maxFeePerGas: Cap on total fee per gas unit (baseFee + priorityFee) 
    - maxPriorityFeePerGas: Miner tip per gas unit
    
    WARNING: Overriding gas parameters is for advanced users only.
    Improper values may cause transactions to fail, overpay, or stall.
    """
    mode: Optional[ConfirmationMode] = Field(None, description="Confirmation mode for transaction")
    confirmations: Optional[int] = Field(None, description="Number of confirmations required (for CUSTOM mode)")
    gas_limit: Optional[int] = Field(None, alias="gasLimit", description="Manual gas limit override")
    max_fee_per_gas: Optional[int] = Field(None, alias="maxFeePerGas", description="Maximum fee per gas unit")
    max_priority_fee_per_gas: Optional[int] = Field(None, alias="maxPriorityFeePerGas", description="Maximum priority fee per gas unit")
    
    
    def model_post_init(self, __context) -> None:
        """Validate transaction options after initialization."""
        # Set default mode if not provided
        if self.mode is None:
            self.mode = ConfirmationMode.FAST
            
        if self.mode == ConfirmationMode.CUSTOM and self.confirmations is None:
            raise ValueError("confirmations must be set when using ConfirmationMode.CUSTOM")
        
        if self.mode == ConfirmationMode.CUSTOM and (self.confirmations is None or self.confirmations < 1):
            raise ValueError("confirmations must be a positive integer for CUSTOM mode")

# Keep backward compatibility alias
TransactionOptions = TxOptions

class SubstrateSendResult(BaseModel):
    """
    Result returned from Substrate transaction sending, matching TypeScript SubstrateSendResult interface.
    """
    tx_hash: str = Field(..., alias="txHash", description="Transaction hash")
    unsubscribe: Callable[[], None] = Field(..., description="Function to unsubscribe from transaction events")
    finalize: Awaitable[Any] = Field(..., description="Promise that resolves when transaction is finalized")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class EvmSendResult(BaseModel):
    """
    Result returned from EVM transaction sending, matching TypeScript EvmSendResult interface.
    """
    tx_hash: str = Field(..., alias="txHash", description="Transaction hash")
    unsubscribe: Optional[Callable[[], None]] = Field(None, description="Optional function to unsubscribe from transaction events")
    receipt: Awaitable[Any] = Field(..., description="Promise that resolves to transaction receipt")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class BuiltEvmTransactionResult(BaseModel):
    """
    Result returned for unsigned EVM transactions, matching TypeScript BuiltEvmTransactionResult interface.
    """
    message: str = Field(..., description="Informational message about the constructed transaction")
    tx: Any = Field(..., description="EVM transaction object")
    

class BuiltCallTransactionResult(BaseModel):
    """
    Result returned for unsigned Substrate calls, matching TypeScript BuiltCallTransactionResult interface.
    """
    message: str = Field(..., description="Informational message about the constructed call")
    extrinsic: Any = Field(..., description="Substrate extrinsic object")
    