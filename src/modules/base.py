# have substrate txs, evm initialization, etc
from src.types.common import ExtrinsicExecutionError, TransactionResult, ChainType

from web3 import Web3
from substrateinterface.keypair import Keypair, KeypairType
from substrateinterface.exceptions import SubstrateRequestException
from eth_account import Account

from typing import Optional
import json
import ast
class Base:
    def __init__(self) -> None:
        pass
    
    def _get_key_pair(self, chain_type: ChainType, seed: str) -> Account | Keypair:
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
    
    def send_substrate_tx(self, call, keypair) -> TransactionResult:
        # send with tip to handle priority issues
        receipt = self._send_with_tip(call, keypair)

        # Analyze the receipt
        if receipt.error_message is not None:
            error_type = receipt.error_message['type']
            error_name = receipt.error_message['name']
            raise ExtrinsicExecutionError(f"The extrinsic of {call.call_module['name']} threw a {error_type} Error with name {error_name}.")

        return TransactionResult(
            block_hash=receipt.block_hash,
            extrinsic_hash=receipt.extrinsic_hash,
            fee=receipt._ExtrinsicReceipt__total_fee_amount
        )
    
    
    def send_evm_tx(self, tx, account):
        try:
            checksum_address = Web3.to_checksum_address(account.address)
            
            # build tx
            tx['from'] = checksum_address
            estimated_gas = self._api.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
            tx['gasPrice'] = self._api.eth.gas_price
            tx['nonce'] = self._api.eth.get_transaction_count(checksum_address)
            tx['chainId'] = self._api.eth.chain_id

            # sign tx on behalf of the user
            signed_tx = account.sign_transaction(tx)
            tx_receipt = self._api.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = self._api.to_hex(tx_receipt)
            receipt = self._api.eth.wait_for_transaction_receipt(tx_hash)
            
            return receipt
        except Exception as error:
            error_dict = ast.literal_eval(error.message)
            raise ExtrinsicExecutionError(f"{error_dict['message']}")
        
    def _send_with_tip(self, call, keypair):
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