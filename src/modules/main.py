# python native imports
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# local imports
from src.modules.base import Base
from src.modules.did import Did
from src.types.common import ChainType
from src.types.main import CreateInstanceOptions

# 3rd party imports



"""
Entry point for the Python SDK. Inherits the Base class that contains 
logic for EVM and Substrate specific low level tasks.
"""
class Main(Base):
    ChainType = ChainType
    

    def __init__(self, options) -> None:
        super().__init__()
        print(options)
        self.did: Did = Did()
    
    def create_instance(
        base_url: str,
        chain_type: Optional[ChainType],
        seed: Optional[str]
        ) -> Main:
        """
        Creates a new instance of the SDK and connects to the network.

        Parameters
        ----------
        chain_type: Indicates whether to use EVM or Substrate
        base_url: Connection URL to the blockchain
        seed: Mnemonic phrase used to execute substrate txs

        Returns
        -------
        sdk: Main
            SDK object that can be used to execute peaq functions

        Raises
        ------
        KeyError
            when a key error
        OtherError
            when an other error
        """
        options = CreateInstanceOptions(base_url, chain_type, seed)
        sdk = Main(options)
        # sdk.connect()
        return sdk
        
    def create_instance() -> None:
        return None