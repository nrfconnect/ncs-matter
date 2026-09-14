.. _release_notes_preview_thread_hdr:

Release notes for preview-thread-hdr
####################################

This page documents the ``preview-thread-hdr`` release of the |addon|.
It is based on the |addon| v\ |addon_version| release and adds experimental Thread High Data Rate (HDR) support.

.. important::
   Thread HDR is provided for evaluation purposes only.

Overview
********

The ``preview-thread-hdr`` release extends the Nordic OpenThread platform, the nRF IEEE 802.15.4 Radio Driver, and related dependencies so that compatible devices can advertise and use an alternate 2 Mbps GFSK PHY while keeping the standard IEEE 802.15.4 MAC and Thread stack.

See :ref:`ncs_matter_thread_hdr_preview` for technical background, enablement, and a test procedure.

Changelog
*********

* Added:

  * Experimental Thread HDR (High Data Rate) support with 2 Mbps GFSK alternate PHY.
  * ``ot-hdr`` and ``ot-hdr-log`` build snippets.
  * OpenThread platform extensions in the |addon| (``ncs-matter/modules/openthread``).
  * :ref:`ncs_matter_thread_hdr_preview` documentation.

* Updated by changing the following west manifest dependencies for Thread HDR support:

  * ``sdk-openthread`` on the ``collab-hdr`` branch (OpenThread stack).
  * ``sdk-nrfxlib`` on the ``collab-hdr`` branch (nRF IEEE 802.15.4 Radio Driver).
