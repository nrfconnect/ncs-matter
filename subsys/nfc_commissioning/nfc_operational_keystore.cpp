/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "nfc_commissioning/nfc_operational_keystore.h"
#include "nfc_commissioning/nfc_unpowered_commissioning.h"

#include <lib/support/DefaultStorageKeyAllocator.h>
#include <lib/support/logging/CHIPLogging.h>

namespace chip
{
namespace DeviceLayer
{

	namespace
	{

		using namespace chip::Crypto;

		StorageKeyName FabricNFCKeyId(FabricIndex fabric)
		{
			return StorageKeyName::Formatted("f/%x/NFCk", fabric);
		}

		StorageKeyName FabricOpKeystoreBackendKey(FabricIndex fabric)
		{
			return StorageKeyName::Formatted("f/%x/OKb", fabric);
		}

		NFCOperationalKeystore sNFCOperationalKeystore;
		NFCHybridOperationalKeystore sNFCHybridOperationalKeystore;

		NfcCommissioningBackend &TagBackend()
		{
			return GetNfcCommissioningBackend();
		}

		bool IsValidOperationalKeyId(uint8_t keyId)
		{
			return (keyId >= NFC_COMMISSIONING_MIN_OPERATIONAL_KEY_ID) &&
			       (keyId <= NFC_COMMISSIONING_MAX_OPERATIONAL_KEY_ID);
		}

	} // namespace

	NFCOperationalKeystore &NFCOperationalKeystoreInstance()
	{
		return sNFCOperationalKeystore;
	}

	NFCHybridOperationalKeystore &NFCHybridOperationalKeystoreInstance()
	{
		return sNFCHybridOperationalKeystore;
	}

	CHIP_ERROR NFCInitOperationalKeystore(PersistentStorageDelegate *storage)
	{
		return sNFCOperationalKeystore.Init(storage);
	}

	NFCOpaqueP256Keypair::NFCOpaqueP256Keypair() = default;
	NFCOpaqueP256Keypair::~NFCOpaqueP256Keypair() = default;

	CHIP_ERROR NFCOpaqueP256Keypair::Initialize(ECPKeyTarget key_target)
	{
		if (mHasKey) {
			return CHIP_NO_ERROR;
		}

		ChipLogError(Crypto, "Initialize() is invalid on opaque keys, use Create() instead");
		return CHIP_ERROR_NOT_IMPLEMENTED;
	}

