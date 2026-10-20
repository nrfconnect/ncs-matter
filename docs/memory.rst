.. _ncs_matter_memory:

Memory requirements
###################

.. contents::
   :local:
   :depth: 2

This page provides information about the amount of flash memory and RAM that is required by the :ref:`matter_samples`.
Use it to check if your application has enough space for a given configuration.

.. _ncs_matter_memory_requirements_ram_flash:

RAM and flash memory requirements
*********************************

RAM and flash memory requirement values differ depending on the DK and the programmed sample.

The following tables and bar charts list memory requirement values for Matter samples.

Memory layout is taken from the DTS files used by each sample variant, while memory usage is taken from the build output.
Values are provided in kilobytes (KB).

Table columns are grouped by internal NVM, external NVM (when used), and RAM.
Application, MCUboot, upgrade slot, and RAM cells show used and free space separated by ``/``.
Other NVM columns list the reserved partition size for that region.

.. tabs::

   .. group-tab:: Charts

      .. tabs::

         .. group-tab:: nRF52840 DK

            Memory requirements for samples running on the `nrf52840dk`_.

            .. memory-board::
               :board: nrf52840

         .. group-tab:: nRF5340 DK

            Memory requirements for samples running on the `nrf5340dk`_.

            .. memory-board::
               :board: nrf5340

         .. group-tab:: Nordic Thingy:53

            Memory requirements for samples running on the `thingy53`_.

            .. memory-board::
               :board: thingy53

         .. group-tab:: nRF54L15 DK

            Memory requirements for samples running on the `nrf54l15dk`_.

            .. memory-board::
               :board: nrf54l15

         .. group-tab:: nRF54L15 DK + CMSE (TF-M)

            Memory requirements for samples running on the `nrf54l15dk`_ with Trusted Firmware-M (TF-M).

            .. memory-board::
               :board: nrf54l15_cmse

         .. group-tab:: nRF54L10 emulation

            Memory requirements for samples running on the `nrf54l15dk`_ with internal memory only.

            .. memory-board::
               :board: nrf54l10

         .. group-tab:: nRF54L15 TAG

            Memory requirements for samples running on the `nrf54l15tag`_.

            .. memory-board::
               :board: nrf54l15tag

         .. group-tab:: nRF54LM20 DK

            Memory requirements for samples running on the `nrf54lm20dk`_.

            .. memory-board::
               :board: nrf54lm20

         .. group-tab:: nRF54LM20 DK + nRF7002 EB2

            Memory requirements for samples running on the `nrf54lm20dk`_ with the nRF7002 EB2 shield.

            .. memory-board::
               :board: nrf54lm20_nrf7002

         .. group-tab:: nRF7120 DK

            Memory requirements for samples running on the `nrf7120dk`_.

            .. memory-board::
               :board: nrf7120

   .. group-tab:: Tables

      .. tabs::

         .. group-tab:: nRF52840 DK

            The following table lists memory requirements for samples running on the `nrf52840dk`_.

            .. memory-table::
               :board: nrf52840

         .. group-tab:: nRF5340 DK

            The following table lists memory requirements for samples running on the `nrf5340dk`_.

            .. memory-table::
               :board: nrf5340

         .. group-tab:: Nordic Thingy:53

            The following table lists memory requirements for samples running on the `thingy53`_.

            .. memory-table::
               :board: thingy53

         .. group-tab:: nRF54L15 DK

            The following table lists memory requirements for samples running on the `nrf54l15dk`_.

            .. memory-table::
               :board: nrf54l15

         .. group-tab:: nRF54L15 DK + CMSE (TF-M)

            The following table lists memory requirements for samples running on the `nrf54l15dk`_ with Trusted Firmware-M (TF-M).

            .. memory-table::
               :board: nrf54l15_cmse

         .. group-tab:: nRF54L10 emulation

            The following table lists memory requirements for samples running on the `nrf54l15dk`_ with internal memory only.

            .. memory-table::
               :board: nrf54l10

         .. group-tab:: nRF54L15 TAG

            The following table lists memory requirements for samples running on the `nrf54l15tag`_.

            .. memory-table::
               :board: nrf54l15tag

         .. group-tab:: nRF54LM20 DK

            The following table lists memory requirements for samples running on the `nrf54lm20dk`_.

            .. memory-table::
               :board: nrf54lm20

         .. group-tab:: nRF54LM20 DK + nRF7002 EB2

            The following table lists memory requirements for samples running on the `nrf54lm20dk`_ with the nRF7002 EB2 shield.

            .. memory-table::
               :board: nrf54lm20_nrf7002

         .. group-tab:: nRF7120 DK

            The following table lists memory requirements for samples running on the `nrf7120dk`_.

            .. memory-table::
               :board: nrf7120

