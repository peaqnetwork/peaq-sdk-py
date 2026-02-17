# import os
# from decimal import Decimal

# import pytest
# from eth_abi import encode
# from eth_account.signers.base import BaseAccount
# from web3 import Web3

# from peaq_sdk import Sdk
# from peaq_sdk.types.common import ChainType, BuiltEvmTransactionResult
# from peaq_sdk.types.transfer import PayFunctionSignatures

# from tests.helpers.config import EVM_CASES


# def _receipt_status(receipt) -> int:
#     return receipt.get("status", 1) if isinstance(receipt, dict) else getattr(receipt, "status", 1)


# def _network_env(label: str, key_suffix: str) -> str | None:
#     """
#     Resolve env var by chain label first, then generic fallback.
#     Example for `peaq` + `ERC20_ADDRESS`:
#       - PEAQ_ERC20_ADDRESS
#       - ERC20_ADDRESS
#     """
#     return os.getenv(f"{label.upper()}_{key_suffix}") or os.getenv(key_suffix)


# def _signed_transfer_tests_enabled() -> bool:
#     return os.getenv("RUN_SIGNED_TRANSFER_TESTS", "").strip().lower() in {"1", "true", "yes"}


# def _erc20_selector(api: Web3) -> str:
#     return "0x" + api.keccak(text=PayFunctionSignatures.ERC_20_TRANSFER.value)[:4].hex()


# def _erc721_selector(api: Web3) -> str:
#     return "0x" + api.keccak(text=PayFunctionSignatures.ERC_721_SAFE_TRANSFER_FROM.value)[:4].hex()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
# @pytest.mark.parametrize(
#     "amount",
#     [
#         1,
#         "0.5",
#         Decimal("0.000000000001"),
#     ],
# )
# async def test_transfer_native_build_unsigned_tx_various_amount_types(
#     label: str,
#     base_url: str,
#     account: BaseAccount | None,
#     amount,
# ):
#     if not base_url:
#         pytest.skip("EVM env not configured")

#     sdk = await Sdk.create_instance({
#         "base_url": base_url,
#         "chain_type": ChainType.EVM,
#     })

#     recipient = "0x9999999999999999999999999999999999999999"
#     built = await sdk.transfer.native({
#         "to": recipient,
#         "amount": amount,
#     })
#     assert isinstance(built.tx, dict)
#     assert Web3.to_checksum_address(built.tx["to"]) == Web3.to_checksum_address(recipient)
#     expected_raw = int(Decimal(str(amount)) * (Decimal(10) ** 18))
#     assert built.tx["value"] == expected_raw

#     await sdk.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
# @pytest.mark.parametrize("amount", ["0.000000000001", "0.000000000002"])
# async def test_transfer_native_signed_smoke_if_enabled(
#     label: str,
#     base_url: str,
#     account: BaseAccount | None,
#     amount: str,
# ):
#     if not _signed_transfer_tests_enabled():
#         pytest.skip("Signed transfer tests disabled (set RUN_SIGNED_TRANSFER_TESTS=1)")
#     if not base_url or not account:
#         pytest.skip("EVM env not configured")

#     sdk = await Sdk.create_instance({
#         "base_url": base_url,
#         "chain_type": ChainType.EVM,
#         "auth": account,
#     })

#     res = await sdk.transfer.native({
#         "to": account.address,
#         "amount": amount,
#     })
#     assert _receipt_status(res.receipt) == 1

#     await sdk.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
# @pytest.mark.parametrize(
#     "amount,token_decimals",
#     [
#         ("1", None),
#         ("1.25", 6),
#         (Decimal("0.000000000000000123"), 18),
#     ],
# )
# async def test_transfer_erc20_build_unsigned_tx_various_amounts(
#     label: str,
#     base_url: str,
#     account: BaseAccount | None,
#     amount,
#     token_decimals,
# ):
#     if not base_url:
#         pytest.skip("EVM env not configured")

#     sdk = await Sdk.create_instance({
#         "base_url": base_url,
#         "chain_type": ChainType.EVM,
#     })

#     erc20_address = "0x1111111111111111111111111111111111111111"
#     recipient_address = "0x2222222222222222222222222222222222222222"
#     opts = {
#         "erc_20_address": erc20_address,
#         "recipient_address": recipient_address,
#         "amount": amount,
#     }
#     if token_decimals is not None:
#         opts["token_decimals"] = token_decimals

#     built = await sdk.transfer.erc20(opts)
#     assert isinstance(built.tx, dict)
#     assert Web3.to_checksum_address(built.tx["to"]) == Web3.to_checksum_address(erc20_address)

