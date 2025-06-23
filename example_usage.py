#!/usr/bin/env python3
"""
Example usage of the enhanced Peaq SDK with improved transaction handling and batching.

This example demonstrates:
1. Different transaction confirmation modes (Fast, Balanced, Safe)
2. Batch processing with Atomic, Parallel, and Sequential modes
3. Fee optimization and benchmarking
4. Error handling and retry mechanisms
"""

import time
import uuid
from datetime import datetime
from peaq_sdk.main import Main
from peaq_sdk.types.common import (
    ChainType, TransactionConfig, BatchConfig, BatchMode, ConfirmationMode
)

# Configuration
SUBSTRATE_URL = "wss://wss-async.agung.peaq.network"
SEED = "fame inside foil shadow equal direct alpha battle spike argue gun satisfy"

def get_unique_id():
    """Generate a unique identifier for transactions."""
    return str(uuid.uuid4())[:8]

def get_timestamp():
    """Get current timestamp for unique data."""
    return int(time.time())

def demonstrate_transaction_modes():
    """Demonstrate different transaction confirmation modes."""
    print("=== Transaction Modes Demo ===")
    
    # Initialize SDK
    sdk = Main.create_instance(SUBSTRATE_URL, ChainType.SUBSTRATE, SEED)
    
    # Generate unique data for each transaction
    timestamp = get_timestamp()
    unique_id = get_unique_id()
    
    # Fast mode - returns immediately with tx hash
    print("1. Fast mode transaction...")
    fast_call = sdk.api.compose_call(
        call_module="PeaqStorage",
        call_function="add_item",
        call_params={
            'item_type': f'demo_fast_{timestamp}_{unique_id}',
            'item': f'Fast transaction at {datetime.now().isoformat()}'
        }
    )
    fast_receipt = sdk.send_transaction_fast(fast_call, fee_multiplier=1.5)
    print(f"Fast tx hash: {fast_receipt.tx_hash}")
    print(f"Finalized: {fast_receipt.finalized}")
    
    # Wait a bit to ensure different timestamp
    time.sleep(1)
    timestamp = get_timestamp()
    unique_id = get_unique_id()
    
    # Balanced mode - waits for inclusion
    print("\n2. Balanced mode transaction...")
    balanced_call = sdk.api.compose_call(
        call_module="PeaqStorage",
        call_function="add_item",
        call_params={
            'item_type': f'demo_balanced_{timestamp}_{unique_id}',
            'item': f'Balanced transaction at {datetime.now().isoformat()}'
        }
    )
    balanced_receipt = sdk.send_transaction_balanced(balanced_call, fee_multiplier=1.2)
    print(f"Balanced tx hash: {balanced_receipt.tx_hash}")
    print(f"Block hash: {balanced_receipt.block_hash}")
    print(f"Success: {balanced_receipt.success}")
    
    # Wait a bit to ensure different timestamp
    time.sleep(1)
    timestamp = get_timestamp()
    unique_id = get_unique_id()
    
    # Safe mode - waits for finalization
    print("\n3. Safe mode transaction...")
    safe_call = sdk.api.compose_call(
        call_module="PeaqStorage",
        call_function="add_item",
        call_params={
            'item_type': f'demo_safe_{timestamp}_{unique_id}',
            'item': f'Safe transaction at {datetime.now().isoformat()}'
        }
    )
    safe_receipt = sdk.send_transaction_safe(safe_call, fee_multiplier=1.0)
    print(f"Safe tx hash: {safe_receipt.tx_hash}")
    print(f"Finalized: {safe_receipt.finalized}")
    print(f"Events: {len(safe_receipt.events)} events recorded")

