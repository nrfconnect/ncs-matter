.. _release_notes_v100:

Release notes for |addon| v1.0.0
################################

This page tracks changes and updates as compared to the latest official release.
For more information refer to the following section.
For the list of potential issues, see the :ref:`ncs_matter_known_issues` page.

Changelog
*********

This release provides Matter samples and documentation migrated from the |NCS| Matter.

* Added:

  * The Matter protocol documentation migrated from the |NCS| Matter user guide.
  * The Matter samples and applications migrated from the |NCS|.
  * The Matter configuration options migrated from the |NCS|.
  * The Matter software maturity levels migrated from the |NCS|.
  * The NFC Commissioning Manager implementation.
    See :ref:`ug_matter_configuring_optional_nfc` for more details.
  * Kconfig options to customize the Thread Network Diagnostics cluster attribute list.
    The ``ExtAddress`` and ``Rloc16`` attributes are optional in the Matter 1.6 specification, but the default Matter SDK implementation still exposes them in the cluster attribute list.
    Use the :option:`CONFIG_DISABLE_THREAD_DIAGNOSTIC_EXTADDR` or :option:`CONFIG_DISABLE_THREAD_DIAGNOSTIC_RLOC16` Kconfig options in your project configuration to omit them from the cluster attribute list.
  * The :ref:`ug_matter_gs_tools_nrf_matter_mobile` section in the :ref:`ug_matter_gs_tools` page.
    You can use the app as a Matter controller for testing :ref:`matter_samples`.
  * Integration of |addon| with the |NCS| v3.4.0.

* Removed the ``Init`` function from the ``Nrf::Matter::IdentifyCluster`` class.
  To add the Identify Matter cluster to your application, declare a new ``Nrf::Matter::IdentifyCluster`` object in your :file:`AppTask.cpp` file and fill all required constructor arguments.

Matter fork
***********

The Matter fork in the |NCS| (``sdk-connectedhomeip``) contains all commits from the upstream Matter repository up to, and including, the ``v1.6.0`` tag.

* Integration of `Matter 1.6.0 <CSA press release for Matter 1.6_>`_:

  * NFC-based commissioning - Allowing the full commissioning exchange over bi-directional NFC communication.
  * Joint Fabric - Enabling multiple user-authorized controllers to co-administer a single shared Matter network, with devices accessible to all participating controllers.
  * Thermostat suggestions - Providing a standardized way for ecosystems to submit time-bound recommended changes that thermostats evaluate against user-defined preferences and current context before acting.
  * Core enhancements - Device capability and limits communication, security sensor event history, unmounted state for smoke and CO alarms, and partitioned certificate revocation lists.
