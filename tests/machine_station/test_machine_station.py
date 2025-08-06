import secrets
import pytest
import re
from web3 import Web3

from peaq_sdk_py_old.types.did import CustomDocumentFields


# Tests for the Machine Station module
#
# This test suite verifies the functionality of the Machine Station smart contract interface.
# Tests are organized into two main categories:
# 1. Signature Generation Tests - Verify correct signature creation for various operations
# 2. Transaction Execution Tests - Verify successful execution of operations on-chain
#
# The test suite uses fixtures defined in conftest.py for common test setup.

# ============================================================================
# Signature Generation Tests
# These tests verify that signatures are correctly generated for various operations
# ============================================================================

def test_deploy_smart_account_signature(machine_station_sdk, machine_smart_account_owner_address):
    """Test signature generation for deploying a new smart account.
    Verifies that the signature has the correct format and length."""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.admin_sign_deploy_machine_smart_account(
        machine_smart_account_owner_address=machine_smart_account_owner_address,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132  # 0x + 130 hex chars

def test_transfer_machine_station_balance_signature(machine_station_sdk, machine_station_address_2):
    """Test signature generation for transferring balance between machine stations.
    Verifies that the signature has the correct format and length."""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.admin_sign_transfer_machine_station_balance(
        new_machine_station_address=machine_station_address_2,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_transaction_signature(machine_station_sdk, storage_precompile_address):
    """Test signature generation for executing a transaction through the machine station.
    Verifies that the signature has the correct format and length."""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    signature = machine_station_sdk.machine_station.admin_sign_transaction(
        target=storage_precompile_address,
        calldata=calldata.tx['data'],
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_machine_transaction_signature(machine_station_sdk, smart_account_address, storage_precompile_address):
    """Test signature generation for executing a transaction through a machine smart account.
    Verifies that both machine station owner and smart account owner signatures are correct."""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    signature = machine_station_sdk.machine_station.admin_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=calldata.tx['data'],
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_batch_transactions_signature(machine_station_sdk, smart_account_address, smart_account_address_2, storage_precompile_address):
    """Test signature generation for batch transactions from multiple smart accounts.
    Verifies that signatures are correctly generated for each transaction in the batch."""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    machine_nonces = [secrets.randbits(128), secrets.randbits(128)]
    smart_accounts = [smart_account_address, smart_account_address_2]
    targets = [storage_precompile_address, storage_precompile_address]
    calldata_list = [calldata.tx['data'], calldata.tx['data']]
    
    signature = machine_station_sdk.machine_station.admin_sign_machine_batch_transactions(
        smart_account_addresses=smart_accounts,
        targets=targets,
        calldata_list=calldata_list,
        nonce=nonce,
        machine_nonces=machine_nonces
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_transfer_machine_balance_signature(machine_station_sdk, smart_account_address, smart_account_address_2):
    """Test signature generation for transferring balance between smart accounts.
    Verifies that the signature has the correct format and length."""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.admin_sign_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=smart_account_address_2,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_machine_owner_sign_machine_transaction(machine_station_sdk, smart_account_address, storage_precompile_address):
    """Test signature generation by machine owner for executing transactions.
    Verifies that the machine owner can correctly sign transaction execution requests."""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=calldata.tx['data'],
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_machine_sign_transfer_machine_balance(machine_station_sdk, smart_account_address, smart_account_address_2):
    """Test signature generation by machine for balance transfers.
    Verifies that the machine can correctly sign balance transfer requests."""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.machine_sign_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=smart_account_address_2,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

# ============================================================================
# Transaction Execution Tests
# These tests verify the actual execution of operations on the blockchain
# ============================================================================

def test_deploy_smart_account(machine_station_sdk, machine_smart_account_owner_address):
    """Test deploying a new smart account and verify its on-chain deployment.
    
    Steps:
    1. Generate deployment signature
    2. Deploy smart account
    3. Verify deployment success and address format
    4. Verify deployment event in transaction logs
    5. Verify contract code exists on chain
    """
    nonce = secrets.randbits(128)
    
    # Get signature for deployment
    signature = machine_station_sdk.machine_station.admin_sign_deploy_machine_smart_account(
        machine_smart_account_owner_address=machine_smart_account_owner_address,
        nonce=nonce
    )
    
    # Deploy the smart account
    result = machine_station_sdk.machine_station.deploy_machine_smart_account(
        machine_smart_account_owner_address=machine_smart_account_owner_address,
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    
    # Test the result object structure
    assert result.deployed_address.startswith("0x")
    assert len(result.deployed_address) == 42
    assert result.message == f"Successfully deployed machine smart account at address {result.deployed_address}."
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    
    # Verify the transaction receipt contains the deployment event
    deployment_event_topic = machine_station_sdk.api.keccak(text="MachineSmartAccountDeployed(address)").hex()
    deployment_log = next(
        (log for log in result.receipt["logs"] 
         if log["topics"][0].hex() == deployment_event_topic),
        None
    )
    assert deployment_log is not None, "Deployment event not found in transaction logs"
    
    # Verify the deployed address matches the event log
    event_address = Web3.to_checksum_address(deployment_log["topics"][1].hex()[24:])
    assert event_address == result.deployed_address
    
    # Verify the contract exists on chain by checking its code
    deployed_code = machine_station_sdk.api.eth.get_code(result.deployed_address)
    assert len(deployed_code) > 0, "No contract code found at deployed address"

def test_transfer_machine_station_balance(machine_station_sdk, machine_station_address_2, machine_station_sdk_2):
    """Test transferring balance between machine stations.
    
    Steps:
    1. Transfer balance from first machine station to second
    2. Verify transfer success
    3. Transfer balance back to first machine station
    4. Verify return transfer success
    """
    nonce = secrets.randbits(128)
    
    # Get signature for transfer
    signature = machine_station_sdk.machine_station.admin_sign_transfer_machine_station_balance(
        new_machine_station_address=machine_station_address_2,
        nonce=nonce
    )
    
    # Execute the transfer
    result = machine_station_sdk.machine_station.transfer_machine_station_balance(
        new_machine_station_address=machine_station_address_2,
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    # Test the result object structure
    assert result is not None
    assert result.message == f"Successfully transferred balance from {machine_station_sdk.machine_station.machine_station_address} to {machine_station_address_2}."
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    
    # Transfer balance back to original machine station
    nonce = secrets.randbits(128)
    # Get signature for transfer
    signature = machine_station_sdk_2.machine_station.admin_sign_transfer_machine_station_balance(
        new_machine_station_address=machine_station_sdk.machine_station.machine_station_address,
        nonce=nonce
    )
    
    # Execute the transfer
    result = machine_station_sdk_2.machine_station.transfer_machine_station_balance(
        new_machine_station_address=machine_station_sdk.machine_station.machine_station_address,
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    # Test the result object structure
    assert result is not None
    assert result.message == f"Successfully transferred balance from {machine_station_sdk_2.machine_station.machine_station_address} to {machine_station_sdk.machine_station.machine_station_address}."
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    
# create and remove an item from storage
def test_transaction_storage(machine_station_sdk, storage_precompile_address, wss_url_agng):
    """Test executing storage operations through the machine station.
    
    Steps:
    1. Create and add a storage item
    2. Verify item was added successfully
    3. Remove the storage item
    4. Verify item was removed successfully
    """
    random_suffix = secrets.token_hex(8)
    test_item_type = f"test_item_{random_suffix}"
    test_item_value = "test_value"
    
    # Create the transaction to add an item
    storage_calldata = machine_station_sdk.storage.add_item(item_type=test_item_type, item=test_item_value)
    nonce = secrets.randbits(128)
    
    # Get signature for the transaction
    signature = machine_station_sdk.machine_station.admin_sign_transaction(
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction
    result = machine_station_sdk.machine_station.execute_transaction(
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    
    # Verify transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed transaction on target {storage_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the item was actually added to storage
    stored_items = machine_station_sdk.storage.get_item(item_type=test_item_type, address=machine_station_sdk.machine_station.machine_station_address, wss_base_url=wss_url_agng)
    assert isinstance(stored_items, dict), "Expected storage.get_item to return a dictionary"
    assert test_item_type in stored_items, f"Expected to find key '{test_item_type}' in storage response"
    assert stored_items[test_item_type] == test_item_value, f"Expected stored value to be '{test_item_value}' but got '{stored_items[test_item_type]}'"
    
    # Create the transaction to remove an item
    storage_calldata = machine_station_sdk.storage.remove_item(item_type=test_item_type)
    nonce = secrets.randbits(128)
    
    # Get signature for the transaction
    signature = machine_station_sdk.machine_station.admin_sign_transaction(
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction
    result = machine_station_sdk.machine_station.execute_transaction(
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    
    # Verify remove transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed transaction on target {storage_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the item was actually removed from storage
    from peaq_sdk_py_old.types.storage import GetItemError
    with pytest.raises(GetItemError) as exc_info:
        machine_station_sdk.storage.get_item(
            item_type=test_item_type, 
            address=machine_station_sdk.machine_station.machine_station_address, 
            wss_base_url=wss_url_agng
        )
    assert str(exc_info.value) == f"Item type of {test_item_type} was not found at address {machine_station_sdk.machine_station.machine_station_address}."

# create and remove a DID
def test_transaction_did(machine_station_sdk, did_precompile_address, wss_url_agng):
    """Test executing DID operations through the machine station.
    
    Steps:
    1. Create a new DID
    2. Verify DID creation success
    3. Remove the DID
    4. Verify DID removal success
    """
    random_suffix = secrets.token_hex(8)
    test_name = f"test_did_{random_suffix}"
    
    # Create the transaction to add a DID
    did_calldata = machine_station_sdk.did.create(
        name=test_name,
        address=machine_station_sdk.machine_station.machine_station_address,
        custom_document_fields=CustomDocumentFields()
    )
    nonce = secrets.randbits(128)
    
    # Get signature for the transaction
    signature = machine_station_sdk.machine_station.admin_sign_transaction(
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction
    result = machine_station_sdk.machine_station.execute_transaction(
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    
    # Verify transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed transaction on target {did_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the DID was actually created
    did = machine_station_sdk.did.read(
        name=test_name,
        address=machine_station_sdk.machine_station.machine_station_address,
        wss_base_url=wss_url_agng
    )
    assert did is not None, "Expected DID to exist"
    assert did.name == test_name, f"Expected DID name to be '{test_name}' but got '{did.name}'"
    
    # Create the transaction to remove the DID
    did_calldata = machine_station_sdk.did.remove(
        name=test_name,
        address=machine_station_sdk.machine_station.machine_station_address
    )
    nonce = secrets.randbits(128)
    
    # Get signature for the transaction
    signature = machine_station_sdk.machine_station.admin_sign_transaction(
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction
    result = machine_station_sdk.machine_station.execute_transaction(
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    
    # Verify remove transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed transaction on target {did_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the DID was actually removed
    from peaq_sdk_py_old.types.did import GetDidError
    with pytest.raises(GetDidError) as exc_info:
        machine_station_sdk.did.read(
            name=test_name,
            address=machine_station_sdk.machine_station.machine_station_address,
            wss_base_url=wss_url_agng
        )
    assert str(exc_info.value) == f"DID of name {test_name} was not found at address {machine_station_sdk.machine_station.machine_station_address}."


def test_machine_transaction_storage(machine_station_sdk, smart_account_address, storage_precompile_address, wss_url_agng):
    """Test executing storage operations through a machine smart account.
    
    Steps:
    1. Create and add a storage item through smart account
    2. Verify item was added successfully
    3. Remove the storage item through smart account
    4. Verify item was removed successfully
    """
    # Create unique test item to prevent collisions
    random_suffix = secrets.token_hex(8)
    test_item_type = f"test_item_{random_suffix}"
    test_item_value = "test_value"
    
    # Create the transaction to add an item
    storage_calldata = machine_station_sdk.storage.add_item(item_type=test_item_type, item=test_item_value)
    nonce = secrets.randbits(128)
    
    # Get signatures from both machine owner and machine station owner
    smart_account_signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce
    )
    
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction to add the item
    result = machine_station_sdk.machine_station.execute_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signature=smart_account_signature
    )
    
    # Verify add transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed machine transaction from {smart_account_address} on target {storage_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the item was actually added to storage
    stored_items = machine_station_sdk.storage.get_item(
        item_type=test_item_type, 
        address=smart_account_address,  # Use smart account address instead of machine station
        wss_base_url=wss_url_agng
    )
    assert isinstance(stored_items, dict), "Expected storage.get_item to return a dictionary"
    assert test_item_type in stored_items, f"Expected to find key '{test_item_type}' in storage response"
    assert stored_items[test_item_type] == test_item_value, f"Expected stored value to be '{test_item_value}' but got '{stored_items[test_item_type]}'"
    
    # Create the transaction to remove the item
    storage_calldata = machine_station_sdk.storage.remove_item(item_type=test_item_type)
    nonce = secrets.randbits(128)
    
    # Get signatures for removal
    smart_account_signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce
    )
    
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction to remove the item
    result = machine_station_sdk.machine_station.execute_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=storage_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signature=smart_account_signature
    )
    
    # Verify remove transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed machine transaction from {smart_account_address} on target {storage_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the item was actually removed from storage
    from peaq_sdk_py_old.types.storage import GetItemError
    with pytest.raises(GetItemError) as exc_info:
        machine_station_sdk.storage.get_item(
            item_type=test_item_type,
            address=smart_account_address,  # Use smart account address instead of machine station
            wss_base_url=wss_url_agng
        )
    assert str(exc_info.value) == f"Item type of {test_item_type} was not found at address {smart_account_address}."

def test_machine_transaction_did(machine_station_sdk, smart_account_address, did_precompile_address, wss_url_agng):
    """Test executing DID operations through a machine smart account.
    
    Steps:
    1. Create a new DID through smart account
    2. Verify DID creation success
    3. Remove the DID through smart account
    4. Verify DID removal success
    """
    # Create unique test name to prevent collisions
    random_suffix = secrets.token_hex(8)
    test_name = f"test_did_{random_suffix}"
    
    # Create the transaction to add a DID
    did_calldata = machine_station_sdk.did.create(
        name=test_name,
        address=smart_account_address,  # Use smart account address instead of machine station
        custom_document_fields=CustomDocumentFields()
    )
    nonce = secrets.randbits(128)
    
    # Get signatures from both machine owner and machine station owner
    smart_account_signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce
    )
    
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction to add the DID
    result = machine_station_sdk.machine_station.execute_machine_transaction(
        smart_account_address=smart_account_address,
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signature=smart_account_signature
    )
    
    # Verify add transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed machine transaction from {smart_account_address} on target {did_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the DID was actually created
    did = machine_station_sdk.did.read(
        name=test_name,
        address=smart_account_address,  # Use smart account address instead of machine station
        wss_base_url=wss_url_agng
    )
    assert did is not None, "Expected DID to exist"
    assert did.name == test_name, f"Expected DID name to be '{test_name}' but got '{did.name}'"
    
    # Create the transaction to remove the DID
    did_calldata = machine_station_sdk.did.remove(
        name=test_name,
        address=smart_account_address  # Use smart account address instead of machine station
    )
    nonce = secrets.randbits(128)
    
    # Get signatures for removal
    smart_account_signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce
    )
    
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_machine_transaction(
        smart_account_address=smart_account_address,
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce
    )
    
    # Execute the transaction to remove the DID
    result = machine_station_sdk.machine_station.execute_machine_transaction(
        smart_account_address=smart_account_address,
        target=did_precompile_address,
        calldata=did_calldata.tx['data'],
        nonce=nonce,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signature=smart_account_signature
    )
    
    # Verify remove transaction result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully executed machine transaction from {smart_account_address} on target {did_precompile_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the DID was actually removed
    from peaq_sdk_py_old.types.did import GetDidError
    with pytest.raises(GetDidError) as exc_info:
        machine_station_sdk.did.read(
            name=test_name,
            address=smart_account_address,  # Use smart account address instead of machine station
            wss_base_url=wss_url_agng
        )
    assert str(exc_info.value) == f"DID of name {test_name} was not found at address {smart_account_address}."

def test_execute_batch_transactions(machine_station_sdk, smart_account_address, smart_account_address_2, storage_precompile_address, did_precompile_address, wss_url_agng):
    """Test executing multiple transactions from multiple smart accounts in a single batch.
    
    Steps:
    1. Create storage item from first account and DID from second account
    2. Execute batch creation transaction
    3. Verify both operations succeeded
    4. Remove both items in another batch transaction
    5. Verify both removals succeeded
    """
    # Create unique test items to prevent collisions
    random_suffix = secrets.token_hex(8)
    test_item_type = f"test_item_{random_suffix}"
    test_item_value = "test_value"
    test_name = f"test_did_{random_suffix}"
    
    # Create storage and DID transactions
    storage_calldata = machine_station_sdk.storage.add_item(
        item_type=test_item_type,
        item=test_item_value
    )
    did_calldata = machine_station_sdk.did.create(
        name=test_name,
        address=smart_account_address,
        custom_document_fields=CustomDocumentFields()
    )
    
    # Setup batch parameters for creation
    smart_accounts = [smart_account_address_2, smart_account_address]  # Storage from first account, DID from second
    targets = [storage_precompile_address, did_precompile_address]
    calldata_list = [storage_calldata.tx['data'], did_calldata.tx['data']]
    
    smart_account_signatures = []
    machine_nonces = []
    
    # Get signatures for each account's transaction
    for i, account in enumerate(smart_accounts):
        machine_nonce = secrets.randbits(128)
        machine_nonces.append(machine_nonce)
        
        signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
            smart_account_address=account,
            target=targets[i],  # Use corresponding target for each account
            calldata=calldata_list[i],  # Use corresponding calldata for each account
            nonce=machine_nonce
        )
        smart_account_signatures.append(signature)
    
    # Get machine station owner signature for batch creation
    nonce = secrets.randbits(128)
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_machine_batch_transactions(
        smart_account_addresses=smart_accounts,
        targets=targets,
        calldata_list=calldata_list,
        nonce=nonce,
        machine_nonces=machine_nonces
    )
    
    # Execute batch creation transaction
    result = machine_station_sdk.machine_station.execute_machine_batch_transactions(
        smart_account_addresses=smart_accounts,
        targets=targets,
        calldata_list=calldata_list,
        nonce=nonce,
        machine_nonces=machine_nonces,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signatures=smart_account_signatures
    )
    
    # Verify batch creation result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    accounts_str = ", ".join(smart_accounts)
    targets_str = ", ".join(targets)
    assert result.message == f"Successfully executed batch transactions from accounts [{accounts_str}] on targets [{targets_str}] through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify the storage item was created
    stored_items = machine_station_sdk.storage.get_item(
        item_type=test_item_type,
        address=smart_account_address_2,
        wss_base_url=wss_url_agng
    )
    assert isinstance(stored_items, dict), "Expected storage.get_item to return a dictionary"
    assert test_item_type in stored_items, f"Expected to find key '{test_item_type}' in storage response"
    assert stored_items[test_item_type] == test_item_value, f"Expected stored value to be '{test_item_value}' but got '{stored_items[test_item_type]}'"
    
    # Verify the DID was created
    did = machine_station_sdk.did.read(
        name=test_name,
        address=smart_account_address,
        wss_base_url=wss_url_agng
    )
    assert did is not None, "Expected DID to exist"
    assert did.name == test_name, f"Expected DID name to be '{test_name}' but got '{did.name}'"
    
    # Create removal transactions
    storage_remove_calldata = machine_station_sdk.storage.remove_item(item_type=test_item_type)
    did_remove_calldata = machine_station_sdk.did.remove(
        name=test_name,
        address=smart_account_address
    )
    
    # Setup batch parameters for removal
    calldata_list = [storage_remove_calldata.tx['data'], did_remove_calldata.tx['data']]
    smart_account_signatures = []
    machine_nonces = []
    
    # Get signatures for each account's removal transaction
    for i, account in enumerate(smart_accounts):
        machine_nonce = secrets.randbits(128)
        machine_nonces.append(machine_nonce)
        
        signature = machine_station_sdk.machine_station.machine_sign_machine_transaction(
            smart_account_address=account,
            target=targets[i],
            calldata=calldata_list[i],
            nonce=machine_nonce
        )
        smart_account_signatures.append(signature)
    
    # Get machine station owner signature for batch removal
    nonce = secrets.randbits(128)
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_machine_batch_transactions(
        smart_account_addresses=smart_accounts,
        targets=targets,
        calldata_list=calldata_list,
        nonce=nonce,
        machine_nonces=machine_nonces
    )
    
    # Execute batch removal transaction
    result = machine_station_sdk.machine_station.execute_machine_batch_transactions(
        smart_account_addresses=smart_accounts,
        targets=targets,
        calldata_list=calldata_list,
        nonce=nonce,
        machine_nonces=machine_nonces,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signatures=smart_account_signatures
    )
    
    # Verify batch removal result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    accounts_str = ", ".join(smart_accounts)
    targets_str = ", ".join(targets)
    assert result.message == f"Successfully executed batch transactions from accounts [{accounts_str}] on targets [{targets_str}] through machine station {machine_station_sdk.machine_station.machine_station_address}."
    
    # Verify storage item was removed
    from peaq_sdk_py_old.types.storage import GetItemError
    with pytest.raises(GetItemError) as exc_info:
        machine_station_sdk.storage.get_item(
            item_type=test_item_type,
            address=smart_account_address_2,
            wss_base_url=wss_url_agng
        )
    assert str(exc_info.value) == f"Item type of {test_item_type} was not found at address {smart_account_address_2}."
    
    # Verify DID was removed
    from peaq_sdk_py_old.types.did import GetDidError
    with pytest.raises(GetDidError) as exc_info:
        machine_station_sdk.did.read(
            name=test_name,
            address=smart_account_address,
            wss_base_url=wss_url_agng
        )
    assert str(exc_info.value) == f"DID of name {test_name} was not found at address {smart_account_address}."

def test_transfer_machine_balance(machine_station_sdk, smart_account_address, smart_account_address_2):
    """Test transferring balance between smart accounts.
    
    Steps:
    1. Transfer balance from first smart account to second
    2. Verify transfer success
    3. Transfer balance back to first smart account
    4. Verify return transfer success
    """
    # First transfer: from deployed_smart_account to smart_account_address_2
    nonce = secrets.randbits(128)
    smart_account_signature = machine_station_sdk.machine_station.machine_sign_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=smart_account_address_2,
        nonce=nonce
    )
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=smart_account_address_2,
        nonce=nonce
    )
    result = machine_station_sdk.machine_station.execute_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=smart_account_address_2,
        nonce=nonce,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signature=smart_account_signature
    )
    
    # Verify first transfer result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully transferred balance from {smart_account_address} to {smart_account_address_2} through machine station {machine_station_sdk.machine_station.machine_station_address}."

    # Second transfer: from smart_account_address_2 back to deployed_smart_account
    nonce = secrets.randbits(128)
    smart_account_signature = machine_station_sdk.machine_station.machine_sign_transfer_machine_balance(
        smart_account_address=smart_account_address_2,
        recipient_address=smart_account_address,
        nonce=nonce
    )
    machine_station_owner_signature = machine_station_sdk.machine_station.admin_sign_transfer_machine_balance(
        smart_account_address=smart_account_address_2,
        recipient_address=smart_account_address,
        nonce=nonce
    )
    result = machine_station_sdk.machine_station.execute_transfer_machine_balance(
        smart_account_address=smart_account_address_2,
        recipient_address=smart_account_address,
        nonce=nonce,
        machine_station_owner_signature=machine_station_owner_signature,
        smart_account_owner_signature=smart_account_signature
    )
    
    # Verify second transfer result
    assert result is not None
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    assert result.message == f"Successfully transferred balance from {smart_account_address_2} to {smart_account_address} through machine station {machine_station_sdk.machine_station.machine_station_address}."