	CHIP_ERROR NFCOpaqueP256Keypair::Serialize(P256SerializedKeypair &output) const
	{
		ReturnErrorOnFailure(output.SetLength(2));
		output.Bytes()[0] = mKeyId;
		output.Bytes()[1] = mFabricId;
		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOpaqueP256Keypair::Deserialize(P256SerializedKeypair &input)
	{
		VerifyOrReturnError(input.Length() >= 2, CHIP_ERROR_INVALID_ARGUMENT);

		mKeyId = input.Bytes()[0];
		mFabricId = input.Bytes()[1];
		mHasKey = true;

		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOpaqueP256Keypair::Create(uint8_t fabricId, NFCOpaqueKeyUsage usage)
	{
		uint8_t keyIndex = 0;

		(void) usage;

		VerifyOrReturnError(TagBackend().GenerateKeyPair(fabricId, &keyIndex) == NFC_COMMISSIONING_STATUS_OK,
				    CHIP_ERROR_HAD_FAILURES);

		mKeyId = keyIndex;
		mFabricId = fabricId;
		mHasKey = true;

		return ExportPublicKey(mPubKey);
	}

	CHIP_ERROR NFCOpaqueP256Keypair::ExportPublicKey(P256PublicKey &out_public_key)
	{
		uint8_t pubkey[kPublicKeyBufferSize] = { 0 };

		VerifyOrReturnError(TagBackend().GetPublicKey(mKeyId, pubkey, sizeof(pubkey)) ==
					    NFC_COMMISSIONING_STATUS_OK,
				    CHIP_ERROR_INTERNAL);

		memcpy(out_public_key.Bytes(), pubkey, kPublicKeyBufferSize);
		mPubKey = out_public_key;

		return CHIP_NO_ERROR;
	}

	const P256PublicKey &NFCOpaqueP256Keypair::Pubkey() const
	{
		return mPubKey;
	}

	CHIP_ERROR NFCOpaqueP256Keypair::ECDSA_sign_msg(const uint8_t *msg, size_t msg_length,
							P256ECDSASignature &out_signature) const
	{
		uint8_t signature[kEcdsaSignatureSize] = { 0 };

		VerifyOrReturnError(TagBackend().SignWithKey(mKeyId, msg, static_cast<uint16_t>(msg_length), signature,
							     sizeof(signature)) == NFC_COMMISSIONING_STATUS_OK,
				    CHIP_ERROR_INTERNAL);

		memcpy(out_signature.Bytes(), signature, kEcdsaSignatureSize);
		return out_signature.SetLength(kEcdsaSignatureSize);
	}

	CHIP_ERROR NFCOpaqueP256Keypair::NewCertificateSigningRequest(uint8_t *out_csr, size_t &csr_length) const
	{
		MutableByteSpan csr(out_csr, csr_length);
		CHIP_ERROR err = GenerateCertificateSigningRequest(this, csr);
		csr_length = (err == CHIP_NO_ERROR) ? csr.size() : 0;
		return err;
	}

	uint8_t NFCOpaqueP256Keypair::GetKeyId() const
	{
		return mKeyId;
	}

	CHIP_ERROR NFCOpaqueP256Keypair::DestroyKey()
	{
		VerifyOrReturnError(mHasKey, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(TagBackend().EraseKeyPair(mKeyId) == NFC_COMMISSIONING_STATUS_OK,
				    CHIP_ERROR_INTERNAL);

		mHasKey = false;
		mKeyId = 0;

		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOperationalKeystore::Init(PersistentStorageDelegate *storage)
	{
		VerifyOrReturnError(mStorage == nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(storage != nullptr, CHIP_ERROR_INVALID_ARGUMENT);

		mPendingFabricIndex = kUndefinedFabricIndex;
		mIsExternallyOwnedKeypair = false;
		mStorage = storage;
		mPendingOpaqueKeypair = nullptr;
		mIsPendingKeypairActive = false;

		return CHIP_NO_ERROR;
	}

	void NFCOperationalKeystore::Finish()
	{
		if (mStorage == nullptr) {
			return;
		}

		ResetPendingKey();
		mStorage = nullptr;
	}

	void NFCOperationalKeystore::ResetPendingKey()
	{
		if (!mIsExternallyOwnedKeypair && (mPendingOpaqueKeypair != nullptr)) {
			Platform::Delete(mPendingOpaqueKeypair);
		}

		mPendingOpaqueKeypair = nullptr;
		mIsExternallyOwnedKeypair = false;
		mIsPendingKeypairActive = false;
		mPendingFabricIndex = kUndefinedFabricIndex;
	}

	bool NFCOperationalKeystore::HasOpKeypairForFabric(FabricIndex fabricIndex) const
	{
		VerifyOrReturnError(mStorage != nullptr, false);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), false);

		if (mIsPendingKeypairActive && (fabricIndex == mPendingFabricIndex) &&
		    (mPendingOpaqueKeypair != nullptr)) {
			return true;
		}

		uint8_t keyId = 0;
		CHIP_ERROR err = GetKeyIdFromFabricId(fabricIndex, keyId);
		return (err == CHIP_NO_ERROR) && IsValidOperationalKeyId(keyId);
	}

	CHIP_ERROR NFCOperationalKeystore::NewOpKeypairForFabric(FabricIndex fabricIndex,
								 MutableByteSpan &outCertificateSigningRequest)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);
		VerifyOrReturnError(IsKeySlotAvailable(), CHIP_ERROR_NO_MEMORY);

		if ((mPendingFabricIndex != kUndefinedFabricIndex) && (fabricIndex != mPendingFabricIndex)) {
			return CHIP_ERROR_INVALID_FABRIC_INDEX;
		}

		VerifyOrReturnError(outCertificateSigningRequest.size() >= Crypto::kMIN_CSR_Buffer_Size,
				    CHIP_ERROR_BUFFER_TOO_SMALL);

		ResetPendingKey();

		mPendingOpaqueKeypair = Platform::New<NFCOpaqueP256Keypair>();
		VerifyOrReturnError(mPendingOpaqueKeypair != nullptr, CHIP_ERROR_NO_MEMORY);

		auto *NFCKeypair = static_cast<NFCOpaqueP256Keypair *>(mPendingOpaqueKeypair);
		ReturnErrorOnFailure(
			NFCKeypair->Create(static_cast<uint8_t>(fabricIndex), NFCOpaqueKeyUsage::ECDSA_P256_SHA256));

		size_t csrLength = outCertificateSigningRequest.size();
		ReturnErrorOnFailure(
			NFCKeypair->NewCertificateSigningRequest(outCertificateSigningRequest.data(), csrLength));
		outCertificateSigningRequest.reduce_size(csrLength);

		mPendingFabricIndex = fabricIndex;
		mIsPendingKeypairActive = false;

		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOperationalKeystore::ActivateOpKeypairForFabric(FabricIndex fabricIndex,
								      const Crypto::P256PublicKey &nocPublicKey)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(mPendingOpaqueKeypair != nullptr, CHIP_ERROR_INVALID_FABRIC_INDEX);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex) && (fabricIndex == mPendingFabricIndex),
				    CHIP_ERROR_INVALID_FABRIC_INDEX);
		VerifyOrReturnError(mPendingOpaqueKeypair->Pubkey().Matches(nocPublicKey),
				    CHIP_ERROR_INVALID_PUBLIC_KEY);

