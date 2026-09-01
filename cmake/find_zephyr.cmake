#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
# Include from Matter sample CMakeLists.txt instead of find_package(Zephyr):
#   include(${CMAKE_CURRENT_LIST_DIR}/../../cmake/find_zephyr.cmake)

include(${CMAKE_CURRENT_LIST_DIR}/native_sim_snippet.cmake)
find_package(Zephyr HINTS $ENV{ZEPHYR_BASE})
