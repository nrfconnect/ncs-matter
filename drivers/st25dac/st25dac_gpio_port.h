/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Board-specific CTRL/VCC GPIO selection (bound from devicetree in app glue).
 */

#pragma once

#include <stdbool.h>

struct gpio_dt_spec;

#ifdef __cplusplus
extern "C" {
#endif

void st25dac_gpio_port_set(const struct gpio_dt_spec *ctrl, const struct gpio_dt_spec *vcc);

/** Idempotent bind from devicetree (safe before first GPIO / I2C use). */
void st25dac_gpio_port_ensure_bound(void);

const struct gpio_dt_spec *st25dac_gpio_port_ctrl(void);

const struct gpio_dt_spec *st25dac_gpio_port_vcc(void);

#ifdef __cplusplus
}
#endif
