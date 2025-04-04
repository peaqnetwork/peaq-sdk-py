import pytest
import os
from dotenv import load_dotenv

from src.modules.main import Main
from src.types.common import ChainType

# loads .env from the current working directory and set to vars
load_dotenv()
base_url = os.getenv("WSS_AGUNG")
seed = os.getenv("SUBSTRATE_SEED")

# initialize sdk of substrate txs
sdk_substrate = Main.create_instance(chain_type=ChainType.SUBSTRATE, base_url=base_url,seed=seed)


# def test_add_storage():
#     result = sdk_substrate.storage.add_item(item_type="substrate polkadot-peaq 3", item={"test": "1234"})
#     print(result)

def test_get_storage():
    result = sdk_substrate.storage.get_item(item_type="substrate polkadot-peaq 3")
    print(result)
    assert result is not None
    assert result['substrate polkadot-peaq 3'] == '{"test": "1234"}'
     

if __name__ == "__main__":
    pytest.main()
