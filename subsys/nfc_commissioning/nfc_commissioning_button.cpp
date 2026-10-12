/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "nfc_commissioning/nfc_unpowered_commissioning.h"

#include <dk_buttons_and_leds.h>
#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

static void nfc_commissioning_button_handler(uint32_t button_state, uint32_t has_changed)
{
	if ((has_changed & DK_BTN4_MSK) && (button_state & DK_BTN4_MSK)) {
		chip::DeviceLayer::NfcCommissioning::Instance().RequestRun();
	}
}

extern "C" void NfcCommissioningButtonInit(void)
{
	static struct button_handler handler = {
		.cb = nfc_commissioning_button_handler,
	};

	dk_button_handler_add(&handler);
}
