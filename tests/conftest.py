import sys
import os

# Add the project root directory (the parent of tests) to the sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from dotenv import load_dotenv
import pytest
from peaq_sdk.modules.main import Main
from peaq_sdk.types.common import ChainType

# Load environment variables from .env in the working directory
load_dotenv()

@pytest.fixture(scope="session")
def config():
    """Central configuration for tests."""
    return {
        # Agung URLs
        "RPC_AGNG_PUBLIC_BASE_URL": os.getenv("RPC_AGNG_PUBLIC_BASE_URL"),
        "WSS_AGNG_PUBLIC_BASE_URL": os.getenv("WSS_AGNG_PUBLIC_BASE_URL"),
        "RPC_AGNG_ONFIN_PRIVATE_BASE_URL": os.getenv("RPC_AGNG_ONFIN_PRIVATE_BASE_URL"),
        "WSS_AGNG_ONFIN_PRIVATE_BASE_URL": os.getenv("WSS_AGNG_ONFIN_PRIVATE_BASE_URL"),
        # Peaq URLs
        "RPC_PEAQ_PUBLIC_BASE_URL": os.getenv("RPC_PEAQ_PUBLIC_BASE_URL"),
        "WSS_PEAQ_PUBLIC_BASE_URL": os.getenv("WSS_PEAQ_PUBLIC_BASE_URL"),
        "RPC_PEAQ_ONFIN_PRIVATE_BASE_URL": os.getenv("RPC_PEAQ_ONFIN_PRIVATE_BASE_URL"),
        "WSS_PEAQ_ONFIN_PUBLIC_BASE_URL": os.getenv("WSS_PEAQ_ONFIN_PUBLIC_BASE_URL"),
        "RPC_PEAQ_QN_PRIVATE_BASE_URL": os.getenv("RPC_PEAQ_QN_PRIVATE_BASE_URL"),
        "WSS_PEAQ_QN_PRIVATE_BASE_URL": os.getenv("WSS_PEAQ_QN_PRIVATE_BASE_URL"),
        # Address and key information
        "SUBSTRATE_ADDRESS": os.getenv("SUBSTRATE_ADDRESS"),
        "SUBSTRATE_SEED": os.getenv("SUBSTRATE_SEED"),
        "EVM_ADDRESS": os.getenv("EVM_ADDRESS"),
        "EVM_PRIVATE": os.getenv("EVM_PRIVATE"),
    }
    
# Parameterize chain with "agung" and "peaq"
@pytest.fixture(params=["agung", "peaq"])
def chain(request):
    return request.param

# Parameterize connection_type with "public", "private", and "quicknode"
# For chains that don't support quicknode (e.g. agung), we skip that option.
@pytest.fixture(params=["public", "private", "quicknode"])
def connection_type(request, chain):
    if chain == "agung" and request.param == "quicknode":
        pytest.skip("Quicknode URLs not available for Agung.")
    return request.param

# Substrate SDK fixture: chooses the appropriate websocket URL based on chain and connection type.
@pytest.fixture
def substrate_sdk(config, chain, connection_type):
    if chain == "agung":
        if connection_type == "public":
            base_url = config["WSS_AGNG_PUBLIC_BASE_URL"]
        else:  # private
            base_url = config["WSS_AGNG_ONFIN_PRIVATE_BASE_URL"]
    elif chain == "peaq":
        if connection_type == "public":
            base_url = config["WSS_PEAQ_PUBLIC_BASE_URL"]
        elif connection_type == "private":
            base_url = config["WSS_PEAQ_ONFIN_PUBLIC_BASE_URL"]
        elif connection_type == "quicknode":
            base_url = config["WSS_PEAQ_QN_PRIVATE_BASE_URL"]
    else:
        raise ValueError(f"Chain {chain} is not recognized.")

    return Main.create_instance(
        chain_type=ChainType.SUBSTRATE,
        base_url=base_url,
        seed=config["SUBSTRATE_SEED"]
    )

@pytest.fixture
def evm_sdk(config, chain, connection_type):
    if chain == "agung":
        base_rpc = config["RPC_AGNG_PUBLIC_BASE_URL"] if connection_type == "public" else config["RPC_AGNG_ONFIN_PRIVATE_BASE_URL"]
        base_wss = config["WSS_AGNG_PUBLIC_BASE_URL"] if connection_type == "public" else config["WSS_AGNG_ONFIN_PRIVATE_BASE_URL"]
    else:  # peaq
        if connection_type == "public":
            base_rpc = config["RPC_PEAQ_PUBLIC_BASE_URL"]
            base_wss = config["WSS_PEAQ_PUBLIC_BASE_URL"]
        elif connection_type == "private":
            base_rpc = config["RPC_PEAQ_ONFIN_PRIVATE_BASE_URL"]
            base_wss = config["WSS_PEAQ_ONFIN_PUBLIC_BASE_URL"]
        else:
            base_rpc = config["RPC_PEAQ_QN_PRIVATE_BASE_URL"]
            base_wss = config["WSS_PEAQ_QN_PRIVATE_BASE_URL"]
    # return both rpc and wss so tests can use them
    sdk = Main.create_instance(
        chain_type=ChainType.EVM, 
        base_url=base_rpc, 
        seed=config["EVM_PRIVATE"])
    return sdk, base_wss