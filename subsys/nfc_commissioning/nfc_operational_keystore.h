/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <crypto/CHIPCryptoPAL.h>
#include <crypto/OperationalKeystore.h>
#include <crypto/PSAOperationalKeystore.h>
#include <lib/core/CHIPPersistentStorageDelegate.h>
#include <lib/core/DataModelTypes.h>
#include <lib/support/CHIPMem.h>
#include <lib/support/CodeUtils.h>
#include <lib/support/Span.h>

namespace chip
{
namespace DeviceLayer
{

	enum class NFCOpaqueKeyUsage : uint8_t { ECDSA_P256_SHA256 = 0, ECDH_P256 = 1 };

	/** Opaque P-256 key whose private material lives on the NFC secure element. */
	class NFCOpaqueP256Keypair : public Crypto::P256Keypair {
	public:
		NFCOpaqueP256Keypair();
		~NFCOpaqueP256Keypair() override;

		CHIP_ERROR Initialize(Crypto::ECPKeyTarget key_target) override;
		CHIP_ERROR Serialize(Crypto::P256SerializedKeypair &output) const override;
		CHIP_ERROR Deserialize(Crypto::P256SerializedKeypair &input) override;

		CHIP_ERROR Create(uint8_t fabricId, NFCOpaqueKeyUsage usage);
		CHIP_ERROR ExportPublicKey(Crypto::P256PublicKey &out_public_key);
		const Crypto::P256PublicKey &Pubkey() const override;
		CHIP_ERROR ECDSA_sign_msg(const uint8_t *msg, size_t msg_length,
					  Crypto::P256ECDSASignature &out_signature) const override;
		CHIP_ERROR NewCertificateSigningRequest(uint8_t *out_csr, size_t &csr_length) const;
		uint8_t GetKeyId() const;
		CHIP_ERROR DestroyKey();

	private:
		static constexpr size_t kEcdsaSignatureSize = 64;
		static constexpr size_t kPublicKeyBufferSize = 65;

		uint8_t mKeyId = 0;
		uint8_t mFabricId = 0;
		bool mHasKey = false;
		Crypto::P256PublicKey mPubKey;
	};

	/** Operational keystore backed by keys stored on the NFC tag. */
	class NFCOperationalKeystore : public Crypto::OperationalKeystore {
	public:
		NFCOperationalKeystore() = default;
		~NFCOperationalKeystore() override { Finish(); }

		NFCOperationalKeystore(const NFCOperationalKeystore &) = delete;
		NFCOperationalKeystore &operator=(const NFCOperationalKeystore &) = delete;

		CHIP_ERROR Init(PersistentStorageDelegate *storage);
		void Finish();

		bool HasPendingOpKeypair() const override { return mPendingOpaqueKeypair != nullptr; }

		bool HasOpKeypairForFabric(FabricIndex fabricIndex) const override;
		CHIP_ERROR NewOpKeypairForFabric(FabricIndex fabricIndex,
						 MutableByteSpan &outCertificateSigningRequest) override;
		CHIP_ERROR ActivateOpKeypairForFabric(FabricIndex fabricIndex,
						      const Crypto::P256PublicKey &nocPublicKey) override;
		CHIP_ERROR CommitOpKeypairForFabric(FabricIndex fabricIndex) override;
		CHIP_ERROR RemoveOpKeypairForFabric(FabricIndex fabricIndex) override;
		void RevertPendingKeypair() override;
		CHIP_ERROR SignWithOpKeypair(FabricIndex fabricIndex, const ByteSpan &message,
					     Crypto::P256ECDSASignature &outSignature) const override;
		Crypto::P256Keypair *AllocateEphemeralKeypairForCASE() override;
		void ReleaseEphemeralKeypair(Crypto::P256Keypair *keypair) override;

		CHIP_ERROR GetKeyIdFromFabricId(FabricIndex fabricIndex, uint8_t &keyId) const;
		CHIP_ERROR SetKeyIdForFabricId(FabricIndex fabricIndex, uint8_t keyId);

	protected:
		void ResetPendingKey();
		bool IsKeySlotAvailable();

		PersistentStorageDelegate *mStorage = nullptr;
		FabricIndex mPendingFabricIndex = kUndefinedFabricIndex;
		Crypto::P256Keypair *mPendingOpaqueKeypair = nullptr;
		bool mIsPendingKeypairActive = false;
		bool mIsExternallyOwnedKeypair = false;
	};

	/**
	 * Routes each fabric's operational key to either the local PSA keystore or the
	 * NFC secure element, based on which one the fabric's key actually lives on.
	 */
	class NFCHybridOperationalKeystore : public Crypto::OperationalKeystore {
	public:
		NFCHybridOperationalKeystore() = default;
		~NFCHybridOperationalKeystore() override = default;

		NFCHybridOperationalKeystore(const NFCHybridOperationalKeystore &) = delete;
		NFCHybridOperationalKeystore &operator=(const NFCHybridOperationalKeystore &) = delete;

		CHIP_ERROR Init(PersistentStorageDelegate *storage);

		/** Record that @p fabricIndex's operational key is NFC key slot @p keyId. */
		CHIP_ERROR RegisterNfcBackedFabric(FabricIndex fabricIndex, uint8_t keyId);

		bool HasPendingOpKeypair() const override;
		bool HasOpKeypairForFabric(FabricIndex fabricIndex) const override;
		CHIP_ERROR NewOpKeypairForFabric(FabricIndex fabricIndex,
						 MutableByteSpan &outCertificateSigningRequest) override;
		CHIP_ERROR ActivateOpKeypairForFabric(FabricIndex fabricIndex,
						      const Crypto::P256PublicKey &nocPublicKey) override;
		CHIP_ERROR CommitOpKeypairForFabric(FabricIndex fabricIndex) override;
		CHIP_ERROR RemoveOpKeypairForFabric(FabricIndex fabricIndex) override;
		void RevertPendingKeypair() override;
		CHIP_ERROR SignWithOpKeypair(FabricIndex fabricIndex, const ByteSpan &message,
					     Crypto::P256ECDSASignature &outSignature) const override;
		Crypto::P256Keypair *AllocateEphemeralKeypairForCASE() override;
		void ReleaseEphemeralKeypair(Crypto::P256Keypair *keypair) override;

	private:
		enum class Backend : uint8_t { kNone = 0, kPSA = 1, kNFC = 2 };

		Backend GetBackendForFabric(FabricIndex fabricIndex) const;
		CHIP_ERROR SetBackendForFabric(FabricIndex fabricIndex, Backend backend);
		CHIP_ERROR ClearBackendForFabric(FabricIndex fabricIndex);

		Crypto::PSAOperationalKeystore mPsaKeystore;
		PersistentStorageDelegate *mStorage = nullptr;
		FabricIndex mPendingFabricIndex = kUndefinedFabricIndex;
		Backend mPendingBackend = Backend::kNone;
	};

	NFCOperationalKeystore &NFCOperationalKeystoreInstance();
	NFCHybridOperationalKeystore &NFCHybridOperationalKeystoreInstance();
	CHIP_ERROR NFCInitOperationalKeystore(PersistentStorageDelegate *storage);

} // namespace DeviceLayer
} // namespace chip
