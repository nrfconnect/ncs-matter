.. _matter_samples:

Samples
#######

The |NCS| provides several samples showcasing the :ref:`Matter <ug_matter>` protocol.
You can build the samples for a variety of board targets and configure them for different usage scenarios.

The following table lists variants and extensions available out of the box for each Matter sample:

.. list-table::
    :widths: auto
    :header-rows: 1

    * - Variant or extension
      - Light bulb
      - Light switch
      - Template
      - Window covering
      - Thermostat
      - Smoke CO alarm
      - Temperature sensor
      - Contact sensor
      - Closure
      - Matter Weather Station
      - Matter Bridge
    * - FEM support
      - ✔
      - ✔
      - ✔
      - ✔
      -
      -
      -
      -
      -
      -
      -
    * - DFU support
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
    * - Thread support
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
      - ✔
    * - :ref:`Thread role <thread_ot_device_types>`
      - Router
      - SED
      - MED
      - SED, SSED (optional)
      - MED
      - SED
      - SED
      - SED
      - FTD
      - SED
      - MTD
    * - :ref:`ICD mode <ug_matter_device_low_power_icd>`
      - Not supported
      - SIT, LIT (optional)
      - Not supported
      - SIT
      - Not supported
      - LIT
      - LIT
      - LIT
      - Not supported
      - SIT
      - Not supported
    * - Wi-Fi® support
      - ✔
      - ✔
      - ✔
      -
      - ✔
      -
      -
      -
      - ✔
      -
      - ✔
    * - Low power configuration by default
      -
      - ✔
      -
      - ✔
      -
      - ✔
      - ✔
      - ✔
      -
      - ✔
      -

See the sample documentation pages for instructions about how to enable these variants and extensions.

Additionally, a Matter Door Lock sample is available in the `nRF Door Lock and Access Control Add-on`_ repository.
This add-on includes also samples with support for the Aliro protocol, and Matter and Aliro combined solution.
