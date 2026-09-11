/*
 * Copyright (c) 2025 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 *
 * native_sim MCUboot boot-API stubs for the upstream Matter Zephyr OTA image
 * processor. BDX download uses stream_flash (slot1); these hooks simulate apply,
 * confirm, and reboot while persisting state in settings + --flash= file.
 */

#include "ota_sim_state.h"

#include <app/clusters/ota-requestor/OTARequestorInterface.h>
#include <lib/support/logging/CHIPLogging.h>
#include <platform/CHIPDeviceLayer.h>

#include <errno.h>

#include <zephyr/dfu/mcuboot.h>

using chip::GetRequestorInstance;
using chip::OTARequestorInterface;

extern "C" {

int boot_request_upgrade(int permanent)
{
	ARG_UNUSED(permanent);

	OTARequestorInterface *requestor = GetRequestorInstance();

	if (requestor == nullptr) {
		ChipLogError(SoftwareUpdate, "OTA sim: no requestor for boot_request_upgrade");
		return -EINVAL;
	}

	if (Nrf::Matter::OtaSimState::CommitAppliedVersion(requestor->GetTargetVersion()) != 0) {
		return -EIO;
	}

	ChipLogProgress(SoftwareUpdate, "OTA sim: scheduled apply for version %u",
			static_cast<unsigned>(requestor->GetTargetVersion()));

	return 0;
}

int mcuboot_swap_type(void)
{
	if (Nrf::Matter::OtaSimState::IsFirstBootPending()) {
		return BOOT_SWAP_TYPE_REVERT;
	}

	return BOOT_SWAP_TYPE_NONE;
}

bool boot_is_img_confirmed(void)
{
	return !Nrf::Matter::OtaSimState::IsFirstBootPending();
}

int boot_write_img_confirmed(void)
{
	if (!Nrf::Matter::OtaSimState::IsFirstBootPending()) {
		return 0;
	}

	Nrf::Matter::OtaSimState::ClearFirstBootPending();
	ChipLogProgress(SoftwareUpdate, "OTA sim: image confirmed");

	return 0;
}

} /* extern "C" */
