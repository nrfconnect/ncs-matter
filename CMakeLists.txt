# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0
#
# This CMake file is picked by the Zephyr build system because it is defined
# as the module CMake entry point (see zephyr/module.yml).

if(CONFIG_CHIP)
  # Enable GNU STD support.
  include(${CONFIG_MATTER_ROOT_PATH}/config/nrfconnect/app/enable-gnu-std.cmake)

  add_subdirectory(subsys)
endif()
