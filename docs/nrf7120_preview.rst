.. _ncs_matter_nrf7120_preview:

nRF7120 DK preview
##################

.. important::

   The |addon| provides nRF7120 DK support as an experimental preview for evaluation purposes only.

Overview
********

The preview lets you evaluate selected Matter over Wi-Fi samples on the nRF7120 DK.
The nRF7120 DK integrates the application processor, Wi-Fi 6 radio, and multiprotocol radio used for Bluetooth LE in one SoC.
This integration allows the Matter application and the Wi-Fi and Bluetooth LE stacks to run on the same device without an external nRF7002-EB II shield.
For details about the nRF7120 Matter over Wi-Fi architecture, see :ref:`ug_matter_overview_architecture_integration_designs_wifi`.

Supported samples
*****************

The nRF7120 DK preview supports the following samples:

* :ref:`Matter light bulb <matter_light_bulb_sample_preview>`
* :ref:`Matter light switch <matter_light_switch_sample_preview>`
* :ref:`Matter template <matter_template_sample_preview>`
* :ref:`Matter thermostat <matter_thermostat_sample_preview>`
* :ref:`Matter closure <matter_closure_sample_preview>`
* :ref:`Matter bridge <matter_bridge_sample_preview>`

Building a sample
*****************

Complete the :ref:`setup instructions <ncs_matter_setup>` before building a sample.
Navigate to the directory of a supported sample and use the following build configuration:

.. include:: /includes/building_and_running/nrf7120_wifi.txt

Limitations
***********

The preview has the following limitations:

* Device Firmware Update (DFU) is disabled.
* MCUboot is disabled.
* The private key migration of the Device Attestation Certificate (DAC) is disabled because MRAM does not currently support clearing factory data.
* nRF Wi-Fi low-power mode is enabled unconditionally for every supported sample.