		mIsPendingKeypairActive = true;
		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOperationalKeystore::CommitOpKeypairForFabric(FabricIndex fabricIndex)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(mPendingOpaqueKeypair != nullptr, CHIP_ERROR_INVALID_FABRIC_INDEX);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex) && (fabricIndex == mPendingFabricIndex),
				    CHIP_ERROR_INVALID_FABRIC_INDEX);
		VerifyOrReturnError(mIsPendingKeypairActive, CHIP_ERROR_INCORRECT_STATE);

		auto *NFCKey = static_cast<NFCOpaqueP256Keypair *>(mPendingOpaqueKeypair);
		ReturnErrorOnFailure(SetKeyIdForFabricId(fabricIndex, NFCKey->GetKeyId()));
		ResetPendingKey();

		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOperationalKeystore::RemoveOpKeypairForFabric(FabricIndex fabricIndex)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		if ((mPendingOpaqueKeypair != nullptr) && (fabricIndex == mPendingFabricIndex)) {
			RevertPendingKeypair();
		}

		uint8_t keyId = 0;
		CHIP_ERROR keyErr = GetKeyIdFromFabricId(fabricIndex, keyId);
		if ((keyErr == CHIP_NO_ERROR) && IsValidOperationalKeyId(keyId)) {
			(void)TagBackend().EraseKeyPair(keyId);
		}

		CHIP_ERROR err = mStorage->SyncDeleteKeyValue(FabricNFCKeyId(fabricIndex).KeyName());
		if (err == CHIP_ERROR_PERSISTED_STORAGE_VALUE_NOT_FOUND) {
			err = CHIP_ERROR_INVALID_FABRIC_INDEX;
		}

		return err;
	}

	void NFCOperationalKeystore::RevertPendingKeypair()
	{
		if (mPendingOpaqueKeypair != nullptr) {
			auto *NFCKey = static_cast<NFCOpaqueP256Keypair *>(mPendingOpaqueKeypair);
			(void)NFCKey->DestroyKey();
		}

		ResetPendingKey();
	}

	CHIP_ERROR NFCOperationalKeystore::SignWithOpKeypair(FabricIndex fabricIndex, const ByteSpan &message,
							     Crypto::P256ECDSASignature &outSignature) const
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		if (mIsPendingKeypairActive && (fabricIndex == mPendingFabricIndex)) {
			VerifyOrReturnError(mPendingOpaqueKeypair != nullptr, CHIP_ERROR_INTERNAL);
			return mPendingOpaqueKeypair->ECDSA_sign_msg(message.data(), message.size(), outSignature);
		}

		uint8_t keyId = 0;
		ReturnErrorOnFailure(GetKeyIdFromFabricId(fabricIndex, keyId));
		VerifyOrReturnError(IsValidOperationalKeyId(keyId), CHIP_ERROR_INVALID_FABRIC_INDEX);

		uint8_t signature[NFC_COMMISSIONING_ECDSA_SIGNATURE_SIZE] = { 0 };

		VerifyOrReturnError(TagBackend().SignWithKey(keyId, message.data(),
							     static_cast<uint16_t>(message.size()), signature,
							     sizeof(signature)) == NFC_COMMISSIONING_STATUS_OK,
				    CHIP_ERROR_INTERNAL);

		memcpy(outSignature.Bytes(), signature, sizeof(signature));
		return outSignature.SetLength(sizeof(signature));
	}

	Crypto::P256Keypair *NFCOperationalKeystore::AllocateEphemeralKeypairForCASE()
	{
		return Platform::New<Crypto::P256Keypair>();
	}

	void NFCOperationalKeystore::ReleaseEphemeralKeypair(Crypto::P256Keypair *keypair)
	{
		Platform::Delete(keypair);
	}

	CHIP_ERROR NFCOperationalKeystore::GetKeyIdFromFabricId(FabricIndex fabricIndex, uint8_t &keyId) const
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		uint16_t size = sizeof(uint8_t);
		uint8_t tmp = 0;

		CHIP_ERROR err = mStorage->SyncGetKeyValue(FabricNFCKeyId(fabricIndex).KeyName(), &tmp, size);
		VerifyOrReturnError(err == CHIP_NO_ERROR && size == sizeof(uint8_t), err);

		keyId = tmp;
		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCOperationalKeystore::SetKeyIdForFabricId(FabricIndex fabricIndex, uint8_t keyId)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		uint8_t stored = keyId;
		return mStorage->SyncSetKeyValue(FabricNFCKeyId(fabricIndex).KeyName(), &stored, sizeof(stored));
	}

	bool NFCOperationalKeystore::IsKeySlotAvailable()
	{
		return TagBackend().IsKeySlotAvailable();
	}

	CHIP_ERROR NFCHybridOperationalKeystore::Init(PersistentStorageDelegate *storage)
	{
		VerifyOrReturnError(storage != nullptr, CHIP_ERROR_INVALID_ARGUMENT);

		mStorage = storage;
		mPendingFabricIndex = kUndefinedFabricIndex;
		mPendingBackend = Backend::kNone;

		return NFCInitOperationalKeystore(storage);
	}

	CHIP_ERROR NFCHybridOperationalKeystore::RegisterNfcBackedFabric(FabricIndex fabricIndex, uint8_t keyId)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		ReturnErrorOnFailure(NFCOperationalKeystoreInstance().SetKeyIdForFabricId(fabricIndex, keyId));
		return SetBackendForFabric(fabricIndex, Backend::kNFC);
	}

	NFCHybridOperationalKeystore::Backend
	NFCHybridOperationalKeystore::GetBackendForFabric(FabricIndex fabricIndex) const
	{
		if ((mPendingBackend != Backend::kNone) && (fabricIndex == mPendingFabricIndex)) {
			return mPendingBackend;
		}

		if (mStorage != nullptr) {
			uint8_t stored = static_cast<uint8_t>(Backend::kNone);
			uint16_t size = sizeof(stored);

			if ((mStorage->SyncGetKeyValue(FabricOpKeystoreBackendKey(fabricIndex).KeyName(), &stored,
						       size) == CHIP_NO_ERROR) &&
			    (size == sizeof(stored))) {
				return static_cast<Backend>(stored);
			}
		}

		if (NFCOperationalKeystoreInstance().HasOpKeypairForFabric(fabricIndex)) {
			return Backend::kNFC;
		}

		return Backend::kPSA;
	}

	CHIP_ERROR NFCHybridOperationalKeystore::SetBackendForFabric(FabricIndex fabricIndex, Backend backend)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);

		uint8_t stored = static_cast<uint8_t>(backend);
		return mStorage->SyncSetKeyValue(FabricOpKeystoreBackendKey(fabricIndex).KeyName(), &stored,
						 sizeof(stored));
	}

	CHIP_ERROR NFCHybridOperationalKeystore::ClearBackendForFabric(FabricIndex fabricIndex)
	{
		VerifyOrReturnError(mStorage != nullptr, CHIP_ERROR_INCORRECT_STATE);

		CHIP_ERROR err = mStorage->SyncDeleteKeyValue(FabricOpKeystoreBackendKey(fabricIndex).KeyName());
		return (err == CHIP_ERROR_PERSISTED_STORAGE_VALUE_NOT_FOUND) ? CHIP_NO_ERROR : err;
	}

	bool NFCHybridOperationalKeystore::HasPendingOpKeypair() const
	{
		return mPendingBackend != Backend::kNone;
	}

	bool NFCHybridOperationalKeystore::HasOpKeypairForFabric(FabricIndex fabricIndex) const
	{
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), false);

		switch (GetBackendForFabric(fabricIndex)) {
		case Backend::kPSA:
			return mPsaKeystore.HasOpKeypairForFabric(fabricIndex);
		case Backend::kNFC:
			return NFCOperationalKeystoreInstance().HasOpKeypairForFabric(fabricIndex);
		default:
			return false;
		}
	}

	CHIP_ERROR NFCHybridOperationalKeystore::NewOpKeypairForFabric(FabricIndex fabricIndex,
								       MutableByteSpan &outCertificateSigningRequest)
	{
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		if (mPendingBackend != Backend::kNone) {
			VerifyOrReturnError(fabricIndex == mPendingFabricIndex, CHIP_ERROR_INVALID_FABRIC_INDEX);
		}

		ReturnErrorOnFailure(mPsaKeystore.NewOpKeypairForFabric(fabricIndex, outCertificateSigningRequest));

		mPendingFabricIndex = fabricIndex;
		mPendingBackend = Backend::kPSA;

		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCHybridOperationalKeystore::ActivateOpKeypairForFabric(FabricIndex fabricIndex,
									    const Crypto::P256PublicKey &nocPublicKey)
	{
		VerifyOrReturnError((mPendingBackend == Backend::kPSA) && (fabricIndex == mPendingFabricIndex),
				    CHIP_ERROR_INVALID_FABRIC_INDEX);

		return mPsaKeystore.ActivateOpKeypairForFabric(fabricIndex, nocPublicKey);
	}

	CHIP_ERROR NFCHybridOperationalKeystore::CommitOpKeypairForFabric(FabricIndex fabricIndex)
	{
		VerifyOrReturnError((mPendingBackend == Backend::kPSA) && (fabricIndex == mPendingFabricIndex),
				    CHIP_ERROR_INVALID_FABRIC_INDEX);

		ReturnErrorOnFailure(mPsaKeystore.CommitOpKeypairForFabric(fabricIndex));
		ReturnErrorOnFailure(SetBackendForFabric(fabricIndex, Backend::kPSA));

		mPendingFabricIndex = kUndefinedFabricIndex;
		mPendingBackend = Backend::kNone;

		return CHIP_NO_ERROR;
	}

	CHIP_ERROR NFCHybridOperationalKeystore::RemoveOpKeypairForFabric(FabricIndex fabricIndex)
	{
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		if ((mPendingBackend != Backend::kNone) && (fabricIndex == mPendingFabricIndex)) {
			RevertPendingKeypair();
			return CHIP_NO_ERROR;
		}

		Backend backend = GetBackendForFabric(fabricIndex);
		CHIP_ERROR err = (backend == Backend::kNFC) ?
					 NFCOperationalKeystoreInstance().RemoveOpKeypairForFabric(fabricIndex) :
					 mPsaKeystore.RemoveOpKeypairForFabric(fabricIndex);

		(void)ClearBackendForFabric(fabricIndex);

		return err;
	}

	void NFCHybridOperationalKeystore::RevertPendingKeypair()
	{
		if (mPendingBackend == Backend::kPSA) {
			mPsaKeystore.RevertPendingKeypair();
		}

		mPendingFabricIndex = kUndefinedFabricIndex;
		mPendingBackend = Backend::kNone;
	}

	CHIP_ERROR NFCHybridOperationalKeystore::SignWithOpKeypair(FabricIndex fabricIndex, const ByteSpan &message,
								   Crypto::P256ECDSASignature &outSignature) const
	{
		VerifyOrReturnError(IsValidFabricIndex(fabricIndex), CHIP_ERROR_INVALID_FABRIC_INDEX);

		switch (GetBackendForFabric(fabricIndex)) {
		case Backend::kPSA:
			return mPsaKeystore.SignWithOpKeypair(fabricIndex, message, outSignature);
		case Backend::kNFC:
			return NFCOperationalKeystoreInstance().SignWithOpKeypair(fabricIndex, message, outSignature);
		default:
			return CHIP_ERROR_INVALID_FABRIC_INDEX;
		}
	}

	Crypto::P256Keypair *NFCHybridOperationalKeystore::AllocateEphemeralKeypairForCASE()
	{
		return mPsaKeystore.AllocateEphemeralKeypairForCASE();
	}

	void NFCHybridOperationalKeystore::ReleaseEphemeralKeypair(Crypto::P256Keypair *keypair)
	{
		mPsaKeystore.ReleaseEphemeralKeypair(keypair);
	}

} // namespace DeviceLayer
} // namespace chip
