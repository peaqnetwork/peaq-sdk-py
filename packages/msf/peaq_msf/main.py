"""
MSF Main class - Simplified interface for Machine Station Factory operations
"""

from typing import Union, Optional
from peaq_msf import Main as SDKMain
from peaq_msf.types.common import ChainType
from eth_account.signers.base import BaseAccount

from .machine_station import MachineStation


class Main:
    """
    MSF SDK Main class providing simplified machine station operations.
    
    This is a wrapper around the core SDK that focuses specifically on
    Machine Station Factory functionality with a flattened API.
    """
    
    def __init__(self, sdk_instance: SDKMain):
        """
        Initialize MSF Main with an SDK instance.
        
        Args:
            sdk_instance: Core SDK instance
        """
        self._sdk = sdk_instance
        self._machine_station = MachineStation(sdk_instance)
    
    @classmethod
    def create_instance(
        cls,
        base_url: str,
        chain_type: ChainType,
        auth: Union[BaseAccount]
    ) -> "Main":
        """
        Create a new MSF SDK instance.
        
        Args:
            base_url: Blockchain RPC URL
            chain_type: EVM or Substrate chain type
            auth: Account or Keypair for signing
            
        Returns:
            Main: MSF SDK instance
        """
        sdk_instance = SDKMain.create_instance(
            base_url=base_url,
            chain_type=chain_type,
            auth=auth
        )
        return cls(sdk_instance)
    
    # Expose machine station methods directly (flattened API)
    def update_configs(self, key: str, value: str, status_callback=None, tx_options=None):
        """Update machine station configurations."""
        return self._machine_station.update_configs(key, value, status_callback, tx_options)
    
    def deploy_machine_smart_account(self, machine_address: str, status_callback=None, tx_options=None):
        """Deploy a machine smart account."""
        return self._machine_station.deploy_machine_smart_account(machine_address, status_callback, tx_options)
    
    def execute_transfer_machine_station_balance(self, machine_address: str, amount: int, status_callback=None, tx_options=None):
        """Execute transfer of machine station balance."""
        return self._machine_station.execute_transfer_machine_station_balance(machine_address, amount, status_callback, tx_options)
    
    def execute_transaction(self, machine_address: str, target: str, value: int, calldata: str, status_callback=None, tx_options=None):
        """Execute a transaction through machine station."""
        return self._machine_station.execute_transaction(machine_address, target, value, calldata, status_callback, tx_options)
    
    def execute_machine_transaction(self, machine_address: str, target: str, value: int, calldata: str, status_callback=None, tx_options=None):
        """Execute a machine transaction."""
        return self._machine_station.execute_machine_transaction(machine_address, target, value, calldata, status_callback, tx_options)
    
    def execute_machine_batch_transactions(self, machine_address: str, targets: list, values: list, calldata: list, status_callback=None, tx_options=None):
        """Execute batch machine transactions."""
        return self._machine_station.execute_machine_batch_transactions(machine_address, targets, values, calldata, status_callback, tx_options)
    
    def execute_transfer_machine_balance(self, machine_address: str, target: str, amount: int, status_callback=None, tx_options=None):
        """Execute transfer of machine balance."""
        return self._machine_station.execute_transfer_machine_balance(machine_address, target, amount, status_callback, tx_options)
    
    def admin_sign_machine_transaction(self, machine_address: str, target: str, calldata: str, nonce: int, refund_amount: int = 0):
        """Admin sign machine transaction - returns signature for off-chain use."""
        return self._machine_station.admin_sign_machine_transaction(machine_address, target, calldata, nonce, refund_amount)
    
    # Expose read methods
    def get_machine_nonce(self, machine_address: str):
        """Get machine transaction nonce."""
        return self._machine_station.get_machine_nonce(machine_address)
    
    def get_machine_smart_account_address(self, machine_address: str):
        """Get machine smart account address."""
        return self._machine_station.get_machine_smart_account_address(machine_address)
    
    def get_machine_station_balance(self, machine_address: str):
        """Get machine station balance."""
        return self._machine_station.get_machine_station_balance(machine_address)
    
    def get_configs(self, key: str):
        """Get machine station configuration."""
        return self._machine_station.get_configs(key)
    
    # Expose SDK properties for advanced usage
    @property
    def sdk(self) -> SDKMain:
        """Access to underlying SDK instance."""
        return self._sdk
    
    @property
    def machine_station(self) -> MachineStation:
        """Access to machine station module (for backward compatibility)."""
        return self._machine_station