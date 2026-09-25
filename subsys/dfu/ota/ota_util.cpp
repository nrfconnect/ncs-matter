/*
 * Copyright (c) 2022 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#include "ota_util.h"

#if CONFIG_CHIP_OTA_REQUESTOR
#include <app/clusters/ota-requestor/BDXDownloader.h>
#include <app/clusters/ota-requestor/CodegenIntegration.h>
#include <app/clusters/ota-requestor/DefaultOTARequestor.h>
#include <app/clusters/ota-requestor/DefaultOTARequestorDriver.h>
#include <app/clusters/ota-requestor/DefaultOTARequestorStorage.h>
#include <app/server/Server.h>
#include <platform/CHIPDeviceLayer.h>
#if defined(CONFIG_ARCH_POSIX) || CONFIG_BOOTLOADER_MCUBOOT
#include <zephyr/dfu/mcuboot.h>
#endif
#endif

#include <lib/support/logging/CHIPLogging.h>

using namespace chip;
using namespace chip::DeviceLayer;

#if CONFIG_CHIP_OTA_REQUESTOR
namespace
{
DefaultOTARequestorStorage sOTARequestorStorage;
DefaultOTARequestorDriver sOTARequestorDriver;
chip::BDXDownloader sBDXDownloader;
chip::DefaultOTARequestor sOTARequestor;

void BindImageProcessorToDownloader(OTAImageProcessorBaseImpl &imageProcessor)
{
#if defined(CONFIG_ARCH_POSIX)
	TEMPORARY_RETURN_IGNORED imageProcessor.Init(&sBDXDownloader);
#else
	imageProcessor.SetOTADownloader(&sBDXDownloader);
#endif
}
} /* namespace */
#endif

namespace Nrf::Matter
{

#if CONFIG_CHIP_OTA_REQUESTOR
OTAImageProcessorBaseImpl &GetOTAImageProcessor()
{
#if defined(CONFIG_ARCH_POSIX)
	return chip::OTAImageProcessorImpl::GetDefaultInstance();
#elif CONFIG_PM_DEVICE && CONFIG_NORDIC_QSPI_NOR
	static OTAImageProcessorBaseImpl sOTAImageProcessor(&ExternalFlashManager::GetInstance());
	return sOTAImageProcessor;
#else
	static OTAImageProcessorBaseImpl sOTAImageProcessor;
	return sOTAImageProcessor;
#endif
}

void InitBasicOTARequestor()
{
	VerifyOrReturn(GetRequestorInstance() == nullptr);

	OTAImageProcessorBaseImpl &imageProcessor = GetOTAImageProcessor();
	BindImageProcessorToDownloader(imageProcessor);
	sBDXDownloader.SetImageProcessorDelegate(&imageProcessor);
	sOTARequestorStorage.Init(Server::GetInstance().GetPersistentStorage());
	TEMPORARY_RETURN_IGNORED sOTARequestor.Init(Server::GetInstance(), sOTARequestorStorage, sOTARequestorDriver,
						    sBDXDownloader, GetOTARequestorAttributes(),
						    GetDefaultOTARequestorEventGenerator());
	chip::SetRequestorInstance(&sOTARequestor);
	sOTARequestorDriver.Init(&sOTARequestor, &imageProcessor);
}

void OtaConfirmNewImage()
{
#if defined(CONFIG_ARCH_POSIX) || CONFIG_BOOTLOADER_MCUBOOT
#ifndef CONFIG_SOC_SERIES_NRF53
	VerifyOrReturn(mcuboot_swap_type() == BOOT_SWAP_TYPE_REVERT);
#endif

	if (!boot_is_img_confirmed()) {
		CHIP_ERROR err = System::MapErrorZephyr(boot_write_img_confirmed());

		if (CHIP_NO_ERROR == err) {
#if !defined(CONFIG_ARCH_POSIX)
			OTAImageProcessorBaseImpl &imageProcessor = GetOTAImageProcessor();
			imageProcessor.SetImageConfirmed();
#endif
			ChipLogProgress(SoftwareUpdate, "New firmware image confirmed");
		} else {
			ChipLogError(SoftwareUpdate,
				     "Failed to confirm firmware image, it will be reverted on the next boot");
		}
	}
#endif
}

#endif

} /* namespace Nrf::Matter */
