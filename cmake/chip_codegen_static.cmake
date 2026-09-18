# Run chip code generation.
#
# Arguments:
#   INPUT     - the name of the ".matter" file to use for generation
#   GENERATOR - generator to use for codegen.py
#   OUTPUTS   - EXPECTED output names. MUST match actual outputs
#
#   OUTPUT_PATH  - [OUT] output variable will contain the directory where the
#                  files will be generated
#   OUTPUT_FILES - [OUT] output variable will contain the path of generated files.
#                  suitable to be added within a build target
#
function(chip_codegen TARGET_NAME)
    cmake_parse_arguments(ARG
         ""
         "INPUT;GENERATOR;OUTPUT_PATH;OUTPUT_FILES"
         "OUTPUTS"
         ${ARGN}
    )

    set(CHIP_CODEGEN_PREGEN_DIR "" CACHE PATH "Pre-generated directory to use instead of compile-time code generation.")

    # Python is required for code generation
    find_package(Python3 REQUIRED)

    # Output paths can contain placeholders such as
    # {{defined_cluster_name}} or {{server_cluster_name}}
    #
    # This translates them to the actually fully expanded path.
    execute_process(
            COMMAND "${Python3_EXECUTABLE}" -X utf8 "${CHIP_ROOT}/scripts/codegen_paths.py" "--idl" "${ARG_INPUT}" ${ARG_OUTPUTS}
            OUTPUT_VARIABLE GENERATED_PATHS_OUT
    )
    string(REPLACE "\n" ";" GENERATED_PATHS "${GENERATED_PATHS_OUT}")

    if("${CHIP_CODEGEN_PREGEN_DIR}" STREQUAL "")
        set(GEN_FOLDER "${CMAKE_BINARY_DIR}/gen/${TARGET_NAME}/${ARG_GENERATOR}")

        string(REPLACE ";" "\n" OUTPUT_AS_NEWLINES "${ARG_OUTPUTS}")

        file(MAKE_DIRECTORY "${GEN_FOLDER}")
        file(GENERATE
            OUTPUT "${GEN_FOLDER}/expected.outputs"
            CONTENT "${OUTPUT_AS_NEWLINES}"
        )


        set(OUT_NAMES)
        foreach(NAME IN LISTS GENERATED_PATHS)
            list(APPEND OUT_NAMES "${GEN_FOLDER}/${NAME}")
        endforeach()

        # Python is expected to be in the path
        find_package(Python3 REQUIRED)
        add_custom_command(
            OUTPUT ${OUT_NAMES}
            COMMAND "${Python3_EXECUTABLE}" -X utf8 "${CHIP_ROOT}/scripts/codegen.py"
            ARGS "--generator" "${ARG_GENERATOR}"
                 "--output-dir" "${GEN_FOLDER}"
                 "--expected-outputs" "${GEN_FOLDER}/expected.outputs"
                 "${ARG_INPUT}"
            DEPENDS
                "${ARG_INPUT}"
            VERBATIM
        )

        add_custom_target(${TARGET_NAME} DEPENDS "${OUT_NAMES}")

        # Forward outputs to the parent
        set(${ARG_OUTPUT_FILES} "${OUT_NAMES}" PARENT_SCOPE)
        set(${ARG_OUTPUT_PATH} "${GEN_FOLDER}" PARENT_SCOPE)
    else()
        file(RELATIVE_PATH MATTER_FILE_PATH "${CHIP_ROOT}" ${ARG_INPUT})

        # Removes the trailing file extension to get something like:
        string(REGEX REPLACE "\.matter$" "" CODEGEN_DIR_PATH "${MATTER_FILE_PATH}")


        # Build the final location within the pregen directory
        set(GEN_FOLDER "${CHIP_CODEGEN_PREGEN_DIR}/${CODEGEN_DIR_PATH}/codegen/${ARG_GENERATOR}")

        # Here we have ${CHIP_CODEGEN_PREGEN_DIR}
        set(OUT_NAMES)
        foreach(NAME IN LISTS GENERATED_PATHS)
            list(APPEND OUT_NAMES "${GEN_FOLDER}/${NAME}")
        endforeach()


        set(${ARG_OUTPUT_FILES} "${OUT_NAMES}" PARENT_SCOPE)
        set(${ARG_OUTPUT_PATH} "${GEN_FOLDER}" PARENT_SCOPE)

        # allow adding dependencies to a phony target since no codegen is done
        add_custom_target(${TARGET_NAME})
    endif()
endfunction()

