# have substrate txs, evm initialization, etc

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