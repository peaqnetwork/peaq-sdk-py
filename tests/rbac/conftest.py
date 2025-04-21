import pytest

@pytest.fixture(params=["my-role"])
def role_name(request):
    return request.param

@pytest.fixture(params=["9120e637-991c-4ea0-b47e-84a8154f"])
def role_id(request):
    return request.param

@pytest.fixture(autouse=True)
def substrate_sdk(evm_sdk, substrate_sdk, chain):
    """
    Choose which SDK instance to use for storage tests.
    You can override or parametrize here if you need separate EVM vs Substrate runs.
    """
    # e.g. default to substrate for storage
    return substrate_sdk

@pytest.fixture(autouse=True)
def evm_sdk(evm_sdk, substrate_sdk, chain):
    """
    Choose which SDK instance to use for storage tests.
    You can override or parametrize here if you need separate EVM vs Substrate runs.
    """
    # e.g. default to substrate for storage
    evm_sdk, base_wss = evm_sdk
    return evm_sdk, base_wss