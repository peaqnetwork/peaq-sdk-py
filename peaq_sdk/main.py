# python native imports
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, List
import time

# local imports
from peaq_sdk.base import Base
from peaq_sdk.did import Did
from peaq_sdk.storage import Storage
from peaq_sdk.rbac import Rbac

from peaq_sdk.transfer import Transfer
from peaq_sdk.get_real import GetReal
from peaq_sdk.machine_station import MachineStation

from peaq_sdk.types.common import ChainType, SDKMetadata, BaseUrlError
from peaq_sdk.types.main import CreateInstanceOptions

# 3rd party imports
from substrateinterface.base import SubstrateInterface, GenericCall
from substrateinterface.keypair import Keypair, KeypairType
from eth_account.signers.base import BaseAccount
from web3 import Web3


class Main(Base):
    """
    Entry point for the Python SDK.

    The Main class serves as the primary interface for the SDK, providing methods for 
    initializing the signer, creating the API connection, and handling blockchain-specific operations.
    It inherits from Base, which contains common logic for both EVM and Substrate operations
    with enhanced batch processing and transaction control.
    """
    def __init__(self, base_url: str, chain_type: Optional[ChainType], machine_station: Optional[ChainType] = False) -> None:
        """
        Initializes the Main class, representing the primary interface for the SDK.

        Args:
            base_url (str): The URL for connecting to the blockchain.
            chain_type (Optional[ChainType]): The type of blockchain (e.g., EVM or Substrate).
        """
        metadata: SDKMetadata = SDKMetadata(
            base_url=base_url,
            chain_type=chain_type,
            pair=None,
            machine_station=machine_station
        )
        api = self._create_api(metadata)
        super().__init__(api, metadata)
        
        self.did: Did = Did(api, metadata)
        self.storage: Storage = Storage(api, metadata)
        self.rbac: Rbac = Rbac(api, metadata)
        self.transfer: Transfer = Transfer(self._api, self._metadata)
    
    @classmethod
    def create_instance(cls,
        base_url: str,
        chain_type: Optional[ChainType],
        auth: Optional[Union[BaseAccount, Keypair]] = None
        ) -> Main:
        """
        Creates and returns a new instance of the SDK, connecting to the specified network.

        Args:
            base_url (str): The connection URL for the blockchain.
            chain_type (Optional[ChainType]): Indicates whether the blockchain is EVM or Substrate.
            auth (Optional[Union[BaseAccount, Keypair]]): The authentication method:
                - BaseAccount: Web3 account object for EVM chains
                - Keypair: Substrate keypair object for Substrate chains

        Returns:
            Main: An initialized SDK object ready for executing blockchain operations.
        """
        sdk = Main(base_url, chain_type)
        sdk._initialize_signer(auth)
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
            api = Web3(Web3.HTTPProvider(base_url))
            return api
        elif metadata.chain_type in (ChainType.SUBSTRATE, None):
            expected_prefix: str = "wss://"
            self._validate_base_url(base_url, expected_prefix, ChainType.SUBSTRATE)
            api = SubstrateInterface(url=base_url, ss58_format=42)
            return api

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
            
    @classmethod
    def machine_station_instance(
        cls,
        base_url: str,
        machine_station_address: str,
        auth: BaseAccount,
        ) -> Main:
        """
        Creates a new Machine Station instance for account abstraction functionality.
        
        Args:
            base_url (str): The connection URL for the blockchain.
            machine_station_address (str): The address of the deployed machine station contract.
            auth (BaseAccount): Web3 account object for the machine station owner (admin).
            
        Returns:
            Main: An initialized SDK object with Machine Station functionality.
        """
        sdk = cls(base_url, ChainType.EVM, machine_station=True)
        sdk._initialize_signer(auth)
        sdk.machine_station = MachineStation(
            sdk=sdk,
            machine_station_address=machine_station_address,
            machine_station_owner_private_key=auth.key.hex(),
            api=sdk.api,
            metadata=sdk.metadata
        )
        return sdk

    
    @classmethod
    def get_real_instance(
        cls,
        base_url: str,
        machine_station_address: str,
        auth: BaseAccount,
        service_url: str,
        api_key: str,
        project_api_key: str,
        ) -> Main:
        """
        Creates a new Get Real instance for DePINs in the campaign. Utilizes the user deployed Machine Station Factory and is
        only EVM compatible.

        Args:
            base_url (str): The connection URL for the blockchain.
            machine_station_address (str): The address of the deployed contract for the machine station factory.
            auth (BaseAccount): Web3 account object for the admin account.
            service_url (str): URL used to connect to peaq's campaign service.
            api_key (str): Key used to provide authentication with the peaq service.
            project_api_key (str): Key used to provide authentication for a specific project.

        Returns:
            Main: An initialized SDK object ready for executing blockchain operations.
        """
        # Initialize SDK with EVM chain type
        sdk = cls(base_url, ChainType.EVM, machine_station=True)
        sdk._initialize_signer(auth)
        
        # Create GetReal instance with machine station functionality
        sdk.get_real = GetReal(
            sdk=sdk,
            machine_station_address=machine_station_address,
            machine_station_owner_private_key=auth.key.hex(),
            service_url=service_url,
            api_key=api_key,
            project_api_key=project_api_key,
            api=sdk.api,
            metadata=sdk.metadata
        )
        return sdk