from typing import Optional, Union, List
import ast
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from peaq_sdk.types.common import (
    ChainType, ExtrinsicExecutionError, EvmTransaction, SeedError, SDKMetadata,
    ConfirmationMode, BatchMode, TransactionConfig, BatchConfig, TxReceipt, 
    BatchReceipt, CallModule, UtilityCallFunction, BatchExecutionError
)

from web3 import Web3
from eth_account import Account
from substrateinterface.base import SubstrateInterface, GenericCall
from substrateinterface.keypair import Keypair, KeypairType
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException

class Base:
    """
    Provides shared functionality for both EVM and Substrate SDK operations,
    including signer generation and transaction submission logic with improved
    batch processing, retry mechanisms, and confirmation modes.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes Base with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        self._api = api
        self._metadata = metadata
    
    @property
    def api(self):
        """Allows access to the same api object across the sdk using self.api"""
        return self._api
    @property
    def metadata(self):
        """Allows access to the same metadata object across the sdk using self.metadata"""
        return self._metadata
    
    def _create_key_pair(self, seed: str):
        """
        Generates a blockchain key pair from a seed string.

        For EVM chains, interprets `seed` as a hex private key and returns an
        `eth_account.Account`. For Substrate chains, treats `seed` as a BIP39
        mnemonic (12 or 24 words) and returns a `substrateinterface.Keypair`.

        Args:
            chain_type (ChainType): The target chain type (EVM or SUBSTRATE).
            seed (str): Hex private key (EVM) or mnemonic phrase (Substrate).

        Returns:
            Account | Keypair: A signing key pair for transactions.

        Raises:
            ValueError: If `seed` is empty or None.
        """
        if not seed:
            raise ValueError('Seed is required')
        if self._metadata.chain_type is ChainType.EVM:
            self._metadata.pair = Account.from_key(seed)
        else:
            self._metadata.pair = Keypair.create_from_mnemonic(
                seed,
                ss58_format=42,
                crypto_type=KeypairType.SR25519
            )
            
    def _resolve_address(self, address: Optional[str] = None) -> str:
            """
            Resolves the user address for DID-related operations based on the chain type
            (EVM or Substrate) and whether a local keypair is available.

            - EVM: If a local pair is provided, the address is derived from the
            `Account` object (`account.address`). Otherwise, `address` is used, and a
            `SeedError` is raised if no `address` is specified.

            - Substrate: If a local pair is provided, uses its `ss58_address`. Otherwise falls
            back to the optional `address`, and raises `SeedError` if neither
            is available.

            Args:
                chain_type (ChainType): The blockchain type (EVM or Substrate).
                pair (Union[Keypair, Account]): A local keypair or EVM account, if any.
                address (Optional[str]): An optional fallback address. For EVM, this
                    should be an H160 address; for Substrate, an SS58 address.

            Returns:
                str: The resolved user address to be used for DID creation, update,
                    or removal.

            Raises:
                SeedError: If neither a local keypair nor a fallback `address` is provided.
            """
            # Check chain type
            if self._metadata.chain_type is ChainType.EVM:
                if self._metadata.pair:
                    # We have a local EVM account
                    account = self._metadata.pair
                    return account.address
                else:
                    # No local account: must rely on 'address' parameter
                    if not address:
                        raise SeedError(
                            "No seed/private key set, and no address was provided. "
                            "Unable to sign or construct the transaction properly."
                        )
                    return address
            else:
                # Substrate path
                if self._metadata.pair:
                    # We have a local Substrate keypair
                    keypair = self._metadata.pair
                    return keypair.ss58_address
                else:
                    # No local keypair: must rely on 'address' parameter
                    if not address:
                        raise SeedError(
                            "No seed/private key set, and no address was provided. "
                            "Unable to sign or construct the transaction properly."
                        )
                    return address

    def send_transaction(
        self, 
        call: GenericCall, 
        config: Optional[TransactionConfig] = None
    ) -> TxReceipt:
        """
        Unified transaction sending with improved retry logic and confirmation modes.
        
        Args:
            call (GenericCall): The substrate call to execute
            config (Optional[TransactionConfig]): Configuration for transaction execution
            
        Returns:
            TxReceipt: Unified receipt format
        """
        if config is None:
            config = TransactionConfig()
            
        if self._metadata.chain_type == ChainType.EVM:
            return self._send_evm_transaction(call, config)
        else:
            return self._send_substrate_transaction(call, config)
    
    def send_batch_transactions(
        self,
        calls: List[GenericCall],
        batch_config: Optional[BatchConfig] = None
    ) -> BatchReceipt:
        """
        Send multiple transactions with various batching strategies.
        
        Args:
            calls (List[GenericCall]): List of calls to execute
            batch_config (Optional[BatchConfig]): Batch execution configuration
            
        Returns:
            BatchReceipt: Receipt containing results of all transactions
        """
        if batch_config is None:
            batch_config = BatchConfig()
            
        if len(calls) > batch_config.max_batch_size:
            raise BatchExecutionError(f"Batch size {len(calls)} exceeds maximum {batch_config.max_batch_size}")
            
        if batch_config.batch_mode == BatchMode.ATOMIC:
            return self._send_atomic_batch(calls, batch_config)
        elif batch_config.batch_mode == BatchMode.PARALLEL:
            return self._send_parallel_batch(calls, batch_config)
        else:  # SEQUENTIAL
            return self._send_sequential_batch(calls, batch_config)
    
    def _send_atomic_batch(self, calls: List[GenericCall], batch_config: BatchConfig) -> BatchReceipt:
        """
        Send calls as a single atomic batch using utility.batchAll.
        If any call fails, the entire batch rolls back.
        """
        if self._metadata.chain_type == ChainType.EVM:
            raise BatchExecutionError("Atomic batch not supported for EVM chains")
            
        # Create utility.batchAll call
        batch_call = self._api.compose_call(
            call_module=CallModule.UTILITY.value,
            call_function=UtilityCallFunction.BATCH_ALL.value,
            call_params={'calls': calls}
        )
        
        try:
            receipt = self.send_transaction(batch_call, batch_config.transaction_config)
            return BatchReceipt(
                batch_hash=receipt.tx_hash,
                receipts=[receipt],
                success=receipt.success
            )
        except Exception as e:
            return BatchReceipt(
                success=False,
                error=str(e)
            )
    
    def _send_parallel_batch(self, calls: List[GenericCall], batch_config: BatchConfig) -> BatchReceipt:
        """
        Send calls concurrently using thread pool.
        """
        receipts = []
        success = True
        failed_at_index = None
        
        with ThreadPoolExecutor(max_workers=min(len(calls), 10)) as executor:
            # Submit all calls
            future_to_index = {
                executor.submit(self.send_transaction, call, batch_config.transaction_config): i
                for i, call in enumerate(calls)
            }
            
            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    receipt = future.result()
                    receipts.append((index, receipt))
                    if not receipt.success:
                        success = False
                        if failed_at_index is None:
                            failed_at_index = index
                except Exception as e:
                    success = False
                    if failed_at_index is None:
                        failed_at_index = index
                    receipts.append((index, TxReceipt(
                        tx_hash="",
                        success=False,
                        error=str(e)
                    )))
        
        # Sort receipts by original order
        receipts.sort(key=lambda x: x[0])
        
        return BatchReceipt(
            receipts=[r[1] for r in receipts],
            success=success,
            failed_at_index=failed_at_index
        )
    
    def _send_sequential_batch(self, calls: List[GenericCall], batch_config: BatchConfig) -> BatchReceipt:
        """
        Send calls one by one in sequence.
        """
        receipts = []
        success = True
        failed_at_index = None
        
        for i, call in enumerate(calls):
            try:
                receipt = self.send_transaction(call, batch_config.transaction_config)
                receipts.append(receipt)
                if not receipt.success:
                    success = False
                    failed_at_index = i
                    break  # Stop on first failure for sequential mode
            except Exception as e:
                success = False
                failed_at_index = i
                receipts.append(TxReceipt(
                    tx_hash="",
                    success=False,
                    error=str(e)
                ))
                break
                
        return BatchReceipt(
            receipts=receipts,
            success=success,
            failed_at_index=failed_at_index
        )
    
    def _send_substrate_transaction(self, call: GenericCall, config: TransactionConfig) -> TxReceipt:
        """
        Enhanced Substrate transaction sending with proper BUILD-SUBMIT-CONFIRM-FORMAT flow.
        """
        # BUILD PHASE
        payment_info = self._api.get_payment_info(call, keypair=self._metadata.pair)
        base_fee = payment_info['partialFee']
        tip = int(base_fee * config.fee_multiplier) if config.fee_multiplier > 0 else 0
        
        # SUBMIT & RETRY PHASE
        attempt = 0
        current_tip = tip
        
        while attempt < config.max_retries:
            try:
                # Sign transaction
                extrinsic = self._api.create_signed_extrinsic(
                    call=call,
                    keypair=self._metadata.pair,
                    tip=current_tip
                )
                
                # Submit transaction
                receipt = self._api.submit_extrinsic(
                    extrinsic,
                    wait_for_inclusion=config.mode != ConfirmationMode.FAST,
                    wait_for_finalization=config.mode == ConfirmationMode.SAFE or config.wait_for_finalization
                )
                
                # CONFIRMATION PHASE
                if config.mode == ConfirmationMode.FAST:
                    # Return immediately with tx hash
                    return self._format_substrate_receipt(receipt, call, finalized=False)
                else:
                    # Wait for inclusion and optionally finalization
                    return self._format_substrate_receipt(receipt, call, finalized=receipt.finalized)
                    
            except WebSocketConnectionClosedException:
                print(f"Attempt {attempt + 1}: WebSocket closed, reconnecting...")
                self._api = SubstrateInterface(url=self._metadata.base_url, ss58_format=42)
                attempt += 1
                time.sleep(0.5)
                
            except SubstrateRequestException as e:
                error_message = str(e)
                print(f"Attempt {attempt + 1}: {error_message}")
                
                # Parse error and determine if we should retry with higher tip
                if self._should_retry_with_higher_tip(error_message):
                    current_tip = int(current_tip * 1.25)
                    attempt += 1
                    time.sleep(0.5)
                else:
                    raise ExtrinsicExecutionError(f"Transaction failed: {error_message}")
                    
        raise ExtrinsicExecutionError(f"Failed to submit transaction after {config.max_retries} attempts")
    
    def _should_retry_with_higher_tip(self, error_message: str) -> bool:
        """
        Determine if we should retry with a higher tip based on the error message.
        """
        low_priority_errors = [
            "Priority is too low",
            "Immediately Dropped", 
            "pool limit",
            "limit"
        ]
        return any(error in error_message for error in low_priority_errors)
    
    def _format_substrate_receipt(self, receipt, call: GenericCall, finalized: bool = False) -> TxReceipt:
        """
        FORMAT RECEIPT PHASE: Safely extract and format receipt data.
        """
        try:
            events = []
            if hasattr(receipt, 'triggered_events'):
                for event in receipt.triggered_events:
                    try:
                        events.append({
                            "module": event.value["event"]["module_id"],
                            "event": event.value["event"]["event_id"],
                            "attributes": event.value["event"]["attributes"]
                        })
                    except (KeyError, IndexError, AttributeError):
                        # Skip malformed events
                        continue
            
            return TxReceipt(
                tx_hash=getattr(receipt, "extrinsic_hash", ""),
                block_hash=getattr(receipt, "block_hash", None),
                success=getattr(receipt, "is_success", True) and receipt.error_message is None,
                finalized=finalized,
                events=events,
                fee=getattr(receipt, "total_fee_amount", None),
                error=str(receipt.error_message) if receipt.error_message else None
            )
        except Exception as e:
            # Fallback for any formatting errors
            return TxReceipt(
                tx_hash=getattr(receipt, "extrinsic_hash", ""),
                success=False,
                error=f"Receipt formatting error: {str(e)}"
            )
    
    # Keep existing legacy methods for backwards compatibility
    def _send_substrate_tx(self, call: GenericCall, tip_multiplier: float = 0.0, wait_for_finalization: bool = True) -> dict:
        """
        Legacy method - redirects to new implementation
        """
        config = TransactionConfig(
            fee_multiplier=tip_multiplier,
            wait_for_finalization=wait_for_finalization,
            mode=ConfirmationMode.SAFE if wait_for_finalization else ConfirmationMode.BALANCED
        )
        receipt = self.send_transaction(call, config)
        
        # Convert back to legacy format
        return self._legacy_format_receipt(receipt, call)

    def _legacy_format_receipt(self, receipt: TxReceipt, call: GenericCall) -> dict:
        """Convert new receipt format back to legacy format for backwards compatibility"""
        return {
            "extrinsic_hash": receipt.tx_hash,
            "block_hash": receipt.block_hash,
            "finalized": receipt.finalized,
            "success": receipt.success,
            "call": {
                "module": call.call_module["name"],
                "function": call.call_function,
                "args": call.call_args
            },
            "events": receipt.events,
            "fee": receipt.fee
        }
        
    # Keep existing EVM methods unchanged for now - can be updated later
    def _send_evm_tx(self, tx: dict, max_attempts: int = 5) -> dict:
        """
        Sends an EVM transaction with retry logic by increasing gas price on failure.
        if disconnection occurs attempts to reconnect.

        Args:
            tx (dict): Transaction dict with at minimum 'to' and 'data'.
            account (Account): Account object with private key.
            max_attempts (int): Max retries on failure due to low priority.

        Returns:
            dict: Transaction receipt

        Raises:
            ExtrinsicExecutionError: If all retries fail or any critical error occurs.
        """
        checksum_address = Web3.to_checksum_address(self._metadata.pair.address)
        tx['from'] = checksum_address
        nonce = self._api.eth.get_transaction_count(checksum_address)
        tx['nonce'] = nonce
        
        gas_price = None
        attempt = 0

        while attempt < max_attempts:
            try:
                # Check connection before attempt
                self._api.eth.chain_id
                
                # Get payment info once
                if attempt == 0:
                    gas_price = self._api.eth.gas_price
                    # Add buffer to initial gas price to reduce base fee conflicts
                    gas_price = int(gas_price * 1.1)  # 10% buffer
                
                # Try to use EIP-1559 style transaction if supported
                try:
                    latest_block = self._api.eth.get_block('latest')
                    if 'baseFeePerGas' in latest_block:
                        # Network supports EIP-1559, use type 2 transaction
                        base_fee = latest_block['baseFeePerGas']
                        max_priority_fee = int(gas_price * 0.1)  # 10% of gas price as priority fee
                        max_fee = base_fee * 2 + max_priority_fee  # 2x base fee + priority
                        
                        tx['maxFeePerGas'] = max_fee
                        tx['maxPriorityFeePerGas'] = max_priority_fee
                        tx['type'] = '0x2'  # EIP-1559 transaction type
                        # Remove legacy gasPrice when using EIP-1559
                        if 'gasPrice' in tx:
                            del tx['gasPrice']
                    else:
                        # Fallback to legacy transaction
                        tx['gasPrice'] = gas_price
                except Exception:
                    # If EIP-1559 detection fails, use legacy transaction
                    tx['gasPrice'] = gas_price
                tx['chainId'] = self._api.eth.chain_id
                tx['gas'] = self._api.eth.estimate_gas(tx)

                signed_tx = self._metadata.pair.sign_transaction(tx)
                tx_hash = self._api.eth.send_raw_transaction(signed_tx.raw_transaction)

                try:
                    receipt = self._api.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    return receipt
                except Exception as wait_error:
                    print(f"Attempt {attempt + 1}: Tx {tx_hash.hex()} not confirmed within timeout: {wait_error}")
                    # Check if the tx is still in the mempool (pending) using the same nonce.
                    try:
                        pending_tx = self._api.eth.get_transaction(tx_hash)
                        print(f"Tx {tx_hash.hex()} is still pending. Increasing gas price by 25% and retrying with the same nonce {nonce}...")
                        gas_price = int(gas_price * 1.25)
                        
                        # Update fees based on transaction type
                        if 'maxFeePerGas' in tx:
                            tx['maxFeePerGas'] = int(tx['maxFeePerGas'] * 1.25)
                            tx['maxPriorityFeePerGas'] = int(tx['maxPriorityFeePerGas'] * 1.25)
                        else:
                            tx['gasPrice'] = gas_price
                            
                        attempt += 1
                        time.sleep(0.5)
                        continue
                    except Exception:
                        raise ExtrinsicExecutionError(
                            f"Transaction {tx_hash.hex()} not found after timeout. It might have been dropped."
                        )

            except Exception as e:
                error_message = str(e)

                # Retry on low gas price errors
                low_fee_errors = [
                    "replacement transaction underpriced",
                    "fee too low",
                    "intrinsic gas too low",
                    "nonce too low",
                    "already known",
                    "transaction underpriced",
                    "gas price less than block base fee"
                ]
                if any(sub in error_message for sub in low_fee_errors):
                    if "gas price less than block base fee" in error_message:
                        # For base fee errors, get fresh gas price and increase more aggressively
                        print(f"Attempt {attempt + 1}: Gas price below base fee. Getting fresh gas price and increasing by 50%...")
                        fresh_gas_price = self._api.eth.gas_price
                        gas_price = max(int(fresh_gas_price * 1.5), int(gas_price * 1.5))
                        
                        # Update EIP-1559 fees if transaction is using them
                        if 'maxFeePerGas' in tx:
                            try:
                                latest_block = self._api.eth.get_block('latest')
                                if 'baseFeePerGas' in latest_block:
                                    base_fee = latest_block['baseFeePerGas']
                                    max_priority_fee = int(gas_price * 0.1)
                                    max_fee = base_fee * 3 + max_priority_fee  # More aggressive: 3x base fee
                                    tx['maxFeePerGas'] = max_fee
                                    tx['maxPriorityFeePerGas'] = max_priority_fee
                            except Exception:
                                # Fallback to legacy transaction on error
                                if 'maxFeePerGas' in tx:
                                    del tx['maxFeePerGas']
                                if 'maxPriorityFeePerGas' in tx:
                                    del tx['maxPriorityFeePerGas']
                                if 'type' in tx:
                                    del tx['type']
                                tx['gasPrice'] = gas_price
                    else:
                        print(f"Attempt {attempt + 1}: Low fee. Increasing gas by 25% and retrying...")
                        gas_price = int(gas_price * 1.25)
                        
                        # Update fees based on transaction type
                        if 'maxFeePerGas' in tx:
                            tx['maxFeePerGas'] = int(tx['maxFeePerGas'] * 1.25)
                            tx['maxPriorityFeePerGas'] = int(tx['maxPriorityFeePerGas'] * 1.25)
                        else:
                            tx['gasPrice'] = gas_price
                    
                    attempt += 1
                    time.sleep(0.5)
                elif "connection error" in error_message.lower() or "connection closed" in error_message.lower():
                    print("Connection lost. Reinitializing Web3 provider and retrying...")
                    self._api = Web3(Web3.HTTPProvider(self._metadata.base_url))
                    attempt += 1
                    time.sleep(0.5)
                else:
                    raise ExtrinsicExecutionError(f"EVM transaction failed: {error_message}")
                
        raise ExtrinsicExecutionError("Failed to submit EVM transaction after multiple attempts.")
    
    def _send_evm_transaction(self, call, config: TransactionConfig) -> TxReceipt:
        """
        Enhanced EVM transaction sending (placeholder for future implementation)
        """
        # For now, convert to legacy format and use existing method
        # This can be enhanced later with proper EVM BUILD-SUBMIT-CONFIRM-FORMAT flow
        try:
            receipt = self._send_evm_tx(call, config.max_retries)
            return TxReceipt(
                tx_hash=receipt['transactionHash'].hex(),
                block_hash=receipt['blockHash'].hex(),
                block_number=receipt['blockNumber'],
                success=receipt['status'] == 1,
                finalized=True,  # EVM transactions are considered finalized once included
                fee=str(receipt.get('gasUsed', 0))
            )
        except Exception as e:
            return TxReceipt(
                tx_hash="",
                success=False,
                error=str(e)
            )

    # Keep old method signatures for backwards compatibility
    def _send_with_tip(self, call: GenericCall, tip_multiplier: float = 0.0, wait_for_finalization: bool = True) -> dict:
        """Legacy method - use _send_substrate_tx instead"""
        return self._send_substrate_tx(call, tip_multiplier, wait_for_finalization)
    
    def _format_receipt(self, receipt, call: GenericCall) -> dict:
        """Legacy method for backwards compatibility"""
        return self._legacy_format_receipt(
            self._format_substrate_receipt(receipt, call),
            call
        )
        
        
