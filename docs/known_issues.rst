.. _ncs_matter_known_issues:

Known issues
############

.. contents::
   :local:
   :depth: 3

Known issues listed on this page and tagged with the :ref:`latest release version <release_notes>` are valid for the current state of development.
Use the drop-down filter to see known issues for previous releases and check if they are still valid.

A known issue can list one or both of the following entries:

* **Affected platforms:**

  If a known issue does not have any specific platforms listed, it is valid for all hardware platforms.

* **Workaround:**

  Some known issues have a workaround.
  Sometimes, they are discovered later and added over time.

.. version-filter::
   :container: dl/dt
   :tags: [("wontfix", "Won't fix")]

.. page-filter::
   :name: issues

   wontfix Won't fix

List of known issues for |addon|
********************************

.. _ncs_matter_known_issue_binding_case_recovery:

.. rst-class:: simple v1-0-0 v1-0-1

KRKNWK-22597: Heap corruption and fault during CASE session recovery in the binding handler
  The :ref:`light_switch` sample can crash with a heap corruption (double free) and a kernel panic when it sends a bound command through a stale CASE session after the bound peer is reset.
  The peer drops the message because it no longer knows the session, the command times out, and the binding handler starts the CASE session recovery.
  During this recovery, the same binding data was passed twice to the Matter Binding Manager, which released it twice.
  The issue can also affect other applications that use the binding handler, such as the :ref:`matter_bridge` and :ref:`thermostat` samples, and applications that use the :file:`subsys/binding` module.

  **Workaround:**  Manually cherry-pick the following commit from the |addon| main branch: ``TBD``

.. _ncs_matter_known_issue_dac_priv_key_its_kmu:

.. rst-class:: simple v1-0-0

KRKNWK-22680: DAC private key stored in PSA ITS instead of CRACEN KMU on nRF54L
  On nRF54L Series SoCs with a Key Management Unit (KMU), the |addon| v1.0.0 selects PSA Internal Trusted Storage (ITS) by default as the DAC private key backend instead of the CRACEN KMU.
  The Matter Kconfig defaults depend on the :kconfig:option:`CONFIG_CRACEN_KMU` Kconfig option, which is not defined in the |NCS| v3.4.0.
  The build therefore silently falls back to :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`, while the documentation describes KMU storage as the default (see :ref:`matter_platforms_security_dac_priv_key_kmu`).
  This causes the device to be unusable if you perform a firmware update from the |NCS| v3.4.0 to |addon| v1.0.0 and then perform a factory reset, because the DAC private key will be lost permanently.

  On the first boot with factory data, ``FactoryDataProvider`` moves the DAC private key out of the factory data partition exactly once.
  The key cannot be exported or copied to another backend.

  Commissioning or attestation might fail in the following cases:

  * KMU → ITS mismatch (recoverable with a fixed firmware):
    The device previously ran in-tree |NCS| Matter firmware (up to |NCS| v3.4.0) that stored the DAC private key in the KMU, and was updated over SMP or Matter OTA to |addon| v1.0.0 firmware that looks for the key in ITS.
    Existing Matter fabrics continue to work, but a new commissioning fails after a factory reset or when adding another administrator.
    Device attestation fails with an Operational Credentials error (for example ``OpCreds: Failed AttestationRequest request with IM error 0x01 (err = ac)``).
    This path is deterministic on every affected nRF54L Series device when migrating from pre-|addon| Matter releases.

  * ITS → KMU mismatch (commissioning failure on v1.0.0, mitigated in v1.0.1):
    The device first booted with the |addon| v1.0.0 (or any firmware that stored the DAC key in ITS).
    The |addon| v1.0.0 firmware that defaults to KMU storage cannot use that key.
    Commissioning fails the same way as the KMU → ITS case.
    If you do not update to firmware that includes the fallback and the device receives a factory reset while the :kconfig:option:`CONFIG_CHIP_FACTORY_RESET_ERASE_SETTINGS` Kconfig option is enabled, the settings partition is erased together with the ITS copy of the DAC private key.
    In that case, if the key was previously stored in ITS and a different backend is selected, the DAC private key is permanently lost and the device can no longer pass device attestation until it is re-provisioned with new factory data.
    Updating to the newest version after the factory reset does not restore the key.

  **Affected platforms:** All nRF54L Series SoCs

  **Workaround:** Pick the step that matches to the location where the DAC private key was stored on first migration (see :ref:`migration_101`).

  * Key in CRACEN KMU (typical after in-tree |NCS| Matter, then a broken update to the |addon| v1.0.0):

    Deploy the |addon| v1.0.1 or newer with :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_FALLBACK` left enabled (default) so that the attestation uses the KMU key.
    Do not perform a factory reset before the update.
    Do not force :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`.
    See :ref:`migration_101` Path A.

  * Key in PSA ITS (typical when the |addon| v1.0.0 completed the first migration on the nRF54L Series device):
    Deploy the |addon| v1.0.1 or newer with :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_FALLBACK` left enabled (default) so that the attestation uses the ITS key.
    Do not perform a factory reset before the update.
    Alternatively, keep an explicit ITS migration destination:

    .. code-block:: kconfig

       CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS=y
       # CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU is not set

    See :ref:`migration_101` Path B.

  * Before updating the firmware on nRF54L Series devices, confirm the effective backend in the build output (``CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`` vs ``CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU`` in the :file:`build/*/zephyr/.config` file).
