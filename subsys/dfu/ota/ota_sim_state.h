/*
 * Copyright (c) 2025 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#pragma once

#include <stdint.h>

namespace Nrf::Matter::OtaSimState
{

/** Persist target software version and first-boot-after-apply flag, then reboot. */
int CommitAppliedVersion(uint32_t version);

bool LoadActiveVersion(uint32_t &version);
bool IsFirstBootPending();
void ClearFirstBootPending();

} /* namespace Nrf::Matter::OtaSimState */
