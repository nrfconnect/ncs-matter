.. _release_notes_v101:

Release notes for |addon| v1.0.1
################################

This page tracks changes and updates as compared to the latest official release.
For more information refer to the following section.
For the list of potential issues, see the :ref:`ncs_matter_known_issues` page.

Devices that first ran |addon| v1.0.0 on nRF54L hardware may have the DAC private key in PSA ITS; v1.0.1 can still commission those units when ITS fallback is enabled (default)—see :ref:`migration_101` before changing Kconfig or provisioning flows on production units.

Changelog
*********

  * Fixed the issue where on nRF54L Series SoCs, |addon| v1.0.0 could store the Device Attestation Certificate (DAC) private key in PSA ITS instead of the CRACEN Key Management Unit (KMU) when built against |NCS| ``v3.4.0`` release.
    Matter Kconfig used the ``CRACEN_KMU`` symbol, which is undefined in that |NCS| ``v3.4.0`` release, so the build silently selected :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`.
    That broke device attestation and re-commissioning after SMP or Matter OTA from in-tree |NCS| Matter firmware that had already moved the DAC key to the KMU.
    See :ref:`ncs_matter_known_issue_dac_priv_key_its_kmu`.

  * Added boot-time handling when KMU migration is configured but the DAC private key is still present in PSA ITS.
    With :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU_ITS_FALLBACK` enabled (default), the device logs a warning, continues boot, and signs device attestation with the ITS key.
    With fallback disabled, boot stops instead of failing attestation later or risking silent misconfiguration.
    Automatic migration from ITS to KMU is not supported; re-provision when the key should live in KMU only (see :ref:`migration_101`).
