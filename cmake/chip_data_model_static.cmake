#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
# Static ZAP/data-model configuration for NCS Matter samples.
# Moved from connectedhomeip to keep Nordic-specific build-time generation
# out of the upstream Matter tree.

if(NOT CHIP_ROOT)
  set(CHIP_ROOT ${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR})
endif()

set(CHIP_APP_BASE_DIR ${CHIP_ROOT}/src/app)

if(NOT CHIP_APP_ZAP_DIR)
  get_filename_component(CHIP_APP_ZAP_DIR ${CHIP_ROOT}/zzz_generated/app-common REALPATH)
endif()

include(${CMAKE_CURRENT_LIST_DIR}/chip_codegen_static.cmake)
include(${CHIP_ROOT}/src/data-model-providers/codegen/model.cmake)

function(chip_configure_cluster APP_TARGET CLUSTER)
  set(CLUSTER_DIR "${CHIP_APP_BASE_DIR}/clusters/${CLUSTER}")
  include("${CLUSTER_DIR}/app_config_dependent_sources.cmake")
endfunction()

function(chip_configure_zap_file APP_TARGET ZAP_FILE EXTERNAL_CLUSTERS)
  find_package(Python3 REQUIRED)
  set(args --zap_file ${ZAP_FILE})

  if(EXTERNAL_CLUSTERS)
    list(APPEND args --external-clusters ${EXTERNAL_CLUSTERS})
  endif()

  execute_process(
    COMMAND ${Python3_EXECUTABLE} ${CHIP_APP_BASE_DIR}/zap_cluster_list.py ${args}
    OUTPUT_VARIABLE CLUSTER_LIST
    ERROR_VARIABLE ERROR_MESSAGE
    RESULT_VARIABLE RC
  )

  if(NOT RC EQUAL 0)
    message(FATAL_ERROR "Failed to execute zap_cluster_list.py: ${ERROR_MESSAGE}")
  endif()

  string(REPLACE "\n" ";" CLUSTER_LIST "${CLUSTER_LIST}")

  foreach(CLUSTER ${CLUSTER_LIST})
    chip_configure_cluster(${APP_TARGET} ${CLUSTER})
  endforeach()
endfunction()

