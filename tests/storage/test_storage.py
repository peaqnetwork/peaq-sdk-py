import pytest
import re
import json

from peaq_sdk.types.storage import GetItemError

# @pytest.mark.skip(reason="Testing EVM")
def test_substrate_storage(substrate_sdk, item_type, item, config):
    # Create a storage item.
    result = substrate_sdk.storage.add_item(item_type=item_type, item=item)
    assert result is not None
    pattern = r'^0x[0-9a-fA-F]{64}$'
    expected_message = (
        f"Successfully added the storage item type {item_type} with item {item} "
        f"for the address {config['SUBSTRATE_ADDRESS']}."
    )
    assert result.message == expected_message
    is_success = result.receipt['_ExtrinsicReceipt__is_success']
    assert is_success, "Transaction did not succeed."
    assert 'extrinsic_hash' in result.receipt
    assert 'block_hash' in result.receipt
    
    # Read back the stored item.
    result = substrate_sdk.storage.get_item(item_type=item_type)
    if isinstance(item, dict):
        assert json.loads(result[item_type]) == item
    else:
        assert result[item_type] == item
    
    # Update the item.
    new_item = 'test123'
    result = substrate_sdk.storage.update_item(item_type=item_type, item=new_item)
    assert result is not None
    expected_update_msg = (
        f"Successfully updated the storage item type {item_type} with item {new_item} "
        f"for the address {config['SUBSTRATE_ADDRESS']}."
    )
    assert result.message == expected_update_msg
    is_success = result.receipt['_ExtrinsicReceipt__is_success']
    assert is_success, "Transaction did not succeed."
    assert 'extrinsic_hash' in result.receipt
    assert 'block_hash' in result.receipt
    
    # Verify the updated item.
    result = substrate_sdk.storage.get_item(item_type=item_type)
    if isinstance(new_item, dict):
        assert json.loads(result[item_type]) == new_item
    else:
        assert result[item_type] == new_item
    
    # Remove the item.
    result = substrate_sdk.storage.remove_item(item_type=item_type)
    assert result is not None
    expected_remove_msg = (
        f"Successfully removed the storage item type {item_type} for the address {config['SUBSTRATE_ADDRESS']}."
    )
    assert result.message == expected_remove_msg
    is_success = result.receipt['_ExtrinsicReceipt__is_success']
    assert is_success, "Transaction did not succeed."
    assert 'extrinsic_hash' in result.receipt
    assert 'block_hash' in result.receipt

    # Attempt to read the removed item and expect failure.
    with pytest.raises(GetItemError) as exc_info:
        substrate_sdk.storage.get_item(item_type=item_type)
    expected_error = (
        f"Item type of {item_type} was not found at address {config['SUBSTRATE_ADDRESS']}."
    )
    assert str(exc_info.value) == expected_error

@pytest.mark.skip(reason="Skipping until remove precompile is added")
def test_evm_storage(evm_sdk, item_type, item, config):
    sdk, wss_url = evm_sdk
    
    # create
    result = sdk.storage.add_item(item_type=item_type, item=item)
    assert result is not None

    pattern = r'^[0-9a-fA-F]{64}$'
    expected_message = (
        f"Successfully added the storage item type {item_type} with item {item} "
        f"for the address {config['EVM_ADDRESS']}."
    )
    assert result.message == expected_message
    assert re.fullmatch(pattern, result.receipt.blockHash.hex())

    # read back—now pass wss_url
    result = sdk.storage.get_item(item_type=item_type,
                                  address=config['EVM_ADDRESS'],
                                  wss_base_url=wss_url)
    if isinstance(item, dict):
        assert json.loads(result[item_type]) == item
    else:
        assert result[item_type] == item
    
    # update
    new_item = 'test123'
    result = sdk.storage.update_item(item_type=item_type, item=new_item)
    assert result is not None
    expected_update_msg = (
        f"Successfully updated the storage item type {item_type} with item {new_item} "
        f"for the address {config['EVM_ADDRESS']}."
    )
    assert result.message == expected_update_msg
    assert re.fullmatch(pattern, result.receipt.blockHash.hex())
    
    # read updated
    result = sdk.storage.get_item(item_type=item_type,
                                  address=config['EVM_ADDRESS'],
                                  wss_base_url=wss_url)
    if isinstance(new_item, dict):
        assert json.loads(result[item_type]) == new_item
    else:
        assert result[item_type] == new_item

    # remove unsupported
    with pytest.raises(ValueError) as exc_info:
        sdk.storage.remove_item(item_type=item_type)
    assert str(exc_info.value) == (
        "Precompile for peaq Storage Remove Item will be included in the next runtime update."
    )
