/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Application-side I2C port for ST25DA-C (devicetree + storage). Not part of libst25dac.a.
 */

#include "st25dac_i2c_port.h"

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/init.h>

#define ST25DAC_NODE DT_NODELABEL(st25dac)

#if !DT_NODE_EXISTS(ST25DAC_NODE)
#error "No st,st25dac node found in devicetree"
#endif

static const struct device *sI2cDev;
static uint8_t sI2cAddr;

void st25dac_i2c_port_set(const struct device *i2c, uint8_t addr_7bit)
{
	sI2cDev = i2c;
	sI2cAddr = addr_7bit;
}

const struct device *st25dac_i2c_port_dev(void)
{
	return sI2cDev;
}

uint8_t st25dac_i2c_port_addr(void)
{
	return sI2cAddr;
}

void st25dac_i2c_ensure_bound(void)
{
	const struct device *i2c;

	if (sI2cDev != NULL) {
		return;
	}

	i2c = DEVICE_DT_GET(DT_BUS(ST25DAC_NODE));
	if (!device_is_ready(i2c)) {
		return;
	}

	st25dac_i2c_port_set(i2c, DT_REG_ADDR(ST25DAC_NODE));
}

static int st25dac_i2c_bind_init(void)
{
	st25dac_i2c_ensure_bound();
	return 0;
}

SYS_INIT(st25dac_i2c_bind_init, POST_KERNEL, CONFIG_APPLICATION_INIT_PRIORITY);
