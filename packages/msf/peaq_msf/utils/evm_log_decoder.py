from __future__ import annotations
import json, os
from typing import Dict, List, Any, Optional, Tuple, Union

from web3 import Web3
from web3._utils.events import get_event_data
from eth_utils import event_abi_to_log_topic
from hexbytes import HexBytes

Hexish = Union[str, bytes, bytearray, HexBytes, int]


def _to_hex(x: Hexish | None) -> str:
    """Return a 0x-prefixed hex string for common types."""
    if x is None:
        return "0x"
    if isinstance(x, str):
        return x if x.startswith("0x") else "0x" + x
    if isinstance(x, HexBytes):
        return x.hex()                          # already 0x-prefixed
    if isinstance(x, (bytes, bytearray)):
        return "0x" + x.hex()
    if isinstance(x, int):
        return hex(x)                           # 0x-prefixed
    # Fallback: try web3
    try:
        return Web3.to_hex(x)                   # may raise if unsupported
    except Exception as e:
        raise TypeError(f"Cannot hex-encode value of type {type(x)}: {x!r}") from e

def _normalize_log(raw: dict) -> dict:
    # topics & data as hex strings
    topics_raw = raw.get("topics", [])
    topics = [_to_hex(t) for t in topics_raw]
    data = _to_hex(raw.get("data", "0x"))

    # addresses/hashes might be bytes/HexBytes; normalize before checksum
    addr_hex = _to_hex(raw["address"])
    txh_hex = _to_hex(raw["transactionHash"])
    blkh_hex = _to_hex(raw["blockHash"])

    return {
        "address": Web3.to_checksum_address(addr_hex),
        "topics": topics,
        "data": data,
        "blockNumber": int(raw["blockNumber"]),
        "transactionHash": txh_hex,
        "transactionIndex": int(raw["transactionIndex"]),
        "blockHash": blkh_hex,
        "logIndex": int(raw["logIndex"]),
        "removed": bool(raw.get("removed", False)),
    }

class MultiAbiLogDecoder:
    def __init__(self, w3: Web3):
        self.w3 = w3
        self._abis_by_addr: Dict[Optional[str], List[dict]] = {}
        self._topic_index: Dict[str, List[Tuple[Optional[str], dict]]] = {}
        self._contracts: Dict[str, Any] = {}

    def register_abi(self, abi: List[dict], address: Optional[str] = None):
        addr_norm = Web3.to_checksum_address(address) if address else None
        self._abis_by_addr.setdefault(addr_norm, []).extend(abi)

        for entry in abi:
            if entry.get("type") == "event" and not entry.get("anonymous", False):
                topic0 = event_abi_to_log_topic(entry).hex()
                self._topic_index.setdefault(topic0, []).append((addr_norm, entry))

        if addr_norm:
            self._contracts[addr_norm] = self.w3.eth.contract(address=addr_norm, abi=abi)

    def decode_receipt(self, receipt: dict) -> List[dict]:
        out: List[dict] = []
        for raw_log in receipt.get("logs", []):
            try:
                log = _normalize_log(raw_log)
            except Exception:
                # Skip logs we cannot normalize
                continue

            if not log["topics"]:
                # Anonymous events cannot be matched; skip quietly
                continue

            topic0 = log["topics"][0]
            candidates = self._topic_index.get(topic0, [])

            addr = log["address"]
            prioritized = [(a, e) for (a, e) in candidates if a == addr]
            global_matches = [(a, e) for (a, e) in candidates if a is None]
            try_order = prioritized + global_matches

            decoded = None
            for (_a, event_abi) in try_order:
                try:
                    evt = get_event_data(self.w3.codec, event_abi, log)
                    name = evt.get("event")
                    # Only include failure-related events
                    if isinstance(name, str) and ("fail" in name.lower()):
                        decoded = {
                            "address": log["address"],
                            "name": name,
                            "events": dict(evt["args"]),
                            "logIndex": evt["logIndex"],
                        }
                        out.append(decoded)
                    # Regardless of inclusion, stop trying other ABIs once decoded
                    break
                except Exception:
                    continue

        return out