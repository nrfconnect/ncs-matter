/*
 * Copyright (c) 2023 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#pragma once

#include <zephyr/devicetree.h>

#ifdef CONFIG_DK_LIBRARY
#include <dk_buttons_and_leds.h>
#endif

#define LEDS_NODE_ID DT_PATH(leds)
#define INCREMENT_BY_ONE(button_or_led) +1
#define NUMBER_OF_LEDS (0 DT_FOREACH_CHILD(LEDS_NODE_ID, INCREMENT_BY_ONE))

#if DT_NODE_EXISTS(DT_PATH(buttons))
#define BUTTONS_NODE_ID DT_PATH(buttons)
#define NUMBER_OF_BUTTONS (0 DT_FOREACH_CHILD(BUTTONS_NODE_ID, INCREMENT_BY_ONE))
#else
#define NUMBER_OF_BUTTONS 0
#endif

#ifdef CONFIG_DK_LIBRARY
#define FUNCTION_BUTTON DK_BTN1
#define FUNCTION_BUTTON_MASK DK_BTN1_MSK

#ifndef BLUETOOTH_ADV_BUTTON
#define BLUETOOTH_ADV_BUTTON DK_BTN1
#endif
#define BLUETOOTH_ADV_BUTTON_MASK BIT(BLUETOOTH_ADV_BUTTON)
#else
#define FUNCTION_BUTTON 0
#define FUNCTION_BUTTON_MASK 0
#define BLUETOOTH_ADV_BUTTON 0
#define BLUETOOTH_ADV_BUTTON_MASK 0
#endif
