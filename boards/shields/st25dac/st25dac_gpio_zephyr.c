/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Application-side GPIO port for ST25DA-C (devicetree + storage). Not part of libst25dac.a.
 */

#include "st25dac_gpio_port.h"

#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>

#define ST25DAC_NODE DT_NODELABEL(st25dac)

#if !DT_NODE_EXISTS(ST25DAC_NODE)
#error "No st,st25dac node found in devicetree"
#endif

static const struct gpio_dt_spec sCtrlGpio = GPIO_DT_SPEC_GET(ST25DAC_NODE, ctrl_gpios);
static const struct gpio_dt_spec sVccGpio  = GPIO_DT_SPEC_GET(ST25DAC_NODE, vcc_gpios);

static const struct gpio_dt_spec *sCtrlPort;
static const struct gpio_dt_spec *sVccPort;

void st25dac_gpio_port_set(const struct gpio_dt_spec *ctrl, const struct gpio_dt_spec *vcc)
{
	sCtrlPort = ctrl;
	sVccPort  = vcc;
}

const struct gpio_dt_spec *st25dac_gpio_port_ctrl(void)
{
	return sCtrlPort;
}

const struct gpio_dt_spec *st25dac_gpio_port_vcc(void)
{
	return sVccPort;
}

void st25dac_gpio_port_ensure_bound(void)
{
	if (sCtrlPort != NULL) {
		return;
	}

	if (!gpio_is_ready_dt(&sCtrlGpio) || !gpio_is_ready_dt(&sVccGpio)) {
		return;
	}

	st25dac_gpio_port_set(&sCtrlGpio, &sVccGpio);
}

static int st25dac_gpio_bind_init(void)
{
	st25dac_gpio_port_ensure_bound();
	return 0;
}

SYS_INIT(st25dac_gpio_bind_init, POST_KERNEL, CONFIG_APPLICATION_INIT_PRIORITY);
