.. _ncs_matter_setup:

Requirements and setup
######################

.. contents::
   :local:
   :depth: 2

This page outlines the requirements that you need to meet before you start working with the |addon|.

.. _ncs_matter_setup_hardware_requirements:

Hardware requirements
*********************

This section outlines the hardware you need to develop and run Matter applications with the |addon|.

Supported SoCs
==============

Currently, the following SoCs from Nordic Semiconductor are supported for use with the Matter protocol:

* `nRF5340 <Programming board names_>`_ (Matter over Thread)
* `nRF52840 <Programming board names_>`_ (Matter over Thread)
* `nRF54L15 <Programming board names_>`_ (Matter over Thread)
* `nRF54L10 <Programming board names_>`_ (Matter over Thread)
* `nRF54LM20 <Programming board names_>`_ (Matter over Thread and Matter over Wi-Fi through the ``nrf7002eb2`` shield)

To use the |addon|, you need a development kit that supports the Matter protocol.

.. table-from-sample-yaml::

Front-End Modules
=================

SoCs from Nordic Semiconductor that can run the Matter protocol over Thread can also work with external Front-End Modules.
For more information about the FEM support in the |NCS|, see `Developing with Front-End Modules`_ and `nRF21540 DK <Programming board names_>`_.

.. _ncs_matter_hw_requirements_external_flash:

External flash
==============

For the currently supported SoCs, you must use an external memory with at least 1 MB of flash for the nRF52840 and nRF54L10 devices, and 1.5 MB for nRF5340 and nRF54L15 devices.
This is required to perform the DFU operation.

.. note::
   The nRF54L15 SoC supports DFU with image compression, which may eliminate the need for external flash.
   For more details, see `MCUboot image compression`_.

The development kits for the supported SoCs from Nordic Semiconductor are supplied with the MX25R64 type of external flash that meets these memory requirements.
However, it is possible to configure the SoCs with different QSPI or SPI memory if it is supported by Zephyr.
For this purpose, check the reference design for Nordic DKs for information about how to connect the external memory with SoC, specifically whether the pins are designed for the QSPI or the high-speed SPIM operations.

Software requirements
*********************

For libraries and code for the |addon|, see the `Matter add-on`_ repository.

To work with the |addon|, you need to install the |NCS|, including all its prerequisites and the |NCS| toolchain.
Follow the `Installing the nRF Connect SDK`_ instructions, with the following exception:

.. tabs::

   .. group-tab:: |nRFVSC|

      1. In the `Installing the nRF Connect SDK`_ section, click :guilabel:`Create a new application`.
      #. Select :guilabel:`Browse nRF Connect SDK Add-on Index`, then choose :guilabel:`NCS Matter`.
      #. Select v\ |addon_version| of the |addon|.
         This step also installs the |NCS| v\ |ncs_version|.

   .. group-tab:: Command line

      **Initialize a new workspace:**

      1. Run the following command to initialize west with the |addon|, which also initializes the |NCS| v\ |ncs_version|:

         .. code-block:: console

            west init -m https://github.com/nrfconnect/ncs-matter

      #. Update the |NCS| modules:

         .. code-block:: console

            west update

      **Include the add-on in an existing nRF Connect SDK workspace:**

      1. Assuming you have an existing |NCS| workspace in the :file:`ncs` folder, run the following commands:

         a. Navigate to the workspace folder:

            .. code-block:: console

               cd ncs

         #. Clone the add-on repository:

            .. code-block:: console

               git clone https://github.com/nrfconnect/ncs-matter

         #. Set the manifest path to the add-on directory:

            .. code-block:: console

               west config manifest.path ncs-matter

         #. Update the |NCS| modules:

            .. code-block:: console

               west update

      2. Optionally, run these commands in case you need to go back to work on the nRF Connect SDK without the add-on:

         a. Configure the manifest path back to the nRF Connect SDK directory:

            .. code-block:: console

               west config manifest.path nrf

         #. Update nRF Connect SDK modules:

            .. code-block:: console

               west update

         #. Check the current manifest path with the following command:

            .. code-block:: console

               west config manifest.path

            The output should be:

            .. code-block:: console

               nrf

            This means that the current workspace is using the nRF Connect SDK.

|config|
