from typing import Optional
import uuid

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    SDKMetadata
)

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from web3 import Web3

class Rbac(Base):
    """
    Provides methods to interact with the peaq on-chain RBAC precompile (EVM)
    or pallet (Substrate). Supports role, group, and permission operations.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes RBAC with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        super().__init__(api, metadata)
        
    def create_role(self, role_name: str, role_id: Optional[str] = None) -> None:
        if role_id is None:
            role_id = str(uuid.uuid4())[:32]
        elif len(role_id) != 32:
            print(len(role_id))
            raise ValueError("Role Id length should be 32 char only")
        
        
        print(role_id)