# import pytest
# from peaq_sdk.types.did import CustomDocumentFields,, Verification

# @pytest.mark.skip(reason="Skip")
# def test_create_minimal_did(substrate_sdk):
#     # arrange
#     name = "did_test"
#     custom_fields = CustomDocumentFields(
#         verifications=[Verification(type="wrong")]
#     )

#     # act
#     result: CreateDidResult = substrate_sdk.did.create(name, custom_fields)

    # # assert
    # assert isinstance(result.did, str)
    # assert result.did.startswith("did:peaq:")
    # # maybe round‐trip:
    # parsed = substrate_sdk.did._deserialize_did(bytes.fromhex(result.did))
    # assert parsed.id == result.did

# add more tests…
