# local imports
from peaq_sdk.types.common import ChainType

# 3rd party imports
from substrateinterface.keypair import Keypair
from eth_account.signers.base import BaseAccount

from pydantic import BaseModel, ConfigDict, Field

class CreateInstanceOptions(BaseModel):
    base_url: str = Field(..., description="HTTPS/WSS endpoint to your node")
    chain_type: ChainType = Field(..., description="EVM or SUBSTRATE")
    auth: BaseAccount | Keypair | None = Field(
        None, description="Optional signer: BaseAccount (EVM) or Keypair (Substrate)"
    )
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )