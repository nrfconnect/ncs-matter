#!/usr/bin/env bash
# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

# -E so the ERR trap in netns_setup also fires for failures inside functions.
set -eEuo pipefail

NETNS_NAME="${NETNS_NAME:-matter-app}"
VETH_APP="${VETH_APP:-veth-app}"
VETH_HOST="${VETH_HOST:-veth-br}"
APP_IPV4="${APP_IPV4:-10.10.10.2/24}"
HOST_IPV4="${HOST_IPV4:-10.10.10.1/24}"
APP_IPV6_LL="${APP_IPV6_LL:-fe80::2/64}"
HOST_IPV6_LL="${HOST_IPV6_LL:-fe80::1/64}"
# Routable ULA prefix, mirroring the Matter upstream test harness (fd00:0:1:1::/64).
APP_IPV6="${APP_IPV6:-fd00:0:1:1::2/64}"
HOST_IPV6="${HOST_IPV6:-fd00:0:1:1::1/64}"

netns_require_root() {
	if [[ "${EUID}" -ne 0 ]]; then
		echo "run-in-netns: need root (sudo) for ip netns" >&2
		exit 2
	fi
}

netns_exists() {
	ip netns list | awk '{print $1}' | grep -Fxq "${NETNS_NAME}"
}

# Duplicate Address Detection leaves a fresh IPv6 address "tentative" for ~1s,
# and sending from a tentative address fails with EADDRNOTAVAIL. mDNS starts
# advertising immediately at boot, so DAD is disabled on both ends and every
# address is added with 'nodad'.
netns_disable_dad() {
	local iface="$1"
	shift

	"$@" sysctl -qw "net.ipv6.conf.${iface}.disable_ipv6=0"
	"$@" sysctl -qw "net.ipv6.conf.${iface}.accept_dad=0"
}

netns_create() {
	# Clear the trap inside the handler so a failing teardown cannot re-trigger it.
	trap 'trap - ERR; netns_teardown' ERR

	ip netns add "${NETNS_NAME}"
	ip link add "${VETH_APP}" type veth peer name "${VETH_HOST}"
	ip link set "${VETH_APP}" netns "${NETNS_NAME}"

	netns_disable_dad "${VETH_HOST}"
	ip addr add "${HOST_IPV4}" dev "${VETH_HOST}"
	ip -6 addr add "${HOST_IPV6_LL}" dev "${VETH_HOST}" nodad
	ip -6 addr add "${HOST_IPV6}" dev "${VETH_HOST}" nodad
	ip link set "${VETH_HOST}" up

	local in_netns=(ip netns exec "${NETNS_NAME}")

	netns_disable_dad "${VETH_APP}" "${in_netns[@]}"
	"${in_netns[@]}" ip link set lo up
	"${in_netns[@]}" ip addr add "${APP_IPV4}" dev "${VETH_APP}"
	"${in_netns[@]}" ip -6 addr add "${APP_IPV6_LL}" dev "${VETH_APP}" nodad
	"${in_netns[@]}" ip -6 addr add "${APP_IPV6}" dev "${VETH_APP}" nodad
	"${in_netns[@]}" ip link set "${VETH_APP}" up

	trap - ERR
}

netns_setup() {
	netns_require_root

	if netns_exists; then
		echo "run-in-netns: netns '${NETNS_NAME}' already exists" >&2
		exit 2
	fi

	netns_create
}

netns_ensure() {
	netns_require_root

	if netns_exists; then
		return 0
	fi

	netns_create
}

netns_teardown() {
	netns_require_root

	if netns_exists; then
		ip netns delete "${NETNS_NAME}"
	fi

	if ip link show "${VETH_HOST}" >/dev/null 2>&1; then
		ip link delete "${VETH_HOST}"
	fi
}

netns_exec() {
	netns_require_root

	if ! netns_exists; then
		echo "run-in-netns: netns '${NETNS_NAME}' missing; run with --setup-only first" >&2
		exit 2
	fi

	ip netns exec "${NETNS_NAME}" "$@"
}

netns_print_info() {
	cat <<EOF
Network namespace: ${NETNS_NAME}
  app iface:  ${VETH_APP}  ${APP_IPV4}  ${APP_IPV6}  ${APP_IPV6_LL}
  host iface: ${VETH_HOST} ${HOST_IPV4}  ${HOST_IPV6}  ${HOST_IPV6_LL}
Run chip-tool on the host over ${VETH_HOST} (${HOST_IPV6%/*}), or inside the netns:
  sudo ip netns exec ${NETNS_NAME} chip-tool ...
EOF
}
