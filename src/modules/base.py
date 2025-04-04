# have substrate txs, evm initialization, etc
from src.types.common import ExtrinsicExecutionError

from substrateinterface.keypair import Keypair, KeypairType

class Base:
    def __init__(self) -> None:
        pass
    
    def _get_key_pair(self, seed: str):
        if not seed:
            ValueError('Seed is required')
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