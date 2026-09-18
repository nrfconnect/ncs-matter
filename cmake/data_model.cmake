#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#

if(NOT CHIP_ROOT)
  set(CHIP_ROOT ${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR})
endif()

if(CONFIG_MATTER_ZAP_GENERATION_BUILD_TIME)
  include(${CMAKE_CURRENT_LIST_DIR}/zap_install.cmake)
  include(${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR}/src/app/chip_data_model.cmake)
elseif(CONFIG_MATTER_ZAP_GENERATION_STATIC)
  include(${CMAKE_CURRENT_LIST_DIR}/chip_data_model_static.cmake)
endif()

function(ncs_configure_data_model)
  string(CONFIGURE "${CONFIG_MATTER_ZAP_FILE_PATH}" zap_file_path)
  cmake_path(GET zap_file_path PARENT_PATH zap_parent_dir)

  cmake_parse_arguments(ARG "" "" "EXTERNAL_CLUSTERS" ${ARGN})

  target_include_directories(matter-data-model
    PUBLIC
    ${zap_parent_dir}
  )

  if(CONFIG_MATTER_ZAP_GENERATION_BUILD_TIME)
    ncs_matter_ensure_zap_cli()

    chip_configure_data_model(matter-data-model
      ZAP_FILE ${zap_file_path}
      ZCL_PATH ${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR}/src/app/zap-templates/zcl/zcl.json
      EXTERNAL_CLUSTERS ${ARG_EXTERNAL_CLUSTERS}
    )

    target_include_directories(app PRIVATE
      $<TARGET_PROPERTY:matter-data-model,INCLUDE_DIRECTORIES>
    )
  elseif(CONFIG_MATTER_ZAP_GENERATION_STATIC)
    chip_configure_data_model_static(matter-data-model
      BYPASS_IDL
      GEN_DIR ${zap_parent_dir}/zap-generated
      ZAP_FILE ${zap_file_path}
      EXTERNAL_CLUSTERS ${ARG_EXTERNAL_CLUSTERS}
    )
  else()
    message(WARNING "Unsupported ZAP generation type")
  endif()
endfunction()
