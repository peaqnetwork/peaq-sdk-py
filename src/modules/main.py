# python native imports
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# local imports
from src.modules.base import Base
from src.modules.did import Did
from src.modules.storage import Storage
from src.types.common import ChainType, SDKMetadata
from src.types.main import CreateInstanceOptions, BaseUrlError

# 3rd party imports
from substrateinterface.base import SubstrateInterface
from substrateinterface.keypair import Keypair, KeypairType
from web3 import Web3


"""
Entry point for the Python SDK. Inherits the Base class that contains 
logic for EVM and Substrate specific operations.
"""
class Main(Base):
    def __init__(self, options) -> None:
        """Initializes main class that the sdk actually is."""
        super().__init__()
        self.__options: CreateInstanceOptions = options
        self.__metadata: SDKMetadata = SDKMetadata(
            base_url=options.base_url,
            chain_type=options.chain_type,
            pair=None
        )
        self._api = self._create_api()
        self.did: Did = Did(self._api, self.__metadata)
        self.storage: Storage = Storage(self._api, self.__metadata)
    
    def create_instance(
        base_url: str,
        chain_type: Optional[ChainType],
        seed: Optional[str] = None
        ) -> Main:
        """
        Creates a new instance of the SDK and connects to the network.

        Parameters
        ----------
        chain_type: Indicates whether to use EVM or Substrate.
        base_url: Connection URL to the blockchain.
        seed: Mnemonic phrase used to execute substrate txs.

        Returns
        -------
        sdk: Main
            SDK object that can be used to execute peaq functions.

        Raises
        ------
        None
        """
        options = CreateInstanceOptions(base_url, chain_type, seed)
        sdk = Main(options)
        sdk.connect()
        return sdk
    
    def connect(self) -> None:
        """
        Validates proper seed format and sets the mnemonic phrase to a 
        key pair used to execute transactions on substrate.

        Parameters
        ----------
        self: Current instance of the main class.

        Returns
        -------
        None

        Raises
        ------
        None
        """
        self._validate_options()
        self._set_metadata()
        
    
    # Check substrate seed
    def _validate_options(self):
        """Checks the seed to make sure it is compatible with substrate."""
        pass
    def _set_metadata(self):
        """Creates a keypair to execute txs based on the substrate seed passed."""
        key_pair = self._get_key_pair(self.__metadata.chain_type, self.__options.seed)
        self.__metadata.pair = key_pair
    
    
    def _create_api(self):
        """Creates an api provider to interact with the substrate side of our chain."""
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
        """Makes sure the correct url is being used in the proper environment."""
        if not base_url.startswith(expected_prefix):
            raise BaseUrlError(
                f"Invalid base URL for {interaction}: {base_url}. "
                f"It must start with '{expected_prefix}' to establish connection."
            )