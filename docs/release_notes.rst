.. _release_notes:

Release notes
#############

.. contents::
   :local:
   :depth: 3

All the notable changes to the |addon| for the |NCS| are listed here.

The |addon| v\ |addon_version| is compatible with |NCS| v\ |ncs_version|.
For a full list of |addon| releases and related |NCS| and Matter SDK versions, view the following table:

+-------------------+------------------+----------------------+
| |addon| version   | |NCS| version    | Matter SDK version   |
+===================+==================+======================+
| 1.0.0             | 3.4.0            | 1.6.0                |
+-------------------+------------------+----------------------+

For detailed list on new features for a specific |addon| release, refer to the following:

Matter fork
***********

The Matter fork in the |NCS| (``sdk-connectedhomeip``) contains all commits from the upstream Matter repository up to, and including, the ``v1.6.0`` tag.

* Integration of `Matter 1.6.0 <CSA press release for Matter 1.6_>`_:

  * NFC-based commissioning - Allowing the full commissioning exchange over bi-directional NFC communication.
  * Joint Fabric - Enabling multiple user-authorized controllers to co-administer a single shared Matter network, with devices accessible to all participating controllers.
  * Thermostat suggestions - Providing a standardized way for ecosystems to submit time-bound recommended changes that thermostats evaluate against user-defined preferences and current context before acting.
  * Core enhancements - Device capability and limits communication, security sensor event history, unmounted state for smoke and CO alarms, and partitioned certificate revocation lists.

.. toctree::
   :maxdepth: 1
   :caption: Contents
   :glob:

   release_notes/release_notes_v101.rst
   release_notes/release_notes_v100.rst
