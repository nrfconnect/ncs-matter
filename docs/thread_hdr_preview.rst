.. _ncs_matter_thread_hdr_preview:

Thread HDR preview
##################

.. contents::
   :local:
   :depth: 2

.. important::
   The |addon| provides experimental Thread HDR (High Data Rate) support as a preview intended for evaluation purposes only.

Overview
********

This preview is based on the |addon| v\ |addon_version| release.
See :ref:`release_notes_preview_thread_hdr` for the changelog.

The |addon| preview adds experimental support for Thread High Data Rate (HDR) - an extension that lets compatible neighbors use a faster radio physical layer while keeping the same MAC and Thread stack above it.

In this preview, the alternate PHY is based on 2 Mbps GFSK.
Data frames that use HDR are transmitted with GFSK at 2 Mbps instead of the default O-QPSK 250 kbps modulation.

Thread HDR-capable devices advertise their alternate PHY capabilities to neighbors through MLE (Mesh Link Establishment).
When two peers support the same alternate PHY, the stack may select it for transmission based on configured PHY priorities and link quality.
Both ends must recognize the capability before HDR is used.
A node does not switch to the faster PHY unless the peer can receive it.

Thread HDR is backward compatible with legacy O-QPSK-only devices in the same Thread network.
Switching to 2 Mbps GFSK takes place for each packet.
It is not a permanent PHY switch.
Each higher-rate transmission is preceded by a short control frame on O-QPSK called DAPS (Dynamic Alternate PHY Switch) that tells the receiver which alternate PHY to use for the following frame.
If HDR cannot be used, traffic continues on O-QPSK.

Expected benefits
=================

* Higher application throughput compared to legacy O-QPSK operation.
  The actual gain depends on many factors, like packet size, link conditions, and the number of nodes in the network.
  The gains in P2P link throughput measured in a UDP payload test compared to legacy O-QPSK operation have been observed to be up to about 4 times.
* Shorter radio activity windows on the alternate PHY may reduce power consumption for a given amount of transferred data.
* Reduced time on air may also lower channel occupancy, which can benefit larger Thread networks.

Enabling HDR
************

Add the ``ot-hdr`` snippet from the |addon| when building:

.. tabs::

   .. group-tab:: Command line

      .. code-block:: console

         west build -p -b <board_target> -- -DSNIPPET=ot-hdr

      For debug logging of Thread HDR activity, combine with ``ot-hdr-log``:

      .. code-block:: console

         west build -p -b <board_target> -- -DSNIPPET="ot-hdr;ot-hdr-log"

   .. group-tab:: |nRFVSC|

      Select the ``ot-hdr`` snippet from the **Snippets** menu.
      Optionally add ``ot-hdr-log``.

The snippet applies the Kconfig options required for HDR.
Inspect the :file:`ncs-matter/snippets/openthread/ot-hdr/ot-hdr.conf` file for the full list of enabled options and default values.
Copy individual settings into your application configuration if you need a custom setup.

Testing scenario
****************

.. note::
   This guide uses the OpenThread CLI application from the |NCS| (:file:`nrf/samples/openthread/cli` folder) as a reference setup for evaluation.

Hardware requirements
=====================

* Two development kits (nRF54L15 DK or nRF54LM20 DK)

Building and flashing
=====================

From your |addon| workspace, build the OpenThread CLI reference application with HDR and ``otperf`` enabled:

.. code-block:: console

   cd nrf/samples/openthread/cli
   west build -p -b nrf54l15dk/nrf54l15/cpuapp -- -DSNIPPET=ot-hdr -DCONFIG_OTPERF=y
   west flash --erase

Repeat for the second board.

Form a Thread network
=====================

On both devices, open the OpenThread shell and run the following commands:

.. code-block:: console

   ot channel 25
   ot panid 0x1234
   ot networkkey 00112233445566778899aabbccddeeff
   ot ifconfig up
   ot thread start

Wait until one device becomes ``Leader`` and the other joins the same network.
Assume that the first device is the server and the second one is the client.

Run a UDP throughput test
=========================

On the server node, read the mesh-local IPv6 address as follows:

.. code-block:: console

   ot ipaddr

Example output:

.. code-block:: console

   fdde:ad00:beef:0:0:ff:fe00:fc00
   fdde:ad00:beef:0:ff:fe00:3800
   fdde:ad00:beef:0:b173:9541:efcd:4237
   fe80:0:0:0:10e0:c3ce:2f2d:e236
   Done

Start the UDP server:

.. code-block:: console

   otperf udp download 5001

On the client, upload to the server address from ``ot ipaddr`` (replace with your address):

.. code-block:: console

   otperf udp upload fdde:ad00:beef:0:b173:9541:efcd:4237 5001 10 1232 410K

Example result:

.. code-block:: console

   Remote port is 5001
   Connecting to fdde:ad00:beef:0:b173:9541:efcd:4237
   Duration:       10.00 s
   Packet size:    1232 bytes
   Rate:           410 Kbps
   Starting...
   Ping reply received!
   Packet duration 23 ms
   -
   Upload completed!
   Statistics:                     server  (client)
   Duration:                       10.01 s (9.95 s)
   Num packets:                    425     (425)
   Num packets out order:          0
   Num packets not received:       0
   Num packets skipped:            0
   Num packets lost:               0
   Jitter:                         1.45 ms
   Rate:                           418 Kbps (420 Kbps)


This example shows a throughput increase from about 100 Kbps that is typically achieved using legacy O-QPSK to more than 400 Kbps.

Limitations
***********

Switching time between O-QPSK and 2 Mbps GFSK is not optimized and implemented in the OpenThread platform layer.
