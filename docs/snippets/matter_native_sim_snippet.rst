.. _snippet_matter_native_sim:
.. _ug_matter_native_sim_snippet:

Matter native_sim snippet (native-sim)
######################################

.. contents::
   :local:
   :depth: 2

To build with this snippet, follow the instructions in the :ref:`using-snippets` page.


.. tabs::

   .. group-tab:: |nRFVSC|

      When using |nRFVSC| select the ``native-sim`` snippet from the list in the **Snippets** menu.

   .. group-tab:: Command line

      When building with west, run the following command from the sample directory:

      .. parsed-literal::
         :class: highlight

         west build -b native_sim/native/64 -DSNIPPET=native-sim

Overview
********

The ``native-sim`` snippet configures Matter samples for host simulation on ``native_sim`` and ``native_sim/native/64``.
It is intended for CI, Twister, and local desktop validation, not for production parity with nRF DK builds.

The snippet supplies :file:`matter_native_sim.conf` (application Kconfig), :file:`matter_native_sim_sysbuild.conf` (disables MCUboot and factory-data generation at sysbuild level), and :file:`matter_native_sim.overlay`.

The snippet enables the following operations:

  * Host BSD sockets for Matter IP over the host Ethernet stack (no Zephyr net or HCI)
  * Simulated flash, NVS, and OTA requestor with MCUboot API stubs (simulated reboot apply)
  * On-network commissioning (no Bluetooth LE; device uses host ``eth0`` or default route)
  * Shell, logging, and UART PTY for interactive host runs
  * CHIP overrides via :kconfig:option:`CONFIG_CHIP_PROJECT_CONFIG` pointing at :file:`snippets/native-sim/chip_project_config_native_sim.h`

Run on host
***********

After building, run from the sample directory (``ncs-matter/samples/<sample>``) using the :file:`scripts/native_sim/bin/run-in-netns` script.

.. code-block:: console

   sudo ../../scripts/native_sim/bin/run-in-netns

UART and logs are printed on the invoking terminal.

You can prepare the firmware to separate logs from the simulated device and UART console by setting the :kconfig:option:`CONFIG_UART_NATIVE_PTY_0_ON_OWN_PTY` to ``y``, and :kconfig:option:`CONFIG_UART_NATIVE_PTY_0_ON_STDINOUT` to ``n``.

For example:

.. code-block:: console

   west build -p -b native_sim/native/64 -- -DSNIPPET=native-sim -DCONFIG_UART_NATIVE_PTY_0_ON_STDINOUT=n -DCONFIG_UART_NATIVE_PTY_0_ON_OWN_PTY=y

Network namespace
=================

For on-network mDNS, prefer an isolated network namespace so that the app does not probe every host interface.
Use :file:`scripts/native_sim/bin/run-in-netns` from the sample directory to automatically create the network namespace and run the application.

The script supports the following options:

.. code-block:: shell

   sudo ../../scripts/native_sim/bin/run-in-netns --info
   sudo ../../scripts/native_sim/bin/run-in-netns --setup-only
   sudo ../../scripts/native_sim/bin/run-in-netns --teardown
   sudo ../../scripts/native_sim/bin/run-in-netns --exe <path_to_zephyr_exe>

``--exe`` accepts a path to ``zephyr.exe`` or to the ``zephyr/`` directory containing it.
When omitted, paths are derived from the current sample directory name (``<pwd>/build/<sample>/zephyr/``).

The script creates the ``matter-app`` netns with ``veth-app`` inside (``10.10.10.2/24``, ``fd00:0:1:1::2/64``) and ``veth-br`` on the host (``10.10.10.1/24``, ``fd00:0:1:1::1/64``).

Commissioning and persistence
=============================

Without factory data, SPAKE2+ credentials come from Kconfig (passcode ``20202021``, discriminator ``3840``/``0xF00``).
The snippet uses Mbed TLS SPAKE2P (PSA PAKE is unavailable on native_sim) and :kconfig:option:`CONFIG_MBEDTLS_HEAP_SIZE` set to 32768.
On-network onboarding QR or manual pairing codes are printed at boot (no Bluetooth LE).

The snippet enlarges the ``storage`` partition to 42 KiB and uses the ZMS settings backend (:kconfig:option:`CONFIG_SETTINGS_ZMS` with 1024 KiB sectors) so that the fabric commit has enough space.
Wipe the simulated flash after the partition or backend changes:

.. code-block:: shell

   rm build/<app>/zephyr/<app>_native_sim.bin

For a teardown operation, use the following command:

``sudo ../../scripts/native_sim/bin/run-in-netns --teardown``
