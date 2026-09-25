#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
# Sysbuild helpers for Matter samples on native_sim / native_sim/native/64.

function(matter_native_sim_sysbuild_pre_cmake)
  if(NOT BOARD MATCHES "native_sim")
    return()
  endif()

  sysbuild_cache_set(VAR ${DEFAULT_IMAGE}_SNIPPET APPEND REMOVE_DUPLICATES native-sim)
endfunction()

function(matter_native_sim_sysbuild_post_cmake)
  if(NOT BOARD MATCHES "native_sim")
    return()
  endif()

  native_simulator_set_final_executable(${DEFAULT_IMAGE})
endfunction()
