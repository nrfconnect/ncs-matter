.. _ncs_matter_setup:

Requirements and setup
######################

.. contents::
   :local:
   :depth: 2

This page outlines the requirements that you need to meet before you start working with the |addon|.

Hardware requirements
*********************

To use the |addon|, you need a development kit that supports the Matter protocol.

.. table-from-sample-yaml::

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
|kconfig_search|
