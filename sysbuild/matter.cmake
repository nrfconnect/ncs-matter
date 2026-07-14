
#
# Copyright (c) 2026 Nordic Semiconductor
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#


if(SB_CONFIG_ZEPHYR_CONNECTEDHOMEIP_MODULE AND SB_CONFIG_MATTER_ADD_ON AND SB_CONFIG_MATTER_ADD_ON_FACTORY_DATA_GENERATE)

  include(${ZEPHYR_NRF_MODULE_DIR}/sysbuild/image_flasher.cmake)
  add_image_flasher(
    NAME matter_factory_data
    HEX_FILE "${CMAKE_BINARY_DIR}/matter_factory_data/zephyr/factory_data.hex"
  )

  if(SB_CONFIG_MERGED_HEX_FILES)
    set(board_target)
    sysbuild_get(board_target IMAGE ${DEFAULT_IMAGE} VAR CONFIG_BOARD_TARGET KCONFIG)
    string(REPLACE "/" "_" board_target ${board_target})
    string(REPLACE "@" "_" board_target ${board_target})

    set_property(GLOBAL APPEND
      PROPERTY sysbuild_merged_hex_dependencies_${board_target} factory_data
    )

    set(board_target)
  endif()
endif()
