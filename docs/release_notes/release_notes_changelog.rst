.. _release_notes_changelog:

Release notes for |addon| |addon_version|
#########################################

This page tracks changes and updates as compared to the latest official release.
For more information refer to the following section.
For the list of potential issues, see the :ref:`ncs_matter_known_issues` page.

Changelog
*********

* Updated the ``Nrf::Matter::IdentifyCluster`` class to use the code-driven Matter SDK Identify cluster implementation directly, instead of the legacy ``Identify`` wrapper.
  The cluster is registered automatically when you create a ``Nrf::Matter::IdentifyCluster`` object.

* Fixed the ``TriggerEffect`` command being advertised and accepted when trigger effects are disabled.
  The ``Nrf::Matter::IdentifyCluster`` class now respects the ``IsTriggerEffectEnabled()`` value from ``IdentifyDelegateImplNrf``.

Matter fork
***********

|no_changes_yet_note|