function(chip_configure_data_model_static APP_TARGET)
  set(SCOPE PRIVATE)
  cmake_parse_arguments(ARG "BYPASS_IDL" "SCOPE;ZAP_FILE;GEN_DIR;IDL;ZCL_PATH" "EXTERNAL_CLUSTERS" ${ARGN})

  if(ARG_SCOPE)
    set(SCOPE ${ARG_SCOPE})
  endif()

  target_sources(${APP_TARGET} ${SCOPE}
    ${CHIP_APP_BASE_DIR}/SafeAttributePersistenceProvider.cpp
    ${CHIP_APP_BASE_DIR}/StorageDelegateWrapper.cpp
    ${CHIP_APP_BASE_DIR}/server/AclStorage.cpp
    ${CHIP_APP_BASE_DIR}/server/CommissioningWindowManager.cpp
    ${CHIP_APP_BASE_DIR}/server/DefaultAclStorage.cpp
    ${CHIP_APP_BASE_DIR}/server/DefaultTermsAndConditionsProvider.cpp
    ${CHIP_APP_BASE_DIR}/server/Dnssd.cpp
    ${CHIP_APP_BASE_DIR}/server/EchoHandler.cpp
    ${CHIP_APP_BASE_DIR}/server/Server.cpp
  )

  target_compile_options(${APP_TARGET} ${SCOPE}
    "-DCHIP_ADDRESS_RESOLVE_IMPL_INCLUDE_HEADER=<lib/address_resolve/AddressResolve_DefaultImpl.h>"
  )

  if(ARG_ZAP_FILE)
    chip_configure_zap_file(${APP_TARGET} ${ARG_ZAP_FILE} "${ARG_EXTERNAL_CLUSTERS}")

    if(NOT ARG_IDL)
      string(REPLACE ".zap" ".matter" ARG_IDL ${ARG_ZAP_FILE})
    endif()
  endif()

  if(ARG_IDL)
    chip_codegen(${APP_TARGET}-codegen
      INPUT "${ARG_IDL}"
      GENERATOR "cpp-app"
      OUTPUTS
      "app/PluginApplicationCallbacks.h"
      "app/callback-stub.cpp"
      "app/cluster-callbacks.cpp"
      "app/static-cluster-config/{{server_cluster_name}}.h"
      OUTPUT_PATH APP_GEN_DIR
      OUTPUT_FILES APP_GEN_FILES
    )

    target_include_directories(${APP_TARGET} ${SCOPE} "${APP_GEN_DIR}")
    add_dependencies(${APP_TARGET} ${APP_TARGET}-codegen)

    if(NOT ARG_BYPASS_IDL)
      chip_zapgen(${APP_TARGET}-zapgen
        INPUT "${ARG_ZAP_FILE}"
        GENERATOR "app-templates"
        OUTPUTS
        "zap-generated/access.h"
        "zap-generated/endpoint_config.h"
        "zap-generated/gen_config.h"
        "zap-generated/IMClusterCommandHandler.cpp"
        "zap-generated/CodeDrivenInitShutdown.cpp"
        "zap-generated/CodeDrivenCallback.h"
        OUTPUT_PATH APP_TEMPLATES_GEN_DIR
        OUTPUT_FILES APP_TEMPLATES_GEN_FILES
        ZCL_PATH ${ARG_ZCL_PATH}
      )
      target_include_directories(${APP_TARGET} ${SCOPE} "${APP_TEMPLATES_GEN_DIR}")
      add_dependencies(${APP_TARGET} ${APP_TARGET}-zapgen)
    else()
      target_compile_definitions(${APP_TARGET} PRIVATE CHIP_BYPASS_IDL)
      target_include_directories(${APP_TARGET} ${SCOPE} ${ARG_GEN_DIR})
      set(APP_GEN_FILES
        ${ARG_GEN_DIR}/callback-stub.cpp
        ${ARG_GEN_DIR}/IMClusterCommandHandler.cpp
        ${ARG_GEN_DIR}/CodeDrivenInitShutdown.cpp
      )
    endif()
  endif()

  target_sources(${APP_TARGET} ${SCOPE}
    ${CHIP_APP_BASE_DIR}/icd/server/ICDMonitoringTable.cpp
    ${CHIP_APP_BASE_DIR}/icd/server/ICDNotifier.cpp
    ${CHIP_APP_BASE_DIR}/icd/server/ICDConfigurationData.cpp
  )

  target_sources(${APP_TARGET} ${SCOPE}
    ${CHIP_APP_BASE_DIR}/../../zzz_generated/app-common/app-common/zap-generated/cluster-objects.cpp
  )

  target_sources(${APP_TARGET} ${SCOPE}
    ${CHIP_APP_ZAP_DIR}/app-common/zap-generated/attributes/Accessors.cpp
    ${CHIP_APP_BASE_DIR}/reporting/reporting.cpp
    ${CHIP_APP_BASE_DIR}/util/attribute-storage.cpp
    ${CHIP_APP_BASE_DIR}/util/attribute-table.cpp
    ${CHIP_APP_BASE_DIR}/util/DataModelHandler.cpp
    ${CHIP_APP_BASE_DIR}/util/ember-io-storage.cpp
    ${CHIP_APP_BASE_DIR}/util/generic-callback-stubs.cpp
    ${CHIP_APP_BASE_DIR}/util/privilege-storage.cpp
    ${CHIP_APP_BASE_DIR}/util/util.cpp
    ${CHIP_APP_BASE_DIR}/persistence/AttributePersistenceProviderInstance.cpp
    ${CHIP_APP_BASE_DIR}/persistence/DefaultAttributePersistenceProvider.cpp
    ${CODEGEN_DATA_MODEL_SOURCES}
    ${APP_GEN_FILES}
    ${APP_TEMPLATES_GEN_FILES}
  )
endfunction()
