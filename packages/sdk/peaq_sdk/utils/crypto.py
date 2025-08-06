"""
Cryptography utilities for the Peaq SDK.
Provides helpers for working with public keys, multibase encoding, and address derivation.
"""

import base58
import varint
import base58
from substrateinterface.utils.ss58 import ss58_decode, ss58_encode
from web3 import Web3
from eth_account import Account
from eth_keys import keys


def generate_evm_public_key_multibase(wallet) -> str:
    """
    Given an EVM wallet/signer with a signing key,
    returns the secp256k1 publicKeyMultibase (z…).
    
    Args:
        wallet: EVM wallet/signer object with signingKey or _key_obj attribute
        
    Returns:
        str: The multibase-encoded public key starting with 'z'
        
    Raises:
        ValueError: If no signing key is available
    """
    if not hasattr(wallet, '_key_obj'):
        raise ValueError(
            "EVM signer required for ECDSA multibase generation. "
            "Please provide a wallet with a signing key."
        )
    
    # Get compressed public key from the signer
    compressed_pub_key = wallet._key_obj.public_key.to_compressed_bytes()
    
    # Multicodec prefix for secp256k1-pub ([0xe7, 0x01])
    prefix = bytes([0xE7, 0x01])
    
    # Concatenate prefix + key bytes
    full = prefix + compressed_pub_key
    
    # Base58-btc encode and prepend 'z'
    multibase = "z" + base58.b58encode(full).decode()
    return multibase


def generate_ed25519_public_key_multibase(address: str) -> str:
    """
    Given a Substrate SS58 address, returns the Ed25519 publicKeyMultibase (z…).
    
    Args:
        address (str): SS58 address
        
    Returns:
        str: The multibase-encoded public key starting with 'z'
    """
    # Decode SS58 address to get raw 32-byte public key
    decoded_hex = ss58_decode(address)
    public_key = bytes.fromhex(decoded_hex)
    
    # Varint-encode the multicodec prefix for ed25519 (0xed)
    prefix = varint.encode(0xed)
    
    # Concatenate prefix + public key
    prefixed_key = prefix + public_key
    
    # Base58-btc encode + 'z' prefix
    multibase = 'z' + base58.b58encode(prefixed_key).decode()
    return multibase


def generate_sr25519_public_key_multibase(address: str) -> str:
    """
    Given a Substrate SS58 address, returns the Sr25519 publicKeyMultibase (z…).
    
    Args:
        address (str): SS58 address
        
    Returns:
        str: The multibase-encoded public key starting with 'z'
    """
    # Decode SS58 address to get raw 32-byte public key
    decoded_hex = ss58_decode(address)
    public_key = bytes.fromhex(decoded_hex)
    
    # Varint-encode the multicodec prefix for sr25519 (0xef)
    prefix = varint.encode(0xef)
    
    # Concatenate prefix + public key
    prefixed_key = prefix + public_key
    
    # Base58-btc encode + 'z' prefix
    multibase = 'z' + base58.b58encode(prefixed_key).decode()
    return multibase


def evm_address_from_public_key_multibase(multibase: str) -> str:
    """
    Given a secp256k1 publicKeyMultibase string (z…),
    returns the canonical Ethereum address (0x…).
    
    Args:
        multibase (str): The multibase string starting with 'z'
        
    Returns:
        str: The EVM address (0x...)
        
    Raises:
        ValueError: If the multibase format is invalid
    """
    if not multibase.startswith('z'):
        raise ValueError("Multibase must start with 'z'")
    
    # Strip 'z' and Base58-decode
    raw = base58.b58decode(multibase[1:])
    
    # Drop the 2-byte multicodec prefix ([0xe7,0x01])
    compressed_pubkey = raw[2:]  # bytes, length 33
    
    # Recover the Ethereum address
    pubkey_obj = keys.PublicKey.from_compressed_bytes(compressed_pubkey)
    eth_address = pubkey_obj.to_checksum_address()
    return eth_address


def substrate_address_from_public_key_multibase(multibase: str, ss58_prefix: int = 42) -> str:
    """
    Given an Ed25519 or Sr25519 publicKeyMultibase string (z…),
    returns the canonical SS58 address.
    
    Args:
        multibase (str): The multibase string starting with 'z'
        ss58_prefix (int): SS58 format prefix (default: 42 for generic substrate)
        
    Returns:
        str: The SS58 address
        
    Raises:
        ValueError: If the multibase format is invalid
    """
    if not multibase.startswith('z'):
        raise ValueError("Multibase must start with 'z'")
    
    # Strip 'z' and decode base58
    decoded = base58.b58decode(multibase[1:])
    
    # Remove the 2-byte multicodec prefix
    public_key = decoded[2:]  # Should be 32 bytes
    
    # Encode to SS58 address format
    ss58_address = ss58_encode(public_key.hex(), ss58_format=ss58_prefix)
    return ss58_address


class Crypto:
    """
    Cryptography utilities for the Peaq SDK.
    Provides helpers for working with public keys, multibase encoding, and address derivation.
    """
    
    @staticmethod
    def generate_evm_public_key_multibase(wallet) -> str:
        """Generate EVM public key multibase from wallet"""
        return generate_evm_public_key_multibase(wallet)
    
    @staticmethod
    def generate_ed25519_public_key_multibase(address: str) -> str:
        """Generate Ed25519 public key multibase from SS58 address"""
        return generate_ed25519_public_key_multibase(address)
    
    @staticmethod
    def generate_sr25519_public_key_multibase(address: str) -> str:
        """Generate Sr25519 public key multibase from SS58 address"""
        return generate_sr25519_public_key_multibase(address)
    
    @staticmethod
    def evm_address_from_public_key_multibase(multibase: str) -> str:
        """Derive EVM address from public key multibase"""
        return evm_address_from_public_key_multibase(multibase)
    
    @staticmethod
    def substrate_address_from_public_key_multibase(multibase: str, ss58_prefix: int = 42) -> str:
        """Derive Substrate SS58 address from public key multibase"""
        return substrate_address_from_public_key_multibase(multibase, ss58_prefix)