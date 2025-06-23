# python native imports
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, List
import time

# local imports
from peaq_sdk.base import Base
from peaq_sdk.did import Did
from peaq_sdk.storage import Storage
from peaq_sdk.pay import Pay
from peaq_sdk.rbac import Rbac
from peaq_sdk.types.common import (
    ChainType, SDKMetadata, BaseUrlError,
    TransactionConfig, BatchConfig, BatchMode, ConfirmationMode,
    TxReceipt, BatchReceipt
)
from peaq_sdk.types.main import CreateInstanceOptions

# 3rd party imports
from substrateinterface.base import SubstrateInterface, GenericCall
from substrateinterface.keypair import Keypair, KeypairType
from web3 import Web3


class Main(Base):
    """
    Entry point for the Python SDK.

    The Main class serves as the primary interface for the SDK, providing methods for 
    initializing the signer, creating the API connection, and handling blockchain-specific operations.
    It inherits from Base, which contains common logic for both EVM and Substrate operations
    with enhanced batch processing and transaction control.
    """
    def __init__(self, base_url: str, chain_type: Optional[ChainType]) -> None:
        """
        Initializes the Main class, representing the primary interface for the SDK.

        Args:
            base_url (str): The URL for connecting to the blockchain.
            chain_type (Optional[ChainType]): The type of blockchain (e.g., EVM or Substrate).
        """
        metadata: SDKMetadata = SDKMetadata(
            base_url=base_url,
            chain_type=chain_type,
            pair=None
        )
        api = self._create_api(metadata)
        super().__init__(api, metadata)
        
        self.did: Did = Did(api, metadata)
        self.storage: Storage = Storage(api, metadata)
        self.pay = Pay(self._api, self._metadata)
        self.rbac: Rbac = Rbac(api, metadata)
    
    @classmethod
    def create_instance(cls,
        base_url: str,
        chain_type: Optional[ChainType],
        seed: Optional[str] = None
        ) -> Main:
        """
        Creates and returns a new instance of the SDK, connecting to the specified network.

        Args:
            base_url (str): The connection URL for the blockchain.
            chain_type (Optional[ChainType]): Indicates whether the blockchain is EVM or Substrate.
            seed (Optional[str]): The secret (mnemonic phrase or private key) used to generate the signer for executing transactions.

        Returns:
            Main: An initialized SDK object ready for executing blockchain operations.
        """
        sdk = Main(base_url, chain_type)
        sdk._initialize_signer(seed)
        return sdk
    
    # Enhanced transaction methods
    def send_transaction_fast(self, call: GenericCall, fee_multiplier: float = 1.0) -> TxReceipt:
        """
        Send a transaction with FAST confirmation mode (returns immediately with tx hash).
        
        Args:
            call (GenericCall): The call to execute
            fee_multiplier (float): Fee multiplier for faster inclusion
            
        Returns:
            TxReceipt: Transaction receipt with tx hash
        """
        config = TransactionConfig(
            mode=ConfirmationMode.FAST,
            fee_multiplier=fee_multiplier
        )
        return self.send_transaction(call, config)
    
    def send_transaction_balanced(
        self, 
        call: GenericCall, 
        fee_multiplier: float = 1.0,
        max_retries: int = 5
    ) -> TxReceipt:
        """
        Send a transaction with BALANCED confirmation mode (waits for inclusion).
        
        Args:
            call (GenericCall): The call to execute
            fee_multiplier (float): Fee multiplier for transaction priority
            max_retries (int): Maximum retry attempts
            
        Returns:
            TxReceipt: Transaction receipt with inclusion confirmation
        """
        config = TransactionConfig(
            mode=ConfirmationMode.BALANCED,
            fee_multiplier=fee_multiplier,
            max_retries=max_retries
        )
        return self.send_transaction(call, config)
    
    def send_transaction_safe(
        self, 
        call: GenericCall, 
        fee_multiplier: float = 1.0,
        max_retries: int = 5
    ) -> TxReceipt:
        """
        Send a transaction with SAFE confirmation mode (waits for finalization).
        
        Args:
            call (GenericCall): The call to execute
            fee_multiplier (float): Fee multiplier for transaction priority
            max_retries (int): Maximum retry attempts
            
        Returns:
            TxReceipt: Transaction receipt with finalization confirmation
        """
        config = TransactionConfig(
            mode=ConfirmationMode.SAFE,
            fee_multiplier=fee_multiplier,
            max_retries=max_retries,
            wait_for_finalization=True
        )
        return self.send_transaction(call, config)
    
    # Batch transaction methods
    def send_batch_atomic(
        self,
        calls: List[GenericCall],
        fee_multiplier: float = 1.0,
        max_retries: int = 5
    ) -> BatchReceipt:
        """
        Send multiple calls atomically - if any fails, all fail.
        Uses Substrate's utility.batchAll for atomic execution.
        
        Args:
            calls (List[GenericCall]): List of calls to execute atomically
            fee_multiplier (float): Fee multiplier for transaction priority
            max_retries (int): Maximum retry attempts
            
        Returns:
            BatchReceipt: Batch execution receipt
        """
        batch_config = BatchConfig(
            batch_mode=BatchMode.ATOMIC,
            transaction_config=TransactionConfig(
                mode=ConfirmationMode.BALANCED,
                fee_multiplier=fee_multiplier,
                max_retries=max_retries
            )
        )
        return self.send_batch_transactions(calls, batch_config)
    
    def send_batch_parallel(
        self,
        calls: List[GenericCall],
        fee_multiplier: float = 1.0,
        max_retries: int = 5
    ) -> BatchReceipt:
        """
        Send multiple calls in parallel for faster execution.
        
        Args:
            calls (List[GenericCall]): List of calls to execute in parallel
            fee_multiplier (float): Fee multiplier for transaction priority
            max_retries (int): Maximum retry attempts
            
        Returns:
            BatchReceipt: Batch execution receipt
        """
        batch_config = BatchConfig(
            batch_mode=BatchMode.PARALLEL,
            transaction_config=TransactionConfig(
                mode=ConfirmationMode.BALANCED,
                fee_multiplier=fee_multiplier,
                max_retries=max_retries
            )
        )
        return self.send_batch_transactions(calls, batch_config)
    
    def send_batch_sequential(
        self,
        calls: List[GenericCall],
        fee_multiplier: float = 1.0,
        max_retries: int = 5
    ) -> BatchReceipt:
        """
        Send multiple calls sequentially, stopping on first failure.
        
        Args:
            calls (List[GenericCall]): List of calls to execute sequentially
            fee_multiplier (float): Fee multiplier for transaction priority
            max_retries (int): Maximum retry attempts
            
        Returns:
            BatchReceipt: Batch execution receipt
        """
        batch_config = BatchConfig(
            batch_mode=BatchMode.SEQUENTIAL,
            transaction_config=TransactionConfig(
                mode=ConfirmationMode.BALANCED,
                fee_multiplier=fee_multiplier,
                max_retries=max_retries
            )
        )
        return self.send_batch_transactions(calls, batch_config)
    
    # Utility methods for benchmarking and optimization
    def benchmark_transaction_modes(
        self,
        call_generator_func,
        fee_multipliers: List[float] = [1.0, 1.5, 2.0]
    ) -> dict:
        """
        Benchmark different transaction modes and fee multipliers.
        
        Args:
            call_generator_func: Function that returns a unique GenericCall for each test
            fee_multipliers (List[float]): Fee multipliers to test
            
        Returns:
            dict: Benchmark results with timing and success rates
        """
        import time
        results = {}
        
        for mode in [ConfirmationMode.FAST, ConfirmationMode.BALANCED, ConfirmationMode.SAFE]:
            results[mode.value] = {}
            for fee_mult in fee_multipliers:
                start_time = time.time()
                error_details = None
                tx_hash = None
                
                try:
                    # Get a unique call from the user-provided generator function
                    unique_call = call_generator_func()
                    
                    config = TransactionConfig(
                        mode=mode,
                        fee_multiplier=fee_mult,
                        wait_for_finalization=(mode == ConfirmationMode.SAFE)
                    )
                    receipt = self.send_transaction(unique_call, config)
                    duration = time.time() - start_time
                    
                    # Check if the transaction actually succeeded
                    if receipt.success:
                        results[mode.value][f"fee_{fee_mult}"] = {
                            "success": True,
                            "duration": duration,
                            "tx_hash": receipt.tx_hash,
                            "finalized": receipt.finalized,
                            "block_hash": receipt.block_hash
                        }
                    else:
                        # Transaction was submitted but failed
                        error_details = f"Transaction failed: {receipt.error or 'Unknown blockchain error'}"
                        tx_hash = receipt.tx_hash
                        results[mode.value][f"fee_{fee_mult}"] = {
                            "success": False,
                            "duration": duration,
                            "error": error_details,
                            "error_stage": "execution",
                            "tx_hash": tx_hash,
                            "receipt_error": receipt.error
                        }
                        
                except Exception as e:
                    duration = time.time() - start_time
                    error_type = type(e).__name__
                    error_message = str(e)
                    
                    # Categorize the error stage
                    if "compose_call" in error_message or "call_generator" in error_message:
                        error_stage = "call_generation"
                    elif "sign" in error_message.lower() or "keypair" in error_message.lower():
                        error_stage = "signing"
                    elif "submit" in error_message.lower() or "send" in error_message.lower():
                        error_stage = "submission"
                    elif "priority" in error_message.lower() or "tip" in error_message.lower():
                        error_stage = "fee_rejection"
                    elif "timeout" in error_message.lower() or "wait" in error_message.lower():
                        error_stage = "confirmation_timeout"
                    elif "websocket" in error_message.lower() or "connection" in error_message.lower():
                        error_stage = "network_connection"
                    else:
                        error_stage = "unknown"
                    
                    error_details = f"{error_type}: {error_message}"
                    
                    results[mode.value][f"fee_{fee_mult}"] = {
                        "success": False,
                        "duration": duration,
                        "error": error_details,
                        "error_stage": error_stage,
                        "error_type": error_type
                    }
                
                # Small delay between tests to ensure different timestamps
                time.sleep(0.5)
        
        return results
    
    def get_optimal_fee_multiplier(
        self,
        call_generator_func,
        target_confirmation_time: float = 30.0
    ) -> float:
        """
        Determine optimal fee multiplier for target confirmation time.
        
        Args:
            call_generator_func: Function that returns a unique GenericCall for each test
            target_confirmation_time (float): Target time in seconds
            
        Returns:
            float: Recommended fee multiplier
        """
        # This is a simplified heuristic - in practice, you'd want more sophisticated
        # analysis based on network conditions and historical data
        import time
        
        try:
            # Test with different multipliers
            test_multipliers = [1.0, 1.25, 1.5, 2.0, 3.0]
            best_multiplier = 1.0
            best_time_diff = float('inf')
            successful_tests = []
            
            for multiplier in test_multipliers:
                start_time = time.time()
                try:
                    # Get a unique call from the user-provided generator function
                    unique_call = call_generator_func()
                    
                    config = TransactionConfig(
                        mode=ConfirmationMode.BALANCED,
                        fee_multiplier=multiplier,
                        max_retries=3
                    )
                    receipt = self.send_transaction(unique_call, config)
                    duration = time.time() - start_time
                    
                    if receipt.success:
                        time_diff = abs(duration - target_confirmation_time)
                        successful_tests.append({
                            "multiplier": multiplier,
                            "duration": duration,
                            "time_diff": time_diff,
                            "tx_hash": receipt.tx_hash
                        })
                        
                        if time_diff < best_time_diff:
                            best_time_diff = time_diff
                            best_multiplier = multiplier
                    else:
                        print(f"  Fee multiplier {multiplier} failed: {receipt.error or 'Unknown error'}")
                            
                except Exception as e:
                    print(f"  Fee multiplier {multiplier} error: {type(e).__name__}: {str(e)}")
                    continue
                
                # Small delay between tests
                time.sleep(0.5)
            
            if successful_tests:
                print(f"  Successful tests: {len(successful_tests)}/{len(test_multipliers)}")
                for test in successful_tests:
                    print(f"    Multiplier {test['multiplier']}: {test['duration']:.2f}s (diff: {test['time_diff']:.2f}s)")
            else:
                print("  Warning: No successful tests for fee optimization")
                    
            return best_multiplier
            
        except Exception as e:
            print(f"  Fee optimization failed with error: {type(e).__name__}: {str(e)}")
            # Fallback to conservative multiplier
            return 1.5
    
    def _initialize_signer(self, seed: Optional[str] = None) -> None:
        """
        Initializes the signer by validating and setting the secret used for generating the key pair/account.

        Args:
            seed (Optional[str]): The mnemonic phrase or private key used to generate the key pair.
        """
        self._validate_secret(seed)
        self._set_metadata(seed)
    
    def _validate_secret(self, seed: Optional[str] = None):
        """
        Validates that the provided seed is compatible with EVM or Substrate.

        Args:
            seed (Optional[str]): The private key (for EVM) or mnemonic phrase (for Substrate)
                to validate.

        Raises:
            ValueError: If the EVM private key is not 64 hex characters (excluding '0x' prefix)
                or is not a valid hexadecimal string.
            ValueError: If the substrate mnemonic does not consist of 12 or 24 words.
        """
        # is_sub = is_valid_ss58_address(addr)
        # is_evm = Web3.is_address(addr)
        # but for private keys??
        if not seed:
            return
        if self._metadata.chain_type == ChainType.EVM:
            # TODO allow setting with a mnemonic phrase for EVM
            key_str = seed[2:] if seed.startswith("0x") else seed
            if len(key_str) != 64:
                raise ValueError("Invalid EVM private key length. Expected 64 hex characters (excluding '0x' prefix).")
            try:
                int(key_str, 16)
            except ValueError:
                raise ValueError("Invalid EVM private key. It must be a valid hexadecimal string.")
        else:
            words = seed.strip().split()
            if len(words) not in (12, 24):
                raise ValueError("Invalid substrate mnemonic. Expected 12 or 24 words.")
        return
    
    def _set_metadata(self, seed: Optional[str] = None) -> None:
        """
        Generates a cryptographic key pair from the provided seed and stores it in the SDK metadata.

        This method invokes _get_key_pair, which applies blockchain-specific logic:
          - For EVM, it generates a key pair from a valid hexadecimal private key.
          - For Substrate, it creates a key pair from a mnemonic phrase (typically 12 or 24 words).
        The resulting key pair is stored in the metadata for use in signing transactions.

        Args:
            seed (Optional[str]): The mnemonic phrase (for Substrate) or private key (for EVM) used to generate the key pair.
        """
        if not seed:
            return
        self._create_key_pair(seed)
    
    
    def _create_api(self, metadata: SDKMetadata) -> Union[Web3, SubstrateInterface]:
        """
        Initializes and returns an API provider for blockchain interaction based on the chain type 
        specified in the SDK metadata.

        Returns:
            Web3 | SubstrateInterface: An API provider instance used to interact with the blockchain.

        Raises:
            BaseUrlError: If the base URL does not start with the expected protocol prefix.
        """
        base_url: str = metadata.base_url
        if metadata.chain_type == ChainType.EVM:
            expected_prefix: str = "https://"
            self._validate_base_url(base_url, expected_prefix, ChainType.EVM)
            api = Web3(Web3.HTTPProvider(base_url))
            return api
        elif metadata.chain_type in (ChainType.SUBSTRATE, None):
            expected_prefix: str = "wss://"
            self._validate_base_url(base_url, expected_prefix, ChainType.SUBSTRATE)
            api = SubstrateInterface(url=base_url, ss58_format=42)
            return api

    def _validate_base_url(self, base_url: str, expected_prefix: str, interaction: ChainType) -> None:
        """
        Validates that the base URL matches the expected protocol for the blockchain.

        Args:
            base_url (str): The URL used to connect to the blockchain.
            expected_prefix (str): The protocol prefix expected in the URL (e.g., "https://" or "wss://").
            interaction (ChainType): The type of blockchain interaction (e.g., ChainType.EVM or ChainType.SUBSTRATE).

        Raises:
            BaseUrlError: If the base URL does not start with the expected prefix.
        """
        if not base_url.startswith(expected_prefix):
            raise BaseUrlError(
                f"Invalid base URL for {interaction}: {base_url}. "
                f"It must start with '{expected_prefix}' to establish connection."
            )