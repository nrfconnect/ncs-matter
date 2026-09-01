/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#pragma once

/**
 * Matter CHIP overrides for native_sim (include from the sample chip_project_config.h).
 *
 * Uses host BSD sockets on ARCH_POSIX, matching Matter nrfconnect test_driver.
 * Do not enable CONFIG_NET_NATIVE_OFFLOADED_SOCKETS here — ZephyrSocket.h
 * conflicts with host sys/select.h on native_sim.
 */

#ifdef CONFIG_ARCH_POSIX
#define CHIP_SYSTEM_CONFIG_USE_POSIX_TIME_FUNCTS 1
#define CHIP_SYSTEM_CONFIG_USE_ZEPHYR_SOCKETS 0
#define CHIP_SYSTEM_CONFIG_USE_ZEPHYR_SOCKET_EXTENSIONS 0
#define CHIP_SYSTEM_CONFIG_USE_ZEPHYR_NET_IF 0
#define CHIP_SYSTEM_CONFIG_USE_BSD_IFADDRS 1
#define CHIP_CONFIG_LAMBDA_EVENT_SIZE 48
#endif