.. note::

   The ``release`` configurations are built with Link-Time Optimization (LTO).

.. _ncs_matter_memory_requirements_layouts:

Reference Matter memory layouts
*******************************

The following tables and bar charts show how the :ref:`Matter stack architecture in the nRF Connect SDK <ug_matter_overview_architecture_integration_stack>` translates to actual memory maps for each of the available :ref:`ug_matter_overview_architecture_integration_designs`.
The memory values match the :ref:`RAM and flash memory requirements <ncs_matter_memory_requirements_ram_flash>` listed.

Each tab shows the memory maps for the development kits supported by the Matter protocol, including two memory maps for the :ref:`matter_weather_station_app`, which uses Nordic Thingy:53.

For more information about configuration of memory layouts in Matter, see :ref:`ug_matter_device_bootloader_partition_layout`.

.. tabs::

   .. group-tab:: Charts

      .. tabs::

         .. group-tab:: nRF52840 DK

            The following memory map is valid for Matter applications running on the `nrf52840dk`_.

            .. memory-layout-board::
               :board: nrf52840

         .. group-tab:: nRF5340 DK

            The following memory map is valid for Matter applications running on the `nrf5340dk`_.

            .. memory-layout-board::
               :board: nrf5340

         .. group-tab:: Nordic Thingy:53

            The following memory map is valid for Matter applications running on the `thingy53`_.

            .. memory-layout-board::
               :board: thingy53

         .. group-tab:: nRF54L15 DK

            The following memory map is valid for Matter applications running on the `nrf54l15dk`_.

            .. memory-layout-board::
               :board: nrf54l15

         .. group-tab:: nRF54L15 DK + CMSE (TF-M)

            The following memory map is valid for Matter applications running on the `nrf54l15dk`_ with Trusted Firmware-M (TF-M).

            .. memory-layout-board::
               :board: nrf54l15_cmse

         .. group-tab:: nRF54L15 DK with internal memory only

            The following memory map is valid for Matter applications running on the `nrf54l15dk`_ with internal memory only.

            .. memory-layout-board::
               :board: nrf54l15_internal

         .. group-tab:: nRF54L10 emulation

            The following memory map is valid for Matter applications running on the `nrf54l15dk`_ with internal memory only.

            .. memory-layout-board::
               :board: nrf54l10

         .. group-tab:: nRF54L15 TAG

            The following memory map is valid for Matter applications running on the `nrf54l15tag`_.

            .. memory-layout-board::
               :board: nrf54l15tag

         .. group-tab:: nRF54LM20 DK

            The following memory map is valid for Matter applications running on the `nrf54lm20dk`_.

            .. memory-layout-board::
               :board: nrf54lm20

         .. group-tab:: nRF54LM20 DK with internal memory only

            The following memory map is valid for Matter applications running on the `nrf54lm20dk`_ with internal memory only.

            .. memory-layout-board::
               :board: nrf54lm20_internal

         .. group-tab:: nRF54LM20 DK + nRF7002 EB2

            The following memory map is valid for Matter applications running on the `nrf54lm20dk`_ with the nRF7002 EB2 shield.

            .. memory-layout-board::
               :board: nrf54lm20_nrf7002

         .. group-tab:: nRF7120 DK

            The following memory map is valid for Matter applications running on the `nrf7120dk`_.

            .. memory-layout-board::
               :board: nrf7120

   .. group-tab:: Tables

      .. tabs::

         .. group-tab:: nRF52840 DK

            The following table lists memory partitions for Matter applications running on the `nrf52840dk`_.

            .. memory-layout-table::
               :board: nrf52840

         .. group-tab:: nRF5340 DK

            The following table lists memory partitions for Matter applications running on the `nrf5340dk`_.

            .. memory-layout-table::
               :board: nrf5340

         .. group-tab:: Nordic Thingy:53

            The following table lists memory partitions for Matter applications running on the `thingy53`_.

            .. memory-layout-table::
               :board: thingy53

         .. group-tab:: nRF54L15 DK

            The following table lists memory partitions for Matter applications running on the `nrf54l15dk`_.

            .. memory-layout-table::
               :board: nrf54l15

         .. group-tab:: nRF54L15 DK + CMSE (TF-M)

            The following table lists memory partitions for Matter applications running on the `nrf54l15dk`_ with Trusted Firmware-M (TF-M).

            .. memory-layout-table::
               :board: nrf54l15_cmse

         .. group-tab:: nRF54L15 DK with internal memory only

            The following table lists memory partitions for Matter applications running on the `nrf54l15dk`_ with internal memory only.

            .. memory-layout-table::
               :board: nrf54l15_internal

         .. group-tab:: nRF54L10 emulation

            The following table lists memory partitions for Matter applications running on the `nrf54l15dk`_ with internal memory only.

            .. memory-layout-table::
               :board: nrf54l10

         .. group-tab:: nRF54L15 TAG

            The following table lists memory partitions for Matter applications running on the `nrf54l15tag`_.

            .. memory-layout-table::
               :board: nrf54l15tag

         .. group-tab:: nRF54LM20 DK

            The following table lists memory partitions for Matter applications running on the `nrf54lm20dk`_.

            .. memory-layout-table::
               :board: nrf54lm20

         .. group-tab:: nRF54LM20 DK with internal memory only

            The following table lists memory partitions for Matter applications running on the `nrf54lm20dk`_ with internal memory only.

            .. memory-layout-table::
               :board: nrf54lm20_internal

         .. group-tab:: nRF54LM20 DK + nRF7002 EB2

            The following table lists memory partitions for Matter applications running on the `nrf54lm20dk`_ with the nRF7002 EB2 shield.

            .. memory-layout-table::
               :board: nrf54lm20_nrf7002

         .. group-tab:: nRF7120 DK

            The following table lists memory partitions for Matter applications running on the `nrf7120dk`_.

            .. memory-layout-table::
               :board: nrf7120

