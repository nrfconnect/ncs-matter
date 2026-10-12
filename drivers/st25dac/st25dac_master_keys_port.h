/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * SCP03 master key delivery for libst25dac.a (implementation in st25dac_board_glue).
 */

#pragma once

#include <stdint.h>

#define ST25DAC_SCP03_KEY_LEN 32U

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
	ST25DAC_MASTER_KEYS_NONE = 0,
	ST25DAC_MASTER_KEYS_ISD,
	ST25DAC_MASTER_KEYS_SSD,
	/** Keys used after pairing (non-production KVN). */
	ST25DAC_MASTER_KEYS_PAIRED,
	/** Keys programmed on tag via NFCTAG_pairingKeys(). */
	ST25DAC_MASTER_KEYS_PAIRING,
} st25dac_master_key_role_t;

/**
 * @brief Return SCP03 master key triple for @p role.
 *
 * @return 0 on success; -EINVAL if @p role is unknown.
 *         @p kenc, @p kmac, @p kdek point at stable 32-byte buffers.
 */
int st25dac_master_keys_get(st25dac_master_key_role_t role, const uint8_t **kenc, const uint8_t **kmac,
			    const uint8_t **kdek);

#ifdef __cplusplus
}
#endif
