import pytest
import os
from dotenv import load_dotenv

from src.modules.main import Main
from src.types.common import ChainType

# loads .env from the current working directory and set to vars
load_dotenv()
base_url = os.getenv("WSS_AGUNG")
seed = os.getenv("SUBSTRATE_SEED")

def test_create_instance():
    # Create an instance using the enum value.
    sdk = Main.create_instance(chain_type=ChainType.SUBSTRATE, base_url=base_url,seed=seed)
    
    # Verify that the instance and its components were created.
    assert sdk is not None
    assert sdk.did is not None
    # assert sdk.rbac is not None
    assert sdk.storage is not None
    # Additional tests can check the metadata and API connection, etc.


if __name__ == "__main__":
    pytest.main()
