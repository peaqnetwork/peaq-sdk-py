from typing import Optional, Union
from decimal import Decimal

from peaq_sdk.base import Base
from peaq_sdk.types.base import TxOptions, StatusCallback
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    PrecompileAddresses,
    WrittenTransactionResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult
)
from peaq_sdk.types.transfer import (
    PayFunctionSignatures,
    NativeTransferOptions,
    ERC20TransferOptions,
    ERC721TransferOptions
)
from peaq_sdk.utils.utils import evm_to_address, parse_options

from web3 import Web3
from web3.types import TxParams
from substrateinterface.base import SubstrateInterface
from substrateinterface.utils.ss58 import is_valid_ss58_address, ss58_decode
from eth_abi import encode


# TODO add option for user to manually send the built tx

class Transfer(Base):
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
        raise ValueError(f"Address {addr!r} is neither a valid Substrate SS58 nor a valid EVM H160.")

# native tokens
    async def native(
        self, 
        options: NativeTransferOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> WrittenTransactionResult:
        """
        Transfers the native token from the signer to a target address.

        - On EVM:
            - If `to` is a Substrate address, uses the precompile to transfer to SS58.
            - If `to` is an EVM address, sends a standard ETH-style value transfer.
        - On Substrate:
            - If `to` is an EVM address, converts it to SS58 and uses `transfer_keep_alive`.
            - If `to` is Substrate, uses `transfer_keep_alive` directly.

        Args:
            options (NativeTransferOptions): Options containing recipient address and amount.
            status_callback: Optional callback function for transaction status updates.
            tx_options: Optional TxOptions for EVM transactions.

        Returns:
            WrittenTransactionResult: A message and transaction receipt object.

        Raises:
            ValueError: If address format is invalid.
        """
        ops = parse_options(NativeTransferOptions, options, caller="transfer.native()")
        
        to = ops.to
        amount = ops.amount
        
        raw = self._to_raw_amount(amount,
            token_decimals=(
                18 if self.metadata.chain_type == ChainType.EVM
                   else self.api.token_decimals
            )
        )
        
        if self.metadata.chain_type == ChainType.EVM:
            addr_type = self._addr_type(to)
            if addr_type == "substrate": # evm->substrate
                function_selector = self.api.keccak(text=PayFunctionSignatures.TRANSFER_TO_ACCOUNT_ID.value)[:4].hex()
                pubkey = bytes.fromhex(ss58_decode(to))
                encoded_params = encode(
                    ["bytes32", "uint256"], 
                    [pubkey, raw]
                ).hex()
                tx: TxParams = {
                    "to": PrecompileAddresses.IERC20.value,
                    "data": f"0x{function_selector}{encoded_params}"
                }
            else:  # evm->evm
                tx = {
                    "to": Web3.to_checksum_address(to),
                    "value": raw,
                }
            return await self._handle_evm_tx(tx, f"transfer {amount} native tokens to {to}", status_callback, tx_options)
            
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
            return self._handle_substrate_tx(call, f"transfer {amount} native tokens to {display_address}", status_callback)


    async def erc20(
        self, 
        options: ERC20TransferOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> WrittenTransactionResult:
        ops = parse_options(ERC20TransferOptions, options, caller="transfer.erc20()")
        
        erc_20_address = ops.erc_20_address
        recipient_address = ops.recipient_address
        amount = ops.amount
        token_decimals = ops.token_decimals
        
        raw = self._to_raw_amount(amount,
            token_decimals=(
                18 if token_decimals == None
                   else token_decimals
            )
        )
        
        function_selector = self.api.keccak(text=PayFunctionSignatures.ERC_20_TRANSFER.value)[:4].hex()
        encoded_params = encode(
            ["address", "uint256"], 
            [recipient_address, raw]
        ).hex()
        erc_20_checksum = Web3.to_checksum_address(erc_20_address)
        tx: TxParams = {
            "to": erc_20_checksum,
            "data": f"0x{function_selector}{encoded_params}"
        }
        return await self._handle_evm_tx(tx, f"transfer {amount} ERC-20 tokens from {erc_20_address} to {recipient_address}", status_callback, tx_options)
        
        
    async def erc721(
        self, 
        options: ERC721TransferOptions,
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ) -> WrittenTransactionResult:
        ops = parse_options(ERC721TransferOptions, options, caller="transfer.erc721()")
        
        erc_721_address = ops.erc_721_address
        recipient_address = ops.recipient_address
        token_id = ops.token_id
        
        function_selector = self.api.keccak(text=PayFunctionSignatures.ERC_721_SAFE_TRANSFER_FROM.value)[:4].hex()
        encoded_params = encode(
            ["address", "address", "uint256"], 
            [self.metadata.pair.address, recipient_address, token_id]
        ).hex()
        erc_721_checksum = Web3.to_checksum_address(erc_721_address)
        tx: TxParams = {
            "to": erc_721_checksum,
            "data": f"0x{function_selector}{encoded_params}"
        }
        return await self._handle_evm_tx(tx, f"transfer ERC-721 token {token_id} from {erc_721_address} to {recipient_address}", status_callback, tx_options)
    


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
    

    # asset_transfer ??
    
    # ---------------  Generalized handlers ----------------
    async def _handle_evm_tx(
        self, 
        tx: TxParams, 
        action: str, 
        status_callback: StatusCallback = None,
        tx_options: TxOptions = {}
    ):
        """
        Generalized handler for EVM transactions.
        
        Args:
            tx (TxParams): The transaction parameters
            action (str): Description of the action being performed
            status_callback: Optional callback for transaction status
            tx_options: Optional transaction options
            
        Returns:
            Union[EvmSendResult, BuiltEvmTransactionResult]: 
                - EvmSendResult: For signed transactions with tx_hash, unsubscribe, and receipt promise
                - BuiltEvmTransactionResult: For unsigned transactions with message and tx object
        """
        if not self.metadata.pair:
            return BuiltEvmTransactionResult(
                message=f"Constructed {action} tx (unsigned).",
                tx=tx
            )
        try:
            return await self._send_evm_tx(tx, on_status=status_callback, opts=tx_options)
        except Exception as err:
            raise Exception(f"Failed to {action}: {str(err)}")

    def _handle_substrate_tx(
        self, 
        call, 
        action: str, 
        status_callback: StatusCallback = None
    ):
        """
        Generalized handler for Substrate transactions.
        
        Args:
            call: The Substrate call object
            action (str): Description of the action being performed
            status_callback: Optional callback for transaction status
            
        Returns:
            Union[SubstrateSendResult, BuiltCallTransactionResult]:
                - SubstrateSendResult: For signed transactions with tx_hash, unsubscribe, and finalize promise
                - BuiltCallTransactionResult: For unsigned transactions with message and call object
        """
        if not self.metadata.pair:
            return BuiltCallTransactionResult(
                message=f"Constructed {action} call (unsigned).",
                call=call
            )
        try:
            return self._send_substrate_tx(call, on_status=status_callback)
        except Exception as err:
            raise Exception(f"Failed to {action}: {str(err)}")