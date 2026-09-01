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

      When using |nRFVSC| select the ``native-sim`` snippet from the list in the :guilabel:`Snippets` menu.

   .. group-tab:: Command line

      When building with west, run the following command:

      .. parsed-literal::
         :class: highlight

         west build -b native_sim/native/64 <sample>


Overview
********

The ``native-sim`` snippet configures Matter samples for host simulation on ``native_sim`` / ``native_sim/native/64``.
It is intended for CI, Twister, and local desktop validation—not production parity with nRF DK builds.

For sysbuild builds (default in |addon| repository samples), :file:`ncs-matter/sysbuild/native_sim.cmake` attaches ``native-sim`` to the main image when ``BOARD`` matches ``native_sim``.
Freestanding builds can use :file:`cmake/find_zephyr.cmake` for the same auto-attach.

Each sample defines a Twister scenario ``sample.matter.<sample>.native_sim`` in :file:`sample.yaml` with the expected sysbuild settings.

The snippet enables:

  * Host BSD sockets for Matter IP over the host Ethernet stack (no Zephyr net / HCI)
  * Simulated flash, NVS, and OTA requestor with MCUboot API stubs (simulated reboot apply)
  * On-network commissioning (no BLE; device uses host ``eth0`` / default route)
  * Shell, logging, and UART PTY for interactive host runs

Each sample :file:`src/chip_project_config.h` includes :file:`subsys/app/chip_project_config_native_sim.h` for matching CHIP overrides.


Run on host
***********

After building, run the Zephyr native binary with simulated flash. UART/shell uses a dedicated
pseudo-terminal (``CONFIG_UART_NATIVE_PTY_0_ON_OWN_PTY``); Matter logs print on the invoking
terminal. Attach a second terminal for the shell:

.. code-block:: shell

   ./build/<app>/zephyr/zephyr.exe -flash=<app>_native_sim.bin -attach_uart

``-attach_uart`` opens ``xterm -e screen /dev/pts/N`` (requires ``xterm`` and ``screen``).
On GNOME without ``xterm``::

  ./zephyr.exe -flash=<app>_native_sim.bin \
      -attach_uart_cmd='gnome-terminal -- screen %s'

Or read the ``connected to pseudotty: /dev/pts/N`` line from the log and run ``screen /dev/pts/N``
in another terminal. Matter shell commands use the ``matter`` prefix (e.g. ``matter help``).

For on-network mDNS, prefer an isolated network namespace so the app does not probe every host interface (``docker0``, Wi-Fi, …):

.. code-block:: shell

   cd ncs-matter/samples/<sample>/build/<app>/zephyr
   sudo ../../../../../scripts/native_sim/bin/run-in-netns -- \
       ./zephyr.exe -flash=<app>_native_sim.bin -attach_uart

The script creates the ``matter-app`` netns with ``veth-app`` inside (``10.10.10.2/24``, ``fd00:0:1:1::2/64``) and ``veth-br`` on the host (``10.10.10.1/24``, ``fd00:0:1:1::1/64``).
Run ``chip-tool`` on the host over ``veth-br`` (``fd00:0:1:1::1``), or inside the namespace::

  sudo ip netns exec matter-app chip-tool pairing onnetwork-long 3840 20202021

Without factory data, SPAKE2+ credentials come from Kconfig (passcode ``20202021``, discriminator ``3840`` / ``0xF00``).
The snippet uses mbedtls SPAKE2P (PSA PAKE is unavailable on native_sim) and ``CONFIG_MBEDTLS_HEAP_SIZE=32768``.

The snippet enlarges the ``storage`` partition to 42 KiB and uses the ZMS settings backend (``CONFIG_SETTINGS_ZMS`` with 10 × 4 KiB sectors) so fabric commit has enough space; wipe simulated flash after partition/backend changes.

Operational fabric keys use ``PersistentStorageOperationalKeystore`` (ZMS) on native_sim (``MATTER_PERSISTENT_STORAGE_OPERATIONAL_KEYS``): host has no PSA persistent/ITS backend, so the default ``PSAOperationalKeystore`` fails ``CommissioningComplete`` with ``PSA error: -134``.

Teardown: ``sudo ../../../../../scripts/native_sim/bin/run-in-netns --teardown``.

IPv6 Duplicate Address Detection is disabled and all addresses are added with ``nodad``.
Matter starts advertising over mDNS during boot, and sending from an address that is still tentative fails with ``EADDRNOTAVAIL``.

Host IPv6 multicast for minimal mDNS is enabled via ``IPV6_MULTICAST_IMPLEMENTED``, added for ``CONFIG_ARCH_POSIX`` in :file:`modules/lib/matter/config/nrfconnect/chip-module/CMakeLists.txt`.


Relation to nRF DK builds
*************************

This snippet is not, and cannot be, network-equivalent to an nRF DK build.
An nRF DK runs Matter on the Zephyr network stack—OpenThread with ``chip_mdns = "platform"``, or nRF70 Wi-Fi with ``chip_mdns = "minimal"`` over Zephyr sockets and ``CHIP_SYSTEM_CONFIG_USE_ZEPHYR_NET_IF=1``.
On ``native_sim`` the application instead uses host BSD sockets and host interfaces.

The Zephyr-stack path is unavailable on ``ARCH_POSIX`` for two independent reasons.
CHIP excludes the combination in :file:`src/system/SystemConfig.h`, which requires ``!defined(CONFIG_ARCH_POSIX)`` before selecting Zephyr sockets, and forcing it produces symbol collisions between :file:`src/inet/ZephyrSocket.h` (``fd_set``, ``select``, ``socket``, ``poll``) plus Zephyr's ``CONFIG_NET_NAMESPACE_COMPAT_MODE`` remapping (``sockaddr``, ``socklen_t``, ``htons``, ``AF_*``) and the host glibc headers.
``CONFIG_NET_SOCKETS_POSIX_NAMES`` was removed in Zephyr 4.1, and ``CONFIG_POSIX_API`` selects ``NATIVE_LIBC_INCOMPATIBLE``, which moves ``native_sim`` off the host libc altogether.
Independently, the nrfconnect platform hardcodes ``CHIP_DEVICE_CONFIG_ENABLE_ETHERNET`` to 0 and provides no Ethernet ``ConnectivityManager``, ``NetworkCommissioning`` driver, or diagnostics.

The parity target for this snippet is therefore the ``native_sim`` configuration maintained upstream in :file:`modules/lib/matter/src/test_driver/nrfconnect/CMakeLists.txt`, which :file:`subsys/app/chip_project_config_native_sim.h` matches.

Use ``native_sim`` for build coverage, cluster and application logic, persistence, and OTA state handling.
Validate anything that depends on the network stack—Thread or Wi-Fi commissioning, SRP and mDNS behaviour, ICD and power characteristics, radio coexistence, and MCUboot DFU—on a DK.


Usage in custom applications
****************************

For Matter applications outside :file:`ncs-matter/samples`, include :file:`cmake/find_zephyr.cmake` (or :file:`cmake/native_sim_snippet.cmake` before ``find_package(Zephyr)``), add the native sim CHIP header to :file:`chip_project_config.h`, and pass ``-D<app>_SNIPPET=native-sim`` for sysbuild or ``-DSNIPPET=native-sim`` for freestanding builds.
