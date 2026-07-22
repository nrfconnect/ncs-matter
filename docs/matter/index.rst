.. _ug_matter:
.. _ug_chip:

Matter
######

.. contents::
   :local:
   :depth: 2

.. matter_intro_start

`Matter`_ (formerly Project Connected Home over IP or Project CHIP) is an open-source application layer that aims at creating a unified communication standard across smart home devices, mobile applications, and cloud services.
It supports a wide range of existing technologies, including Wi-Fi®, Thread, and Bluetooth® LE, and uses IPv6-based transport protocols like TCP and UDP to ensure connectivity between different kinds of networks.

If you want to go through a hands-on online training to familiarize yourself with Matter development, enroll in the `Matter Fundamentals course`_ in the `Nordic Developer Academy`_.

.. matter_intro_end

|addon| |release| allows you to develop applications with Matter specification version 1.5.0 and `Matter SDK version`_ 1.5.0.0.
For a full list of |NCS| and Matter versions, view the following table:

.. toggle:: nRF Connect SDK, Matter specification, and Matter SDK versions

   +-----------------------+--------------------------+-----------------------------------------------------+------------------------+
   | Matter Add-on version | nRF Connect SDK version  | Matter specification version                        | Matter SDK version     |
   +=======================+==========================+=====================================================+========================+
   | |release|             | v3.4.0                   | :ref:`1.5.0 <ug_matter_overview_dev_model_support>` | 1.5.0.0                |
   +-----------------------+--------------------------+-----------------------------------------------------+------------------------+

.. note::
   The Matter SDK version is taken as the base for the `dedicated Matter fork`_, which can then include additional changes for each |addon| release.
   These changes are listed in the Matter fork section of the |addon| :ref:`release_notes`.

For more information about Matter compatibility, see :ref:`ug_matter_overview_dev_model_support` and :ref:`supported Matter features per SoC <software_maturity_protocol_matter>`.

See :ref:`matter_samples` for the list of available samples, or :ref:`Matter Weather Station <matter_weather_station_app>` or :ref:`Matter bridge <matter_bridge_app>` for specific Matter applications.
If you are new to Matter, you can follow along with the video tutorials on Nordic Semiconductor's YouTube channel, for example `Developing Matter 1.0 products with nRF Connect SDK`_.

.. note::
    |matter_gn_required_note|

.. toctree::
   :maxdepth: 1
   :caption: Subpages:

   overview/index
   getting_started/index
   end_product/index
