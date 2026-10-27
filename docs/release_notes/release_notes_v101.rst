.. _release_notes_v101:

Release notes for |addon| v1.0.1
################################

This page tracks changes and updates as compared to the latest official release.
For more information refer to the following section.
For the list of potential issues, see the :ref:`ncs_matter_known_issues` page.

Devices that first ran |addon| v1.0.0 on the nRF54L Series hardware may have the DAC private key in PSA ITS.
v1.0.1 can still commission those units when the DAC private key fallback is enabled (default).
If you do not update to this version before performing a factory reset, the key stored in ITS can be permanently lost (see :ref:`ncs_matter_known_issue_dac_priv_key_its_kmu`).
See :ref:`migration_101` before changing Kconfig or provisioning flows on production units.

Changelog
*********

* Added a generic fallback for the DAC private key location.
  When the DAC private key is stored in a different backend than the one currently selected, the :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_FALLBACK` Kconfig option (enabled by default) allows the device to sign device attestation with the legacy key.

  * If the KMU backend is selected and the key is in PSA ITS, the device falls back to ITS.
  * If the ITS backend is selected and the key is in the CRACEN KMU, the device falls back to KMU.

  The key in the selected backend always takes precedence over a key in the other backend.
  The fallback option is available only on devices with CRACEN KMU.
  The device logs a warning and continues boot.
  With fallback disabled, boot stops instead of failing attestation later or risking silent misconfiguration.
  Automatic migration of the key between ITS and KMU is not supported.
  Reprovision when the key should reside in the selected backend only (see :ref:`migration_101`).
  If you do not update to the firmware with the fallback and perform a factory reset that erases settings, a DAC private key stored in ITS is lost permanently.

* Fixed an issue where on nRF54L Series SoCs, the |addon| v1.0.0 could store the Device Attestation Certificate (DAC) private key in PSA ITS instead of the CRACEN Key Management Unit (KMU) when built against the |NCS| v3.4.0 release.
  Matter Kconfig used the ``CRACEN_KMU`` symbol, which is undefined in the |NCS| v3.4.0 release, so the build silently selected the :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS` Kconfig option.
  This broke the device attestation and re-commissioning after SMP or Matter OTA from in-tree |NCS| Matter firmware that had already moved the DAC key to the KMU.
  See :ref:`ncs_matter_known_issue_dac_priv_key_its_kmu`.
