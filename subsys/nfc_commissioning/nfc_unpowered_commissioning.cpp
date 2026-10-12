/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "nfc_commissioning/nfc_unpowered_commissioning.h"

#include <platform/CHIPDeviceLayer.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

namespace chip
{
namespace DeviceLayer
{

	namespace
	{

		uint8_t s_tlv_work_buffer[NFC_COMMISSIONING_TLV_BUFFER_SIZE];
		K_MUTEX_DEFINE(s_tlv_buffer_mutex);

	} // namespace

	NfcCommissioning &NfcCommissioning::Instance()
	{
		static NfcCommissioning s_instance;
		return s_instance;
	}

	CHIP_ERROR NfcCommissioning::Run()
	{
		return ApplyFromTag();
	}

	void NfcCommissioning::RequestRun()
	{
		(void)PlatformMgr().ScheduleWork(
			[](intptr_t /* context */) {
				CHIP_ERROR err = NfcCommissioning::Instance().Run();
				if (err == CHIP_ERROR_NOT_FOUND) {
					LOG_INF("No commissioning TLV on NFC tag");
					NfcCommissioning::Instance().ReleaseTagForNfcField();
				} else if (err != CHIP_NO_ERROR) {
					LOG_ERR("NfcCommissioning::Run() failed: %" CHIP_ERROR_FORMAT, err.Format());
					NfcCommissioning::Instance().ReleaseTagForNfcField();
				}
			},
			0);
	}

	CHIP_ERROR NfcCommissioning::ApplyFromTag()
	{
		return Backend().CommissionToMatter();
	}

	uint8_t *NfcCommissioning::WorkBuffer()
	{
		return s_tlv_work_buffer;
	}

	uint16_t NfcCommissioning::WorkBufferSize()
	{
		return NFC_COMMISSIONING_TLV_BUFFER_SIZE;
	}

	void NfcCommissioning::LockWorkBuffer()
	{
		k_mutex_lock(&s_tlv_buffer_mutex, K_FOREVER);
	}

	void NfcCommissioning::UnlockWorkBuffer()
	{
		k_mutex_unlock(&s_tlv_buffer_mutex);
	}

	NFCHybridOperationalKeystore &NfcCommissioning::GetHybridOperationalKeystore()
	{
		return NFCHybridOperationalKeystoreInstance();
	}

	NFCOperationalKeystore &NfcCommissioning::GetNfcOperationalKeystore()
	{
		return NFCOperationalKeystoreInstance();
	}

} // namespace DeviceLayer
} // namespace chip
