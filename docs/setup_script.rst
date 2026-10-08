.. _ncs_matter_setup_script:

Automated workspace setup script
################################

.. contents::
   :local:
   :depth: 2

The :file:`scripts/setup.sh` script automates command-line installation of the |addon| workspace on Linux and macOS.
It installs the required nRF Util commands, SEGGER J-Link, the |NCS| version defined in :file:`west.yml`, the toolchain, and the Door Lock add-on repository.
It also builds samples and prints the command to flash them.

Run the script from an existing |addon| git checkout.
The script does not clone |addon| itself.
Instead, it symlinks your checkout into the SDK workspace installed by ``nrfutil sdk-manager``.

The script is an alternative to the manual steps described in :ref:`ncs_matter_setup`.

.. _ncs_matter_setup_script_prerequisites:

Prerequisites
*************

Make sure that ``curl`` and ``git`` are available on your system.

The script installs the following tools at the versions defined at the top of :file:`scripts/setup.sh`.
The defaults match the Matter ``chip-build-nrf-platform`` Docker image.

* ``nrfutil`` (default ``8.1.1``)
* ``nrfutil device`` (default ``2.19.0``)
* ``nrfutil sdk-manager``
* SEGGER J-Link (default ``V924a``), installed when ``JLinkExe`` is missing or has a different version

On Linux, J-Link is installed in :file:`~/ncs/nRF5_tools`.
On macOS, the J-Link ``.pkg`` installer is run system-wide, and it may ask for an administrator password.

.. _ncs_matter_setup_script_install:

Installing the workspace
************************

Clone the |addon| repository and run the script from that checkout:

.. code-block:: console

   git clone https://github.com/nrfconnect/ncs-matter
   cd ncs-matter
   ./scripts/setup.sh

By default, the script checks out the ``main`` revision of your local checkout.
To use a different branch, tag, or commit, pass ``--revision`` or ``--branch``:

.. code-block:: console

   ./scripts/setup.sh --revision my-feature-branch

The script prints short phase summaries.
Add ``--verbose`` to print detailed progress messages.

The script performs the following steps:

1. Verifies the local |addon| checkout, removes symlinks from a previous run, and checks out the requested revision.
#. Installs or upgrades ``nrfutil``, ``nrfutil device``, ``nrfutil sdk-manager``, and J-Link.
#. Reads the required |NCS| version from :file:`west.yml` and installs the matching SDK and toolchain.
#. Symlinks :file:`<sdk-workspace>/ncs-matter` to your local checkout.
#. Clones the `Door Lock and Access Control add-on`_ into the SDK workspace and symlinks it as :file:`ncs-matter/samples/lock`.
#. Initializes west if needed, sets the west manifest to |addon|, and runs ``west update`` inside the toolchain environment.

The SDK workspace is the directory reported by ``nrfutil sdk-manager list --all-fields``.
For example, :file:`~/ncs/v3.4.0` on Linux or :file:`/opt/nordic/ncs/v3.4.0` on macOS.

.. note::
   The first ``west update`` can take 15-30 minutes or longer, especially while updating Zephyr.
   This is expected.

   If ``nrfutil sdk-manager install`` reports ``failed to run west zephyr-export in SDK directory``, the script continues when the SDK files are present.
   It runs ``west zephyr-export`` again after ``west update``.

You can safely re-run the script.
Symlinks created by a previous run are removed and created again.
If a symlink path is occupied by a regular file or directory, the script stops and asks you to remove it manually.

Entering the toolchain environment
==================================

To open an interactive shell in the SDK workspace, run:

.. code-block:: console

   ./scripts/setup.sh --launch

This requires a completed setup, with the matching toolchain installed and west initialized in the workspace.
To set up the workspace and open the shell in one step, combine ``--launch`` with setup options:

.. code-block:: console

   ./scripts/setup.sh --revision main --launch

To export ``ZEPHYR_BASE`` in your current shell, source the script instead of executing it:

.. code-block:: console

   source ./scripts/setup.sh

.. _ncs_matter_setup_script_build:

Building Matter samples
***********************

After the setup completes, build samples with the ``build`` command.

To list all samples and their default boards, run:

.. code-block:: console

   ./scripts/setup.sh build

To build a sample, pass its name:

.. code-block:: console

   ./scripts/setup.sh build light_bulb

All builds enable merged hex output with ``-DSB_CONFIG_MERGED_HEX_FILES=y``.
Use the following options to change the build:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Description
   * - ``--debug``
     - Builds with the ``diagnostic-logs`` and ``debug`` snippets, by adding ``-D<sample>_SNIPPET=diagnostic-logs;debug``.
       This is the default.
   * - ``--release``
     - Builds with ``-DFILE_SUFFIX=release``.
   * - ``--board BOARD``
     - Overrides the default board from :file:`sample.yaml`, for example ``nrf52840dk/nrf52840``.
   * - ``--outdir DIR``
     - Copies the merged hex file to ``DIR`` after a successful build.
   * - ``--name SUFFIX``
     - Names the copied file ``<sample><board><SUFFIX>.hex`` with slashes removed from the board name.
       Requires ``--outdir``.

For example, the following command copies the merged hex to :file:`~/firmware/weather_stationnrf52840dknrf52840debug.hex`:

.. code-block:: console

   ./scripts/setup.sh build weather_station --outdir ~/firmware --name debug

The ``lock`` sample is a symlink to the Door Lock add-on application at :file:`ncs-door-lock-and-access-control/applications/matter-door-lock-app`.
When you build it, the script sets the west manifest to :file:`ncs-door-lock-and-access-control`.
For all other samples, and for setup and ``--launch``, the west manifest is :file:`ncs-matter`.
The script switches the manifest automatically before each build.

Flashing a sample
=================

When the build completes, the script prints the command to flash the merged hex file, using the copy in ``--outdir`` if you set it:

.. code-block:: console

   nrfutil device program --firmware <merged.hex> \
     --options chip_erase_mode=ERASE_RANGES_TOUCHED_BY_FIRMWARE,verify=VERIFY_READ \
     && nrfutil device reset

If more than one DK is connected, list the devices and select the target by its serial number.
Add ``--serial-number`` to both commands:

.. code-block:: console

   nrfutil device list
   nrfutil device program --serial-number <SERIAL_NUMBER> --firmware <merged.hex> \
     --options chip_erase_mode=ERASE_RANGES_TOUCHED_BY_FIRMWARE,verify=VERIFY_READ \
     && nrfutil device reset --serial-number <SERIAL_NUMBER>

.. _ncs_matter_setup_script_cleanup:

Removing the workspace
**********************

To remove the workspace created by the script, run:

.. code-block:: console

   ./scripts/setup.sh --cleanup

The script prints a warning and asks you to type ``y`` to confirm.
Any other input cancels the cleanup.

.. warning::
   The cleanup permanently removes the following items:

   * The :file:`<sdk-workspace>/ncs-matter` symlink and the :file:`ncs-matter/samples/lock` symlink
   * The :file:`ncs-door-lock-and-access-control` repository clone
   * The |NCS| SDK and toolchain version defined in :file:`west.yml`, and the SDK workspace directory
   * The west manifest override, when it points to |addon|

   Your local |addon| git checkout and other content in the |NCS| installation directory are not removed.

.. note::
   The ``--cleanup`` option cannot be combined with ``--branch``, ``--revision``, or ``--launch``.
   Like ``--launch`` and ``build``, it must be run as a script and cannot be used with ``source``.

.. _ncs_matter_setup_script_help:

Getting help
************

To display usage information, run:

.. code-block:: console

   ./scripts/setup.sh --help
