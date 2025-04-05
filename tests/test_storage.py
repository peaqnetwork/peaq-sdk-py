import pytest
import os
from dotenv import load_dotenv
import re
import json

from src.modules.main import Main
from src.types.common import ChainType
from src.types.storage import GetItemError


# loads .env from the current working directory and set to vars
load_dotenv()
WSS_AGUNG = os.getenv("WSS_AGUNG")
PRIVATE_RPC_AGUNG = os.getenv("PRIVATE_RPC_AGUNG")

WSS_PEAQ = os.getenv("WSS_PEAQ")
RPC_PEAQ = os.getenv("RPC_PEAQ")

SUBSTRATE_ADDRESS = os.getenv("SUBSTRATE_ADDRESS")
SUBSTRATE_SEED = os.getenv("SUBSTRATE_SEED")

EVM_ADDRESS= os.getenv("EVM_ADDRESS")
EVM_PRIVATE = os.getenv("EVM_PRIVATE")

def test_substrate(item_type, item, chain):
    if chain == "agung":
        wss_base_url = WSS_AGUNG
        sdk_substrate = Main.create_instance(chain_type=ChainType.SUBSTRATE, base_url=wss_base_url, seed=SUBSTRATE_SEED)
    elif chain == "peaq":
        wss_base_url = WSS_PEAQ
        sdk_substrate = Main.create_instance(chain_type=ChainType.SUBSTRATE, base_url=wss_base_url, seed=SUBSTRATE_SEED)
    else:
        raise ValueError(f"Chain of {chain} is not recognized.")
        
    
    # Substrate tests:
    # create storage
    result = sdk_substrate.storage.add_item(item_type=item_type, item=item)
    assert result is not None
    pattern = r'^0x[0-9a-fA-F]{64}$'
    assert result.message == f"Successfully added the storage item type {item_type} with item {item} for the address {SUBSTRATE_ADDRESS}"
    assert re.fullmatch(pattern, result.receipt.block_hash) is not None
    assert re.fullmatch(pattern, result.receipt.extrinsic_hash) is not None
    assert result.receipt.fee is not None
    
    # read result
    result = sdk_substrate.storage.get_item(item_type=item_type)
    if (type(item) is dict):
        assert json.loads(result[item_type]) == item
    else:
        assert result[item_type] == item
    
    # update item
    new_item='test123'
    result = sdk_substrate.storage.update_item(item_type=item_type, item=new_item)
    assert result is not None
    pattern = r'^0x[0-9a-fA-F]{64}$'
    assert result.message == f"Successfully updated the storage item type {item_type} with item {new_item} for the address {SUBSTRATE_ADDRESS}"
    assert re.fullmatch(pattern, result.receipt.block_hash) is not None
    assert re.fullmatch(pattern, result.receipt.extrinsic_hash) is not None
    assert result.receipt.fee is not None
    
    # read updated item
    result = sdk_substrate.storage.get_item(item_type=item_type)
    if (type(new_item) is dict):
        assert json.loads(result[item_type]) == item
    else:
        assert result[item_type] == new_item
    
    # delete item
    result = sdk_substrate.storage.remove_item(item_type=item_type)
    assert result is not None
    pattern = r'^0x[0-9a-fA-F]{64}$'
    assert result.message == f"Successfully removed the storage item type {item_type} for the address {SUBSTRATE_ADDRESS}"
    assert re.fullmatch(pattern, result.receipt.block_hash) is not None
    assert re.fullmatch(pattern, result.receipt.extrinsic_hash) is not None
    assert result.receipt.fee is not None
    
    # try to read to confirm failure
    with pytest.raises(GetItemError) as exc_info:
        result = sdk_substrate.storage.get_item(item_type=item_type)
    assert str(exc_info.value) == f"Item type of {item_type} was not found at address {SUBSTRATE_ADDRESS}."
    
def test_evm(item_type, item, chain):
    if chain == "agung":
        wss_base_url = WSS_AGUNG
        rpc_base_url = PRIVATE_RPC_AGUNG
        sdk_evm= Main.create_instance(chain_type=ChainType.EVM, base_url=rpc_base_url, seed=EVM_PRIVATE)
    elif chain == "peaq":
        wss_base_url = WSS_PEAQ
        rpc_base_url = RPC_PEAQ
        sdk_evm= Main.create_instance(chain_type=ChainType.EVM, base_url=rpc_base_url, seed=EVM_PRIVATE)
    else:
        raise ValueError(f"Chain of {chain} is not recognized.")
    
    sdk_evm= Main.create_instance(chain_type=ChainType.EVM, base_url=rpc_base_url, seed=EVM_PRIVATE)
    
    # EVM tests:
    # create storage
    result = sdk_evm.storage.add_item(item_type=item_type, item=item)
    assert result is not None
    pattern = r'^[0-9a-fA-F]{64}$'
    assert result.message == f"Successfully added the storage item type {item_type} with item {item} for the address {EVM_ADDRESS}"
    assert re.fullmatch(pattern, result.receipt.blockHash.hex()) is not None
    
    # read result
    result = sdk_evm.storage.get_item(item_type=item_type, address = EVM_ADDRESS, wss_base_url=wss_base_url)
    if (type(item) is dict):
        assert json.loads(result[item_type]) == item
    else:
        assert result[item_type] == item
    
    # update
    new_item='test123'
    result = sdk_evm.storage.update_item(item_type=item_type, item=new_item)
    assert result is not None
    pattern = r'^[0-9a-fA-F]{64}$'
    assert result.message == f"Successfully updated the storage item type {item_type} with item {new_item} for the address {EVM_ADDRESS}"
    assert re.fullmatch(pattern, result.receipt.blockHash.hex()) is not None
    
    # read updated result
    result = sdk_evm.storage.get_item(item_type=item_type, address = EVM_ADDRESS, wss_base_url=wss_base_url)
    if (type(new_item) is dict):
        assert json.loads(result[item_type]) == item
    else:
        assert result[item_type] == new_item
    
    # TEMPORARY FIX since no delete precompile...
    with pytest.raises(ValueError) as exc_info:
        result = sdk_evm.storage.remove_item(item_type=item_type)
    assert str(exc_info.value) == "Precompile for peaq Storage Remove Item will be included in the next runtime update."

def test_storage_on_chain(chain):
    item_type = "python-sdk-storage-006"
    item = "test"
    test_substrate(item_type, item, chain)
    test_evm(item_type, item, chain)
    
    item_type2 = "python-sdk-storage-007"
    item2 = {"test": {"hi": 123}}
    test_substrate(item_type2, item2, chain)
    test_evm(item_type2, item2, chain)
    
def test_storage():
    test_storage_on_chain("agung")
    # test_storage_on_chain("peaq")
    

if __name__ == "__main__":
    pytest.main()
