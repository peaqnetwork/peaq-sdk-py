from typing import Optional, Union

from peaq_sdk.base import Base
from peaq_sdk.types.common import (
    ChainType,
    SDKMetadata,
    SeedError,
    CallModule,
    PrecompileAddresses,
    WrittenTransactionResult,
    BuiltEvmTransactionResult,
    BuiltCallTransactionResult,
    BaseUrlError
)
from peaq_sdk.types.did import (
    CustomDocumentFields, 
    Verification,
    Signature,
    Service,
    DidFunctionSignatures,
    DidCallFunction,
    ReadDidResult,
    GetDidError
)
from peaq_sdk.utils import peaq_proto
from peaq_sdk.utils.utils import evm_to_address

from substrateinterface.base import SubstrateInterface
from substrateinterface.utils.ss58 import ss58_decode
from web3 import Web3
from web3.types import TxParams
from eth_abi import encode
from google.protobuf.json_format import MessageToDict
import varint
import base58

class Did(Base):
    """
    Provides methods to interact with the peaq on-chain DID precompile (EVM)
    or pallet (Substrate). Supports add, get, update, and remove operations.
    """
    def __init__(self, api: Web3 | SubstrateInterface, metadata: SDKMetadata) -> None:
        """
        Initializes DID with a connected API instance and shared SDK metadata.

        Args:
            api (Web3 | SubstrateInterface): The blockchain API connection.
                which may be a Web3 (EVM) or SubstrateInterface (Substrate).
            metadata (SDKMetadata): Shared metadata, including chain type,
                and optional signer.
        """
        super().__init__(api, metadata)
        
    def create(self, name: str, custom_document_fields: CustomDocumentFields, address: Optional[str] = None) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Creates a new Decentralized Identifier (DID) on-chain with the specified `name`
        and `custom_document_fields`.

        - EVM: Constructs a transaction to the `addAttribute` DID precompile contract.
        - Substrate: Composes an `add_attribute` extrinsic to the peaqDid
            pallet.

        Args:
            name (str): The name or alias of the DID.
            custom_document_fields (CustomDocumentFields): Additional fields/claims to embed
                in the DID document.
            address (Optional[str]): An optional address if no local keypair is present.
                On EVM, this should be an H160 address. On Substrate, a SS58 address.

        Returns:
            Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
                - WrittenTransactionResult: The transaction or extrinsic was signed and broadcasted.
                    Returned with a message and receipt.
                - BuiltEvmTransactionResult or BuiltCallTransactionResult: The tx/call was constructed
                    but not signed (no local signer). Returned with message and tx/call.

        Raises:
            TypeError: If `custom_document_fields` is not an instance of `CustomDocumentFields`.
        """
        if not isinstance(custom_document_fields, CustomDocumentFields):
            raise TypeError(
                f"custom_document_fields object must be CustomDocumentFields, "
                f"got {type(custom_document_fields).__name__!r}"
            )

        user_address = self._resolve_address(address=address)
        
        serialized_did = self._generate_did_document(user_address, custom_document_fields)
        
        if self.metadata.chain_type is ChainType.EVM:
            did_function_selector = self.api.keccak(text=DidFunctionSignatures.ADD_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            did_encoded = serialized_did.encode("utf-8").hex()
            encoded_params = encode(
                ['address', 'bytes', 'bytes', 'uint32'],
                [user_address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.metadata.pair and not self.metadata.machine_station:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully added the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID create transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.ADD_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name,
                    'value': serialized_did,
                    'valid_for': None
                    }
            )
            
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully added the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID create call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )
            
            
            
    def read(self, name: str, address: Optional[str] = None) -> ReadDidResult:
        """
        Reads (fetches) an on-chain DID identified by `name`. This method locates
        the DID document stored at `name` for the given user address.

        - EVM: Uses the EVM address (either from a local signer if present, or the
            passed `address` parameter). Because DID data is actually stored in the
            Substrate-based registry, an evm wallet must be converted to a substrate wallet to
            temporarily connect and query the Substrate chain.
        - Substrate: Queries the DID registry directly via the existing Substrate connection
            (`self.api`). The address defaults to the local keypair's SS58 address
            if none is explicitly provided.

        Args:
            name (str): The DID name or label under which the document is stored.
            address (Optional[str]): The address owning the DID. On EVM, this should
                be a H160 address; on Substrate, an SS58 address. If not provided,
                falls back to the local signer's address (if any).


        Returns:
            ReadDidResult:
                An object containing the DID name, on-chain value, validity, creation
                timestamp, and the deserialized DID document.

        Raises:
            TypeError:
                If no valid address can be determined (no local signer and no `address`).
            GetDidError:
                If the DID specified by `name` does not exist on-chain for `address`.
        """
        
        if self.metadata.chain_type is ChainType.EVM:
            evm_address = (
                getattr(self.metadata.pair, 'address', address)
                if self.metadata.pair and not self.metadata.machine_station
                else address
            )
            if not evm_address:
                raise TypeError(f"Address is set to {evm_address}. Please either set seed at instance creation or pass an address.")
            owner_address = evm_to_address(evm_address)
            api = SubstrateInterface(url=self.metadata.base_url, ss58_format=42)
            display_address = evm_address
        else:
            owner_address = (
                getattr(self.metadata.pair, 'ss58_address', address)
                if self.metadata.pair
                else address
            )
            if not owner_address:
                raise TypeError(f"Address is set to {owner_address}. Please either set seed at instance creation or pass an address.")
            api = self.api
            display_address = owner_address
        
        # Query storage
        name_encoded = "0x" + name.encode("utf-8").hex()
        block_hash = api.get_block_hash(None)
        
        resp = api.rpc_request(
            DidCallFunction.READ_ATTRIBUTE.value, [owner_address, name_encoded, block_hash]
        )
        # Check result
        if resp['result'] is None:
            raise GetDidError(f"DID of name {name} was not found at address {display_address}.")

        read_name = bytes.fromhex(resp['result']['name'][2:]).decode('utf-8')
        value = bytes.fromhex(resp['result']['value'][2:]).decode('utf-8')
        to_deserialize = bytes.fromhex(value)
        document = self._deserialize_did(to_deserialize)
        
        return ReadDidResult(
            name=read_name,
            value=value,
            validity=str(resp['result']['validity']),
            created=str(resp['result']['created']),
            document=MessageToDict(document)
        )


    def update(self, name: str, custom_document_fields: CustomDocumentFields, address: Optional[str] = None) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Updates an existing DID identified by `name`, overwriting the entire DID
        document with new `custom_document_fields`. Use caution, as all existing
        data is replaced with the newly provided fields.
        
        - EVM: Constructs a transaction to the `updateAttribute` DID precompile contract.
        - Substrate: Composes an `update_attribute` extrinsic to the peaqDid
            pallet.
        
        Args:
            name (str): The unique DID name or label to update.
            custom_document_fields (CustomDocumentFields): The new fields to
                embed in the DID document. These fully replace the prior document.
            address (Optional[str]): An optional address if no local keypair is present.
                On EVM, this should be an H160 address. On Substrate, a SS58 address.

        Returns:
            Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
                - WrittenTransactionResult: The transaction or extrinsic was signed and broadcasted.
                    Returned with a message and receipt.
                - BuiltEvmTransactionResult or BuiltCallTransactionResult: The tx/call was constructed
                    but not signed (no local signer). Returned with message and tx/call.

        Raises:
            TypeError: If `custom_document_fields` is not an instance of `CustomDocumentFields`.
        """
        if not isinstance(custom_document_fields, CustomDocumentFields):
            raise TypeError(
                f"custom_document_fields object must be CustomDocumentFields, "
                f"got {type(custom_document_fields).__name__!r}"
            )
            
        user_address = self._resolve_address(address=address)
        
        serialized_did = self._generate_did_document(user_address, custom_document_fields)
        
        if self.metadata.chain_type is ChainType.EVM:
            serialized_did = self._generate_did_document(user_address, custom_document_fields)
            did_function_selector = self.api.keccak(text=DidFunctionSignatures.UPDATE_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            did_encoded = serialized_did.encode("utf-8").hex()
            
            encoded_params = encode(
                ['address', 'bytes', 'bytes', 'uint32'],
                [user_address, bytes.fromhex(name_encoded), bytes.fromhex(did_encoded), 0]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.metadata.pair:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully updated the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID update transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.UPDATE_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name,
                    'value': serialized_did,
                    'valid_for': None
                    }
            )
            
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully updated the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID update call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )


    
    def remove(self, name: str, address: Optional[str] = None) -> Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
        """
        Removes an existing on-chain DID identified by `name`. Once removed,
        the DID data is no longer accessible via subsequent reads.
        
        - EVM: Constructs a transaction to the `removeAttribute` DID precompile contract.
        - Substrate: Composes an `remove_attribute` extrinsic to the peaqDid
            pallet.
        
        Args:
            name (str): The DID name or alias to remove from the chain.
            address (Optional[str]): An optional address if no local keypair is present.
                On EVM, this should be an H160 address. On Substrate, a SS58 address.

        Returns:
            Union[WrittenTransactionResult, BuiltEvmTransactionResult, BuiltCallTransactionResult]:
                - WrittenTransactionResult: The transaction or extrinsic was signed and broadcasted.
                    Returned with a message and receipt.
                - BuiltEvmTransactionResult or BuiltCallTransactionResult: The tx/call was constructed
                    but not signed (no local signer). Returned with message and tx/call.
        """
        
        user_address = self._resolve_address(address=address)
        
        if self.metadata.chain_type is ChainType.EVM:
            did_function_selector = self.api.keccak(text=DidFunctionSignatures.REMOVE_ATTRIBUTE.value)[:4].hex()
            name_encoded = name.encode("utf-8").hex()
            encoded_params = encode(
                ['address', 'bytes'],
                [user_address, bytes.fromhex(name_encoded)]
            ).hex()
            
            tx: TxParams = {
                "to": PrecompileAddresses.DID.value,
                "data": f"0x{did_function_selector}{encoded_params}"
            }
            
            if self.metadata.pair and not self.metadata.machine_station:
                receipt = self._send_evm_tx(tx)
                return WrittenTransactionResult(
                    message=f"Successfully removed the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltEvmTransactionResult(
                    message=f"Constructed DID remove transaction for {user_address} of the name {name}. You must sign and send it externally.",
                    tx=tx
                )
                
        else:
            call = self.api.compose_call(
                call_module=CallModule.PEAQ_DID.value,
                call_function=DidCallFunction.REMOVE_ATTRIBUTE.value,
                call_params={
                    'did_account': user_address,
                    'name': name
                    }
            )
            
            if self.metadata.pair:
                receipt = self._send_substrate_tx(call)
                return WrittenTransactionResult(
                    message=f"Successfully removed the DID under the name {name} for user {user_address}.",
                    receipt=receipt
                )
            else:
                return BuiltCallTransactionResult(
                    message=f"Constructed DID remove call for {user_address} of the name {name}. You must sign and send externally.",
                    call=call
                )
    
    
    def _generate_did_document(self, address: str, custom_document_fields: CustomDocumentFields) -> str:
        """
        Constructs and serializes a DID document in Protobuf format based on the
        provided `address` and `custom_document_fields`. The result is returned as
        a hex-encoded string.

        This document includes:
        - `id` and `controller` fields both set to `"did:peaq:{address}"`.
        - Verification methods (and authentications) if present in `custom_document_fields.verifications`.
        - A signature if `custom_document_fields.signature` is set.
        - One or more services if `custom_document_fields.services` is provided.

        Args:
            address (str): The on-chain address (EVM hex or Substrate SS58) representing
                the DID subject.
            custom_document_fields (CustomDocumentFields): Additional fields or claims
                (verification methods, signature, services) to embed into the DID document.

        Returns:
            str: A hex-encoded Protobuf serialization of the DID document.

        Raises:
            ValueError: If a verification type or signature type is invalid for the
                current chain type (checked inside helper methods).
        """
        doc = peaq_proto.Document()
        doc.id = f"did:peaq:{address}"
        doc.controller = f"did:peaq:{address}"
        
        if custom_document_fields.verifications:
            for key_counter, verification in enumerate(custom_document_fields.verifications, start=1):
                id = f"did:peaq:{address}#keys-{key_counter}"
                verification_method = self._create_verification_method(
                    id,
                    address,
                    verification
                )
                doc.verification_methods.append(verification_method)
                doc.authentications.append(id)
            
        if custom_document_fields.signature:
            document_signature = self._add_signature(custom_document_fields.signature)
            doc.signature.CopyFrom(document_signature)

            
        if custom_document_fields.services:
            for service in custom_document_fields.services:
                document_service = self._add_service(service)
                doc.services.append(document_service)
        
        serialized_data = doc.SerializeToString()
        serialized_hex = serialized_data.hex()
        return serialized_hex
    
    def _create_verification_method(self, id: str, address: str, verification: Verification) -> peaq_proto.VerificationMethod:
        """
        Builds a Protobuf `VerificationMethod` from the given `verification`
        object. Enforces certain constraints depending on whether the chain type
        is EVM or Substrate.

        For EVM chains:
        - Only "EcdsaSecp256k1RecoveryMethod2020" is supported.

        For Substrate chains:
        - The `verification.type` must be one of "Ed25519VerificationKey2020",
            "Sr25519VerificationKey2020", or "EcdsaSecp256k1RecoveryMethod2020".

        Args:
            id (str): A string identifier for the verification method,
                typically `"did:peaq:{address}#keys-{N}"`.
            address (str): The address used as controller and public key fallback
                if no `public_key_multibase` is specified in `verification`.
            verification (Verification): Contains details such as the type, potential
                `public_key_multibase`, etc.

        Returns:
            peaq_proto.VerificationMethod: A populated Protobuf verification method.

        Raises:
            ValueError: If the `verification.type` is unsupported for the current chain.
        """
        verification_method = peaq_proto.VerificationMethod()
        verification_method.id = id
        
        if self.metadata.chain_type is ChainType.EVM:
            if verification.type != "EcdsaSecp256k1RecoveryMethod2020":
                raise ValueError(
                    f"EVM only supports EcdsaSecp256k1RecoveryMethod2020, got {verification.type}"
                )
            verification_method.type = verification.type
            verification_method.controller = f"did:peaq:{address}"
            
            # Use provided multibase or generate from signer
            if verification.public_key_multibase:
                verification_method.public_key_multibase = verification.public_key_multibase
            else:
                verification_method.public_key_multibase = address
                # TODO: figure out when public key multibase in btc base58 is required
                # verification_method.public_key_multibase = self._generate_multibase_for_verification(
                #     address, verification.type
                # )
            return verification_method
        
        if verification.type not in ("Sr25519VerificationKey2020", "Ed25519VerificationKey2020"):
            raise ValueError(
                "Substrate verification.type must be "
                "'Ed25519VerificationKey2020', or 'Sr25519VerificationKey2020'"
            )
        verification_method.type = verification.type
        verification_method.controller = f"did:peaq:{address}"
    
        if verification.public_key_multibase:
            verification_method.public_key_multibase = verification.public_key_multibase
        else:
            # Generate multibase from address and verification type
            verification_method.public_key_multibase = self._generate_multibase_for_verification(
                address, verification.type
            )
        
        return verification_method
    
    def _add_signature(self, signature: Signature) -> peaq_proto.Signature:
        """
        Constructs a Protobuf `Signature` object from a given `Signature` dataclass,
        enforcing the supported signature types and mandatory fields.

        Supported types:
        - "EcdsaSecp256k1RecoveryMethod2020"
        - "Ed25519VerificationKey2020"
        - "Sr25519VerificationKey2020"

        Args:
            signature (Signature): Contains `type`, `issuer`, and `hash`.

        Returns:
            peaq_proto.Signature: The Protobuf representation of the signature.

        Raises:
            ValueError: If `signature.type` is not one of the allowed types, or if
                `issuer` or `hash` are missing.
        """
        allowed = {
            "EcdsaSecp256k1RecoveryMethod2020",
            "Ed25519VerificationKey2020",
            "Sr25519VerificationKey2020",
        }
        if signature.type not in allowed:
            raise ValueError(
                'Signature.type must be one of '
                '"EcdsaSecp256k1RecoveryMethod2020", '
                '"Ed25519VerificationKey2020", or '
                '"Sr25519VerificationKey2020".'
            )
        if not signature.issuer:
            raise ValueError("Signature.issuer is required")
        if not signature.hash:
            raise ValueError("Signature.hash is required")

        proto_signature = peaq_proto.Signature()
        proto_signature.type = signature.type
        proto_signature.issuer = signature.issuer
        proto_signature.hash = signature.hash
        return proto_signature
    
    def _add_service(self, service: Service):
        """
        Builds a Protobuf `Services` message representing one service entry in the
        DID document. Validates required fields and stores either a service endpoint
        or some `data` (if provided).

        Args:
            service (Service): Must include an `id`, `type`, and at least one of
                `service_endpoint` or `data`.

        Returns:
            peaq_proto.Services: A populated Protobuf service record.

        Raises:
            ValueError: If `service.id` or `service.type` is missing, or if neither
                `service_endpoint` nor `data` is provided.
        """
        if not service.id:
            raise ValueError("Service.id is required")
        if not service.type:
            raise ValueError("Service.type is required")
        if not (service.service_endpoint or service.data):
            raise ValueError(
                "Either serviceEndpoint or data must be provided for Service"
            )
        proto_service = peaq_proto.Services()
        proto_service.id = service.id
        proto_service.type = service.type

        if service.service_endpoint:
            proto_service.service_endpoint = service.service_endpoint
        if service.data:
            proto_service.data = service.data

        return proto_service
    
    def _generate_sr25519_multibase(self, address: str) -> str:
        """
        Generates Sr25519 publicKeyMultibase from a Substrate SS58 address.
        
        Args:
            address (str): SS58 address
            
        Returns:
            str: publicKeyMultibase with 'z' prefix
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
    
    def _generate_ed25519_multibase(self, address: str) -> str:
        """
        Generates Ed25519 publicKeyMultibase from a Substrate SS58 address.
        
        Args:
            address (str): SS58 address
            
        Returns:
            str: publicKeyMultibase with 'z' prefix
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
    
    def _generate_ecdsa_multibase(self, address: str) -> str:
        """
        Generates ECDSA publicKeyMultibase from an EVM address using the connected signer.
        
        Args:
            address (str): EVM address (used for validation, actual key comes from signer)
            
        Returns:
            str: publicKeyMultibase with 'z' prefix
            
        Raises:
            ValueError: If no EVM signer is available or signer doesn't match address
        """
        if not self.metadata.pair or not hasattr(self.metadata.pair, '_key_obj'):
            raise ValueError(
                "EVM signer required for ECDSA multibase generation. "
                "Please provide a seed when creating the SDK instance."
            )
        
        # Get compressed public key from the signer
        compressed_pub_key = self.metadata.pair._key_obj.public_key.to_compressed_bytes()
        
        # Multicodec prefix for secp256k1-pub ([0xe7, 0x01])
        prefix = bytes([0xE7, 0x01])
        
        # Concatenate prefix + key bytes
        full = prefix + compressed_pub_key
        
        # Base58-btc encode and prepend 'z'
        multibase = "z" + base58.b58encode(full).decode()
        return multibase
    
    def _generate_multibase_for_verification(self, address: str, verification_type: str) -> str:
        """
        Generates the appropriate publicKeyMultibase based on verification type and chain.
        
        Args:
            address (str): The address (EVM or SS58)
            verification_type (str): The verification method type
            
        Returns:
            str: Generated publicKeyMultibase
            
        Raises:
            ValueError: If verification type is unsupported or required signer is missing
        """
        if verification_type == "EcdsaSecp256k1RecoveryMethod2020":
            if self.metadata.chain_type == ChainType.EVM:
                return self._generate_ecdsa_multibase(address)
            else:
                # For Substrate chains with ECDSA, we still need the actual public key
                # For now, fall back to address until we have proper key extraction
                return address
        elif verification_type == "Ed25519VerificationKey2020":
            if self.metadata.chain_type == ChainType.SUBSTRATE:
                return self._generate_ed25519_multibase(address)
            else:
                raise ValueError("Ed25519VerificationKey2020 is only supported on Substrate chains")
        elif verification_type == "Sr25519VerificationKey2020":
            if self.metadata.chain_type == ChainType.SUBSTRATE:
                return self._generate_sr25519_multibase(address)
            else:
                raise ValueError("Sr25519VerificationKey2020 is only supported on Substrate chains")
        else:
            raise ValueError(f"Unsupported verification type: {verification_type}")
    
    def _deserialize_did(self, data):
        """
        Parses a Protobuf-serialized DID document from the given raw `data` bytes.

        Args:
            data (bytes): The raw Protobuf-encoded DID document.

        Returns:
            peaq_proto.Document: The deserialized DID document.
        """
        deserialized_doc = peaq_proto.Document()
        deserialized_doc.ParseFromString(data)
        return deserialized_doc