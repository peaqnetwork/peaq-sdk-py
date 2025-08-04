"""
Base types for transaction status and callbacks
"""

from typing import Optional, runtime_checkable, Protocol, Callable, Awaitable, Any

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

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
    status: TransactionStatus = Field(..., description="Current transaction status")
    confirmation_mode: ConfirmationMode = Field(..., description="Confirmation mode being used")
    total_confirmations: int = Field(..., description="Total number of confirmations")
    hash: str = Field(..., description="Transaction hash")
    receipt: Optional[dict] = Field(default=None, description="Transaction receipt")
    nonce: Optional[int] = Field(default=None, description="Transaction nonce")
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    def to_dict(self, clean_fn=None) -> dict:
        """
        Convert to a dictionary. Optionally clean with a provided function.
        """
        raw_dict = self.model_dump()
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
        
# TransactionOptions = TxOptions

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