def demonstrate_batch_modes():
    """Demonstrate different batch processing modes."""
    print("\n=== Batch Processing Demo ===")
    
    sdk = Main.create_instance(SUBSTRATE_URL, ChainType.SUBSTRATE, SEED)
    
    # Generate unique data for batch operations
    timestamp = get_timestamp()
    batch_id = get_unique_id()
    
    # Prepare multiple storage operations with unique identifiers
    items = [
        (f"user_profile_{timestamp}_{batch_id}_1", {
            "name": "Alice",
            "age": 30,
            "created_at": datetime.now().isoformat(),
            "batch_id": batch_id
        }),
        (f"user_preferences_{timestamp}_{batch_id}_2", {
            "theme": "dark",
            "language": "en",
            "created_at": datetime.now().isoformat(),
            "batch_id": batch_id
        }),
        (f"user_settings_{timestamp}_{batch_id}_3", {
            "notifications": True,
            "privacy": "public",
            "created_at": datetime.now().isoformat(),
            "batch_id": batch_id
        })
    ]
    
    # Atomic batch - all or nothing
    print("1. Atomic batch processing...")
    try:
        atomic_receipt = sdk.storage.add_items_atomic(items)
        
        print(f"Atomic batch success: {atomic_receipt.receipt.success}")
        print(f"Atomic receipt: {atomic_receipt}")

        if atomic_receipt.receipt.batch_hash:
            print(f"Batch tx hash: {atomic_receipt.receipt.batch_hash}")
    except Exception as e:
        print(f"Atomic batch failed: {e}")
    
    # Generate new unique data for parallel batch
    time.sleep(1)
    timestamp = get_timestamp()
    batch_id = get_unique_id()
    
    # parallel_items = [
    #     (f"parallel_item_{timestamp}_{batch_id}_1", {
    #         "data": "parallel_data_1",
    #         "timestamp": timestamp,
    #         "batch_id": batch_id
    #     }),
    #     (f"parallel_item_{timestamp}_{batch_id}_2", {
    #         "data": "parallel_data_2", 
    #         "timestamp": timestamp,
    #         "batch_id": batch_id
    #     }),
    #     (f"parallel_item_{timestamp}_{batch_id}_3", {
    #         "data": "parallel_data_3",
    #         "timestamp": timestamp,
    #         "batch_id": batch_id
    #     })
    # ]
    
    # # Parallel batch - concurrent execution
    # print("\n2. Parallel batch processing...")
    # try:
    #     parallel_receipt = sdk.storage.add_items_parallel(parallel_items)
    #     print(f"Parallel batch success: {parallel_receipt.receipt.success}")
    #     print(f"Processed {len(parallel_receipt.receipt.receipts)} transactions")
    #     for i, receipt in enumerate(parallel_receipt.receipt.receipts):
    #         print(f"  Transaction {i+1}: {'✓' if receipt.success else '✗'}")
    # except Exception as e:
    #     print(f"Parallel batch failed: {e}")
    
    # Generate new unique data for sequential batch
    time.sleep(1)
    timestamp = get_timestamp()
    batch_id = get_unique_id()
    
    sequential_items = [
        (f"sequential_item_{timestamp}_{batch_id}_1", {
            "data": "sequential_data_1",
            "timestamp": timestamp,
            "batch_id": batch_id
        }),
        (f"sequential_item_{timestamp}_{batch_id}_2", {
            "data": "sequential_data_2",
            "timestamp": timestamp,
            "batch_id": batch_id
        }),
        (f"sequential_item_{timestamp}_{batch_id}_3", {
            "data": "sequential_data_3",
            "timestamp": timestamp,
            "batch_id": batch_id
        })
    ]
    
    # Sequential batch - one by one
    print("\n3. Sequential batch processing...")
    try:
        sequential_receipt = sdk.storage.add_items_batch(
            sequential_items,
            BatchConfig(batch_mode=BatchMode.SEQUENTIAL)
        )
        print(f"Sequential batch success: {sequential_receipt.receipt.success}")
        print(f"Sequential receipt: {sequential_receipt}")
        
        if sequential_receipt.receipt.failed_at_index is not None:
            print(f"Failed at index: {sequential_receipt.receipt.failed_at_index}")
    except Exception as e:
        print(f"Sequential batch failed: {e}")