Diagnostic logs RAM memory requirements
=======================================

:ref:`Diagnostic logs support<ug_matter_configuration_diagnostic_logs>` requires changing the RAM memory layout by adding three retained RAM partitions to keep the log data persistent across device reboots.
The :ref:`snippet_matter_diagnostic_logs` adds these RAM partitions and also reduces the amount of SRAM available for the application by the size of the retained partitions.
You can adjust the retained partitions for your needs by editing the :ref:`snippet_matter_diagnostic_logs` devicetree file for the relevant board.

.. tabs::

   .. tab:: nRF52840 DK

    The following RAM memory layout is valid for Matter applications running on the `nrf52840dk`_.

    Base Application core SRAM size (size: 0x40000 = 256 kB)
    SRAM is located at the address ``0x20000000`` in the memory address space of the application.

      +-------------------------------+----------------------+----------------------+
      | Partition                     | Offset               | Size                 |
      +===============================+======================+======================+
      | Application core SRAM primary | 0 (0x0)              | 247,8125 kB (0x3DF40)|
      +-------------------------------+----------------------+----------------------+
      | Crash retention               | 247,8125 kB (0x3DF40)| 192 B (0xC0)         |
      +-------------------------------+----------------------+----------------------+
      | Network logs retention        | 248 kB (0x3E000)     | 6 kB (0x1800)        |
      +-------------------------------+----------------------+----------------------+
      | User data logs retention      | 254 kB (0x3F800)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+

   .. tab:: nRF5340 DK

    The following RAM memory layout is valid for Matter applications running on the `nrf5340dk`_.

    Application core SRAM primary (size: 0x80000 = 512 kB)
    SRAM is located at the address ``0x20000000`` in the memory address space of the application.

      +-------------------------------+----------------------+----------------------+
      | Partition                     | Offset               | Size                 |
      +===============================+======================+======================+
      | Application core SRAM primary | 0 (0x0)              | 503,8125 kB (0x7DF40)|
      +-------------------------------+----------------------+----------------------+
      | Crash retention               | 503,8125 kB (0x7DF40)| 192 B (0xC0)         |
      +-------------------------------+----------------------+----------------------+
      | Network logs retention        | 504 kB (0x7E000)     | 6 kB (0x1800)        |
      +-------------------------------+----------------------+----------------------+
      | User data logs retention      | 510 kB (0x7F800)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+

   .. tab:: Nordic Thingy:53

    The following RAM memory layout for the :ref:`Matter weather station <matter_weather_station_app>` application running on the `thingy53`_.

    Application core SRAM primary (size: 0x80000 = 512 kB)
    SRAM is located at the address ``0x20000000`` in the memory address space of the application.

      +-------------------------------+----------------------+----------------------+
      | Partition                     | Offset               | Size                 |
      +===============================+======================+======================+
      | Application core SRAM primary | 0 (0x0)              | 503,8125 kB (0x7DF40)|
      +-------------------------------+----------------------+----------------------+
      | Crash retention               | 503,8125 kB (0x7DF40)| 192 B (0xC0)         |
      +-------------------------------+----------------------+----------------------+
      | Network logs retention        | 504 kB (0x7E000)     | 6 kB (0x1800)        |
      +-------------------------------+----------------------+----------------------+
      | User data logs retention      | 510 kB (0x7F800)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+

   .. tab:: nRF54L15 DK

    The following RAM memory layout is valid for Matter applications running on the `nrf54l15dk`_.

    Base SRAM size (size: 0x40000 = 256 kB)
    SRAM is located at the address ``0x20000000`` in the memory address space of the application.

      +-------------------------------+----------------------+----------------------+
      | Partition                     | Offset               | Size                 |
      +===============================+======================+======================+
      | Application core SRAM primary | 0 (0x0)              | 247,8125 kB (0x3DF40)|
      +-------------------------------+----------------------+----------------------+
      | Crash retention               | 247,8125 kB (0x3DF40)| 192 B (0xC0)         |
      +-------------------------------+----------------------+----------------------+
      | Network logs retention        | 248 kB (0x3E000)     | 6 kB (0x1800)        |
      +-------------------------------+----------------------+----------------------+
      | User data logs retention      | 254 kB (0x3F800)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+

   .. tab:: nRF54L10 emulation on nRF54L15 DK

    The following RAM memory layout is valid for Matter applications running on the `nrf54l15dk`_.

    Base SRAM size (size: 0x30000 = 192 kB)
    SRAM is located at the address ``0x20000000`` in the memory address space of the application.

      +-------------------------------+----------------------+----------------------+
      | Partition                     | Offset               | Size                 |
      +===============================+======================+======================+
      | Application core SRAM primary | 0 (0x0)              | 187,8125 kB (0x2EF40)|
      +-------------------------------+----------------------+----------------------+
      | Crash retention               | 187.8125 kB (0x2EF40)| 192 B (0xC0)         |
      +-------------------------------+----------------------+----------------------+
      | Network logs retention        | 188 kB (0x2F000)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+
      | User data logs retention      | 190 kB (0x2F800)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+

   .. tab:: nRF54LM20 DK

    The following RAM memory layout is valid for Matter applications running on the `nrf54lm20dk`_.

    Base SRAM size (size: 0x7FC00 = 511 kB)
    SRAM is located at the address ``0x20000000`` in the memory address space of the application.

      +-------------------------------+----------------------+----------------------+
      | Partition                     | Offset               | Size                 |
      +===============================+======================+======================+
      | Application core SRAM primary | 0 (0x0)              | 502,8125 kB (0x7DB40)|
      +-------------------------------+----------------------+----------------------+
      | Crash retention               | 502,8125 kB (0x7DB40)| 192 B (0xC0)         |
      +-------------------------------+----------------------+----------------------+
      | Network logs retention        | 503 kB (0x7DC00)     | 6 kB (0x1800)        |
      +-------------------------------+----------------------+----------------------+
      | User data logs retention      | 509 kB (0x7F400)     | 2 kB (0x800)         |
      +-------------------------------+----------------------+----------------------+
..
