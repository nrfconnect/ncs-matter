#
# Copyright (c) 2023 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr HINTS $ENV{ZEPHYR_BASE})

project(matter-thermostat)

# NORDIC SDK APP START

# Include all source files that are located in the Matter common directory.
include(${ZEPHYR_NCS_MATTER_MODULE_DIR}/cmake/sample.cmake)

ncs_get_zap_parent_dir(ZAP_PARENT_DIR)

target_include_directories(app PRIVATE
  src
  ${ZAP_PARENT_DIR}
)

target_sources(app PRIVATE
  src/app_task.cpp
  src/main.cpp
  src/temp_sensor_manager.cpp
  src/temperature_manager.cpp
  src/temperature_measurement/sensor.cpp
  src/zcl_callbacks.cpp
  ${ZEPHYR_NCS_MATTER_MODULE_DIR}/subsys/binding/binding_handler.cpp
)

ncs_configure_data_model()
# NORDIC SDK APP END
