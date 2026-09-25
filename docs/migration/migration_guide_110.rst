:orphan:

.. _migration_110:

Migration notes for |addon| v1.1.0
##################################

.. contents::
   :local:
   :depth: 3

This document describes the changes required or recommended when migrating your Matter application from the |NCS| Matter samples to the |addon| v1.0.0.

.. _migration_110_required:

Required changes
****************

The following changes are mandatory to make your application work in the same way as in previous releases.

Build-time ZAP code generation
==============================

.. toggle::

   The |addon| samples no longer include pre-generated ZAP output under :file:`zap-generated/` in the sample source tree.
   By default, ZAP artifacts are generated automatically during the build.

   The default Kconfig option is :kconfig:option:`CONFIG_MATTER_ZAP_GENERATION_BUILD_TIME`.
   No other source changes are required when you adopt this mode.

   .. important::

      On the first build of a sample, the build system downloads and installs the ZAP tool into the Matter SDK :file:`.zap-install` directory.
      This happens automatically when :kconfig:option:`CONFIG_MATTER_ZAP_CLI_INSTALL_PATH` is empty and ``zap-cli`` is not already available on :envvar:`PATH`.
      The download runs once for each Matter SDK revision.
      Later builds reuse the installed tool.

   You can provide ``zap-cli`` in one of the following ways:

   * Leave both :envvar:`PATH` and :kconfig:option:`CONFIG_MATTER_ZAP_CLI_INSTALL_PATH` unset and let the build system install ZAP automatically (recommended for most users).
   * Add the Matter SDK :file:`.zap-install` directory to :envvar:`PATH` before building.
   * Set :kconfig:option:`CONFIG_MATTER_ZAP_CLI_INSTALL_PATH` to the directory that contains ``zap-cli``.

   Automatic ZAP installation (default)
   ------------------------------------

   .. tabs::

      .. group-tab:: |nRFVSC|

         Build the application as usual.
         On the first build, the build system downloads and installs the ZAP tool automatically.
         No extra configuration is required.

         See `How to work with build configurations`_ in the |nRFVSC| documentation for more information.

      .. group-tab:: Command line

         Build the sample from the command line.
         On the first build, the build system downloads and installs the ZAP tool automatically.

         .. code-block:: console

            west build -b nrf52840dk/nrf52840

   Provide ``zap-cli`` on :envvar:`PATH`
   -------------------------------------

   .. tabs::

      .. group-tab:: |nRFVSC|

         Before building, add the Matter SDK :file:`.zap-install` directory to :envvar:`PATH` in the terminal session used by the extension, then build the application as usual.

         .. code-block:: console

            export PATH="${ZEPHYR_BASE}/../modules/lib/matter/.zap-install:${PATH}"

         Alternatively, add the same export to your shell startup file so it applies to every |nRFVSC| terminal session.

      .. group-tab:: Command line

         Export the Matter SDK :file:`.zap-install` directory on :envvar:`PATH`, then build the sample:

         .. code-block:: console

            export PATH="${ZEPHYR_BASE}/../modules/lib/matter/.zap-install:${PATH}"
            west build -b nrf52840dk/nrf52840

   Provide an explicit ZAP install path
   ------------------------------------

   .. tabs::

      .. group-tab:: |nRFVSC|

         Add :kconfig:option:`CONFIG_MATTER_ZAP_CLI_INSTALL_PATH` to the build configuration's :guilabel:`Extra CMake arguments`, pointing to the directory that contains ``zap-cli``.
         Rebuild the build configuration after adding the argument.

         See `How to work with build configurations`_ in the |nRFVSC| documentation for more information.

      .. group-tab:: Command line

         Pass the install path as a CMake argument when building:

         .. code-block:: console

            west build -b nrf52840dk/nrf52840 -- -DCONFIG_MATTER_ZAP_CLI_INSTALL_PATH=\"${ZEPHYR_BASE}/../modules/lib/matter/.zap-install\"

.. _migration_110_recommended:

Recommended changes
*******************

The following changes are not mandatory, but improve your workflow when migrating.

Continue using the legacy static ZAP workflow
=============================================

.. toggle::

   If you prefer to keep generating ZAP output manually and checking it into your project, select the legacy mode in Kconfig:

   * Set :kconfig:option:`CONFIG_MATTER_ZAP_GENERATION_STATIC` to ``y``.

   Apart from this Kconfig change, your existing workflow stays the same.
   You still generate C++ files with the Matter west commands described on the :ref:`ug_matter_gs_tools_matter_west_commands` page:

   * :ref:`ug_matter_gs_tools_matter_west_commands_zap_tool_gui` - Edit the :file:`.zap` file.
   * :ref:`ug_matter_gs_tools_matter_west_commands_zap_tool_generate` - Generate the :file:`zap-generated/` directory.

   .. tabs::

      .. group-tab:: |nRFVSC|

         1. Open the :guilabel:`Kconfig` configuration for your build configuration.
         2. Search for ``MATTER_ZAP_GENERATION`` and enable :kconfig:option:`CONFIG_MATTER_ZAP_GENERATION_STATIC`.
         3. Rebuild the application.
         4. After editing the :file:`.zap` file, open a terminal with the toolchain environment and run:

            .. code-block:: console

               west zap-generate

      .. group-tab:: Command line

         Add the following options to :file:`prj.conf`, or pass them as CMake arguments:

         .. code-block:: none

            CONFIG_MATTER_ZAP_GENERATION_STATIC=y

         After editing the :file:`.zap` file, generate the output files:

         .. code-block:: console

            west zap-generate

   The generated files are written to :file:`zap-generated/` next to the :file:`.zap` file unless you pass ``--output``.

   .. note::

      When using static generation, you are responsible for re-running ``west zap-generate`` after every change in the :file:`.zap` and for keeping the generated files in version control.

Remove checked-in :file:`zap-generated/` directories
=====================================================

.. toggle::

   If you switch to build-time generation, delete any :file:`zap-generated/` directories from your application source tree.
   They are recreated in the build directory during compilation and no longer need to be stored in the repository.
