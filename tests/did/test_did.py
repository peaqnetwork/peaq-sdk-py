import re
import pytest
from peaq_sdk.types.did import CustomDocumentFields, Verification, Signature, Service, GetDidError
from peaq_sdk.types.storage import GetItemError
from peaq_sdk.main import Main

# @pytest.mark.skip(reason="Testing EVM")
def test_substrate_did(substrate_sdk, name, custom_document_fields, connection_type, config):
    # create a DID
    create_result = substrate_sdk.did.create(name=name, custom_document_fields=custom_document_fields)
    assert create_result.message.startswith("Successfully added the DID under the name")
    assert hasattr(create_result.receipt, "extrinsic_hash")
    assert hasattr(create_result.receipt, "block_hash")
    assert isinstance(create_result.receipt.fee, int)

    # read DID
    read_result = substrate_sdk.did.read(name=name)
    assert read_result.name == name
    assert "did:peaq:" in read_result.document.id
    assert read_result.document.verification_methods[0].type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_result.document.signature.type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_result.document.services[0].id == "#ipfs"
    assert read_result.document.services[0].type == "peaqStorage"
    assert read_result.document.services[0].data == "123456789"
    
    # Update DID
    updated_cid = "987654321"
    updated_fields = CustomDocumentFields(
        verifications=[
            Verification(type='EcdsaSecp256k1RecoveryMethod2020')
        ],
        signature=Signature(
            type='EcdsaSecp256k1RecoveryMethod2020',
            issuer='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641C',
            hash='123'
        ),
        services=[
            Service(id='#ipfs', type='peaqStorage', data=updated_cid)
        ]
    )
    update_result = substrate_sdk.did.update(name=name, custom_document_fields=updated_fields)
    assert update_result.message.startswith("Successfully updated the DID under the name")
    assert hasattr(update_result.receipt, "extrinsic_hash")
    
    # read DID
    read_after_update = substrate_sdk.did.read(name=name)
    assert read_after_update.name == name
    assert "did:peaq:" in read_result.document.id
    assert read_after_update.document.verification_methods[0].type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_after_update.document.signature.type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_after_update.document.services[0].id == "#ipfs"
    assert read_after_update.document.services[0].type == "peaqStorage"
    assert read_after_update.document.services[0].data == updated_cid
    
    # remove did
    remove_result = substrate_sdk.did.remove(name=name)
    assert remove_result.message.startswith("Successfully removed the DID under the name")
    
    # confirm deletion
    with pytest.raises(GetDidError, match=f"DID of name {name} was not found at address {config['SUBSTRATE_ADDRESS']}."):
        substrate_sdk.did.read(name=name)

# @pytest.mark.skip(reason="Testing Substrate")
def test_evm_did(evm_sdk, name, custom_document_fields, connection_type, config):
    sdk, base_wss = evm_sdk
    
    # create did
    create_result = sdk.did.create(name=name, custom_document_fields=custom_document_fields)
    assert create_result.message.startswith("Successfully added the DID under the name")
    assert hasattr(create_result.receipt, "transactionHash")
    assert create_result.receipt.status == 1

    # read did
    read_result = sdk.did.read(name=name, wss_base_url=base_wss)
    assert read_result.name == name
    assert "did:peaq:" in read_result.document.id
    assert read_result.document.verification_methods[0].type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_result.document.signature.type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_result.document.services[0].id == "#ipfs"
    assert read_result.document.services[0].type == "peaqStorage"
    assert read_result.document.services[0].data == "123456789"
    
    # update did
    updated_cid = "987654321"
    updated_fields = CustomDocumentFields(
        verifications=[Verification(type='EcdsaSecp256k1RecoveryMethod2020')],
        signature=Signature(
            type='EcdsaSecp256k1RecoveryMethod2020',
            issuer='0x9Eeab1aCcb1A701aEfAB00F3b8a275a39646641C',
            hash='123'
        ),
        services=[Service(id='#ipfs', type='peaqStorage', data=updated_cid)]
    )
    update_result = sdk.did.update(name=name, custom_document_fields=updated_fields)
    assert update_result.message.startswith("Successfully updated the DID under the name")
    assert hasattr(update_result.receipt, "transactionHash")
    assert update_result.receipt.status == 1
    
    # read did
    read_after_update = sdk.did.read(name=name, wss_base_url=base_wss)
    assert read_after_update.name == name
    assert "did:peaq:" in read_result.document.id
    assert read_after_update.document.verification_methods[0].type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_after_update.document.signature.type == "EcdsaSecp256k1RecoveryMethod2020"
    assert read_after_update.document.services[0].id == "#ipfs"
    assert read_after_update.document.services[0].type == "peaqStorage"
    assert read_after_update.document.services[0].data == updated_cid
    
    # remove did
    remove_result = sdk.did.remove(name=name)
    assert remove_result.message.startswith("Successfully removed the DID under the name")
    assert hasattr(remove_result.receipt, "transactionHash")
    assert remove_result.receipt.status == 1
    
    # confirm deletion
    with pytest.raises(GetDidError, match=f"DID of name {name} was not found at address {config['EVM_ADDRESS']}."):
        sdk.did.read(name=name, wss_base_url=base_wss)