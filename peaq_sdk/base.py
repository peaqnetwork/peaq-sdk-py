from typing import Optional, Union
import ast
import json
import time
import signal

from peaq_sdk.types.common import ChainType, ExtrinsicExecutionError, EvmTransaction, SeedError, SDKMetadata

from web3 import Web3
from eth_account import Account
from substrateinterface.base import SubstrateInterface, GenericCall
from substrateinterface.keypair import Keypair, KeypairType
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException

class Base:
    """
    Provides shared functionality for both EVM and Substrate SDK operations,
    including signer generation and transaction submission logic.
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
    
    def _send_substrate_tx(self, call: GenericCall) -> dict:
        """
        Submits and waits for inclusion of a Substrate extrinsic, automatically
        retrying with increasing tip if needed.

        Args:
            call (GenericCall): A `substrateinterface` call object created via `compose_call`.
            keypair (Keypair): Used to sign the extrinsic.

        Returns:
            dict: Full substrate receipt object.

        Raises:
            ExtrinsicExecutionError: If the extrinsic fails or is rejected by the chain.
        """
        receipt = self._send_with_tip(call)

        if receipt.error_message is not None:
            error_type = receipt.error_message['type']
            error_name = receipt.error_message['name']
            raise ExtrinsicExecutionError(f"The extrinsic of {call.call_module['name']} threw a {error_type} Error with name {error_name}.")

        return receipt.__dict__
    
    def _send_with_tip(self, call: GenericCall) -> dict:
        """
        Attempts to submit a Substrate extrinsic, retrying up to 5 times
        with an increasing tip if the node rejects due to low priority.
        If the api disconnects, tries to establish a new connection.

        Args:
            call (GenericCall): A `substrateinterface` call object.
            keypair (Keypair): The `Keypair` for signing.

        Returns:
            The extrinsic receipt object upon successful inclusion.

        Raises:
            ExtrinsicExecutionError: If all retry attempts fail due to low priority.
            Exception: For other submission errors.
        """
        tip_value = 0
        max_attempts = 8  # Increased from 5 to handle pool congestion better
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Check connection before attempt
                self._api.rpc_request(method="system_health", params=[])

                # Get payment info once
                if attempt == 0:
                    payment_info = self._api.get_payment_info(call, keypair=self._metadata.pair)
                    tip_increment = payment_info['partialFee']

                # Build + submit transaction
                extrinsic = self._api.create_signed_extrinsic(call=call, keypair=self._metadata.pair, tip=tip_value)
                
                # Submit with timeout to prevent hanging

                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Transaction submission timed out after 60 seconds")
                
                # Set timeout for slow networks
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)  # 60 second timeout
                
                try:
                    receipt = self._api.submit_extrinsic(extrinsic, wait_for_inclusion=True)
                    signal.alarm(0)  # Cancel timeout
                except TimeoutError:
                    signal.alarm(0)  # Cancel timeout
                    print(f"Attempt {attempt + 1}: Transaction timed out after 60 seconds, retrying...")
                    attempt += 1
                    time.sleep(1.0)
                    continue
                
                # check receipt
                if receipt.error_message is not None:
                    error_type = receipt.error_message['type']
                    error_name = receipt.error_message['name']
                    raise ExtrinsicExecutionError(f"The extrinsic of {call.call_module['name']} threw a {error_type} Error with name {error_name}.")
                return receipt

            except WebSocketConnectionClosedException:
                print("WebSocket was closed during submission. Reconnecting and retrying...")
                self._api = SubstrateInterface(url=self._metadata.base_url, ss58_format=42)
                attempt += 1
                time.sleep(0.5)
                
            except SubstrateRequestException as e:
                error_message = str(e)
                print(error_message)
                # Parse JSON error if it's a JSON string
                try:
                    error_data = ast.literal_eval(error_message) if isinstance(error_message, str) and error_message.startswith('{') else {'message': error_message}
                except (ValueError, SyntaxError):
                    error_data = {'message': error_message}
                
                # Extract the actual error message
                actual_error = error_data.get('message', error_message)
                
                if "Priority is too low" in actual_error:
                    print(f"Attempt {attempt + 1}: Priority too low with tip {tip_value}, incrementing tip by 25%...")
                    tip_value += int(tip_increment * 1.25)
                    attempt += 1
                    time.sleep(0.5)
                elif "Immediately Dropped" in actual_error or error_data.get('code') == 1016:
                    print(f"Attempt {attempt + 1}: Transaction dropped from pool (tip={tip_value}), increasing tip more aggressively...")
                    # Increase tip more aggressively for pool rejection
                    tip_value += int(tip_increment * 2.0)  # 100% increase instead of 25%
                    attempt += 1
                    time.sleep(1.0)  # Longer wait to let pool clear
                elif "limit" in actual_error.lower() or "pool" in actual_error.lower():
                    print(f"Attempt {attempt + 1}: Pool limit reached (tip={tip_value}), waiting and retrying with higher tip...")
                    tip_value += int(tip_increment * 1.5)  # 50% increase
                    attempt += 1
                    time.sleep(2.0)  # Wait longer for pool to clear
                else:
                    raise Exception(error_message)
        else:
            raise ExtrinsicExecutionError("Failed to submit extrinsic after multiple attempts due to low priority.")
    
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
        
        
