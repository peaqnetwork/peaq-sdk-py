import hashlib
import base58
from pydantic import ValidationError
from substrateinterface.utils.ss58 import ss58_decode


class CreateStorageKeysEnum:
    """
    Mirrors the JS SDK CreateStorageKeysEnum.
    ADDRESS: decode ss58 address into bytes
    STANDARD: UTF-8 bytes of a string
    """
    ADDRESS = "ADDRESS"
    STANDARD = "STANDARD"


def create_storage_keys(args, ss58_format: int = 42) -> dict:
    """
    Python equivalent of JS `createStorageKeys`:

    - ADDRESS: decodeAddress(value, false, ss58_format) -> bytes
    - STANDARD: u8aToU8a(value) -> UTF-8 bytes
    - Concatenate and blake2_256 hash -> hex key

    Returns:
        { "hashed_key": "0x..." }
    """
    keys_byte_array = []

    for item in args:
        t = item.get("type")
        v = item.get("value")
        if t == CreateStorageKeysEnum.ADDRESS:
            # ss58_decode returns hex string (accountId) for substrateinterface
            decoded = ss58_decode(v, valid_ss58_format=ss58_format)
            decoded_bytes = bytes.fromhex(decoded) if isinstance(decoded, str) else bytes(decoded)
            keys_byte_array.append(decoded_bytes)
        elif t == CreateStorageKeysEnum.STANDARD:
            if isinstance(v, bytes):
                keys_byte_array.append(v)
            else:
                keys_byte_array.append(str(v).encode("utf-8"))
        else:
            raise ValueError(f"Unsupported storage key type: {t}")

    key = u8a_concat(*keys_byte_array)
    hashed_key = blake2b_256(key).hex()
    return {"hashed_key": "0x" + hashed_key}

def blake2b_256(data):
    """
    Compute the Blake2b-256 hash of the given data.
    """
    return hashlib.blake2b(data, digest_size=32).digest()

def u8a_concat(*args):
    """
    Concatenate multiple byte arrays into one.
    """
    return b"".join(args)

def hasher(hash_type, data):
    """
    Hash the data using the specified hash type.
    Args:
        hash_type (str): The hash algorithm to use ('blake2' or 'keccak').
        data (bytes): The data to hash.
    Returns:
        bytes: The hashed data.
    """
    if hash_type == "keccak":
        return hashlib.new("keccak256", data).digest()
    elif hash_type == "blake2":
        return blake2b_256(data)
    else:
        raise ValueError(f"Unsupported hash type: {hash_type}")

def encode_address(public_key, ss58_format):
    """
    Encode a public key into SS58 format.
    Args:
        public_key (bytes): The public key or hashed address.
        ss58_format (int): The SS58 prefix (e.g., 42 for testnet).
    Returns:
        str: The SS58 address.
    """
    # SS58 prefix
    ss58_prefix = b"SS58PRE"
    # Concatenate the format byte with the public key
    payload = bytes([ss58_format]) + public_key
    # Compute the checksum
    checksum = hashlib.blake2b(ss58_prefix + payload, digest_size=64).digest()[:2]
    # Concatenate the payload and checksum
    full_payload = payload + checksum
    # Encode the result into Base58
    return base58.b58encode(full_payload).decode("utf-8")

def evm_to_address(evm_address, ss58_format=42, hash_type="blake2"):
    """
    Converts an EVM address to its corresponding SS58 address.
    Args:
        evm_address (str | bytes): The EVM address (20 bytes).
        ss58_format (int): The SS58 prefix (default is 42 for testnet).
        hash_type (str): The hash algorithm to use ('blake2' or 'keccak').
    Returns:
        str: The SS58 address.
    """
    if isinstance(evm_address, str):
        # Remove the '0x' prefix if present and convert to bytes
        if evm_address.startswith("0x"):
            evm_address = bytes.fromhex(evm_address[2:])
        else:
            evm_address = bytes.fromhex(evm_address)

    # Ensure the length of the address is 20 bytes
    if len(evm_address) != 20:
        raise ValueError(f"Invalid EVM address length: {len(evm_address)}")

    # Concatenate "evm:" with the address
    message = u8a_concat(b"evm:", evm_address)

    # Hash the concatenated message
    hashed_message = hasher(hash_type, message)

    # Encode the hashed message as an SS58 address
    return encode_address(hashed_message, ss58_format)

def parse_options(cls, options: dict, caller: str = "function"):
    try:
        return cls(**options)
    except ValidationError as e:
        missing = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
        if missing:
            raise ValueError(f"{caller}(): missing required field(s): {', '.join(missing)}") from None
        raise