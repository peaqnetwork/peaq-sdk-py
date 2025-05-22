from typing import Optional, Union
from decimal import Decimal

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    EvmTransaction,
    PrecompileAddresses,
    WrittenTransactionResult
)
from peaq_sdk.types.token import (
    TokenFunctionSignatures
)
from peaq_sdk.utils.utils import evm_to_address

from web3 import Web3
from substrateinterface.base import SubstrateInterface
from substrateinterface.utils.ss58 import is_valid_ss58_address, ss58_decode
from eth_abi import encode

class Token(Base):
    """
    Provides methods to transfer the native token across supported chains (peaq and agung).

    - On EVM: Sends native token via a standard value transfer or through the precompile if
      transferring to a Substrate address.
    - On Substrate: Sends native token via `transfer_keep_alive`, with automatic
      address format conversion for EVM targets.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata):
        """
        Initializes the Token class with API and metadata.

        Args:
            api (Web3 | SubstrateInterface): Blockchain connection instance.
            metadata (SDKMetadata): Shared SDK metadata including chain type and signer.
        """
        super().__init__(api, metadata)
        
    def _addr_type(self, addr: str) -> str:
        """
        Classifies the provided address string.

        Args:
            addr (str): Address to classify.

        Returns:
            str: 'substrate' if valid SS58, 'evm' if valid H160.

        Raises:
            ValueError: If the address is not a valid SS58 or EVM address.
        """
        is_sub = is_valid_ss58_address(addr)
        is_evm = Web3.is_address(addr)
        if is_sub and not is_evm:
            return "substrate"
        if is_evm and not is_sub:
            return "evm"
        raise ValueError(f"Address {addr!r} is neither a valid SS58 nor a valid EVM H160.")

    def transfer(self, to: str, amount: Union[int, float, str, Decimal]) -> WrittenTransactionResult:
        """
        Transfers the native token from the signer to a target address.

        - On EVM:
            - If `to` is a Substrate address, uses the precompile to transfer to SS58.
            - If `to` is an EVM address, sends a standard ETH-style value transfer.
        - On Substrate:
            - If `to` is an EVM address, converts it to SS58 and uses `transfer_keep_alive`.
            - If `to` is Substrate, uses `transfer_keep_alive` directly.

        Args:
            to (str): The recipient address (either SS58 or EVM H160).
            amount (int | float | str | Decimal): Human-readable token amount (e.g., 1.5).

        Returns:
            WrittenTransactionResult: A message and transaction receipt object.

        Raises:
            ValueError: If address format is invalid.
        """
        raw = self._to_raw_amount(amount,
            token_decimals=(
                18 if self.metadata.chain_type == ChainType.EVM
                   else self.api.token_decimals
            )
        )
        
        if self.metadata.chain_type == ChainType.EVM:
            addr_type = self._addr_type(to)
            if addr_type == "substrate": # evm->substrate
                function_selector = self.api.keccak(text=TokenFunctionSignatures.TRANSFER_TO_ACCOUNT_ID.value)[:4].hex()
                pubkey = bytes.fromhex(ss58_decode(to))
                encoded_params = encode(
                    ["bytes32", "uint256"], 
                    [pubkey, raw]
                ).hex()
                tx: EvmTransaction = {
                    "to": PrecompileAddresses.IERC20.value,
                    "data": f"0x{function_selector}{encoded_params}"
                }
            else:  # evm->evm
                tx = {
                    "to": Web3.to_checksum_address(to),
                    "value": raw,
                }
            receipt = self._send_evm_tx(tx)
            return WrittenTransactionResult(
                message=f"Sent {amount} native-token from {self.metadata.pair.address} to {to}.",
                receipt=receipt
            )
            
        else:
            # Substrate side
            addr_type = self._addr_type(to)
            display_address = to
            if addr_type == "evm": # substrate->evm
                to = evm_to_address(to)
                
            call = self.api.compose_call(
                call_module="Balances",
                call_function="transfer_keep_alive",
                call_params={"dest": to, "value": raw},
            )
            receipt = self._send_substrate_tx(call)
            return WrittenTransactionResult(
                message=f"Sent {amount} native-token from {self.metadata.pair.ss58_address} to {display_address}.",
                receipt=receipt
            )

    def _to_raw_amount(self, human_amount: Union[int, float, str, Decimal], token_decimals) -> int:
        """
        Converts a human-readable token amount to its raw on-chain format.

        Args:
            human_amount (int | float | str | Decimal): The human amount to convert.
            token_decimals (int): The number of decimals used by the chain's token.

        Returns:
            int: The scaled, raw amount suitable for use in a transaction.
        """
        d = Decimal(str(human_amount))
        scale = Decimal(10) ** token_decimals
        return int(d * scale)
    

    # native_transfer
    # erc20_transfer
    # asset_transfer