:orphan:

.. _migration_101:

Migration notes for |addon| v1.0.1
##################################

.. contents::
   :local:
   :depth: 3

This document describes changes required or recommended for migrating your Matter application from |addon| v1.0.0 to v1.0.1.

.. _migration_101_required:

Required changes
****************

Identify where the DAC private key is stored
============================================

Use the **first firmware** that completed factory-data migration on each device, not the Kconfig defaults of your current project alone.

+---------------------------+---------------------------------------------------------------------+
| First boot that migrated  | DAC private key location                                            |
| the DAC key               |                                                                     |
+===========================+=====================================================================+
| In-tree |NCS| Matter      | CRACEN KMU (expected on nRF54L with factory data)                   |
| (through |NCS| v3.4.0)    |                                                                     |
+---------------------------+---------------------------------------------------------------------+
| |addon| v1.0.0 on nRF54L  | PSA ITS (:kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`) |
+---------------------------+---------------------------------------------------------------------+

You can confirm the **current** firmware intent in :file:`build/<image>/zephyr/.config`:

* :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU=y` - firmware migrates new keys to KMU.
* :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS=y` - firmware migrates new keys to ITS.
* :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU_ITS_FALLBACK=y` - when KMU is selected, an existing ITS copy may still be used for signing (default in v1.0.1).

Choose a migration path
=======================

Path A — Device previously on in-tree |NCS| Matter (key in KMU), updated to v1.0.0
----------------------------------------------------------------------------------

**Symptom:** Re-commissioning after performing factory reset fails after DFU.
Attestation errors such as ``OpCreds: Failed AttestationRequest request with IM error 0x01 (err = ac)`` occur.
Existing Matter fabrics may still operate.

**Action:** Deploy |addon| v1.0.1 (or newer) firmware with KMU defaults restored.

Path B — Product shipped or first flashed with |addon| v1.0.0 on nRF54L series device (key in ITS)
--------------------------------------------------------------------------------------------------

Until each unit is re-provisioned with new factory data (new DAC key and certificates), choose one of the following for **every** firmware image you ship to those devices.

**Option 1 — KMU defaults with ITS fallback (recommended for v1.0.1+ field updates):**

Use the normal nRF54L KMU migration settings and leave the :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU_ITS_FALLBACK` Kconfig option set to ``y`` (default).
Commissioning and device attestation keep working because the stack detects the ITS copy at boot and uses it for signing while logging a warning.
Plan re-provisioning when you want the key stored in KMU only.

**Option 2 — Explicit ITS backend:**

Keep the migration destination aligned with where the key already lives:

.. code-block:: kconfig

   CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS=y
   # CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU is not set

Add this to :file:`prj.conf` or a board overlay and verify it in the merged :file:`.config` after building.

**Do not:**

* Disable :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU_ITS_FALLBACK` on KMU-default v1.0.1 firmware for these units unless you intend boot to stop until the ITS copy is removed or the device is re-provisioned.

* Perform a factory reset on firmware that erases settings (:kconfig:option:`CONFIG_CHIP_FACTORY_RESET_ERASE_SETTINGS`) while the DAC key exists only in ITS.
  That can **permanently erase** the DAC private key.

Path C — New development on v1.0.1+
-----------------------------------

No Kconfig changes are required for new nRF54L devices that will boot v1.0.1 first: KMU remains the default when :kconfig:option:`CONFIG_CRACEN_LIB_KMU` is available.
See :ref:`matter_platforms_security_dac_priv_key` for backend options.

Recommended validation
======================

After changing DAC storage settings or migration firmware on nRF54L hardware:

#. Build and inspect :file:`build/<app>/zephyr/.config` for the expected :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_*` symbol.
#. On a test device, run through factory reset (if applicable) and full Matter commissioning, including device attestation.
#. When migrating from older |NCS| Matter releases, include commissioning **after** SMP or Matter OTA in your release test plan (not only the DFU step).
