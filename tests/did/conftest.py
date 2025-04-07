import pytest
from peaq_sdk.main import Main
from peaq_sdk.types.common import ChainType

@pytest.fixture(autouse=True)
def storage_sdk(evm_sdk, substrate_sdk, chain):
    """
    Choose which SDK instance to use for storage tests.
    You can override or parametrize here if you need separate EVM vs Substrate runs.
    """
    # e.g. default to substrate for storage
    return substrate_sdk