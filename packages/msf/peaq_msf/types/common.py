"""
Common types and enums for the MSF SDK
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from eth_account.signers.base import BaseAccount

from .base import ConfirmationMode

class ChainType(str, Enum):
    """Supported blockchain types"""
    EVM = "evm"
    SUBSTRATE = "substrate"

@dataclass
class SDKMetadata:
    """Metadata for SDK configuration"""
    base_url: str
    chain_type: ChainType
    pair: Optional[BaseAccount] = None
    machine_station: bool = False


@dataclass
class CreateInstanceOptions:
    """Options for creating an MSF SDK instance"""
    base_url: str
    machine_station_address: str
    station_admin: BaseAccount
    station_manager: Optional[BaseAccount] = None


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