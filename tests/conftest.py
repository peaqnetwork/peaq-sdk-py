import sys
import os

# Add the project root directory (the parent of tests) to the sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from dotenv import load_dotenv
import pytest
from peaq_sdk_py_old.main import Main
from peaq_sdk_py_old.types.common import ChainType

# Load environment variables from .env in the working directory
load_dotenv()

@pytest.fixture(scope="session")
def config():
    """Central configuration for tests with all possible URL combinations."""
    return {
        # Agung URLs - Public
        "RPC_AGNG_PUBLIC_BASE_URL": os.getenv("RPC_AGNG_PUBLIC_BASE_URL"),
        "WSS_AGNG_PUBLIC_BASE_URL": os.getenv("WSS_AGNG_PUBLIC_BASE_URL"),
        
        # Agung URLs - OnFinality Private
        "RPC_AGNG_ONFIN_PRIVATE_BASE_URL": os.getenv("RPC_AGNG_ONFIN_PRIVATE_BASE_URL"),
        "WSS_AGNG_ONFIN_PRIVATE_BASE_URL": os.getenv("WSS_AGNG_ONFIN_PRIVATE_BASE_URL"),
        
        # Agung URLs - OnFinality Public (if different from private)
        "RPC_AGNG_ONFIN_PUBLIC_BASE_URL": os.getenv("RPC_AGNG_ONFIN_PUBLIC_BASE_URL"),
        "WSS_AGNG_ONFIN_PUBLIC_BASE_URL": os.getenv("WSS_AGNG_ONFIN_PUBLIC_BASE_URL"),
        
        # Peaq URLs - Public
        "RPC_PEAQ_PUBLIC_BASE_URL": os.getenv("RPC_PEAQ_PUBLIC_BASE_URL"),
        "WSS_PEAQ_PUBLIC_BASE_URL": os.getenv("WSS_PEAQ_PUBLIC_BASE_URL"),
        
        # Peaq URLs - OnFinality Private
        "RPC_PEAQ_ONFIN_PRIVATE_BASE_URL": os.getenv("RPC_PEAQ_ONFIN_PRIVATE_BASE_URL"),
        "WSS_PEAQ_ONFIN_PRIVATE_BASE_URL": os.getenv("WSS_PEAQ_ONFIN_PRIVATE_BASE_URL"),
        "RPC_PEAQ_ONFIN_PUBLIC_BASE_URL": os.getenv("RPC_PEAQ_ONFIN_PUBLIC_BASE_URL"),
        "WSS_PEAQ_ONFIN_PUBLIC_BASE_URL": os.getenv("WSS_PEAQ_ONFIN_PUBLIC_BASE_URL"),
        
        # Peaq URLs - QuickNode
        "RPC_PEAQ_QN_PUBLIC_BASE_URL": os.getenv("RPC_PEAQ_QN_PUBLIC_BASE_URL"),
        "WSS_PEAQ_QN_PUBLIC_BASE_URL": os.getenv("WSS_PEAQ_QN_PUBLIC_BASE_URL"),
        "RPC_PEAQ_QN_PRIVATE_BASE_URL": os.getenv("RPC_PEAQ_QN_PRIVATE_BASE_URL"),
        "WSS_PEAQ_QN_PRIVATE_BASE_URL": os.getenv("WSS_PEAQ_QN_PRIVATE_BASE_URL"),
    
        
        # Address and key information
        "SUBSTRATE_ADDRESS": os.getenv("SUBSTRATE_ADDRESS"),
        "SUBSTRATE_SEED": os.getenv("SUBSTRATE_SEED"),
        "EVM_ADDRESS": os.getenv("EVM_ADDRESS"),
        "EVM_PRIVATE": os.getenv("EVM_PRIVATE"),
    }

def get_test_mode():
    """Determine test mode from environment variables."""
    quick_test = os.getenv("QUICK_TEST", "false").lower() == "true"
    test_provider = os.getenv("TEST_PROVIDER", "public").lower()  # public, private, quicknode, quicknode_private, onfinality
    test_chain = os.getenv("TEST_CHAIN", "agung").lower()  # agung, peaq
    return quick_test, test_provider, test_chain

# Get test configuration
QUICK_TEST, TEST_PROVIDER, TEST_CHAIN = get_test_mode()

# Define all possible combinations
ALL_CHAINS = ["agung", "peaq"]
ALL_CONNECTION_TYPES = ["public", "private", "quicknode", "quicknode_private", "onfinality"]

# Filter combinations based on availability
def get_available_combinations():
    """Get available chain/connection combinations based on environment and test mode."""
    if QUICK_TEST:
        # Quick test mode - use only specified chain and provider
        chains = [TEST_CHAIN] if TEST_CHAIN in ALL_CHAINS else ["agung"]
        connection_types = [TEST_PROVIDER]
        return [(chain, conn) for chain in chains for conn in connection_types]
    else:
        # Full test mode - use all available combinations
        combinations = []
        for chain in ALL_CHAINS:
            for conn_type in ALL_CONNECTION_TYPES:
                # Skip combinations that don't exist for certain chains
                if chain == "agung" and conn_type in ["quicknode", "quicknode_private"]:
                    continue  # Agung doesn't have QuickNode
                combinations.append((chain, conn_type))
        return combinations

