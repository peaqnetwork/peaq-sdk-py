import pytest
from src.modules.main import Main
from src.types.common import ChainType

def test_create_instance():
    # Create an instance using the enum value.
    sdk = Main.create_instance(chain_type=ChainType.EVM, base_url='123',seed='123')
    print(sdk)
    # Verify that the instance and its components were created.
    assert sdk is not None
    assert sdk.did is not None
    # assert sdk.rbac is not None
    # assert sdk.storage is not None
    # Additional tests can check the metadata and API connection, etc.

if __name__ == "__main__":
    pytest.main()
