"""
Common types and enums for the MSF SDK
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from eth_account.signers.base import BaseAccount
from pydantic import BaseModel, ConfigDict, Field


from .base import ConfirmationMode


class ChainType(str, Enum):
    """Supported blockchain types"""
    EVM = "evm"
    SUBSTRATE = "substrate"
    
class SDKMetadata(BaseModel):
    """SDK metadata containing chain configuration and authentication"""
    base_url: str = Field(..., description="Base URL for the blockchain endpoint")
    chain_type: Optional[ChainType] = Field(..., description="The blockchain type (EVM or Substrate)")
    pair: Optional[BaseAccount] = Field(None, description="Optional keypair or account for signing transactions")
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow Keypair and Account types
    )

class CreateInstanceOptions(BaseModel):
    base_url: str = Field(..., description="HTTPS/WSS endpoint to your node")
    machine_station_address: str = Field(..., description="Machine Station Contract being connected to")
    station_admin: BaseAccount = Field(..., description="Signer - BaseAccount; represents the station admin"    )
    station_manager: Optional[BaseAccount] = Field(None, description="Optional signer - BaseAccount; represents the station admin")
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


@dataclass
class TxOptions:
    """Transaction options for EVM transactions"""
    mode: Optional[ConfirmationMode] = None
    confirmations: Optional[int] = None
    gas_limit: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None


@dataclass(kw_only=True)
class EvmSendResult:
    """Base result for EVM transaction sends"""
    tx_hash: str
    receipt: Optional[Dict[str, Any]] = None
    unsubscribe: Optional[callable] = None


@dataclass
class WrittenTransactionResult:
    """Base result for written transactions"""
    message: str
    success: bool
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None