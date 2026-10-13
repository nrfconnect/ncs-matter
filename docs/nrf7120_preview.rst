.. _ncs_matter_nrf7120_preview:

nRF7120 DK preview
##################

.. important::

   The |addon| provides nRF7120 DK support as an experimental preview for evaluation purposes only.

.. note::

   The nRF7120 SoC is also capable of supporting Thread over IEEE 802.15.4.
   However, Thread is not supported in this preview release.

Overview
********

The preview lets you evaluate selected Matter over Wi-Fi samples on the nRF7120 DK.
The nRF7120 combines an application processor, a Wi-Fi 6 radio, and a multiprotocol radio for Bluetooth LE in a single SoC.
As a result, the Matter application and the Wi-Fi and Bluetooth LE stacks can run on the same device without an external Wi-Fi companion chip.
This is a significant improvement over the nRF54LM20 SoC, which requires an external nRF7002-EB II shield for Wi-Fi support.
For information about the nRF7120 Matter over Wi-Fi architecture, see :ref:`ug_matter_overview_architecture_integration_designs_wifi`.
For more information about the nRF71 Series, see the `nRF71 Series product documentation <https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/app_dev/device_guides/nrf71/index.html#ug-nrf71>`_.

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

* Matter support is limited to Matter over Wi-Fi.
* Device Firmware Update (DFU) is not supported.
* MCUboot is not supported.
* Device Attestation Certificate (DAC) private key migration is not supported because MRAM does not currently support clearing factory data.
* nRF Wi-Fi low-power mode must be enabled when using Wi-Fi in the 2.4 GHz band because of Wi-Fi and Bluetooth LE coexistence issues.
  It is not required when using the 5 GHz band.
