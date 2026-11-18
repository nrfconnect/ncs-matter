.. _ncs_matter_config:

Configuration options
#####################

.. contents::
   :local:
   :depth: 2

This page lists the Kconfig options provided by the |addon|.

To use the add-on in a Matter application, enable the :kconfig:option:`CONFIG_CHIP` Kconfig option.
This option enables the Matter protocol stack and other associated features and components.

|config|

.. _ncs_matter_kconfig:

Add-on Kconfig options
**********************

Shared configurations in Matter stack
#####################################

.. options-from-kconfig:: /../Kconfig
   :show-type:

Zephyr configuration options (inherited by nRF Connect)
*******************************************************

.. options-from-kconfig:: ../modules/lib/matter/zephyr/Kconfig
   :show-type:

nRF Connect Configuration
=========================

.. options-from-kconfig:: ../modules/lib/matter/config/nrfconnect/chip-module/Kconfig
   :show-type:

Matter features
===============

.. options-from-kconfig:: ../modules/lib/matter/config/nrfconnect/chip-module/Kconfig.features