def demonstrate_fee_optimization():
    """Demonstrate fee optimization and benchmarking."""
    print("\n=== Fee Optimization Demo ===")
    
    sdk = Main.create_instance(SUBSTRATE_URL, ChainType.SUBSTRATE, SEED)
    
    # Create a call generator function that produces unique calls for each test
    def create_benchmark_call():
        """Generate a unique call for benchmark testing."""
        timestamp = get_timestamp()
        unique_id = get_unique_id()
        return sdk.api.compose_call(
            call_module="PeaqStorage",
            call_function="add_item",
            call_params={
                'item_type': f'benchmark_test_{timestamp}_{unique_id}',
                'item': f'Benchmark test data created at {datetime.now().isoformat()}'
            }
        )
    
    # Benchmark different transaction modes
    print("1. Benchmarking transaction modes...")
    try:
        # Pass the call generator function - SDK will call it for each unique test
        results = sdk.benchmark_transaction_modes(
            call_generator_func=create_benchmark_call,
            fee_multipliers=[1.0, 1.5, 2.0]
        )
        
        for mode, mode_results in results.items():
            print(f"\n{mode.upper()} mode results:")
            for fee_config, result in mode_results.items():
                if result['success']:
                    print(f"  {fee_config}: {result['duration']:.2f}s - ✅ Success")
                    print(f"    └─ Tx Hash: {result['tx_hash']}")
                    if result.get('finalized'):
                        print(f"    └─ Finalized: Yes")
                    if result.get('block_hash'):
                        print(f"    └─ Block: {result['block_hash']}")
                else:
                    print(f"  {fee_config}: {result['duration']:.2f}s - ❌ Failed")
                    print(f"    └─ Stage: {result.get('error_stage', 'unknown')}")
                    print(f"    └─ Error: {result.get('error', 'No error details')}")
                    if result.get('tx_hash'):
                        print(f"    └─ Tx Hash: {result['tx_hash']}")
                    if result.get('error_type'):
                        print(f"    └─ Error Type: {result['error_type']}")
    except Exception as e:
        print(f"Benchmarking failed: {type(e).__name__}: {e}")
    
    # Get optimal fee multiplier
    print("\n2. Finding optimal fee multiplier...")
    try:
        # Create a separate call generator for fee optimization
        def create_optimization_call():
            """Generate a unique call for fee optimization testing."""
            timestamp = get_timestamp()
            unique_id = get_unique_id()
            return sdk.api.compose_call(
                call_module="PeaqStorage",
                call_function="add_item",
                call_params={
                    'item_type': f'fee_optimization_{timestamp}_{unique_id}',
                    'item': f'Fee optimization test at {datetime.now().isoformat()}'
                }
            )
        
        # Pass the call generator function
        optimal_fee = sdk.get_optimal_fee_multiplier(
            call_generator_func=create_optimization_call,
            target_confirmation_time=30.0
        )
        print(f"Recommended fee multiplier: {optimal_fee}")
    except Exception as e:
        print(f"Fee optimization failed: {type(e).__name__}: {e}")

def demonstrate_storage_batch_operations():
    """Demonstrate storage-specific batch operations."""
    print("\n=== Storage Batch Operations Demo ===")
    
    sdk = Main.create_instance(SUBSTRATE_URL, ChainType.SUBSTRATE, SEED)
    
    # Generate unique product data
    timestamp = get_timestamp()
    store_id = get_unique_id()
    
    # Batch add items with unique identifiers
    items_to_add = [
        (f"product_{store_id}_laptop_{timestamp}", {
            "name": "Laptop",
            "price": 999,
            "store_id": store_id,
            "created_at": datetime.now().isoformat()
        }),
        (f"product_{store_id}_mouse_{timestamp}", {
            "name": "Mouse",
            "price": 25,
            "store_id": store_id,
            "created_at": datetime.now().isoformat()
        }),
        (f"product_{store_id}_keyboard_{timestamp}", {
            "name": "Keyboard",
            "price": 75,
            "store_id": store_id,
            "created_at": datetime.now().isoformat()
        })
    ]
    
    print("1. Adding items in batch...")
    try:
        add_result = sdk.storage.add_items_batch(items_to_add)
        print(f"Add batch result: {add_result.message}")
        
        # Extract item types for future operations
        item_types = [item[0] for item in items_to_add]
        
    except Exception as e:
        print(f"Batch add failed: {e}")
        return  # Exit if add failed
    
    # Batch get items
    print("\n2. Getting items in batch...")
    try:
        get_results = sdk.storage.get_items_batch(item_types)
        
        for i, result in enumerate(get_results):
            if isinstance(result, dict):  # Success
                print(f"  {item_types[i]}: Found")
            else:  # Error
                print(f"  {item_types[i]}: Error - {result}")
    except Exception as e:
        print(f"Batch get failed: {e}")
    
    # Batch update items with new unique data
    time.sleep(1)
    update_timestamp = get_timestamp()
    
    items_to_update = [
        (item_types[0], {
            "name": "Gaming Laptop",
            "price": 1299,
            "store_id": store_id,
            "updated_at": datetime.now().isoformat(),
            "version": 2
        }),
        (item_types[1], {
            "name": "Gaming Mouse", 
            "price": 45,
            "store_id": store_id,
            "updated_at": datetime.now().isoformat(),
            "version": 2
        })
    ]
    
    print("\n3. Updating items atomically...")
    try:
        update_result = sdk.storage.update_items_atomic(items_to_update)
        print(f"Atomic update result: {update_result.message}")
    except Exception as e:
        print(f"Atomic update failed: {e}")
    
    # Batch remove items (remove the updated ones)
    print("\n4. Removing items atomically...")
    try:
        items_to_remove = [item_types[1], item_types[2]]  # Remove mouse and keyboard
        remove_result = sdk.storage.remove_items_atomic(items_to_remove)
        print(f"Atomic remove result: {remove_result.message}")
    except Exception as e:
        print(f"Atomic remove failed: {e}")

