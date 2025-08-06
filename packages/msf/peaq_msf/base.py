from typing import Optional, Dict, Any
from enum import Enum
import asyncio
from hexbytes import HexBytes
from peaq_msf.utils.utils import parse_options

from peaq_msf.types.common import ChainType, SDKMetadata
from peaq_msf.types.base import (
    TransactionStatus, 
    ConfirmationMode, 
    TransactionStatusCallback, 
    TxOptions,
    EvmSendResult,
    StatusCallback
)

from web3 import Web3
from web3.types import TxParams
from eth_account.signers.base import BaseAccount


class Base:
    """
    Provides shared functionality for both EVM and Substrate SDK operations,
    including signer generation and transaction submission logic.
    """
    def __init__(self, api: Web3, metadata: SDKMetadata) -> None:
        """
        Initializes Base with a connected API instance and shared SDK metadata.

        Args:
            api (Web3): The blockchain API connection.
                which must be a Web3 (EVM).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        self._api = api
        self._metadata = metadata
        self._chain_id: Optional[int] = None
    
    @property
    def api(self):
        """Allows access to the same api object across the sdk using self.api"""
        return self._api
    @property
    def metadata(self):
        """Allows access to the same metadata object across the sdk using self.metadata"""
        return self._metadata
    
    async def get_chain_id(self) -> int:
        """
        Gets the chain ID for EVM-compatible blockchains using Web3 provider.
        Caches the chain ID after first fetch to avoid repeated RPC calls.
        
        Returns:
            int: The EVM chain ID as a number
            
        Raises:
            ValueError: If chain type is not EVM or if Web3 provider is not available
        """
        if self._metadata.chain_type is ChainType.EVM:
            if self._api:
                try:
                    # Cache on first fetch
                    if self._chain_id is None:
                        self._chain_id = await self._api.eth.chain_id
                    return self._chain_id
                except Exception as e:
                    raise ValueError(f'Failed to get chain ID from Web3 provider: {str(e)}')
            else:
                raise ValueError('EVM chain type requires Web3 provider')
        else:
            raise ValueError('Only EVM chain type is supported by Machine Station SDK')
    
    def _set_signer(self, auth: BaseAccount):
        """
        Sets the signer from auth input - handles BaseAccount or Keypair.

        Args:
            auth: BaseAccount instance (EVM) or Keypair instance (Substrate)

        Returns:
            BaseAccount | Keypair: The configured signer

        Raises:
            ValueError: If auth is invalid or incompatible with chain type
        """
        if self._metadata.chain_type.value is ChainType.EVM.value:
            if isinstance(auth, BaseAccount):
                self._metadata.pair = auth
                return auth
        else:
            raise ValueError('Invalid chain type')

    def _emit_status_callback(
        self,
        on_status,
        cancelled: bool,
        status_update: TransactionStatusCallback
    ) -> None:
        """
        Emit status callback if provided and not cancelled.
        
        Args:
            on_status: Optional callback function
            cancelled: Whether callbacks are cancelled
            status_update: Status update data
        """
        if on_status and not cancelled:
            cleaned_data = self._clean_callback_data(status_update.model_dump())
            on_status(cleaned_data)
    
    def _create_status_update(
        self,
        status: TransactionStatus,
        confirmation_mode: ConfirmationMode,
        total_confirmations: int,
        tx_hash: str,
        receipt: Optional[Dict[str, Any]] = None,
        nonce: Optional[int] = None
    ) -> TransactionStatusCallback:
        """
        Create a status update object for callbacks.
        
        Args:
            status: Current transaction status
            confirmation_mode: Transaction confirmation mode
            total_confirmations: Number of confirmations seen
            tx_hash: Transaction hash
            receipt: Optional transaction receipt
            nonce: Optional transaction nonce
            
        Returns:
            TransactionStatusCallback object with current transaction state
        """
        return TransactionStatusCallback(
            status=status.value,
            confirmation_mode=confirmation_mode.value,
            total_confirmations=total_confirmations,
            hash=tx_hash,
            receipt=receipt,
            nonce=nonce
        )

    def _clean_callback_data(self, obj: Any) -> Any:
        """
        Recursively clean callback data by converting HexBytes to hex strings,
        Enums to their values, and other types into JSON-serializable formats.
        Also ensures transaction hashes and block hashes have '0x' prefix.
        """
        
        if isinstance(obj, HexBytes):
            return obj.hex()
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool)):
            return self._clean_callback_data(vars(obj))
        if isinstance(obj, dict):
            cleaned_dict = {}
            for k, v in obj.items():
                cleaned_value = self._clean_callback_data(v)
                # Add '0x' prefix to transaction hashes and block hashes
                if k in ['transactionHash', 'blockHash'] and isinstance(cleaned_value, str) and cleaned_value and not cleaned_value.startswith('0x'):
                    cleaned_value = '0x' + cleaned_value
                cleaned_dict[k] = cleaned_value
            return cleaned_dict
        if isinstance(obj, list):
            return [self._clean_callback_data(v) for v in obj]
        return obj
    

    async def _send_evm_tx(
        self, 
        tx: TxParams,
        on_status: StatusCallback = None,
        opts: TxOptions = {},
        iface: Optional[Any] = None
    ) -> EvmSendResult:
        """
        Sends an EVM transaction and returns a structured EvmSendResult.
        
        Args:
            tx: Transaction parameters
            on_status: Optional status callback
            opts: Transaction options
            iface: Optional contract interface for better error decoding
            
        Returns:
            EvmSendResult with tx_hash (immediate), unsubscribe function, and receipt promise
        """
        opts = parse_options(TxOptions, opts, caller="_send_evm_tx()")
        
        
        if not self._metadata.pair:
            raise Exception('No signer available for signing')
        
        # Build transaction
        built_tx = await self._build_evm_tx(tx, opts)
        
        # Sign and send transaction
        signed_tx = self._metadata.pair.sign_transaction(built_tx)
        tx_hash = await self._api.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Emit BROADCAST status immediately
        if on_status:
            status_update = self._create_status_update(
                status=TransactionStatus.BROADCAST,
                confirmation_mode=opts.mode,
                total_confirmations=0,
                tx_hash="0x" + tx_hash.hex(),
                nonce=built_tx.get('nonce')
            )
            self._emit_status_callback(on_status, False, status_update)
        
        # Create a flag to track if unsubscribed
        is_unsubscribed = False
        
        def unsubscribe():
            nonlocal is_unsubscribed
            is_unsubscribed = True
        
        async def get_receipt():
            """Async function that waits for transaction receipt and confirmations"""
            try:
                # Wait for first confirmation
                receipt = await self._api.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 0:
                    raise Exception('Transaction failed')
                
                # Check if unsubscribed before emitting status
                if not is_unsubscribed and on_status:
                    status_update = self._create_status_update(
                        status=TransactionStatus.IN_BLOCK,
                        confirmation_mode=opts.mode,
                        total_confirmations=1,
                        tx_hash="0x" + tx_hash.hex(),
                        receipt=dict(receipt),
                        nonce=built_tx.get('nonce')
                    )
                    self._emit_status_callback(on_status, False, status_update)
                
                # Wait for confirmations based on mode using native async
                if not is_unsubscribed:
                    final_receipt = await self._wait_for_confirmations(tx_hash, receipt, opts, on_status if not is_unsubscribed else None)
                    return final_receipt
                else:
                    raw = dict(receipt)
                    cleaned = self._clean_callback_data(raw)
                    return cleaned
                
            except Exception as error:
                # Use enhanced error parsing if iface is provided
                if iface:
                    error_message = self._parse_evm_error(error, iface)
                    raise Exception(f"EVM transaction failed: {error_message}")
                else:
                    raise Exception(f"EVM transaction failed: {str(error)}")
        
        return EvmSendResult(
            tx_hash="0x" + tx_hash.hex(),
            unsubscribe=unsubscribe,
            receipt=get_receipt()
        )


    async def _build_evm_tx(
        self, 
        tx: TxParams,
        opts: TxOptions
    ) -> TxParams:
        """
        Builds an EVM transaction with gas estimation and fee calculation.
        """
        checksum_address = Web3.to_checksum_address(self._metadata.pair.address)
        tx['from'] = checksum_address
        tx['nonce'] = await self._api.eth.get_transaction_count(checksum_address)
        tx['chainId'] = await self.get_chain_id()

        # Estimate gas limit if not provided
        estimated_gas = await self._api.eth.estimate_gas(tx)
        tx['gas'] = opts.gas_limit if opts.gas_limit else estimated_gas

        # Get current fee data
        pending = await self._api.eth.get_block("pending")
        base_fee = pending.get("baseFeePerGas")
        priority_fee = await self._api.eth.max_priority_fee
        tx['type'] = 2

        tx['maxFeePerGas'] = opts.max_fee_per_gas if opts.max_fee_per_gas else base_fee
        tx['maxPriorityFeePerGas'] = opts.max_priority_fee_per_gas if opts.max_priority_fee_per_gas else priority_fee
        
        return tx

    async def _wait_for_confirmations(
        self,
        tx_hash,
        receipt,
        opts: TxOptions,
        on_status
    ) -> dict:
        """
        Waits for confirmations based on the specified mode.
        """
        if opts.mode == ConfirmationMode.FAST:
            # Already have 1 confirmation, nothing more needed
            raw = dict(receipt)
            cleaned = self._clean_callback_data(raw)
            return cleaned

        elif opts.mode == ConfirmationMode.CUSTOM:
            # Wait for user's target confirmations
            CUSTOM_POLL_INTERVAL_MS = 1000
            starting_finalized = await self._api.eth.get_block("finalized")
            if not starting_finalized:
                raise Exception("Could not fetch finalized head")
            
            inclusion_block = receipt['blockNumber']
            
            # Wait for the finalized head to advance by the required confirmations
            while True:
                try:
                    current_finalized = await self._api.eth.get_block("finalized")
                    if not current_finalized:
                        raise Exception("Could not fetch current finalized head")
                    
                    confirmations_seen = current_finalized['number'] - starting_finalized['number'] + 1
                    
                    if confirmations_seen >= opts.confirmations:
                        break
                    
                    await asyncio.sleep(CUSTOM_POLL_INTERVAL_MS / 1000)
                    
                except Exception as e:
                    raise Exception(f"Error waiting for confirmations: {str(e)}")
            
            # Validate the receipt is still canonical to guard against chain reorgs
            try:
                canonical_receipt = await self._api.eth.get_transaction_receipt(tx_hash)
                if not canonical_receipt:
                    raise Exception('Could not fetch canonical transaction receipt')
            except Exception:
                canonical_receipt = receipt
            
            # Final finalized head check
            finalized_head = await self._api.eth.get_block("finalized")
            if not finalized_head:
                raise Exception("Could not fetch finalized head")
            
            # Check if finalized head is at or ahead of inclusion block
            confirmations_seen = finalized_head['number'] - starting_finalized['number'] + 1
            status = TransactionStatus.FINALIZED if finalized_head['number'] >= inclusion_block else TransactionStatus.IN_BLOCK
            
            # Emit final custom confirmations callback
            if on_status:
                status_update = self._create_status_update(
                    status=status,
                    confirmation_mode=opts.mode,
                    total_confirmations=confirmations_seen,
                    tx_hash="0x" + tx_hash.hex(),
                    receipt=dict(canonical_receipt)
                )
                self._emit_status_callback(on_status, False, status_update)
            
            raw = dict(canonical_receipt)
            cleaned = self._clean_callback_data(raw)
            return cleaned

        elif opts.mode == ConfirmationMode.FINAL:
            # Poll until the finalized head >= inclusion block
            FINALITY_POLL_INTERVAL_MS = 1000
            starting_block = await self._api.eth.get_block("finalized")
            if not starting_block:
                raise Exception('Could not get finalized block')
            
            inclusion_block = receipt['blockNumber']
            
            # Wait until finalized head reaches inclusion block
            while True:
                finalized_head_final = await self._api.eth.get_block("finalized")
                if not finalized_head_final:
                    raise Exception('Could not get finalized block')
                
                if finalized_head_final['number'] >= inclusion_block:
                    break
                    
                await asyncio.sleep(FINALITY_POLL_INTERVAL_MS / 1000)  # Convert to seconds
            
            # Fetch new receipt after finalized head has passed inclusion block
            final_receipt = await self._api.eth.get_transaction_receipt(tx_hash)
            if not final_receipt:
                raise Exception("Could not fetch final receipt")
            
            final_confirmations = final_receipt['blockNumber'] - starting_block['number']
            
            # Emit finalized status callback
            if on_status:
                status_update = self._create_status_update(
                    status=TransactionStatus.FINALIZED,
                    confirmation_mode=opts.mode,
                    total_confirmations=final_confirmations,
                    tx_hash="0x" + tx_hash.hex(),
                    receipt=dict(final_receipt)
                )
                self._emit_status_callback(on_status, False, status_update)
            
            raw = dict(final_receipt)
            
            cleaned = self._clean_callback_data(raw)
            return cleaned

        else:
            raise ValueError(f"Unknown confirmation mode: {opts.mode}")

    def _parse_evm_error(self, error: Any, iface: Optional[Any] = None) -> str:
        """
        Enhanced error parsing for smart contract errors.
        This method uses the contract interface to decode known errors from the ABI,
        while also handling wrapped errors from target contracts.
        
        Args:
            error: The error object from web3
            iface: Optional contract interface to decode custom errors
            
        Returns:
            A human-readable error message
        """
        if not error:
            return 'Unknown error occurred'

        # Contract exception
        if hasattr(error, 'code') and error.code == 'CALL_EXCEPTION':
            # Try to decode contract errors first
            if hasattr(error, 'data') and error.data and iface:
                try:
                    # Try to decode the error using the contract interface
                    decoded_error = iface.decode_function_result(error.data)
                    if decoded_error:
                        # Format the decoded error nicely
                        args = decoded_error.args if hasattr(decoded_error, 'args') else []
                        args_str = ''
                        if args:
                            formatted_args = []
                            for arg in args:
                                if isinstance(arg, str) and arg.startswith('0x') and len(arg) == 42:
                                    # Shorten addresses
                                    formatted_args.append(f"{arg[:6]}...{arg[-4:]}")
                                else:
                                    formatted_args.append(str(arg))
                            args_str = f" ({', '.join(formatted_args)})"
                        
                        error_name = getattr(decoded_error, 'name', 'UnknownError')
                        return f"Contract error: {error_name}{args_str}"
                except Exception:
                    # Fall through to wrapped error handling
                    pass

        # Handle web3 specific errors
        if hasattr(error, 'shortMessage'):
            error_data = getattr(error, 'data', '')
            
            # Handle unknown custom error with helpful messages
            if error.shortMessage == 'execution reverted (unknown custom error)':
                target_address = self._extract_target_address(getattr(error, 'transaction', {}).get('data', ''))
                if target_address:
                    return f"Contract error: Operation failed with selector {error_data[:10]} (likely item already exists, incorrect machine owner signature, insufficient permissions, invalid parameters, or machine station factory out of gas)"
            
            return error.shortMessage

        # Handle other common error cases
        if hasattr(error, 'code'):
            if error.code == 'INSUFFICIENT_FUNDS':
                return 'Insufficient funds to complete the transaction'
            if error.code == 'NONCE_EXPIRED':
                return 'Transaction nonce has expired. Please try again'
            if error.code == 'REPLACEMENT_UNDERPRICED':
                return 'Gas price too low to replace pending transaction'

        # If we can't parse it specifically, return the message or toString()
        return getattr(error, 'message', str(error))

    def _extract_target_address(self, tx_data: str) -> Optional[str]:
        """
        Extract target address from transaction data.
        
        Args:
            tx_data: Transaction data string
            
        Returns:
            Target address if found, None otherwise
        """
        if not tx_data or not tx_data.startswith('0x'):
            return None
        
        try:
            # Extract the target address from the transaction data
            # This is a simplified version - in practice you might need more sophisticated parsing
            if len(tx_data) >= 42:  # Minimum length for address
                # Look for address pattern in the data
                for i in range(len(tx_data) - 40):
                    potential_addr = tx_data[i:i+42]
                    if potential_addr.startswith('0x') and len(potential_addr) == 42:
                        return potential_addr
        except Exception:
            pass
        
        return None