import os
import secrets
import pytest
from dotenv import load_dotenv
from peaq_sdk.main import Main
from peaq_sdk.types.common import ChainType

# Load environment variables from .env file
load_dotenv()


# EVM ONLY!!
def is_agung_network(url: str) -> bool:
    """Check if the URL is for the Agung network"""
    return 'agung' in url.lower()

@pytest.fixture(params=[os.getenv("AGNG_MACHINE_STATION_ADDRESS")])
def machine_station_address(request):
    """
    Machine station contract address from environment variable AGNG_MACHINE_STATION_ADDRESS
    """
    if not request.param:
        pytest.skip("AGNG_MACHINE_STATION_ADDRESS not set in environment")
    return request.param

@pytest.fixture(params=[os.getenv("AGNG_MACHINE_STATION_ADDRESS_2")])
def machine_station_address_2(request):
    """
    Machine station contract address from environment variable AGNG_MACHINE_STATION_ADDRESS
    """
    if not request.param:
        pytest.skip("AGNG_MACHINE_STATION_ADDRESS_2 not set in environment")
    return request.param


@pytest.fixture
def machine_station_owner_private_key():
    """
    Machine station owner's private key from environment variable AGNG_MACHINE_STATION_OWNER_PRIVATE_KEY
    """
    private_key = os.getenv("AGNG_MACHINE_STATION_OWNER_PRIVATE_KEY")
    if not private_key:
        pytest.skip("AGNG_MACHINE_STATION_OWNER_PRIVATE_KEY not set in environment")
    return private_key

@pytest.fixture
def machine_station_2_owner_private_key():
    """
    Machine station owner's private key from environment variable AGNG_MACHINE_STATION_OWNER_PRIVATE_KEY
    """
    private_key = os.getenv("AGNG_MACHINE_STATION_2_OWNER_PRIVATE_KEY")
    if not private_key:
        pytest.skip("AGNG_MACHINE_STATION_2_OWNER_PRIVATE_KEY not set in environment")
    return private_key

@pytest.fixture
def machine_account_owner_private_key():
    """
    Machine account owner's private key from environment variable AGNG_MACHINE_ACCOUNT_OWNER_PRIVATE_KEY
    """
    private_key = os.getenv("AGNG_MACHINE_ACCOUNT_OWNER_PRIVATE_KEY")
    if not private_key:
        pytest.skip("AGNG_MACHINE_ACCOUNT_OWNER_PRIVATE_KEY not set in environment")
    return private_key

@pytest.fixture
def smart_account_address():
    """
    Smart account address from environment variable AGNG_SMART_ACCOUNT_ADDRESS
    Falls back to default if not set
    """
    return os.getenv("AGNG_SMART_ACCOUNT_ADDRESS")

@pytest.fixture
def smart_account_address_2():
    """
    Smart account address from environment variable AGNG_SMART_ACCOUNT_ADDRESS
    Falls back to default if not set
    """
    return os.getenv("AGNG_SMART_ACCOUNT_ADDRESS_2")

@pytest.fixture
def machine_smart_account_owner_address():
    """
    Smart account address from environment variable AGNG_SMART_ACCOUNT_ADDRESS
    Falls back to default if not set
    """
    return os.getenv("AGNG_MACHINE_SMART_ACCOUNT_OWNER_ADDRESS")

@pytest.fixture
def storage_precompile_address():
    """
    Storage precompile address from environment variable AGNG_STORAGE_PRECOMPILE_ADDRESS
    Falls back to default if not set
    """
    return os.getenv("AGNG_STORAGE_PRECOMPILE_ADDRESS")

@pytest.fixture
def did_precompile_address():
    """
    DID precompile address from environment variable AGNG_DID_PRECOMPILE_ADDRESS
    Falls back to default if not set
    """
    return os.getenv("AGNG_DID_PRECOMPILE_ADDRESS")

@pytest.fixture
def machine_station_sdk(evm_sdk, machine_station_address, machine_station_owner_private_key, machine_account_owner_private_key):
    """
    Creates a machine station SDK instance for testing.
    Only runs on Agung network.
    """
    sdk, _ = evm_sdk
    
    # Skip if not on Agung network
    if not is_agung_network(sdk.metadata.base_url):
        pytest.skip("Machine Station tests only run on Agung network")
    
    return Main.machine_station_instance(
        base_url=sdk.metadata.base_url,
        machine_station_address=machine_station_address,
        machine_station_owner_private_key=machine_station_owner_private_key,
        machine_account_owner_private_key=machine_account_owner_private_key
    )
    
@pytest.fixture
def machine_station_sdk_2(evm_sdk, machine_station_address_2, machine_station_2_owner_private_key, machine_account_owner_private_key):
    """
    Creates a machine station SDK instance for testing.
    Only runs on Agung network.
    """
    sdk, _ = evm_sdk
    
    # Skip if not on Agung network
    if not is_agung_network(sdk.metadata.base_url):
        pytest.skip("Machine Station tests only run on Agung network")
    
    return Main.machine_station_instance(
        base_url=sdk.metadata.base_url,
        machine_station_address=machine_station_address_2,
        machine_station_owner_private_key=machine_station_2_owner_private_key,
        machine_account_owner_private_key=machine_account_owner_private_key
    )

@pytest.fixture
def deployed_smart_account(machine_station_sdk, smart_account_address):
    """
    Fixture to deploy a smart account for testing.
    Returns the deployed smart account address.
    """
    nonce = secrets.randbits(128)
    signature = machine_station_sdk.machine_station.admin_sign_deploy_machine_smart_account(
        machine_smart_account_owner_address=smart_account_address,
        nonce=nonce
    )
    result = machine_station_sdk.machine_station.deploy_machine_smart_account(
        machine_smart_account_owner_address=smart_account_address,
        nonce=nonce,
        machine_station_owner_signature=signature
    )
    assert result.success == True, "Smart account deployment failed"
    assert result.deployed_address.startswith("0x")
    assert len(result.deployed_address) == 42
    return result.deployed_address 

@pytest.fixture
def wss_url_agng():
    """
    WSS URL from environment variable WSS_AGNG_PUBLIC_BASE_URL
    """
    return os.getenv("WSS_AGNG_PUBLIC_BASE_URL")