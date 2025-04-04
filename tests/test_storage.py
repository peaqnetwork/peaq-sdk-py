import pytest
import os
from dotenv import load_dotenv

from src.modules.main import Main
from src.types.common import ChainType

# loads .env from the current working directory and set to vars
load_dotenv()
wss_base_url = os.getenv("WSS_AGUNG")
rpc_base_url = os.getenv("PRIVATE_RPC_AGUNG")
SUBSTRATE_SEED = os.getenv("SUBSTRATE_SEED")

EVM_ADDRESS= os.getenv("EVM_PRIVATE")
EVM_PRIVATE = os.getenv("EVM_PRIVATE")


# initialize sdk of substrate txs
sdk_substrate = Main.create_instance(chain_type=ChainType.SUBSTRATE, base_url=wss_base_url,seed=SUBSTRATE_SEED)
sdk_evm= Main.create_instance(chain_type=ChainType.EVM, base_url=rpc_base_url, seed=EVM_PRIVATE)


# def test_add_storage():
#     result = sdk_evm.storage.add_item(item_type="substrate polkadot-peaq 4", item="test")
#     print(result)

def test_get_storage():
    result = sdk_evm.storage.get_item(item_type="substrate polkadot-peaq 4", wss_base_url=wss_base_url)
    print(result)
    assert result is not None
    assert result['substrate polkadot-peaq 4'] == "test"
     

if __name__ == "__main__":
    pytest.main()
