/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <stdint.h>

struct device;

#ifdef __cplusplus
extern "C" {
#endif

void st25dac_i2c_port_set(const struct device *i2c, uint8_t addr_7bit);

/** Idempotent bind from devicetree (safe to call before first I2C transfer). */
void st25dac_i2c_ensure_bound(void);

const struct device *st25dac_i2c_port_dev(void);

uint8_t st25dac_i2c_port_addr(void);

#ifdef __cplusplus
}
#endif