#     decimals = 18 if token_decimals is None else int(token_decimals)
#     raw_amount = int(Decimal(str(amount)) * (Decimal(10) ** decimals))
#     expected_data = _erc20_selector(sdk.api) + encode(
#         ["address", "uint256"],
#         [recipient_address, raw_amount],
#     ).hex()
#     assert built.tx["data"] == expected_data

#     await sdk.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
# @pytest.mark.parametrize("token_id", [1, 42, 999999])
# async def test_transfer_erc721_build_unsigned_tx_various_token_ids(
#     label: str,
#     base_url: str,
#     account: BaseAccount | None,
#     token_id: int,
# ):
#     if not base_url:
#         pytest.skip("EVM env not configured")

#     sdk = await Sdk.create_instance({
#         "base_url": base_url,
#         "chain_type": ChainType.EVM,
#     })

#     erc721_address = "0x3333333333333333333333333333333333333333"
#     recipient_address = "0x4444444444444444444444444444444444444444"
#     sender_address = "0x5555555555555555555555555555555555555555"

#     # Transfer uses signer address as `from`; set a deterministic value.
#     sdk.transfer.metadata.pair = type("PairStub", (), {"address": sender_address})()
#     # Bypass send path to keep this deterministic and offline.
#     async def _fake_handle_evm_tx(tx, action, status_callback=None, tx_options=None):
#         return BuiltEvmTransactionResult(
#             message=f"Constructed {action} tx (unsigned).",
#             tx=tx,
#         )
#     sdk.transfer._handle_evm_tx = _fake_handle_evm_tx

#     built = await sdk.transfer.erc721({
#         "erc_721_address": erc721_address,
#         "recipient_address": recipient_address,
#         "token_id": token_id,
#     })
#     assert isinstance(built.tx, dict)
#     assert Web3.to_checksum_address(built.tx["to"]) == Web3.to_checksum_address(erc721_address)

#     expected_data = _erc721_selector(sdk.api) + encode(
#         ["address", "address", "uint256"],
#         [sender_address, recipient_address, token_id],
#     ).hex()
#     assert built.tx["data"] == expected_data

#     await sdk.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
# async def test_transfer_erc20_signed_smoke_if_configured(label: str, base_url: str, account: BaseAccount | None):
#     if not _signed_transfer_tests_enabled():
#         pytest.skip("Signed transfer tests disabled (set RUN_SIGNED_TRANSFER_TESTS=1)")
#     if not base_url or not account:
#         pytest.skip("EVM env not configured")

#     erc20_address = _network_env(label, "ERC20_ADDRESS")
#     if not erc20_address:
#         pytest.skip("ERC20 contract not configured (set <NETWORK>_ERC20_ADDRESS)")

#     recipient = _network_env(label, "ERC20_RECIPIENT") or account.address
#     decimals = int(_network_env(label, "ERC20_DECIMALS") or "18")
#     amount = _network_env(label, "ERC20_AMOUNT") or "0.000001"

#     sdk = await Sdk.create_instance({
#         "base_url": base_url,
#         "chain_type": ChainType.EVM,
#         "auth": account,
#     })

#     res = await sdk.transfer.erc20({
#         "erc_20_address": erc20_address,
#         "recipient_address": recipient,
#         "amount": amount,
#         "token_decimals": decimals,
#     })
#     assert _receipt_status(res.receipt) == 1

#     await sdk.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.parametrize("label,base_url,account", EVM_CASES, ids=[c[0] for c in EVM_CASES])
# async def test_transfer_erc721_signed_smoke_if_configured(label: str, base_url: str, account: BaseAccount | None):
#     if not _signed_transfer_tests_enabled():
#         pytest.skip("Signed transfer tests disabled (set RUN_SIGNED_TRANSFER_TESTS=1)")
#     if not base_url or not account:
#         pytest.skip("EVM env not configured")

#     erc721_address = _network_env(label, "ERC721_ADDRESS")
#     token_id_raw = _network_env(label, "ERC721_TOKEN_ID")
#     if not erc721_address or token_id_raw is None:
#         pytest.skip("ERC721 test not configured (set <NETWORK>_ERC721_ADDRESS and <NETWORK>_ERC721_TOKEN_ID)")

#     recipient = _network_env(label, "ERC721_RECIPIENT") or account.address
#     token_id = int(token_id_raw)

#     sdk = await Sdk.create_instance({
#         "base_url": base_url,
#         "chain_type": ChainType.EVM,
#         "auth": account,
#     })

#     res = await sdk.transfer.erc721({
#         "erc_721_address": erc721_address,
#         "recipient_address": recipient,
#         "token_id": token_id,
#     })
#     assert _receipt_status(res.receipt) == 1

#     await sdk.disconnect()
