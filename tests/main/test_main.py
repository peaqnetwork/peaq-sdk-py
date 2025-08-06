import pytest
from peaq_sdk_py_old.main import Main
from peaq_sdk_py_old.types.common import ChainType, BaseUrlError
from substrateinterface.base import SubstrateInterface
from web3 import Web3


def test_create_instance_returns_main(substrate_sdk):
    # substrate_sdk is returned by your fixture; it's an instance of Main
    assert isinstance(substrate_sdk, Main)

def test_create_instance_sets_correct_api(substrate_sdk, chain):
    if chain == "agung" or chain == "peaq":
        assert isinstance(substrate_sdk._api, SubstrateInterface)

@pytest.mark.parametrize("chain_type", [ChainType.EVM, ChainType.SUBSTRATE])
def test_create_instance_with_valid_seed(config, chain_type):
    if chain_type == ChainType.EVM:
        sdk = Main.create_instance(
            base_url=config["RPC_PEAQ_PUBLIC_BASE_URL"],
            chain_type=ChainType.EVM,
            seed=config["EVM_PRIVATE"]
        )
        assert isinstance(sdk._api, Web3)
        assert sdk._metadata.pair is not None

    if chain_type == ChainType.SUBSTRATE:
        sdk = Main.create_instance(
            base_url=config["WSS_PEAQ_PUBLIC_BASE_URL"],
            chain_type=ChainType.SUBSTRATE,
            seed=config["SUBSTRATE_SEED"]
        )
        assert isinstance(sdk._api, SubstrateInterface)
        assert sdk._metadata.pair is not None
        
def test_create_instance_invalid_base_url_raises_error():
    with pytest.raises(BaseUrlError):
        Main.create_instance(
            base_url="ftp://invalid-url.com",  # Invalid prefix
            chain_type=ChainType.EVM,
            seed="0x" + "1" * 64
        )