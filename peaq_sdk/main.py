# python native imports
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

# local imports
from peaq_sdk.base import Base
from peaq_sdk.did import Did
from peaq_sdk.storage import Storage
from peaq_sdk.types.common import ChainType, SDKMetadata, BaseUrlError
from peaq_sdk.types.main import CreateInstanceOptions

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from substrateinterface.keypair import Keypair, KeypairType
from web3 import Web3


class Main(Base):
    """
    Entry point for the Python SDK.

    The Main class serves as the primary interface for the SDK, providing methods for 
    initializing the signer, creating the API connection, and handling blockchain-specific operations.
    It inherits from Base, which contains common logic for both EVM and Substrate operations.
    """
    def __init__(self, base_url: str, chain_type: Optional[ChainType]) -> None:
        """
        Initializes the Main class, representing the primary interface for the SDK.

        Args:
            base_url (str): The URL for connecting to the blockchain.
            chain_type (Optional[ChainType]): The type of blockchain (e.g., EVM or Substrate).
        """
        super().__init__()
        self.__metadata: SDKMetadata = SDKMetadata(
            base_url=base_url,
            chain_type=chain_type,
            pair=None
        )
        self._api = self._create_api()
        self.did: Did = Did(self._api, self.__metadata)
        self.storage: Storage = Storage(self._api, self.__metadata)
    
    @classmethod
    def create_instance(cls,
        base_url: str,
        chain_type: Optional[ChainType],
        seed: Optional[str] = None
        ) -> Main:
        """
        Creates and returns a new instance of the SDK, connecting to the specified network.

        Args:
            base_url (str): The connection URL for the blockchain.
            chain_type (Optional[ChainType]): Indicates whether the blockchain is EVM or Substrate.
            seed (Optional[str]): The secret (mnemonic phrase or private key) used to generate the signer for executing transactions.

        Returns:
            Main: An initialized SDK object ready for executing blockchain operations.
        """
        sdk = Main(base_url, chain_type)
        sdk._initialize_signer(seed)
        return sdk
    
    def _initialize_signer(self, seed: Optional[str] = None) -> None:
        """
        Initializes the signer by validating and setting the secret used for generating the key pair/account.

        Args:
            seed (Optional[str]): The mnemonic phrase or private key used to generate the key pair.
        """
        self._validate_secret(seed)
        self._set_metadata(seed)
    
    def _validate_secret(self, seed: Optional[str] = None):
        """
        Validates that the provided seed is compatible with EVM or Substrate.

        Args:
            seed (Optional[str]): The private key (for EVM) or mnemonic phrase (for Substrate)
                to validate.

        Raises:
            ValueError: If the EVM private key is not 64 hex characters (excluding '0x' prefix)
                or is not a valid hexadecimal string.
            ValueError: If the substrate mnemonic does not consist of 12 or 24 words.
        """
        if not seed:
            return
        if self.__metadata.chain_type == ChainType.EVM:
            key_str = seed[2:] if seed.startswith("0x") else seed
            if len(key_str) != 64:
                raise ValueError("Invalid EVM private key length. Expected 64 hex characters (excluding '0x' prefix).")
            try:
                int(key_str, 16)
            except ValueError:
                raise ValueError("Invalid EVM private key. It must be a valid hexadecimal string.")
        else:
            words = seed.strip().split()
            if len(words) not in (12, 24):
                raise ValueError("Invalid substrate mnemonic. Expected 12 or 24 words.")
        return
    
    def _set_metadata(self, seed: Optional[str] = None) -> None:
        """
        Generates a cryptographic key pair from the provided seed and stores it in the SDK metadata.

        This method invokes _get_key_pair, which applies blockchain-specific logic:
          - For EVM, it generates a key pair from a valid hexadecimal private key.
          - For Substrate, it creates a key pair from a mnemonic phrase (typically 12 or 24 words).
        The resulting key pair is stored in the metadata for use in signing transactions.

        Args:
            seed (Optional[str]): The mnemonic phrase (for Substrate) or private key (for EVM) used to generate the key pair.
        """
        if not seed:
            return
        key_pair = self._create_key_pair(self.__metadata.chain_type, seed)
        self.__metadata.pair = key_pair
    
    
    def _create_api(self) -> Union[Web3, SubstrateInterface]:
        """
        Initializes and returns an API provider for blockchain interaction based on the chain type 
        specified in the SDK metadata.

        Returns:
            Web3 | SubstrateInterface: An API provider instance used to interact with the blockchain.

        Raises:
            BaseUrlError: If the base URL does not start with the expected protocol prefix.
        """
        base_url: str = self.__metadata.base_url
        if self.__metadata.chain_type == ChainType.EVM:
            expected_prefix: str = "https://"
            self._validate_base_url(base_url, expected_prefix, ChainType.EVM)
            api = Web3(Web3.HTTPProvider(base_url))
            return api
        elif self.__metadata.chain_type in (ChainType.SUBSTRATE, None):
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