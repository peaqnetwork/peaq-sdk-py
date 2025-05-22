from enum import Enum


class TokenFunctionSignatures(str, Enum):
    TRANSFER_TO_ACCOUNT_ID = "transferToAccountId(bytes32,uint256)"