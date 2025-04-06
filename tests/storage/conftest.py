# tests/storage/conftest.py
import pytest
from src.modules.main import Main
from src.types.common import ChainType

@pytest.fixture(params=["python-sdk-storage-010"])
def item_type(request):
    return request.param

@pytest.fixture(params=["test", {"test": {"hi": 123}}])
def item(request):
    return request.param

@pytest.fixture(autouse=True)
def storage_sdk(evm_sdk, substrate_sdk, chain):
    """
    Choose which SDK instance to use for storage tests.
    You can override or parametrize here if you need separate EVM vs Substrate runs.
    """
    # e.g. default to substrate for storage
    return substrate_sdk