def demonstrate_advanced_configurations():
    """Demonstrate advanced transaction configurations."""
    print("\n=== Advanced Configurations Demo ===")
    
    sdk = Main.create_instance(SUBSTRATE_URL, ChainType.SUBSTRATE, SEED)
    
    # Custom transaction config
    custom_config = TransactionConfig(
        mode=ConfirmationMode.BALANCED,
        fee_multiplier=2.0,
        max_retries=10,
        timeout_seconds=300
    )
    
    # Generate unique data for custom config test
    timestamp = get_timestamp()
    config_id = get_unique_id()
    
    print("1. Using custom transaction configuration...")
    call = sdk.api.compose_call(
        call_module="PeaqStorage",
        call_function="add_item",
        call_params={
            'item_type': f'custom_config_test_{timestamp}_{config_id}',
            'item': f'Custom config test data at {datetime.now().isoformat()}'
        }
    )
    
    try:
        receipt = sdk.send_transaction(call, custom_config)
        print(f"Custom config tx: {receipt.tx_hash}")
        print(f"Success: {receipt.success}")
    except Exception as e:
        print(f"Custom config failed: {e}")
    
    # Custom batch config with unique data
    custom_batch_config = BatchConfig(
        batch_mode=BatchMode.ATOMIC,
        transaction_config=custom_config,
        max_batch_size=50
    )
    
    time.sleep(1)
    batch_timestamp = get_timestamp()
    batch_config_id = get_unique_id()
    
    print("\n2. Using custom batch configuration...")
    batch_items = [
        (f"batch_item_{batch_timestamp}_{batch_config_id}_1", {
            "data": "custom_batch_data_1",
            "timestamp": batch_timestamp,
            "config_id": batch_config_id
        }),
        (f"batch_item_{batch_timestamp}_{batch_config_id}_2", {
            "data": "custom_batch_data_2",
            "timestamp": batch_timestamp,
            "config_id": batch_config_id
        }),
        (f"batch_item_{batch_timestamp}_{batch_config_id}_3", {
            "data": "custom_batch_data_3",
            "timestamp": batch_timestamp,
            "config_id": batch_config_id
        })
    ]
    
    try:
        batch_result = sdk.storage.add_items_batch(batch_items, custom_batch_config)
        print(f"Custom batch result: {batch_result.message}")
    except Exception as e:
        print(f"Custom batch failed: {e}")

def main():
    """Run all demonstrations."""
    print("Peaq SDK Enhanced Transaction Handling Demo")
    print("=" * 50)
    
    try:
        # demonstrate_transaction_modes()
        # demonstrate_batch_modes()
        demonstrate_fee_optimization()
        # demonstrate_storage_batch_operations()
        # demonstrate_advanced_configurations()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        print("Please check your configuration and network connection.")

if __name__ == "__main__":
    # Note: Replace SEED with your actual mnemonic before running
    if SEED == "your_12_or_24_word_mnemonic_here":
        print("Please set your actual mnemonic in the SEED variable before running this example.")
    else:
        main() 