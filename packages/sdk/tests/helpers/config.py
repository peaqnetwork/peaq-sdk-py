import os
from dotenv import load_dotenv
load_dotenv()
from typing import List, Tuple, Optional

from eth_account import Account
from eth_account.signers.base import BaseAccount



# Returns list of tuples: (label, base_url, account)
def build_evm_cases() -> List[Tuple[str, str, BaseAccount]]:
    evm_private = os.getenv("EVM_PRIVATE", "")
    if not evm_private:
        return []
    account: BaseAccount = Account.from_key(evm_private)

    cases: List[Tuple[str, str, BaseAccount]] = []
    peaq_https = os.getenv("PEAQ_HTTPS")
    agung_https = os.getenv("AGUNG_HTTPS")
    if peaq_https:
        cases.append(("peaq", peaq_https, account))
    if agung_https:
        cases.append(("agung", agung_https, account))
    return cases

# Exported cases for tests to consume
EVM_CASES: List[Tuple[str, str, BaseAccount]] = build_evm_cases() or [("skipped", "", None)]  # type: ignore