.. _ncs_matter_thread_hdr_preview:

Thread HDR preview
##################

.. contents::
   :local:
   :depth: 2

.. important::
   The |addon| provides experimental Thread HDR (High Data Rate) support as a preview intended **for evaluation purposes only**.

Overview
********

This preview is based on the |addon| v\ |addon_version| release.
See :ref:`release_notes_preview_thread_hdr` for the changelog.

The |addon| preview adds experimental support for Thread **High Data Rate (HDR)** - an extension that lets compatible neighbors use a faster radio physical layer while keeping the same MAC and Thread stack above it.

In this preview, the alternate PHY is based on **2 Mbps GFSK**.
Data frames that use HDR are transmitted with GFSK at 2 Mbps instead of the default **O-QPSK 250 kbps** modulation.

Thread HDR-capable devices advertise their alternate PHY capabilities to neighbors through **MLE** (Mesh Link Establishment).
When two peers both support the same alternate PHY, the stack may select it for transmission based on configured PHY priorities and link quality.
Both ends must recognize the capability before HDR is used.
A node does not switch to the faster PHY unless the peer can receive it.

Thread HDR is **backward compatible** with legacy O-QPSK-only devices in the same Thread network.
Switching to 2 Mbps GFSK is **per packet**, not a permanent PHY switch.
Each higher-rate transmission is preceded by a short **control frame on O-QPSK** called DAPS (Dynamic Alternate PHY Switch) that tells the receiver which alternate PHY to use for the following frame.
If HDR cannot be used, traffic continues on O-QPSK.

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

      Select the ``ot-hdr`` snippet from the :guilabel:`Snippets` menu.
      Optionally add ``ot-hdr-log``.

The snippet applies the Kconfig options required for HDR.
Inspect ``ncs-matter/snippets/openthread/ot-hdr/ot-hdr.conf`` for the full list of enabled options and default values.
Copy individual settings into your application configuration if you need a custom setup.

Testing scenario
****************

.. note::
   This guide uses the OpenThread CLI application from the |NCS| (``nrf/samples/openthread/cli``) as a **reference setup** for evaluation.

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

On **both** devices, open the OpenThread shell and run:

.. code-block:: console

   ot channel 25
   ot panid 0x1234
   ot networkkey 00112233445566778899aabbccddeeff
   ot ifconfig up
   ot thread start

Wait until one device becomes ``Leader`` and the other joins the same network.
Assume the first device is the **server** and the second is the **client**.

Run a UDP throughput test
=========================

On the **server** node, read the mesh-local IPv6 address:

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

On the **client**, upload to the server address from ``ot ipaddr`` (replace with your address):

.. code-block:: console

   otperf udp upload fdde:ad00:beef:0:b173:9541:efcd:4237 5001 10 1000 400K

Example result:

.. code-block:: console

   Remote port is 5001
   Connecting to fdde:ad00:beef:0:b173:9541:efcd:4237
   Duration:       10.00 s
   Packet size:    1000 bytes
   Rate:           400 Kbps
   Starting...
   Ping reply received!
   Packet duration 19 ms
   -
   Upload completed!
   Statistics:                     server   (client)
   Duration:                       10.14 s  (9.98 s)
   Num packets:                    510      (510)
   Num packets out order:          0
   Num packets not received:       0
   Num packets skipped:            0
   Num packets lost:               0
   Jitter:                         2.35 ms
   Rate:                           402 Kbps (408 Kbps)

This example shows a throughput increase from about 100 Kbps to about 400 Kbps.

Limitations
***********

* Switching time between O-QPSK and 2 Mbps GFSK is not optimized, and implement in the OpenThread platform layer.
