# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

if(CONFIG_FPU)
  if(CONFIG_FP_HARDABI)
    set(float_dir hard-float)
  elseif(CONFIG_FP_SOFTABI)
    set(float_dir softfp-float)
  else()
    message(FATAL_ERROR "Unsupported FP ABI for ST25DA-C library")
  endif()
else()
  set(float_dir soft-float)
endif()

set(ST25DAC_LIB_DIR ${ZEPHYR_NCS_MATTER_MODULE_DIR}/lib/st25dac/${GCC_M_CPU}/${float_dir})
set(ST25DAC_EXPORT_DIR ${CMAKE_BINARY_DIR}/st25dac_export/${GCC_M_CPU}/${float_dir})
set(ST25DAC_MASTERKEYS_H ${ZEPHYR_NCS_MATTER_MODULE_DIR}/drivers/st25dac/masterkeys_nda.h)

if(CONFIG_ST25DAC AND NOT EXISTS ${ST25DAC_MASTERKEYS_H})
  message(FATAL_ERROR "Missing ${ST25DAC_MASTERKEYS_H} (SCP03 keys)")
endif()

if(CONFIG_ST25DAC_BUILD_FROM_SOURCE)
  include(${CMAKE_CURRENT_LIST_DIR}/st25dac.cmake)
else()
  if(NOT EXISTS ${ST25DAC_LIB_DIR}/libst25dac.a)
    message(FATAL_ERROR
      "No prebuilt libst25dac.a for ${GCC_M_CPU}/${float_dir} at ${ST25DAC_LIB_DIR}. "
      "Enable ST25DAC_BUILD_FROM_SOURCE or add the prebuilt library.")
  endif()

  zephyr_library_import(st25dac ${ST25DAC_LIB_DIR}/libst25dac.a)
  target_link_libraries(st25dac INTERFACE mbedTLS chip)
endif()

# Devicetree + SCP03 master keys (symbols satisfy libst25dac.a).
zephyr_library_named(st25dac_board_glue)
zephyr_library_sources(
  ${CMAKE_CURRENT_LIST_DIR}/st25dac_i2c_zephyr.c
  ${CMAKE_CURRENT_LIST_DIR}/st25dac_gpio_zephyr.c
  ${CMAKE_CURRENT_LIST_DIR}/st25dac_master_keys_port.c
)
zephyr_library_include_directories(
  ${CMAKE_CURRENT_LIST_DIR}
  ${ZEPHYR_NCS_MATTER_MODULE_DIR}
)
target_link_libraries(st25dac INTERFACE st25dac_board_glue)