# Parameterize chain and connection_type based on test mode
AVAILABLE_COMBINATIONS = get_available_combinations()

# Create descriptive test IDs for better test naming
def create_test_id(chain, provider):
    """Create descriptive test ID for chain/provider combination."""
    provider_names = {
        "public": "public-rpc",
        "private": "onfinality-private", 
        "onfinality": "onfinality-public",
        "onfinality_private": "onfinality-private",
        "quicknode": "quicknode-public",
        "quicknode_private": "quicknode-private"
    }
    provider_display = provider_names.get(provider, provider)
    return f"{chain}-{provider_display}"

COMBINATION_IDS = [create_test_id(chain, provider) for chain, provider in AVAILABLE_COMBINATIONS]

# Use single combined fixture to avoid cartesian product
@pytest.fixture(params=AVAILABLE_COMBINATIONS, ids=COMBINATION_IDS)
def chain_connection_combo(request):
    """Combined fixture for chain and connection type with descriptive naming."""
    return request.param

@pytest.fixture
def chain(chain_connection_combo):
    """Chain derived from the combination."""
    chain, connection_type = chain_connection_combo
    return chain

@pytest.fixture
def connection_type(chain_connection_combo):
    """Connection type derived from the combination."""
    chain, connection_type = chain_connection_combo
    return connection_type

def get_urls_for_combination(config, chain, connection_type):
    """Get RPC and WSS URLs for a given chain and connection type combination."""
    url_mapping = {
        # Agung combinations
        ("agung", "public"): (
            config["RPC_AGNG_PUBLIC_BASE_URL"],
            config["WSS_AGNG_PUBLIC_BASE_URL"]
        ),
        ("agung", "private"): (
            config["RPC_AGNG_ONFIN_PRIVATE_BASE_URL"],
            config["WSS_AGNG_ONFIN_PRIVATE_BASE_URL"]
        ),
        ("agung", "onfinality"): (
            config["RPC_AGNG_ONFIN_PUBLIC_BASE_URL"],
            config["WSS_AGNG_ONFIN_PUBLIC_BASE_URL"]
        ),
        
        # Peaq combinations
        ("peaq", "public"): (
            config["RPC_PEAQ_PUBLIC_BASE_URL"],
            config["WSS_PEAQ_PUBLIC_BASE_URL"]
        ),
        ("peaq", "private"): (
            config["RPC_PEAQ_ONFIN_PRIVATE_BASE_URL"],
            config["WSS_PEAQ_ONFIN_PRIVATE_BASE_URL"]
        ),
        ("peaq", "onfinality"): (
            config["RPC_PEAQ_ONFIN_PUBLIC_BASE_URL"],
            config["WSS_PEAQ_ONFIN_PUBLIC_BASE_URL"]
        ),
        ("peaq", "quicknode"): (
            config["RPC_PEAQ_QN_PUBLIC_BASE_URL"],
            config["WSS_PEAQ_QN_PUBLIC_BASE_URL"]
        ),
        ("peaq", "quicknode_private"): (
            config["RPC_PEAQ_QN_PRIVATE_BASE_URL"],
            config["WSS_PEAQ_QN_PRIVATE_BASE_URL"]
        ),
    }
    
    combination_key = (chain, connection_type)
    if combination_key not in url_mapping:
        pytest.skip(f"URL combination {chain}-{connection_type} not available.")
    
    rpc_url, wss_url = url_mapping[combination_key]
    
    # Skip if URLs are not configured
    if not rpc_url or not wss_url:
        pytest.skip(f"URLs not configured for {chain}-{connection_type}")
    
    return rpc_url, wss_url

# Substrate SDK fixture
@pytest.fixture
def substrate_sdk(config, chain, connection_type):
    """Create Substrate SDK instance based on chain and connection type."""
    rpc_url, wss_url = get_urls_for_combination(config, chain, connection_type)
    
    return Main.create_instance(
        chain_type=ChainType.SUBSTRATE,
        base_url=wss_url,
        seed=config["SUBSTRATE_SEED"]
    )

# EVM SDK fixture
@pytest.fixture
def evm_sdk(config, chain, connection_type):
    """Create EVM SDK instance based on chain and connection type."""
    rpc_url, wss_url = get_urls_for_combination(config, chain, connection_type)
    
    # Create EVM SDK with RPC URL and return both SDK and WSS URL for tests that need it
    sdk = Main.create_instance(
        chain_type=ChainType.EVM, 
        base_url=rpc_url, 
        seed=config["EVM_PRIVATE"]
    )
    return sdk, wss_url