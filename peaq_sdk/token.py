from peaq_sdk.base import Base
from typing import Optional, Union

from peaq_sdk.types.common import ExtrinsicExecutionError
from substrateinterface import Keypair
from web3 import Web3
from eth_account import Account

from substrateinterface.base import SubstrateInterface
from substrateinterface.utils.ss58 import is_valid_ss58_address


from peaq_sdk.types.common import ChainType, SDKMetadata, BaseUrlError

from decimal import Decimal, getcontext
from peaq_sdk.utils.utils import evm_to_address


# TODO error checks if address format not recognized

class Token(Base):
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata):
        super().__init__(api, metadata)

    def transfer(self, to: str, amount: int) -> dict:
        """
        Transfer the native token.

        TODO
        """
        
        if self.metadata.chain_type == ChainType.EVM:
            # evm - substrate
            # print(is_valid_ss58_address(to)) if true TODO address unification
            if is_valid_ss58_address(to) is True and Web3.is_address(to) is False:
                raise ValueError("See address unification pallet for more information.")
            
            # evm - evm
            
            raw = self._to_raw_amount(human_amount=amount, token_decimals=18)
            tx = {
                "to": Web3.to_checksum_address(to),
                "value": raw,
            }
            return self._send_evm_tx(tx)

        else:
            # substrate - evm
            if is_valid_ss58_address(to) is False and Web3.is_address(to) is True:
                to = evm_to_address(to)
            
            
            # substrate - substrate works automatically
            
            raw = self._to_raw_amount(amount, self.api.token_decimals)
            
            call = self.api.compose_call(
                call_module="Balances",
                call_function="transfer_keep_alive",
                call_params={"dest": to, "value": raw},
            )
            return self._send_with_tip(call)

        
    def _to_raw_amount(self, human_amount: Union[int, float, str, Decimal], token_decimals) -> int:
        """
        If the user passed an int, assume it's already raw.
        Otherwise, scale by 10**decimals.
        
        TODO
        """
        if isinstance(human_amount, int):
            return human_amount
        
        d = Decimal(str(human_amount))
        scale = Decimal(10) ** token_decimals
        return int(d * scale)
        
