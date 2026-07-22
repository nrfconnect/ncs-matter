.. _ug_matter_hw_requirements:

Matter hardware and memory requirements
#######################################

.. contents::
   :local:
   :depth: 2

Hardware that runs Matter protocol applications must meet specification requirements, including providing the right amount of flash memory and being able to run Bluetooth® LE and Thread or Wi-Fi® concurrently.

.. _ug_matter_hw_requirements_socs:

Supported SoCs
**************

Currently the following SoCs from Nordic Semiconductor are supported for use with the Matter protocol:

* `nRF5340 <Programming board names>`_ (Matter over Thread)
* `nRF52840 <Programming board names>`_ (Matter over Thread)
* `nRF54L15 <Programming board names>`_ (Matter over Thread)
* `nRF54L10 <Programming board names>`_ (Matter over Thread)
* `nRF54LM20 <Programming board names>`_ (Matter over Thread and Matter over Wi-Fi through the ``nrf7002eb2`` shield)

Front-End Modules
=================

SoCs from Nordic Semiconductor that can run the Matter protocol over Thread can also work with external Front-End Modules.
For more information about the FEM support in the |NCS|, see `Developing with Front-End Modules <Developing with Front-End Modules>`_ and `nRF21540 DK <Programming board names>`_.

.. _ug_matter_hw_requirements_external_flash:

External flash
**************

For the currently supported SoCs, you must use an external memory with at least 1 MB of flash for nRF52840 and nRF54L10, and 1.5 MB for nRF5340 and nRF54L15.
This is required to perform the DFU operation.

.. note::
   The nRF54L15 supports DFU with image compression, which may eliminate the need for external flash.
   For more details, see `MCUboot image compression <MCUboot image compression>`_.

The development kits for the supported SoCs from Nordic Semiconductor are supplied with the MX25R64 type of external flash that meets these memory requirements.
However, it is possible to configure the SoCs with different QSPI or SPI memory if it is supported by Zephyr.
For this purpose, check the reference design for Nordic DKs for information about how to connect the external memory with SoC, specifically whether the pins are designed for the QSPI or the high-speed SPIM operations.

.. _ug_matter_hw_requirements_ram_flash:

RAM and flash memory requirements
*********************************

RAM and flash memory requirement values differ depending on the DK and the programmed sample.

The following tables and bar charts list memory requirement values for Matter samples.

Values are provided in kilobytes (KB).

Table columns are grouped by internal NVM, external NVM (when used), and RAM.
Application, MCUboot, upgrade slot, and RAM cells show used and free space separated by ``/``.
Other NVM columns list the reserved partition size for that region.

.. tabs::

   .. group-tab:: Charts

      .. memory-usage::
         :file: data/memory_usage.yaml

   .. group-tab:: Tables

      .. memory-table::
         :file: data/memory_usage.yaml

.. note::

   The ``release`` configurations are built with Link-Time Optimization (LTO).

.. _ug_matter_hw_requirements_layouts:

Reference Matter memory layouts
*******************************

The following tabs show how the :ref:`Matter stack architecture in the nRF Connect SDK <ug_matter_overview_architecture_integration_stack>` translates to actual memory maps for each of the available :ref:`ug_matter_overview_architecture_integration_designs`.
The memory values match :ref:`RAM and flash memory requirements <ug_matter_hw_requirements_ram_flash>` listed above.

Each tab shows the memory maps for the development kits supported by the Matter protocol, including two memory maps for the `Matter weather station sample <Matter weather station sample>`_, which uses Nordic Thingy:53.

For more information about configuration of memory layouts in Matter, see :ref:`ug_matter_device_bootloader_partition_layout`.

.. memory-layouts::
   :file: data/memory_layouts.yaml

Diagnostic logs RAM memory requirements
=======================================

:ref:`Diagnostic logs support<ug_matter_configuration_diagnostic_logs>` requires changing the RAM memory layout by adding three retained RAM partitions to keep the log data persistent across device reboots.
The :ref:`snippet_matter_diagnostic_logs` adds these RAM partitions and also reduces the amount of SRAM available for the application by the size of the retained partitions.
You can adjust the retained partitions for your needs by editing the :ref:`snippet_matter_diagnostic_logs` devicetree file for the relevant board.

.. tabs::

   .. tab:: nRF52840 DK

    The following RAM memory layout is valid for Matter applications running on the `nrf52840dk <nrf52840dk>`_.

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

    The following RAM memory layout is valid for Matter applications running on the `nrf5340dk <nrf5340dk>`_.

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

    The following RAM memory layout for the `Matter weather station <Matter weather station sample>`_ application running on the `thingy53 <thingy53>`_.

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

    The following RAM memory layout is valid for Matter applications running on the `nrf54l15dk <nrf54l15dk>`_.

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

    The following RAM memory layout is valid for Matter applications running on the `nrf54l15dk <nrf54l15dk>`_.

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

    The following RAM memory layout is valid for Matter applications running on the `nrf54lm20dk <nrf54lm20dk>`_.

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
