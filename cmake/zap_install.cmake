#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
# Ensures zap-cli is installed and resolvable on PATH for build-time ZAP
# code generation, without touching upstream Matter SDK CMake code.

if(NCS_MATTER_ZAP_INSTALL_SETUP)
  return()
endif()
set(NCS_MATTER_ZAP_INSTALL_SETUP TRUE)

find_package(Python3 REQUIRED)

set(NCS_MATTER_ZAP_INSTALL_SCRIPT "${ZEPHYR_NCS_MATTER_MODULE_DIR}/scripts/west/zap_install.py")

if(CMAKE_HOST_WIN32)
  set(NCS_MATTER_ZAP_CLI_NAME "zap-cli.exe")
  set(NCS_MATTER_PATH_SEPARATOR ";")
else()
  set(NCS_MATTER_ZAP_CLI_NAME "zap-cli")
  set(NCS_MATTER_PATH_SEPARATOR ":")
endif()

# Makes ${ZAP_CLI_DIR}/zap-cli resolvable via a plain PATH lookup at build
# time. CMake configure-time environment changes never reach the later,
# separate `cmake --build`/ninja invocation, so instead of relying on that,
# this places a symlink (or a copy, e.g. on a Windows machine without
# symlink privilege, or a read-only shared toolchain install) into whichever
# directory already on $ENV{PATH} turns out to be writable. Since $ENV{PATH}
# is inherited unchanged from the same west/CI process for the whole build,
# a directory found writable now stays valid at build time too.
function(ncs_matter_expose_zap_cli ZAP_CLI_DIR)
  set(zap_cli "${ZAP_CLI_DIR}/${NCS_MATTER_ZAP_CLI_NAME}")
  if(NOT EXISTS "${zap_cli}")
    message(FATAL_ERROR "zap-cli was not found in ${ZAP_CLI_DIR}")
  endif()

  get_filename_component(zap_cli_dir_real "${ZAP_CLI_DIR}" REALPATH)
  string(REPLACE "${NCS_MATTER_PATH_SEPARATOR}" ";" path_dirs "$ENV{PATH}")

  foreach(dir IN LISTS path_dirs)
    if(IS_DIRECTORY "${dir}")
      get_filename_component(dir_real "${dir}" REALPATH)
      if("${dir_real}" STREQUAL "${zap_cli_dir_real}")
        return() # zap-cli's own directory is already on PATH
      endif()
    endif()
  endforeach()

  foreach(dir IN LISTS path_dirs)
    if(IS_DIRECTORY "${dir}")
      file(CREATE_LINK "${zap_cli}" "${dir}/${NCS_MATTER_ZAP_CLI_NAME}"
        SYMBOLIC COPY_ON_ERROR RESULT link_result
      )
      if(link_result EQUAL 0)
        return()
      endif()
    endif()
  endforeach()

  message(FATAL_ERROR
    "Could not make zap-cli available on PATH: none of the directories in "
    "$ENV{PATH} are writable. Either fix permissions on one of them, or add "
    "${ZAP_CLI_DIR} to PATH yourself before building.")
endfunction()

function(ncs_matter_ensure_zap_cli)
  string(CONFIGURE "${CONFIG_MATTER_ZAP_CLI_INSTALL_PATH}" manual_zap_dir)

  if(NOT "${manual_zap_dir}" STREQUAL "")
    set(zap_dir "${manual_zap_dir}")
  else()
    set(zap_dir "${CHIP_ROOT}/.zap-install")

    # CHIP_ROOT (and its .zap-install directory) can be shared by multiple
    # concurrent builds (e.g. parallel CI jobs/boards reusing one west
    # workspace checkout). Without this lock, two configures racing to
    # install/replace .zap-install at the same time can corrupt each
    # other's download/extract, e.g. failing with EEXIST or ENOENT.
    file(LOCK "${zap_dir}.lock" TIMEOUT 600 RESULT_VARIABLE lock_result)
    if(NOT lock_result EQUAL 0)
      message(FATAL_ERROR "Failed to acquire ZAP install lock (${zap_dir}.lock): ${lock_result}")
    endif()

    execute_process(
      COMMAND "${Python3_EXECUTABLE}" -X utf8 "${NCS_MATTER_ZAP_INSTALL_SCRIPT}" -m "${CHIP_ROOT}"
      RESULT_VARIABLE zap_install_result
    )

    file(LOCK "${zap_dir}.lock" RELEASE)

    if(NOT zap_install_result EQUAL 0)
      message(FATAL_ERROR "Failed to install Matter ZAP tool")
    endif()
  endif()

  if(NOT IS_DIRECTORY "${zap_dir}")
    message(FATAL_ERROR "ZAP install directory does not exist: ${zap_dir}")
  endif()

  ncs_matter_expose_zap_cli("${zap_dir}")
endfunction()
