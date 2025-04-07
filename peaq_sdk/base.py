from typing import Optional, Union
import ast
import json

from peaq_sdk.types.common import ChainType, ExtrinsicExecutionError, TransactionResult, EvmTransaction, SeedError

from web3 import Web3
from eth_account import Account
from substrateinterface.base import GenericCall
from substrateinterface.keypair import Keypair, KeypairType
from substrateinterface.exceptions import SubstrateRequestException

class Base:
    """
    Provides shared functionality for both EVM and Substrate SDK operations,
    including signer generation and transaction submission logic.
    """
    def __init__(self) -> None:
        """Base initializer (no-op)."""
        pass
    
    def _create_key_pair(self, chain_type: ChainType, seed: str) -> Union[Account, Keypair]:
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
        if chain_type is ChainType.EVM:
            return Account.from_key(seed)
        else:
            return Keypair.create_from_mnemonic(
                seed,
                ss58_format=42,
                crypto_type=KeypairType.SR25519
            )
            
    def _resolve_address(self, chain_type: ChainType, pair: Union[Keypair, Account], address: Optional[str] = None) -> str:
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
            if chain_type is ChainType.EVM:
                if pair:
                    # We have a local EVM account
                    account = pair
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
                if pair:
                    # We have a local Substrate keypair
                    keypair = pair
                    return keypair.ss58_address
                else:
                    # No local keypair: must rely on 'address' parameter
                    if not address:
                        raise SeedError(
                            "No seed/private key set, and no address was provided. "
                            "Unable to sign or construct the transaction properly."
                        )
                    return address
    
    def _send_substrate_tx(self, call: GenericCall, keypair: Keypair) -> TransactionResult:
        """
        Submits and waits for inclusion of a Substrate extrinsic, automatically
        retrying with increasing tip if needed.

        Args:
            call (GenericCall): A `substrateinterface` call object created via `compose_call`.
            keypair (Keypair): Used to sign the extrinsic.

        Returns:
            TransactionResult: Contains `block_hash`, `extrinsic_hash`, and fee paid.

        Raises:
            ExtrinsicExecutionError: If the extrinsic fails or is rejected by the chain.
        """
        receipt = self._send_with_tip(call, keypair)

        if receipt.error_message is not None:
            error_type = receipt.error_message['type']
            error_name = receipt.error_message['name']
            raise ExtrinsicExecutionError(f"The extrinsic of {call.call_module['name']} threw a {error_type} Error with name {error_name}.")

        return TransactionResult(
            block_hash=receipt.block_hash,
            extrinsic_hash=receipt.extrinsic_hash,
            fee=receipt._ExtrinsicReceipt__total_fee_amount
        )
    
    
    def _send_evm_tx(self, tx: EvmTransaction, account: Account) -> dict:
        """
        Builds, signs, and broadcasts an EVM transaction via the Web3 provider.

        It estimates gas, fetches gas price, nonce, and chain ID, then signs
        with the provided `Account` and waits for the receipt.

        Args:
            tx (dict): A transaction dict containing at minimum `to` and `data`.
            account (Account): An `eth_account.Account` with a private key.

        Returns:
            dict: The transaction receipt returned by Web3.

        Raises:
            ExtrinsicExecutionError: If Web3 returns an error string.
        """
        try:
            checksum_address = Web3.to_checksum_address(account.address)
            tx['from'] = checksum_address
            estimated_gas = self._api.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
            tx['gasPrice'] = self._api.eth.gas_price
            tx['nonce'] = self._api.eth.get_transaction_count(checksum_address)
            tx['chainId'] = self._api.eth.chain_id

            signed_tx = account.sign_transaction(tx)
            tx_receipt = self._api.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = self._api.to_hex(tx_receipt)
            receipt = self._api.eth.wait_for_transaction_receipt(tx_hash)
            return receipt
        
        except Exception as error:
            try:
                err_dict = ast.literal_eval(error.message)
                message = err_dict.get("message", str(error))
            except Exception:
                message = str(error)
            raise ExtrinsicExecutionError(message)
        
    def _send_with_tip(self, call: GenericCall, keypair: Keypair) -> dict:
        """
        Attempts to submit a Substrate extrinsic, retrying up to 5 times
        with an increasing tip if the node rejects due to low priority.

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
        max_attempts = 5
        attempt = 0
        
        # Get payment info to see the current fee estimation for increment
        payment_info = self._api.get_payment_info(call, keypair=keypair)
        tip_increment = payment_info['partialFee']
        while attempt < max_attempts:
            try:
                extrinsic = self._api.create_signed_extrinsic(call=call, keypair=keypair, tip=tip_value)
                receipt = self._api.submit_extrinsic(extrinsic, wait_for_inclusion=True)
                break  # success: exit the loop
            except SubstrateRequestException as e:
                error_message = str(e)
                if "Priority is too low" in error_message:
                    print(f"Attempt {attempt + 1}: Priority too low with tip {tip_value}, incrementing tip based on expected...")
                    tip_value += tip_increment
                    attempt += 1
                else:
                    raise Exception(error_message)
        else:
            raise ExtrinsicExecutionError("Failed to submit extrinsic after multiple attempts due to low priority.")
        return receipt