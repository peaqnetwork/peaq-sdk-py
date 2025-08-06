import pytest
from peaq_sdk_py_old.main import Main
from peaq_sdk_py_old.types.common import ChainType
from peaq_sdk_py_old.types.did import CustomDocumentFields, Verification, Signature, Service


@pytest.fixture(params=["auto-did-test-015"])
def name(request):
    return request.param

@pytest.fixture(params=
    [CustomDocumentFields(
        verifications=[
            Verification(type='EcdsaSecp256k1RecoveryMethod2020')
            ],
        signature=Signature(type='EcdsaSecp256k1RecoveryMethod2020', issuer='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641C', hash='123'),
        services=[
            Service(id='#ipfs', type='peaqStorage', data='123456789')
            ]
)])
def custom_document_fields(request):
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