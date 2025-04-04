# have substrate txs, evm initialization, etc
from src.types.common import ExtrinsicExecutionError
from src.types.common import ChainType

from web3 import Web3
from substrateinterface.keypair import Keypair, KeypairType
from eth_account import Account

class Base:
    def __init__(self) -> None:
        pass
    
    def _get_key_pair(self, chain_type: ChainType, seed: str):
        if not seed:
            ValueError('Seed is required')
        if chain_type is ChainType.EVM:
            return Account.from_key(seed)
        else:
            return Keypair.create_from_mnemonic(
                seed,
                ss58_format=42,
                crypto_type=KeypairType.SR25519
            )
    
    def send_substrate_tx(self, call, keypair):
        extrinsic = self._api.create_signed_extrinsic(call=call, keypair=keypair)
        receipt = self._api.submit_extrinsic(extrinsic, wait_for_inclusion=True)

        # Analyze the receipt
        if receipt.error_message is not None:
            error_type = receipt.error_message['type']
            error_name = receipt.error_message['name']
            raise ExtrinsicExecutionError(f"The extrinsic of {call.call_module['name']} threw a {error_type} Error with name {error_name}.")
        
        return receipt
    
    
    def send_evm_tx(self, tx, account):
        checksum_address = Web3.to_checksum_address(account.address)
        
        # build tx
        tx['from'] = checksum_address
        estimated_gas = self._api.eth.estimate_gas(tx)        
        tx['gas'] = estimated_gas
        tx['gasPrice'] = self._api.eth.gas_price  # or use w3.eth.gas_price
        tx['nonce'] = self._api.eth.get_transaction_count(checksum_address)
        tx['chainId'] = self._api.eth.chain_id

        # sign tx on behalf of the user
        signed_tx = account.sign_transaction(tx)
        tx_receipt = self._api.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = self._api.to_hex(tx_receipt)
        receipt = self._api.eth.wait_for_transaction_receipt(tx_hash)
        
        # TODO debug when error
        
        return receipt