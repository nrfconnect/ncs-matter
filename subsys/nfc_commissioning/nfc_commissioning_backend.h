/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @file nfc_commissioning_backend.h
 * @brief Backend-agnostic NFC commissioning API for Matter unpowered commissioning.
 *
 * Defines shared status codes, secure-element key slot limits, and the abstract
 * interface that concrete tag backends implement in a driver library.
 */

#pragma once

#include <lib/core/CHIPError.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Result of an NFC commissioning or secure-element operation. */
typedef enum {
	NFC_COMMISSIONING_STATUS_OK = 0,
	NFC_COMMISSIONING_STATUS_BAD_VALUE,
	NFC_COMMISSIONING_STATUS_BAD_SIZE,
	NFC_COMMISSIONING_STATUS_BUSY,
	NFC_COMMISSIONING_STATUS_NOT_FOUND,
	NFC_COMMISSIONING_STATUS_IO,
	NFC_COMMISSIONING_STATUS_INTERNAL,
} NfcCommissioningStatus;

/** Maximum TLV payload size read from or written to the NFC tag. */
#define NFC_COMMISSIONING_TLV_BUFFER_SIZE 2048U

/** Maximum number of operational key slots exposed by the secure element. */
#define NFC_COMMISSIONING_MAX_KEY_SLOTS 9U
/** First key slot used for Matter operational credentials (slot 0–1 are reserved). */
#define NFC_COMMISSIONING_MIN_OPERATIONAL_KEY_ID 2U
/** Last operational key slot index (inclusive). */
#define NFC_COMMISSIONING_MAX_OPERATIONAL_KEY_ID                                                                       \
	(NFC_COMMISSIONING_MIN_OPERATIONAL_KEY_ID + NFC_COMMISSIONING_MAX_KEY_SLOTS - 1U)
/** Uncompressed P-256 public key size returned by the tag. */
#define NFC_COMMISSIONING_P256_PUBLIC_KEY_SIZE 65U
/** ECDSA P-256 signature size produced by SignWithKey(). */
#define NFC_COMMISSIONING_ECDSA_SIGNATURE_SIZE 64U

#ifdef __cplusplus
}
#endif

namespace chip
{
namespace DeviceLayer
{

	/**
	 * Abstract NFC tag backend.
	 *
	 * Implemented by the selected driver library (link-time). Callers should use
	 * NfcCommissioning forwarders or GetNfcCommissioningBackend() rather than
	 * backend-specific driver APIs.
	 */
	class NfcCommissioningBackend {
	public:
		virtual ~NfcCommissioningBackend() = default;

		/**
		 * @brief Power the tag (VCC), assert I2C mode (CTRL), and start the I2C session.
		 */
		virtual NfcCommissioningStatus PrepareTagForCommunication() = 0;

		/**
		 * @brief Read and decrypt the commissioning TLV from the tag.
		 */
		virtual NfcCommissioningStatus ReadTlv(uint8_t *buffer, uint16_t buffer_max, uint16_t *out_len) = 0;

		/** @brief Clear commissioning TLV data on the tag and release GPIO for NFC field use. */
		virtual NfcCommissioningStatus ClearTagData() = 0;

		/** @brief Perform a full factory reset on the tag and release GPIO for NFC field use. */
		virtual NfcCommissioningStatus FactoryReset() = 0;

		/** @brief Drop I2C session state and release VCC/CTRL for NFC field use. */
		virtual void ReleaseTagForNfcField() = 0;

		/**
		 * @brief Read TLV from the tag, parse it, and drive the Matter commissioning flow.
		 */
		virtual CHIP_ERROR CommissionToMatter() = 0;

		virtual NfcCommissioningStatus GenerateKeyPair(uint8_t fabricId, uint8_t *out_key_id) = 0;

		virtual NfcCommissioningStatus GetPublicKey(uint8_t key_id, uint8_t *pubkey, size_t pubkey_size) = 0;

		virtual NfcCommissioningStatus SignWithKey(uint8_t key_id, const uint8_t *message, uint16_t message_len,
							 uint8_t *signature, size_t signature_size) = 0;

		virtual NfcCommissioningStatus EraseKeyPair(uint8_t key_id) = 0;

		virtual bool IsKeySlotAvailable() = 0;
	};

	/** @brief Return the NFC tag backend selected at link time. */
	NfcCommissioningBackend &GetNfcCommissioningBackend();

} // namespace DeviceLayer
} // namespace chip