# Run chip code generation using zap
#
# Example usage:
#   chip_zapgen("app"
#      INPUT     "some_file.zap"
#      GENERATOR "app-templates"
#      OUTPUTS
#            "zap-generated/access.h",
#            "zap-generated/endpoint_config.h",
#            "zap-generated/gen_config.h",
#            "zap-generated/IMClusterCommandHandler.cpp"
#     OUTPUT_PATH  DIR_NAME_VAR
#     OUTPUT_FILES  FILE_NAMES_VAR
#     ZCL_PATH     "path/to/custom/zcl.json" # Optional: override default ZCL path
#   )
#
# Arguments:
#   INPUT     - the name of the ".zap" file to use for generation
#   GENERATOR - generator to use, like "app-templates"
#   OUTPUTS   - EXPECTED output names
#
#   OUTPUT_PATH  - [OUT] output variable will contain the directory where the
#                  files will be generated
#
#   OUTPUT_FILES - [OUT] output variable will contain the path of generated files.
#                  suitable to be added within a build target
#   ZCL_PATH     - [OPTIONAL] Path to a custom ZCL JSON file.
#                  This maps to the '--zcl' argument in the "scripts/tools/zap/generate.py" script.
#                  By default, generate.py attempts to autodetect the ZCL path from the .zap
#                  file which is often a relative path. When the .zap file is relocated or symlinked,
#                  these relative paths become invalid, causing the build to fail.
#                  Passing ZCL_PATH explicitly via CMake ensures the build remains robust and portable.
#                  If ZCL_PATH is not provided, the default behavior is preserved unless CHIP_ENABLE_ZCL_ARG
#                  is enabled, in which case the default path "src/app/zap-templates/zcl/zcl.json" is
#                  automatically injected to simplify usage.
#
function(chip_zapgen TARGET_NAME)
    cmake_parse_arguments(ARG
         ""
         "INPUT;GENERATOR;OUTPUT_PATH;OUTPUT_FILES;ZCL_PATH"
         "OUTPUTS"
         ${ARGN}
    )

    set(CHIP_CODEGEN_PREGEN_DIR "" CACHE PATH "Pre-generated directory to use instead of compile-time code generation.")

    if("${CHIP_CODEGEN_PREGEN_DIR}" STREQUAL "")
        set(GEN_FOLDER "${CMAKE_BINARY_DIR}/gen/${TARGET_NAME}/zapgen/${ARG_GENERATOR}")

        string(REPLACE ";" "\n" OUTPUT_AS_NEWLINES "${ARG_OUTPUTS}")

        file(MAKE_DIRECTORY "${GEN_FOLDER}")
        file(GENERATE
            OUTPUT "${GEN_FOLDER}/expected.outputs"
            CONTENT "${OUTPUT_AS_NEWLINES}"
        )

        set(OUT_NAMES)
        foreach(NAME IN LISTS ARG_OUTPUTS)
            list(APPEND OUT_NAMES "${GEN_FOLDER}/${NAME}")
        endforeach()

        if("${ARG_GENERATOR}" STREQUAL "app-templates")
            SET(TEMPLATE_PATH "${CHIP_ROOT}/src/app/zap-templates/app-templates.json")

            SET(EXTRA_DEPENDENCIES
                "${CHIP_ROOT}/src/app/zap-templates/partials/header.zapt"
                "${CHIP_ROOT}/src/app/zap-templates/templates/app/access.zapt"
                "${CHIP_ROOT}/src/app/zap-templates/templates/app/endpoint_config.zapt"
                "${CHIP_ROOT}/src/app/zap-templates/templates/app/gen_config.zapt"
                "${CHIP_ROOT}/src/app/zap-templates/templates/app/im-cluster-command-handler.zapt"
           )
           SET(OUTPUT_SUBDIR "zap-generated")
        else()
            message(SEND_ERROR "Unsupported zap generator: ${ARG_GENERATOR}")
        endif()

        set(ZAPGEN_ARGS
            "--no-prettify-output"
            "--templates" "${TEMPLATE_PATH}"
            "--output-dir" "${GEN_FOLDER}/${OUTPUT_SUBDIR}"
            "--lock-file" "${CMAKE_BINARY_DIR}/zap_gen.lock"
            "--parallel"
            "${ARG_INPUT}"
        )

        # Optional ZCL path for zapgen:
        # - If ZCL_PATH is passed, use it.
        # - If CHIP_ENABLE_ZCL_ARG is ON, use default path.
        # - Otherwise, skip --zcl to preserve default behavior.
        if(ARG_ZCL_PATH)
            list(APPEND ZAPGEN_ARGS "--zcl" "${ARG_ZCL_PATH}")
        elseif(CHIP_ENABLE_ZCL_ARG)
            list(APPEND ZAPGEN_ARGS "--zcl" "${CHIP_ROOT}/src/app/zap-templates/zcl/zcl.json")
        endif()

        # Python is expected to be in the path
        # Forcing a call to find find_package here as ${Python3_EXECUTABLE} would be used
        find_package(Python3 REQUIRED)

        add_custom_command(
            OUTPUT ${OUT_NAMES}
            COMMAND "${Python3_EXECUTABLE}" -X utf8 "${CHIP_ROOT}/scripts/tools/zap/generate.py"
            ARGS ${ZAPGEN_ARGS}
            DEPENDS
                "${ARG_INPUT}"
                ${EXTRA_DEPENDENCIES}
            VERBATIM
        )

        add_custom_target(${TARGET_NAME} DEPENDS "${OUT_NAMES}")

        # Forward outputs to the parent
        set(${ARG_OUTPUT_FILES} "${OUT_NAMES}" PARENT_SCOPE)
        set(${ARG_OUTPUT_PATH} "${GEN_FOLDER}" PARENT_SCOPE)
    else()
        # Gets a path such as:
        file(RELATIVE_PATH MATTER_FILE_PATH "${CHIP_ROOT}" ${ARG_INPUT})

        # Removes the trailing file extension to get something like:
        string(REGEX REPLACE "\.zap$" "" CODEGEN_DIR_PATH "${MATTER_FILE_PATH}")

        # Build the final location within the pregen directory
        set(GEN_FOLDER "${CHIP_CODEGEN_PREGEN_DIR}/${CODEGEN_DIR_PATH}/zap/${ARG_GENERATOR}")

        # Here we have ${CHIP_CODEGEN_PREGEN_DIR}
        set(OUT_NAMES)
        foreach(NAME IN LISTS ARG_OUTPUTS)
            list(APPEND OUT_NAMES "${GEN_FOLDER}/${NAME}")
        endforeach()


        set(${ARG_OUTPUT_FILES} "${OUT_NAMES}" PARENT_SCOPE)
        set(${ARG_OUTPUT_PATH} "${GEN_FOLDER}" PARENT_SCOPE)

        # allow adding dependencies to a phony target since no codegen is done
        add_custom_target(${TARGET_NAME})
    endif()
endfunction()
