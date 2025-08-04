"""
Common types and enums for the MSF SDK
"""

from enum import Enum
from typing import Optional, Dict, Any
from eth_account.signers.base import BaseAccount
from pydantic import BaseModel, ConfigDict, Field


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