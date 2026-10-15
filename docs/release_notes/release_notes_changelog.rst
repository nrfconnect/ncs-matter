.. _release_notes_changelog:

Release notes for |addon| |addon_version|
#########################################

This page tracks changes and updates as compared to the latest official release.
For more information refer to the following section.
For the list of potential issues, see the :ref:`ncs_matter_known_issues` page.

Changelog
*********

* Added experimental Matter over Wi-Fi support for the nRF7120 DK to selected samples.
  For supported samples, build instructions, and limitations, see the :ref:`nRF7120 DK preview <ncs_matter_nrf7120_preview>`.

* Updated the ``Nrf::Matter::IdentifyCluster`` class to use the code-driven Matter SDK Identify cluster implementation directly, instead of the legacy ``Identify`` wrapper.
  The cluster is registered automatically when you create an ``Nrf::Matter::IdentifyCluster`` object.

* Fixed the ``TriggerEffect`` command being advertised and accepted when trigger effects are disabled.
  The ``Nrf::Matter::IdentifyCluster`` class now respects the ``IsTriggerEffectEnabled()`` value from ``IdentifyDelegateImplNrf``.

Matter fork
***********

|no_changes_yet_note|
