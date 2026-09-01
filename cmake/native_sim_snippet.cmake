#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
# Include before find_package(Zephyr) in Matter sample CMakeLists.txt, e.g.:
#   include(${ZEPHYR_NCS_MATTER_MODULE_DIR}/cmake/native_sim_snippet.cmake)

if(DEFINED BOARD AND BOARD MATCHES "native_sim")
  if(DEFINED SNIPPET)
    set(SNIPPET "${SNIPPET};native-sim")
  else()
    set(SNIPPET "native-sim")
  endif()
endif()
