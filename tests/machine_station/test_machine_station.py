import secrets
import pytest
import re
from web3 import Web3


# EVM ONLY!!
def test_deploy_smart_account_signature(machine_station_sdk, smart_account_address):
    """Test creation of signature for deploying smart account"""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_deploy_machine_smart_account(
        machine_smart_account_owner_address=smart_account_address,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132  # 0x + 130 hex chars

def test_transfer_machine_station_balance_signature(machine_station_sdk, recipient_address):
    """Test creation of signature for transferring machine station balance"""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_transfer_machine_station_balance(
        new_machine_station_address=recipient_address,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_execute_transaction_signature(machine_station_sdk, storage_precompile_address):
    """Test creation of signature for executing transaction"""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_execute_transaction(
        target=storage_precompile_address,
        calldata=calldata.tx['data'],
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_execute_machine_transaction_signature(machine_station_sdk, smart_account_address, storage_precompile_address):
    """Test creation of signature for executing machine transaction"""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_execute_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=calldata.tx['data'],
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_batch_transactions_signature(machine_station_sdk, smart_account_address, recipient_address, storage_precompile_address):
    """Test creation of signature for batch transactions"""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    machine_nonces = [secrets.randbits(128), secrets.randbits(128)]
    smart_accounts = [smart_account_address, recipient_address]
    targets = [storage_precompile_address, storage_precompile_address]
    calldata_list = [calldata.tx['data'], calldata.tx['data']]
    
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_execute_machine_batch_transactions(
        smart_account_addresses=smart_accounts,
        targets=targets,
        calldata_list=calldata_list,
        nonce=nonce,
        machine_nonces=machine_nonces
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_transfer_machine_balance_signature(machine_station_sdk, smart_account_address, recipient_address):
    """Test creation of signature for transferring machine balance"""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.owner_sign_typed_data_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=recipient_address,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_machine_owner_sign_execute_machine_transaction(machine_station_sdk, smart_account_address, storage_precompile_address):
    """Test creation of signature for executing machine transaction"""
    nonce = secrets.randbits(128)
    calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
    signature = machine_station_sdk.machine_station.machine_owner_sign_typed_data_execute_machine_transaction(
        smart_account_address=smart_account_address,
        target=storage_precompile_address,
        calldata=calldata.tx['data'],
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_machine_sign_transfer_machine_balance(machine_station_sdk, smart_account_address, recipient_address):
    """Test creation of signature for transferring machine balance"""
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.machine_sign_typed_data_transfer_machine_balance(
        smart_account_address=smart_account_address,
        recipient_address=recipient_address,
        nonce=nonce
    )
    assert signature.startswith("0x")
    assert len(signature) == 132

def test_deploy_smart_account(machine_station_sdk, machine_smart_account_owner_address):
    """Test deploying a new smart account and verify its on-chain deployment"""
    nonce = secrets.randbits(128)
    
    # Get signature for deployment
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_deploy_machine_smart_account(
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

def test_transfer_machine_station_balance(machine_station_sdk, recipient_address):
    """Test transferring balance to a new machine station"""
    nonce = secrets.randbits(128)
    
    # Get signature for transfer
    signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_transfer_machine_station_balance(
        new_machine_station_address=recipient_address,
        nonce=nonce
    )
    
    # Execute the transfer
    result = machine_station_sdk.machine_station.execute_transfer_machine_station_balance(
        new_machine_station_address=recipient_address,
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    
    # Test the result object structure
    assert result is not None
    assert result.message == f"Successfully transferred balance from {machine_station_sdk.machine_station_address} to {recipient_address}."
    assert result.receipt is not None
    assert result.receipt["status"] == 1  # Check transaction success
    
    # TODO: Add balance checks before and after transfer once we have a way to query balances
    # This would involve:
    # 1. Check original machine station balance
    # 2. Check new machine station balance (should be 0)
    # 3. Execute transfer
    # 4. Check original machine station balance (should be 0)
    # 5. Check new machine station balance (should have the transferred amount)

# def test_execute_transaction(machine_station_sdk, storage_precompile_address):
#     """Test executing a transaction through the machine station"""
#     storage_calldata = machine_station_sdk.storage.add_item(item_type="test_item", item="test_value")
#     nonce = secrets.randbits(128)
#     signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_execute_transaction(
#         target=storage_precompile_address,
#         calldata=storage_calldata.tx['data'],
#         nonce=nonce
#     )
#     result = machine_station_sdk.machine_station.execute_transaction(
#         target=storage_precompile_address,
#         calldata=storage_calldata.tx['data'],
#         nonce=nonce,
#         machine_station_owner_signature=signature
#     )
#     assert result is not None
#     assert hasattr(result, 'transactionHash')
#     assert result.status == 1

# def test_execute_machine_transaction(machine_station_sdk, deployed_smart_account, storage_precompile_address):
#     """Test executing a transaction from a smart account"""
#     storage_calldata = machine_station_sdk.storage.add_item(item_type="test_item_2", item="test_value_2")
#     nonce = secrets.randbits(128)
    
#     smart_account_signature = machine_station_sdk.machine_station.machine_owner_sign_typed_data_execute_machine_transaction(
#         smart_account_address=deployed_smart_account,
#         target=storage_precompile_address,
#         calldata=storage_calldata.tx['data'],
#         nonce=nonce
#     )
    
#     machine_station_owner_signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_execute_machine_transaction(
#         smart_account_address=deployed_smart_account,
#         target=storage_precompile_address,
#         calldata=storage_calldata.tx['data'],
#         nonce=nonce
#     )
    
#     result = machine_station_sdk.machine_station.execute_machine_transaction(
#         smart_account_address=deployed_smart_account,
#         target=storage_precompile_address,
#         calldata=storage_calldata.tx['data'],
#         nonce=nonce,
#         machine_station_owner_signature=machine_station_owner_signature,
#         smart_account_owner_signature=smart_account_signature
#     )
#     assert result is not None
#     assert hasattr(result, 'transactionHash')
#     assert result.status == 1

# def test_execute_batch_transactions(machine_station_sdk, deployed_smart_account, smart_account_address, storage_precompile_address):
#     """Test executing multiple transactions from multiple smart accounts"""
#     smart_accounts = [deployed_smart_account, smart_account_address]
#     targets = [storage_precompile_address, storage_precompile_address]
#     storage_calldata = machine_station_sdk.storage.add_item(item_type="test_batch", item="test_value")
#     calldata_list = [storage_calldata.tx['data'], storage_calldata.tx['data']]
    
#     smart_account_signatures = []
#     machine_nonces = []
    
#     for smart_account_address in smart_accounts:
#         machine_nonce = secrets.randbits(128)
#         machine_nonces.append(machine_nonce)
        
#         signature = machine_station_sdk.machine_station.machine_owner_sign_typed_data_execute_machine_transaction(
#             smart_account_address=smart_account_address,
#             target=targets[0],
#             calldata=calldata_list[0],
#             nonce=machine_nonce
#         )
#         smart_account_signatures.append(signature)
    
#     nonce = secrets.randbits(128)
#     machine_station_owner_signature = machine_station_sdk.machine_station.depin_owner_sign_typed_data_execute_machine_batch_transactions(
#         smart_account_addresses=smart_accounts,
#         targets=targets,
#         calldata_list=calldata_list,
#         nonce=nonce,
#         machine_nonces=machine_nonces
#     )
    
#     result = machine_station_sdk.machine_station.execute_machine_batch_transaction(
#         smart_account_addresses=smart_accounts,
#         targets=targets,
#         calldata_list=calldata_list,
#         nonce=nonce,
#         machine_nonces=machine_nonces,
#         machine_station_owner_signature=machine_station_owner_signature,
#         smart_account_owner_signatures=smart_account_signatures
#     )
#     assert result is not None
#     assert hasattr(result, 'transactionHash')
#     assert result.status == 1

# def test_transfer_machine_balance(machine_station_sdk, deployed_smart_account, recipient_address):
#     """Test transferring balance from a smart account"""
#     nonce = secrets.randbits(128)
#     smart_account_signature = machine_station_sdk.machine_station.machine_sign_typed_data_transfer_machine_balance(
#         smart_account_address=deployed_smart_account,
#         recipient_address=recipient_address,
#         nonce=nonce
#     )
#     machine_station_owner_signature = machine_station_sdk.machine_station.owner_sign_typed_data_transfer_machine_balance(
#         smart_account_address=deployed_smart_account,
#         recipient_address=recipient_address,
#         nonce=nonce
#     )
#     result = machine_station_sdk.machine_station.execute_machine_transfer_balance(
#         smart_account_address=deployed_smart_account,
#         recipient_address=recipient_address,
#         nonce=nonce,
#         machine_station_owner_signature=machine_station_owner_signature,
#         smart_account_owner_signature=smart_account_signature
#     )
#     assert result is not None
#     assert hasattr(result, 'transactionHash')
#     assert result.status == 1 