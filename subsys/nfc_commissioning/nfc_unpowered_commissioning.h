/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @file nfc_unpowered_commissioning.h
 * @brief Matter NFC unpowered commissioning facade and shell integration.
 *
 *
 * NfcCommissioning delegates tag operations to the selected backend library and provides
 * operational-keystore access plus a shared TLV work buffer.
 */

#pragma once

#include "nfc_commissioning/nfc_commissioning_backend.h"
#include "nfc_commissioning/nfc_operational_keystore.h"

#include <lib/core/CHIPError.h>
#include <stdarg.h>
#include <stddef.h>

namespace chip
{
namespace DeviceLayer
{

	/**
	 * Singleton entry point for NFC unpowered commissioning.
	 *
	 * Forwards tag-backend methods to GetNfcCommissioningBackend().
	 */
	class NfcCommissioning {
	public:
		static NfcCommissioning &Instance();

		NfcCommissioningStatus PrepareTagForCommunication()
		{
			return Backend().PrepareTagForCommunication();
		}

		NfcCommissioningStatus ReadTlv(uint8_t *buffer, uint16_t buffer_max, uint16_t *out_len)
		{
			return Backend().ReadTlv(buffer, buffer_max, out_len);
		}

		NfcCommissioningStatus ClearTagData() { return Backend().ClearTagData(); }

		NfcCommissioningStatus FactoryReset() { return Backend().FactoryReset(); }

		void ReleaseTagForNfcField() { Backend().ReleaseTagForNfcField(); }

		NfcCommissioningStatus GenerateKeyPair(uint8_t fabricId, uint8_t *out_key_id)
		{
			return Backend().GenerateKeyPair(fabricId, out_key_id);
		}

		NfcCommissioningStatus GetPublicKey(uint8_t key_id, uint8_t *pubkey, size_t pubkey_size)
		{
			return Backend().GetPublicKey(key_id, pubkey, pubkey_size);
		}

		NfcCommissioningStatus SignWithKey(uint8_t key_id, const uint8_t *message, uint16_t message_len,
						   uint8_t *signature, size_t signature_size)
		{
			return Backend().SignWithKey(key_id, message, message_len, signature, signature_size);
		}

		NfcCommissioningStatus EraseKeyPair(uint8_t key_id) { return Backend().EraseKeyPair(key_id); }

		bool IsKeySlotAvailable() { return Backend().IsKeySlotAvailable(); }

		/**
		 * @brief Read commissioning data from the tag and apply it to Matter.
		 */
		CHIP_ERROR Run();

		/**
		 * @brief Schedule Run() on the Matter platform worker thread.
		 */
		void RequestRun();

		/** @brief Apply commissioning data from the tag via the backend. */
		CHIP_ERROR ApplyFromTag();

		uint8_t *WorkBuffer();
		uint16_t WorkBufferSize();
		void LockWorkBuffer();
		void UnlockWorkBuffer();

		NFCHybridOperationalKeystore &GetHybridOperationalKeystore();
		NFCOperationalKeystore &GetNfcOperationalKeystore();

		static NfcCommissioningBackend &Backend() { return GetNfcCommissioningBackend(); }

	private:
		NfcCommissioning() = default;
	};

} // namespace DeviceLayer
} // namespace chip

#ifdef __cplusplus
extern "C" {
#endif

/** Output sink for NFC shell command handlers. */
struct NfcCommissioningShellOut {
	int (*print)(void *ctx, const char *fmt, va_list args);
	void *ctx;
};

typedef int (*NfcCommissioningShellHandler)(struct NfcCommissioningShellOut *out, int argc, char **argv);

struct NfcCommissioningShellCommand {
	const char *name;
	const char *help;
	NfcCommissioningShellHandler handler;
};

const struct NfcCommissioningShellCommand *NfcCommissioningShellGetCommands(size_t *out_count);
const char *NfcCommissioningShellGetHelpHeader(void);
int NfcCommissioningShellExec(int argc, char **argv, int (*print)(void *ctx, const char *fmt, va_list args), void *ctx);

#ifdef CONFIG_MATTER_NFC_COMMISSIONING_BUTTON_TRIGGER
void NfcCommissioningButtonInit(void);
#endif

#ifdef __cplusplus
}
#endif
