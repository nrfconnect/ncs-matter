# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0

if(CONFIG_CHIP_NFC_COMMISSIONING_MODE_UNPOWERED)

  target_sources(app PRIVATE
    nfc_unpowered_commissioning.cpp
    nfc_operational_keystore.cpp
  )

  target_sources_ifdef(CONFIG_MATTER_NFC_COMMISSIONING_BUTTON_TRIGGER app PRIVATE
    nfc_commissioning_button.cpp
  )

  if(CONFIG_MATTER_NFC_COMMISSIONING_BACKEND_ST25DAC)
    target_link_libraries(app PRIVATE st25dac)
  endif()

  if(CONFIG_MATTER_NFC_COMMISSIONING_SHELL)
    target_sources(app PRIVATE nfc_commissioning_shell.cpp)
  endif()

endif()
