/*
 * Copyright (c) 2025 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#include "ota_sim_state.h"

#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

namespace
{
constexpr char kActiveVersionKey[] = "matter/ota_sim/active_ver";
constexpr char kFirstBootKey[] = "matter/ota_sim/first_boot";

int SaveU32(const char *key, uint32_t value)
{
	return settings_save_one(key, &value, sizeof(value));
}

int SaveU8(const char *key, uint8_t value)
{
	return settings_save_one(key, &value, sizeof(value));
}

bool LoadU32(const char *key, uint32_t &value)
{
	ssize_t len = settings_load_one(key, &value, sizeof(value));

	return len == static_cast<ssize_t>(sizeof(value));
}

bool LoadU8(const char *key, uint8_t &value)
{
	ssize_t len = settings_load_one(key, &value, sizeof(value));

	return len == static_cast<ssize_t>(sizeof(value));
}

} /* namespace */

namespace Nrf::Matter::OtaSimState
{

int CommitAppliedVersion(uint32_t version)
{
	const uint8_t firstBoot = 1;
	int err = SaveU32(kActiveVersionKey, version);

	if (err == 0) {
		err = SaveU8(kFirstBootKey, firstBoot);
	}

	if (err != 0) {
		LOG_ERR("Failed to persist OTA sim state: %d", err);
	}

	return err;
}

bool LoadActiveVersion(uint32_t &version)
{
	return LoadU32(kActiveVersionKey, version);
}

bool IsFirstBootPending()
{
	uint8_t pending = 0;

	return LoadU8(kFirstBootKey, pending) && pending != 0;
}

void ClearFirstBootPending()
{
	const uint8_t cleared = 0;

	(void)SaveU8(kFirstBootKey, cleared);
}

} /* namespace Nrf::Matter::OtaSimState */
