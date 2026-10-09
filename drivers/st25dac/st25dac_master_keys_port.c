/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * SCP03 master key material for ST25DA-C (linked via st25dac_board_glue).
 */

#include "drivers/st25dac/st25dac_master_keys_port.h"
#include "masterkeys_nda.h"

#include <errno.h>
#include <stddef.h>

static const uint8_t s_zero_keys[ST25DAC_SCP03_KEY_LEN];

static void set_triple(const uint8_t **kenc, const uint8_t **kmac, const uint8_t **kdek,
		       const uint8_t *enc, const uint8_t *mac, const uint8_t *dek)
{
	*kenc = enc;
	*kmac = mac;
	*kdek = dek;
}

int st25dac_master_keys_get(st25dac_master_key_role_t role, const uint8_t **kenc, const uint8_t **kmac,
			    const uint8_t **kdek)
{
	if (kenc == NULL || kmac == NULL || kdek == NULL) {
		return -EINVAL;
	}

	switch (role) {
	case ST25DAC_MASTER_KEYS_NONE:
		set_triple(kenc, kmac, kdek, s_zero_keys, s_zero_keys, s_zero_keys);
		return 0;
	case ST25DAC_MASTER_KEYS_ISD:
		set_triple(kenc, kmac, kdek, (const uint8_t *)NFC_MASTERKEY_ISD_KENC,
			   (const uint8_t *)NFC_MASTERKEY_ISD_KMAC, (const uint8_t *)NFC_MASTERKEY_ISD_KDEK);
		return 0;
	case ST25DAC_MASTER_KEYS_SSD:
		set_triple(kenc, kmac, kdek, (const uint8_t *)NFC_MASTERKEY_SSD_KENC,
			   (const uint8_t *)NFC_MASTERKEY_SSD_KMAC, (const uint8_t *)NFC_MASTERKEY_SSD_KDEK);
		return 0;
	case ST25DAC_MASTER_KEYS_PAIRED:
	case ST25DAC_MASTER_KEYS_PAIRING:
		set_triple(kenc, kmac, kdek, (const uint8_t *)NFC_MASTERKEY_PAIRING_KENC,
			   (const uint8_t *)NFC_MASTERKEY_PAIRING_KMAC,
			   (const uint8_t *)NFC_MASTERKEY_PAIRING_KDEK);
		return 0;
	default:
		return -EINVAL;
	}
}
