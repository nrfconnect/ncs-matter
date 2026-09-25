.. _matter_samples:

Samples
#######

The |addon| provides several samples showcasing the :ref:`Matter <ug_matter>` protocol.
You can build the samples for a variety of board targets and configure them for different usage scenarios.

The following table lists variants and extensions available out of the box for each Matter sample:

.. list-table::
    :widths: auto
    :header-rows: 1

    * - Variant or extension
      - :ref:`Light bulb <matter_light_bulb_sample_preview>`
      - :ref:`Light switch <matter_light_switch_sample_preview>`
      - :ref:`Template <matter_template_sample_preview>`
      - :ref:`Window covering <matter_window_covering_sample_preview>`
      - :ref:`Thermostat <matter_thermostat_sample_preview>`
      - :ref:`Smoke CO alarm <matter_smoke_co_alarm_sample_preview>`
      - :ref:`Temperature sensor <matter_temperature_sensor_sample_preview>`
      - :ref:`Contact sensor <matter_contact_sensor_sample_preview>`
      - :ref:`Closure <matter_closure_sample_preview>`
      - :ref:`Weather Station <matter_weather_station_sample_preview>`
      - :ref:`Bridge <matter_bridge_sample_preview>`
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
    * - `Thread device types`_
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

.. toctree::
   :maxdepth: 1
   :caption: Contents
   :glob:

   */README
