.. _ncs_matter_known_issues:

Known issues
############

.. contents::
   :local:
   :depth: 3

Known issues listed on this page *and* tagged with the :ref:`latest release version <release_notes>` are valid for the current state of development.
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

.. _ncs_matter_known_issue_dac_priv_key_its_kmu:

.. rst-class:: simple v1-0-0

KRKNWK-22680: DAC private key stored in PSA ITS instead of CRACEN KMU on nRF54L
  On nRF54L Series SoCs with a Key Management Unit (KMU), |addon| v1.0.0 selects PSA Internal Trusted Storage (ITS) by default as the DAC private key backend instead of the CRACEN KMU.
  The Matter Kconfig defaults depend on the ``CRACEN_KMU`` symbol, which is not defined in |NCS| v3.4.0.
  The build therefore silently falls back to :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`, while the documentation describes KMU storage as the default (see :ref:`matter_platforms_security_dac_priv_key_kmu`).

  On the first boot with factory data, ``FactoryDataProvider`` moves the DAC private key out of the factory data partition exactly once.
  The key cannot be exported or copied to another backend.

  When commissioning or attestation may fail

  * KMU - ITS mismatch (recoverable with a fixed firmware):
    The device previously ran in-tree |NCS| Matter firmware (up to |NCS| v3.4.0) that stored the DAC private key in the KMU, and was updated over SMP or Matter OTA to |addon| v1.0.0 firmware that looks for the key in ITS.
    Existing Matter fabrics continue to work, but **new commissioning fails** after a factory reset or when adding another administrator.
    Device attestation fails with an Operational Credentials error (for example ``OpCreds: Failed AttestationRequest request with IM error 0x01 (err = ac)``).
    This path is **deterministic** on every affected nRF54L device when migrating from pre–|addon| Matter releases.

  * ITS - KMU mismatch (commissioning failure on v1.0.0; mitigated in v1.0.1):
    The device **first booted** with |addon| v1.0.0 (or any firmware that stored the DAC key in ITS).
    |addon| v1.0.0 firmware that defaults to KMU storage cannot use that key; commissioning fails the same way as the KMU→ITS case.
    |addon| v1.0.1 and newer sdk-connectedhomeip revisions can boot with KMU migration selected when :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU_ITS_FALLBACK` is enabled (default): the ITS copy is used for attestation signing and a warning is logged.
    Automatic migration from ITS to KMU is still not supported.
    If such a device receives a **factory reset** while :kconfig:option:`CONFIG_CHIP_FACTORY_RESET_ERASE_SETTINGS` is enabled and the DAC key exists only in ITS, the settings partition is erased together with the ITS copy of the DAC private key, and the **DAC private key is permanently lost**.
    The device can no longer pass device attestation until it is re-provisioned with new factory data.

  **Affected platforms:** nRF54L15 and nRF54LM20A/B Series SoCs

  **Workaround:**

  Pick the step that matches where the DAC private key was stored on **first** migration (see :ref:`migration_101`).

  * **Key in CRACEN KMU** (typical after in-tree |NCS| Matter, then a broken update to |addon| v1.0.0):
    Deploy |addon| v1.0.1 or newer firmware with KMU migration selected (``CRACEN_LIB_KMU`` defaults restored).
    Do **not** force :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`; ITS storage cannot read a KMU-resident key and commissioning stays broken.
    See :ref:`migration_101` Path A.

  * **Key in PSA ITS** (typical when |addon| v1.0.0 completed the first migration on nRF54L):
    Deploy |addon| v1.0.1 or newer with :kconfig:option:`CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU_ITS_FALLBACK` left enabled (default) so attestation uses the ITS copy, or keep an explicit ITS migration destination until re-provisioning:

    .. code-block:: kconfig

       CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS=y
       # CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU is not set

    See :ref:`migration_101` Path B.

  * Before updating firmware on nRF54L series devices, confirm the effective backend in the build output (``CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_ITS`` vs ``CONFIG_CHIP_CRYPTO_PSA_DAC_PRIV_KEY_KMU`` in :file:`build/*/zephyr/.config`).
