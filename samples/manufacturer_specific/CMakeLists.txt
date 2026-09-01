#
# Copyright (c) 2025 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#

cmake_minimum_required(VERSION 3.20.0)

include(${CMAKE_CURRENT_LIST_DIR}/../../cmake/find_zephyr.cmake)

project(matter-manufacturer_specific)

include(${ZEPHYR_NCS_MATTER_MODULE_DIR}/cmake/zap_helpers.cmake)
ncs_get_zap_parent_dir(ZAP_PARENT_DIR)

# Override zap-generated directory.
get_filename_component(CHIP_APP_ZAP_DIR ${ZAP_PARENT_DIR}/zap-generated REALPATH CACHE)

# NORDIC SDK APP START

include(${ZEPHYR_NCS_MATTER_MODULE_DIR}/cmake/data_model.cmake)

target_include_directories(app PRIVATE
  src
  ${ZAP_PARENT_DIR}
)

target_sources(app PRIVATE
  src/app_task.cpp
  src/zcl_callbacks.cpp
  src/main.cpp
  src/basic_information_extension.cpp
)

ncs_configure_data_model(
  EXTERNAL_CLUSTERS "NORDIC_DEV_KIT_CLUSTER"
)
# NORDIC SDK APP END
