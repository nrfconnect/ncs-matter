#
# Copyright (c) 2026 Nordic Semiconductor
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#

#########################################################
# Actions to be performed before the CMake is run       #
#########################################################
function(${SYSBUILD_CURRENT_MODULE_NAME}_pre_cmake)
endfunction(${SYSBUILD_CURRENT_MODULE_NAME}_pre_cmake)

#########################################################
# Actions to be performed before the each Image is built#
#########################################################
function(${SYSBUILD_CURRENT_MODULE_NAME}_pre_image_cmake)

    if(SB_CONFIG_ZEPHYR_CONNECTEDHOMEIP_MODULE AND SB_CONFIG_MATTER_ADD_ON)
    set_config_bool(${DEFAULT_IMAGE} CONFIG_CHIP y)
    if(SB_CONFIG_MATTER_ADD_ON_OTA)
        set_config_bool(${DEFAULT_IMAGE} CONFIG_CHIP_OTA_REQUESTOR y)
        set_config_bool(${DEFAULT_IMAGE} CONFIG_CHIP_OTA_IMAGE_BUILD y)
    else()
        set_config_bool(${DEFAULT_IMAGE} CONFIG_CHIP_OTA_REQUESTOR n)
        set_config_bool(${DEFAULT_IMAGE} CONFIG_CHIP_OTA_IMAGE_BUILD n)
    endif()
    else()
    set_config_bool(${DEFAULT_IMAGE} CONFIG_CHIP n)
    endif()

endfunction(${SYSBUILD_CURRENT_MODULE_NAME}_pre_image_cmake)

#########################################################
# Actions to be performed after the Images are built    #
#########################################################
function(${SYSBUILD_CURRENT_MODULE_NAME}_post_image_cmake)
endfunction(${SYSBUILD_CURRENT_MODULE_NAME}_post_image_cmake)

#########################################################
# Actions to be performed after the CMake is run        #
#########################################################
function(${SYSBUILD_CURRENT_MODULE_NAME}_post_cmake)
  # Matter related configurations
  if(SB_CONFIG_ZEPHYR_CONNECTEDHOMEIP_MODULE AND SB_CONFIG_MATTER_ADD_ON)
    if(SB_CONFIG_MATTER_ADD_ON_FACTORY_DATA_GENERATE)
      include(${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR}/config/nrfconnect/chip-module/generate_factory_data.cmake)
      nrfconnect_generate_factory_data()
    endif()

    if(SB_CONFIG_MATTER_ADD_ON_OTA AND SB_CONFIG_DFU_MULTI_IMAGE_PACKAGE_BUILD)
      include(${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR}/config/zephyr/ota-image_sysbuild.cmake)
      chip_ota_image(chip-ota-image
        INPUT_FILES ${CMAKE_BINARY_DIR}/dfu_multi_image.bin
        OUTPUT_FILE ${CMAKE_BINARY_DIR}/${SB_CONFIG_MATTER_ADD_ON_OTA_IMAGE_FILE_NAME}
      )
    endif()
  endif()

endfunction(${SYSBUILD_CURRENT_MODULE_NAME}_post_cmake)

#########################################################
# CMAKE Includes                                        #
#########################################################
include(${CMAKE_CURRENT_LIST_DIR}/matter.cmake)
