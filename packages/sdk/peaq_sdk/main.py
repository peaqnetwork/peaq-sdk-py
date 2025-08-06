# python native imports
from __future__ import annotations
from typing import Optional, Union

# local imports
from peaq_sdk.base import Base
from peaq_sdk.did import Did
from peaq_sdk.storage import Storage
from peaq_sdk.rbac import Rbac
from peaq_sdk.utils.utils import parse_options


from peaq_sdk.transfer import Transfer

from peaq_sdk.types.common import ChainType, SDKMetadata, BaseUrlError
from peaq_sdk.types.main import CreateInstanceOptions

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from substrateinterface.keypair import Keypair
from eth_account.signers.base import BaseAccount
from web3 import Web3
from web3 import AsyncWeb3, AsyncHTTPProvider


class Main(Base):
    """
    Entry point for the Python SDK.

    The Main class serves as the primary interface for the SDK, providing methods for 
    initializing the signer, creating the API connection, and handling blockchain-specific operations.
    It inherits from Base, which contains common logic for both EVM and Substrate operations
    with enhanced batch processing and transaction control.
    """
    
    def __init__(self, options: CreateInstanceOptions) -> None:
        """
        Initializes the Main class, representing the primary interface for the SDK.

        Args:
            base_url (str): The URL for connecting to the blockchain.
            chain_type (ChainType): The type of blockchain (e.g., EVM or Substrate).
        """
        metadata: SDKMetadata = SDKMetadata(
            base_url=options.base_url,
            chain_type=options.chain_type,
            pair=None
        )
        api = self._create_api(metadata)
        super().__init__(api, metadata)
        
        self.did: Did = Did(self._api, self._metadata)
        self.storage: Storage = Storage(self._api, self._metadata)
        self.rbac: Rbac = Rbac(self._api, self._metadata)
        self.transfer: Transfer = Transfer(self._api, self._metadata)
    
    @classmethod
    async def create_instance(cls,
        options: CreateInstanceOptions
        ) -> Main:
        """
        Creates and returns a new instance of the SDK, connecting to the specified network.

        Args:
            base_url (str): The connection URL for the blockchain.
            chain_type (ChainType): Indicates whether the blockchain is EVM or Substrate.
            auth (Optional[Union[BaseAccount, Keypair]]): The authentication method:
                - BaseAccount: Web3 account object for EVM chains
                - Keypair: Substrate keypair object for Substrate chains

        Returns:
            Main: An initialized SDK object ready for building or executing blockchain operations.
        """
        ops = parse_options(CreateInstanceOptions, options, caller="create_instance()")
        sdk = cls(ops)
        sdk._initialize_signer(ops.auth)
        return sdk
    
    def _initialize_signer(self, auth: Optional[Union[BaseAccount, Keypair]] = None) -> None:
        """
        Initializes the signer by validating and setting the authentication method.

        Args:
            auth (Optional[Union[BaseAccount, Keypair]]): The authentication method:
                - BaseAccount: Web3 account object for EVM chains
                - Keypair: Substrate keypair object for Substrate chains
        """
        if auth is not None:
            self._set_signer(auth)
    
    
    def _create_api(self, metadata: SDKMetadata) -> Union[Web3, SubstrateInterface]:
        """
        Initializes and returns an API provider for blockchain interaction based on the chain type 
        specified in the SDK metadata.

        Returns:
            Web3 | SubstrateInterface: An API provider instance used to interact with the blockchain.

        Raises:
            BaseUrlError: If the base URL does not start with the expected protocol prefix.
        """
        base_url: str = metadata.base_url
        if metadata.chain_type == ChainType.EVM:
            expected_prefix: str = "https://"
            self._validate_base_url(base_url, expected_prefix, ChainType.EVM)
            api = AsyncWeb3(AsyncHTTPProvider(base_url))
            return api
        elif metadata.chain_type == ChainType.SUBSTRATE:
            expected_prefix: str = "wss://"
            self._validate_base_url(base_url, expected_prefix, ChainType.SUBSTRATE)
            api = SubstrateInterface(url=base_url, ss58_format=42)
            return api
        else:
            raise ValueError(f"Invalid chain type: {metadata.chain_type}")

    def _validate_base_url(self, base_url: str, expected_prefix: str, interaction: ChainType) -> None:
        """
        Validates that the base URL matches the expected protocol for the blockchain.

        Args:
            base_url (str): The URL used to connect to the blockchain.
            expected_prefix (str): The protocol prefix expected in the URL (e.g., "https://" or "wss://").
            interaction (ChainType): The type of blockchain interaction (e.g., ChainType.EVM or ChainType.SUBSTRATE).

        Raises:
            BaseUrlError: If the base URL does not start with the expected prefix.
        """
        if not base_url.startswith(expected_prefix):
            raise BaseUrlError(
                f"Invalid base URL for {interaction}: {base_url}. "
                f"It must start with '{expected_prefix}' to establish connection."
            )