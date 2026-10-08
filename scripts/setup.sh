#!/usr/bin/env bash
# Copyright (c) 2026 Nordic Semiconductor ASA
# SPDX-License-Identifier: Apache-2.0
#
# Set up an nRF Connect SDK workspace with the Matter add-on (and optional
# Door Lock add-on) on Linux and macOS.
#
# Run from an existing ncs-matter checkout. The script symlinks that checkout
# into the sdk-manager SDK workspace (for example ~/ncs/v3.4.0/ncs-matter).
#
# Usage:
#   ./scripts/setup.sh [--branch REVISION] [--launch]
#   ./scripts/setup.sh [--revision REVISION] [--launch]
#   ./scripts/setup.sh --launch
#   ./scripts/setup.sh --cleanup
#   ./scripts/setup.sh build [--debug|--release] [--board BOARD] [--outdir DIR] [--name SUFFIX] [SAMPLE]
#   source ./scripts/setup.sh [--revision REVISION]   # export vars in current shell
#
# See docs/setup.rst and:
# https://docs.nordicsemi.com/bundle/ncs-latest/page/nrf/installation/install_ncs.html
#
# Tool versions are configured below (NRFUTIL_*, JLINK_*). Defaults match the Matter
# chip-build-nrf-platform Docker image.

set -euo pipefail

readonly DOOR_LOCK_REPO="https://github.com/nrfconnect/ncs-door-lock-and-access-control"
readonly DOOR_LOCK_DIR="ncs-door-lock-and-access-control"
readonly DOOR_LOCK_APP_DIR="applications/matter-door-lock-app"
readonly DOOR_LOCK_VERSION="v1.2.0"
readonly NCS_MATTER_DIR="ncs-matter"
readonly LOCK_SAMPLE_NAME="lock"
readonly NRFUTIL_BASE_URL="https://files.nordicsemi.com/artifactory/swtools/external/nrfutil/executables"

# Tool versions (aligned with matter chip-build-nrf-platform Docker image).
readonly NRFUTIL_VERSION="8.1.1"
readonly NRFUTIL_DEVICE_VERSION="2.19.0"
readonly NRFUTIL_SDK_MANGER_VERSION="1.16.1"
readonly NRFUTIL_FORCE_INSTALL=true
readonly JLINK_VERSION_LINUX_x86_64="JLink_Linux_V924a_x86_64"
readonly JLINK_VERSION_LINUX_aarch64="JLink_Linux_V924a_aarch64"
readonly JLINK_VERSION_MACOS="JLink_MacOSX_V924a_universal"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly PROG="${0##*/}"

COMMAND="setup"
REVISION="main"
CLEANUP=false
VERBOSE=false
LAUNCH=false
REVISION_EXPLICIT=false
FORCE_INSTALL=false # only the setup command force-reinstalls the nrfutil tools
WEST_MANIFEST_DIR="${NCS_MATTER_DIR}"
BUILD_SAMPLE=""
BUILD_MODE=""
BUILD_BOARD=""
BUILD_OUTDIR=""
BUILD_NAME=""
RUNNING_AS_SCRIPT=false
[[ "${BASH_SOURCE[0]}" == "${0}" ]] && RUNNING_AS_SCRIPT=true

# Set by init_platform.
OS=""
INSTALL_DIR=""
NRFUTIL_URL=""
JLINK_PACKAGE=""
JLINK_TAG=""
TOOLS_DIR=""

log() { printf '%s\n' "$*"; }

vlog() {
	[[ "${VERBOSE}" == true ]] || return 0
	printf '  %s\n' "$*"
}

phase() { printf '\n── %s ──\n' "$*"; }

die() {
	printf 'error: %s\n' "$*" >&2
	exit 1
}

usage() {
	cat <<EOF
Usage: ${PROG} [--revision REVISION]
       ${PROG} --cleanup
       ${PROG} build [--debug|--release] [--board BOARD] [--outdir DIR] [--name SUFFIX] [SAMPLE]

Commands:
  (default)         Install and configure the Matter add-on workspace
  build             Build a Matter sample (list samples when SAMPLE is omitted)
  --cleanup         Remove workspace symlinks, Door Lock add-on, SDK, and toolchain

Setup options:
  --branch REVISION    ncs-matter git branch, tag, or commit to check out (default: main)
  --revision REVISION  Same as --branch
  --launch             Enter the toolchain shell after setup (or launch only if workspace exists)
  --verbose            Print detailed progress messages

Build options:
  --debug           Build with matter-diagnostic-logs and matter-debug snippets (default)
  --release         Build with FILE_SUFFIX=release
  --board BOARD     Override the default board from sample.yaml
  --outdir DIR      Copy merged.hex to DIR after a successful build
  --name SUFFIX     Output hex name suffix: <sample><board><suffix>.hex (requires --outdir)
  -h, --help        Show this help message
EOF
}

parse_build_args() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--debug | --release)
			local mode="${1#--}"
			[[ -z "${BUILD_MODE}" || "${BUILD_MODE}" == "${mode}" ]] ||
				die "cannot combine --debug and --release"
			BUILD_MODE="${mode}"
			shift
			;;
		--board | --outdir | --name)
			[[ $# -ge 2 ]] || die "$1 requires a value"
			case "$1" in
			--board) BUILD_BOARD="$2" ;;
			--outdir) BUILD_OUTDIR="$2" ;;
			--name) BUILD_NAME="$2" ;;
			esac
			shift 2
			;;
		--verbose)
			VERBOSE=true
			shift
			;;
		-h | --help)
			usage
			exit 0
			;;
		-*) die "unknown build option: $1" ;;
		*)
			[[ -z "${BUILD_SAMPLE}" ]] || die "unexpected argument: $1"
			BUILD_SAMPLE="$1"
			shift
			;;
		esac
	done
}

parse_args() {
	if [[ "${1:-}" == "build" ]]; then
		COMMAND="build"
		shift
		parse_build_args "$@"
		return
	fi

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--branch | --revision)
			[[ $# -ge 2 ]] || die "$1 requires a value"
			REVISION="$2"
			REVISION_EXPLICIT=true
			shift 2
			;;
		--cleanup)
			CLEANUP=true
			shift
			;;
		--launch)
			LAUNCH=true
			shift
			;;
		--verbose)
			VERBOSE=true
			shift
			;;
		-h | --help)
			usage
			exit 0
			;;
		*) die "unknown option: $1" ;;
		esac
	done

	if [[ "${CLEANUP}" == true && "${REVISION}" != "main" ]]; then
		die "--cleanup cannot be combined with --branch or --revision"
	fi
	if [[ "${CLEANUP}" == true && "${LAUNCH}" == true ]]; then
		die "--cleanup cannot be combined with --launch"
	fi
}

# Detect OS/architecture once and derive every platform-dependent value.
init_platform() {
	[[ -z "${OS}" ]] || return 0

	local arch
	arch="$(uname -m)"
	case "$(uname -s)" in
	Linux)
		OS="linux"
		INSTALL_DIR="${HOME}/ncs"
		case "${arch}" in
		x86_64 | amd64)
			NRFUTIL_URL="${NRFUTIL_BASE_URL}/x86_64-unknown-linux-gnu/nrfutil"
			JLINK_PACKAGE="${JLINK_VERSION_LINUX_x86_64}"
			;;
		aarch64 | arm64)
			NRFUTIL_URL="${NRFUTIL_BASE_URL}/aarch64-unknown-linux-gnu/nrfutil"
			JLINK_PACKAGE="${JLINK_VERSION_LINUX_aarch64}"
			;;
		*) die "unsupported Linux architecture: ${arch}" ;;
		esac
		;;
	Darwin)
		OS="macos"
		INSTALL_DIR="/opt/nordic/ncs"
		NRFUTIL_URL="${NRFUTIL_BASE_URL}/universal-apple-darwin/nrfutil"
		JLINK_PACKAGE="${JLINK_VERSION_MACOS}"
		;;
	*)
		die "unsupported operating system: $(uname -s) (only Linux and macOS are supported)"
		;;
	esac

	# "JLink_Linux_V924a_x86_64" -> "924a"
	JLINK_TAG="${JLINK_PACKAGE#*_V}"
	JLINK_TAG="${JLINK_TAG%%_*}"
	TOOLS_DIR="${INSTALL_DIR}/nRF5_tools"
}

parse_ncs_version() {
	local west_file="$1" version

	[[ -f "${west_file}" ]] || die "west manifest not found: ${west_file}"

	version="$(
		awk '
			/^[[:space:]]*- name: nrf[[:space:]]*$/ { in_nrf = 1; next }
			in_nrf && /^[[:space:]]*revision:[[:space:]]*/ { print $2; exit }
			in_nrf && /^[[:space:]]*- name:[[:space:]]*/ { exit }
		' "${west_file}"
	)"

	[[ -n "${version}" ]] || die "could not read NCS revision from ${west_file}"
	printf '%s\n' "${version}"
}

ensure_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

# ── nrfutil ──────────────────────────────────────────────────────────────────

ensure_nrfutil_home_unlocked() {
	local lock="${NRFUTIL_HOME:-${HOME}/.nrfutil}/locked"

	if [[ -f "${lock}" ]]; then
		vlog "removing nrfutil home directory lock (${lock})"
		rm -f "${lock}"
	fi
}

ensure_local_bin_path() {
	case ":${PATH}:" in
	*":${HOME}/.local/bin:"*) ;;
	*) export PATH="${HOME}/.local/bin:${PATH}" ;;
	esac
}

nrfutil_current_version() {
	nrfutil --version 2>/dev/null | awk 'NR == 1 { print $2; exit }'
}

# Print the installed version of an nrfutil command (for example "device").
nrfutil_command_version() {
	nrfutil list 2>/dev/null | awk -v cmd="$1" '$1 == cmd { print $2; exit }'
}

ensure_nrfutil() {
	local current

	ensure_nrfutil_home_unlocked

	if command -v nrfutil >/dev/null 2>&1; then
		vlog "nrfutil already installed: $(command -v nrfutil)"
	else
		ensure_command curl
		mkdir -p "${HOME}/.local/bin"
		vlog "downloading nrfutil to ${HOME}/.local/bin/nrfutil"
		curl -fsSL "${NRFUTIL_URL}" -o "${HOME}/.local/bin/nrfutil"
		chmod +x "${HOME}/.local/bin/nrfutil"
		ensure_local_bin_path
		command -v nrfutil >/dev/null 2>&1 || die "nrfutil installation failed"
	fi
	ensure_local_bin_path

	current="$(nrfutil_current_version || true)"
	if [[ "${current}" == "${NRFUTIL_VERSION}" && "${FORCE_INSTALL}" != true ]]; then
		vlog "nrfutil ${current} matches ${NRFUTIL_VERSION}"
		return 0
	fi

	vlog "setting nrfutil version to ${NRFUTIL_VERSION} (current: ${current:-none})"
	nrfutil self-upgrade --to-version "${NRFUTIL_VERSION}"

	current="$(nrfutil_current_version || true)"
	[[ "${current}" == "${NRFUTIL_VERSION}" ]] ||
		die "nrfutil version is ${current:-unknown}, expected ${NRFUTIL_VERSION}"
}

install_nrfutil_device() {
	local current

	ensure_nrfutil_home_unlocked
	current="$(nrfutil_command_version device || true)"

	if [[ "${current}" == "${NRFUTIL_DEVICE_VERSION}" && "${FORCE_INSTALL}" != true ]]; then
		vlog "nrfutil device ${current} matches ${NRFUTIL_DEVICE_VERSION}"
		return 0
	fi

	vlog "installing nrfutil device ${NRFUTIL_DEVICE_VERSION} (current: ${current:-none})"
	if [[ "${FORCE_INSTALL}" == true ]]; then
		nrfutil install "device=${NRFUTIL_DEVICE_VERSION}" --force
	else
		nrfutil install "device=${NRFUTIL_DEVICE_VERSION}"
	fi
}

# ── J-Link ───────────────────────────────────────────────────────────────────

# Print the JLinkExe path: the managed copy (Linux), then PATH, then macOS defaults.
jlink_exe_path() {
	local candidate

	if [[ "${OS}" == linux ]]; then
		candidate="${TOOLS_DIR}/${JLINK_PACKAGE}/JLinkExe"
		if [[ -x "${candidate}" ]]; then
			printf '%s\n' "${candidate}"
			return 0
		fi
	fi

	if candidate="$(command -v JLinkExe 2>/dev/null)"; then
		printf '%s\n' "${candidate}"
		return 0
	fi

	if [[ "${OS}" == macos ]]; then
		for candidate in /Applications/SEGGER/JLink_*/JLinkExe; do
			[[ -x "${candidate}" ]] || continue
			printf '%s\n' "${candidate}"
			return 0
		done
	fi

	return 1
}

jlink_is_installed() {
	local jlink_exe line

	jlink_exe="$(jlink_exe_path)" || return 1
	line="$("${jlink_exe}" -? 2>&1 | awk '/SEGGER J-Link Commander/ { print; exit }' || true)"

	# "SEGGER J-Link Commander V9.24a (...)" -> "924a"
	[[ "${line}" =~ V([0-9][0-9.]*[a-z]*) ]] || return 1
	local version="${BASH_REMATCH[1]//./}"
	[[ "${version}" == "${JLINK_TAG}" ]]
}

export_jlink_path() {
	local jlink_exe jlink_dir

	export NCS_TOOLS_DIR="${TOOLS_DIR}"

	jlink_exe="$(jlink_exe_path)" || return 0
	jlink_dir="${jlink_exe%/*}"
	case ":${PATH}:" in
	*":${jlink_dir}:"*) ;;
	*) export PATH="${jlink_dir}:${PATH}" ;;
	esac
}

install_jlink() {
	local url archive post_data

	ensure_command curl
	mkdir -p "${TOOLS_DIR}"

	if [[ "${OS}" == linux ]]; then
		url="https://www.segger.com/downloads/jlink/${JLINK_PACKAGE}.tgz"
		archive="${TOOLS_DIR}/${JLINK_PACKAGE}.tgz"
		post_data="accept_license_agreement=accepted&submit=Download+software"
	else
		url="https://www.segger.com/downloads/jlink/${JLINK_PACKAGE}.pkg"
		archive="${TOOLS_DIR}/${JLINK_PACKAGE}.pkg"
		post_data="accept_license_agreement=accepted&non_emb_ctr=confirmed&submit=Download+software"
	fi

	vlog "downloading J-Link ${url##*/}"
	curl -fsSL -d "${post_data}" -X POST -o "${archive}" "${url}"

	if [[ "${OS}" == linux ]]; then
		vlog "extracting J-Link to ${TOOLS_DIR}"
		tar -xf "${archive}" -C "${TOOLS_DIR}"
		rm -f "${archive}"
		[[ -x "${TOOLS_DIR}/${JLINK_PACKAGE}/JLinkExe" ]] ||
			die "J-Link install failed: ${TOOLS_DIR}/${JLINK_PACKAGE}/JLinkExe not found"
	else
		vlog "installing J-Link package (administrator password may be required)"
		if command -v sudo >/dev/null 2>&1; then
			sudo installer -pkg "${archive}" -target /
		else
			installer -pkg "${archive}" -target /
		fi
		rm -f "${archive}"
		jlink_exe_path >/dev/null ||
			die "J-Link install failed: JLinkExe not found after installing ${JLINK_PACKAGE}.pkg"
	fi
}

ensure_jlink() {
	if jlink_is_installed; then
		vlog "J-Link already installed: $(jlink_exe_path)"
		export_jlink_path
		return 0
	fi

	vlog "installing J-Link (${JLINK_PACKAGE})"
	install_jlink
	export_jlink_path

	jlink_is_installed || die "J-Link install failed; expected ${JLINK_PACKAGE}"
	vlog "installed J-Link: $(jlink_exe_path)"
}

# Install/verify nrfutil, its device and sdk-manager modules, and J-Link.
ensure_nrfutil_sdk_manager() {
	ensure_nrfutil
	install_nrfutil_device
	ensure_nrfutil_home_unlocked

	if [[ "${FORCE_INSTALL}" == true ]] || ! nrfutil sdk-manager --help >/dev/null 2>&1; then
		vlog "installing nrfutil sdk-manager module"
		nrfutil install "sdk-manager=${NRFUTIL_SDK_MANGER_VERSION}" --force
	fi

	ensure_jlink
}

# ── sdk-manager ──────────────────────────────────────────────────────────────

# Run an sdk-manager subcommand against INSTALL_DIR (not for `toolchain launch`).
sdk_manager() {
	nrfutil sdk-manager "$@" --install-dir "${INSTALL_DIR}"
}

ncs_version_available() {
	sdk_manager search 2>/dev/null | awk -v wanted="$1" '
		NR > 1 && $2 == wanted && ($3 == "Available" || $3 == "Installed") { found = 1 }
		END { exit !found }
	'
}

# Sets HAVE_SDK / HAVE_TOOLCHAIN (0 or 1) for the given NCS version.
sdk_manager_entry_status() {
	local status
	status="$(sdk_manager list 2>/dev/null | awk -v wanted="$1" '
		$1 == wanted {
			if ($2 == "Installed") sdk = 1
			if ($3 == "Installed") tc = 1
		}
		END { print sdk + 0, tc + 0 }
	' || true)"
	read -r HAVE_SDK HAVE_TOOLCHAIN <<<"${status:-0 0}"
}

toolchain_installed_for_version() {
	sdk_manager toolchain list 2>/dev/null |
		awk -v wanted="$1" '$1 == wanted { found = 1 } END { exit !found }'
}

sdk_workspace_ready() {
	[[ -d "$1/.west" && -d "$1/nrf" && -d "$1/zephyr" ]]
}

# Print the SDK workspace directory for a version.
sdk_workspace_for_version() {
	local version="$1" sdk_dir

	sdk_dir="$(
		sdk_manager list --all-fields 2>/dev/null |
			awk -v wanted="${version}" '
				$1 == wanted && $2 == "Installed" { print $3; exit }
			' || true
	)"

	if [[ -n "${sdk_dir}" && "${sdk_dir}" != "Not" ]]; then
		printf '%s\n' "${INSTALL_DIR}/${sdk_dir}"
	elif [[ -d "${INSTALL_DIR}/${version}" ]]; then
		printf '%s\n' "${INSTALL_DIR}/${version}"
	elif [[ -d "${INSTALL_DIR}/${version#v}" ]]; then
		printf '%s\n' "${INSTALL_DIR}/${version#v}"
	else
		printf '%s\n' "${INSTALL_DIR}/${version}"
	fi
}

ensure_ncs_and_toolchain() {
	local version="$1" workspace

	ncs_version_available "${version}" ||
		die "NCS version ${version} is not available from nrfutil sdk-manager search"

	sdk_manager_entry_status "${version}"
	if [[ "${HAVE_SDK}" == 1 && "${HAVE_TOOLCHAIN}" == 1 ]]; then
		vlog "NCS ${version} SDK and toolchain are already installed"
		return 0
	fi

	vlog "installing NCS ${version} SDK and toolchain via sdk-manager"
	if sdk_manager install "${version}"; then
		return 0
	fi

	workspace="$(sdk_workspace_for_version "${version}")"
	if sdk_workspace_ready "${workspace}" ||
		{ [[ -d "${workspace}" ]] && toolchain_installed_for_version "${version}"; }; then
		log "SDK install reported zephyr-export failure; continuing (fixed after west update)"
		return 0
	fi

	die "nrfutil sdk-manager install failed for ${version}; run with --verbose and check ~/.nrfutil/logs/"
}

# ── Workspace / checkout discovery ───────────────────────────────────────────

clone_or_update_repo() {
	local url="$1" dest="$2" version="$3"

	if [[ -d "${dest}/.git" ]]; then
		vlog "repository already exists: ${dest}"
		return
	fi

	vlog "cloning ${url} into ${dest}"
	git clone "${url}" "${dest}" 

	if [[ -n "${version}" ]]; then
		cd "${dest}"
		git checkout "${version}"
		cd -
	fi
}

# Print a workspace containing the ncs-matter manifest. $1 (optional) is the
# preferred workspace path, checked before scanning INSTALL_DIR.
find_setup_workspace() {
	local preferred="${1:-}" west_file

	if [[ -n "${preferred}" && -f "${preferred}/${NCS_MATTER_DIR}/west.yml" ]]; then
		printf '%s\n' "${preferred}"
		return 0
	fi

	for west_file in "${INSTALL_DIR}"/*/"${NCS_MATTER_DIR}"/west.yml; do
		[[ -f "${west_file}" ]] || continue
		printf '%s\n' "${west_file%/*/*}"
		return 0
	done

	if [[ -f "${INSTALL_DIR}/${NCS_MATTER_DIR}/west.yml" && -d "${INSTALL_DIR}/.west" ]]; then
		printf '%s\n' "${INSTALL_DIR}"
		return 0
	fi

	return 1
}

resolve_workspace() {
	local ncs_version="${1:-}" candidate=""

	if [[ -n "${ncs_version}" ]]; then
		candidate="$(sdk_workspace_for_version "${ncs_version}")"
	fi

	find_setup_workspace "${candidate}" 2>/dev/null && return 0

	if [[ -n "${candidate}" && -d "${candidate}" ]]; then
		printf '%s\n' "${candidate}"
		return 0
	fi

	return 1
}

verify_west_workspace() {
	local workspace="$1" dir

	[[ -d "${workspace}/.west" ]] ||
		die "west workspace not initialized at ${workspace}; run ./scripts/setup.sh first"
	for dir in zephyr nrf; do
		[[ -d "${workspace}/${dir}" ]] ||
			die "${dir} not found in ${workspace}; run ./scripts/setup.sh first"
	done
}

verify_toolchain_for_version() {
	toolchain_installed_for_version "$1" ||
		die "toolchain for $1 is not installed; run ./scripts/setup.sh first"
}

user_ncs_matter_path() {
	printf '%s\n' "${SCRIPT_DIR%/*}"
}

verify_ncs_matter_checkout() {
	[[ -d "$1/.git" ]] || die "ncs-matter git checkout required at $1"
	[[ -f "$1/west.yml" ]] || die "west.yml not found in ncs-matter checkout: $1"
}

resolve_ncs_matter_path() {
	local workspace link_path resolved

	if workspace="$(find_setup_workspace)"; then
		link_path="${workspace}/${NCS_MATTER_DIR}"
		if [[ -L "${link_path}" ]]; then
			resolved="$(readlink -f "${link_path}")"
			[[ -n "${resolved}" && -d "${resolved}" ]] || die "broken ncs-matter symlink: ${link_path}"
			printf '%s\n' "${resolved}"
			return
		fi
		if [[ -d "${link_path}" ]]; then
			printf '%s\n' "${link_path}"
			return
		fi
	fi

	verify_ncs_matter_checkout "$(user_ncs_matter_path)"
	user_ncs_matter_path
}

# ── Symlinks ─────────────────────────────────────────────────────────────────

remove_path_if_symlink() {
	local path="$1" label="$2"

	if [[ -L "${path}" ]]; then
		vlog "removing existing ${label} symlink: ${path}"
		rm -f "${path}"
	elif [[ -e "${path}" ]]; then
		die "${path} exists and is not a symlink; remove it manually before re-running setup"
	fi
}

lock_sample_symlink_path() {
	printf '%s\n' "$1/samples/${LOCK_SAMPLE_NAME}"
}

# Remove the lock sample symlink, or a placeholder directory without a CMakeLists.txt.
remove_lock_sample_path() {
	local link_path="$1/samples/${LOCK_SAMPLE_NAME}"

	if [[ -L "${link_path}" ]]; then
		vlog "removing existing lock sample symlink: ${link_path}"
		rm -f "${link_path}"
	elif [[ -e "${link_path}" && ! -f "${link_path}/CMakeLists.txt" ]]; then
		vlog "removing lock sample placeholder: ${link_path}"
		rm -rf "${link_path}"
	fi
}

remove_setup_symlinks() {
	local ncs_matter_src="$1" workspace="${2:-}"

	vlog "checking for existing setup symlinks from a previous run"
	remove_lock_sample_path "${ncs_matter_src}"

	if [[ -n "${workspace}" ]]; then
		remove_path_if_symlink "${workspace}/${NCS_MATTER_DIR}" "ncs-matter workspace"
		if [[ -d "${workspace}/${NCS_MATTER_DIR}" ]]; then
			remove_lock_sample_path "${workspace}/${NCS_MATTER_DIR}"
		fi
	fi
}

ensure_ncs_matter_workspace_link() {
	local workspace="$1" ncs_matter_src

	ncs_matter_src="$(cd "$2" && pwd)"
	vlog "linking ${workspace}/${NCS_MATTER_DIR} -> ${ncs_matter_src}"
	ln -s "${ncs_matter_src}" "${workspace}/${NCS_MATTER_DIR}"
}

ensure_lock_sample_symlink() {
	local workspace="$1"
	local ncs_matter_dir="${workspace}/${NCS_MATTER_DIR}"
	local link_path="${ncs_matter_dir}/samples/${LOCK_SAMPLE_NAME}"
	local target="${workspace}/${DOOR_LOCK_DIR}/${DOOR_LOCK_APP_DIR}"

	[[ -d "${target}" ]] || die "door lock application not found: ${target}"

	mkdir -p "${ncs_matter_dir}/samples"

	if [[ -L "${link_path}" && "$(readlink "${link_path}")" == "${target}" ]]; then
		vlog "lock sample symlink already present: ${link_path}"
		return 0
	fi

	if [[ ! -L "${link_path}" && -f "${link_path}/CMakeLists.txt" ]]; then
		vlog "lock sample already present at ${link_path}"
		return 0
	fi

	remove_lock_sample_path "${ncs_matter_dir}"

	vlog "creating lock sample symlink: ${link_path} -> ${target}"
	ln -s "${target}" "${link_path}"
}

# ── Samples / build ──────────────────────────────────────────────────────────

sample_default_board() {
	[[ -f "$1" ]] || return 1

	awk '
		/^[[:space:]]*integration_platforms:[[:space:]]*$/ {
			while (getline > 0) {
				if ($0 ~ /^[[:space:]]*- /) {
					sub(/^[[:space:]]*- /, "", $0)
					print $0
					exit
				}
				if ($0 !~ /^[[:space:]]/ || $0 ~ /^[[:space:]]*[A-Za-z_]+:/) {
					exit
				}
			}
		}
	' "$1"
}

sample_is_valid() {
	[[ -f "$1/$2/CMakeLists.txt" || -L "$1/$2" ]]
}

list_buildable_samples() {
	local samples_dir="$1" sample board

	printf 'Available Matter samples:\n\n'
	for sample in "${samples_dir}"/*; do
		[[ -e "${sample}" ]] || continue
		[[ -f "${sample}/CMakeLists.txt" || -L "${sample}" ]] || continue
		board="$(sample_default_board "${sample}/sample.yaml" || true)"
		printf '  %-22s default board: %s\n' "${sample##*/}" \
			"${board:-(see sample documentation)}"
	done
	printf '\nBuild with:\n  %s build [--debug|--release] [--board BOARD] [--outdir DIR] [--name SUFFIX] <sample>\n' "${PROG}"
}

# Make sure --outdir exists before building; offer to create it.
ensure_outdir() {
	local outdir="$1" answer

	[[ -d "${outdir}" ]] && return 0
	[[ ! -e "${outdir}" ]] || die "output path exists and is not a directory: ${outdir}"

	printf 'Output directory does not exist: %s\nCreate it? [y/N] ' "${outdir}"
	answer=""
	read -r answer || true
	[[ "${answer}" == "y" || "${answer}" == "Y" ]] ||
		die "output directory ${outdir} does not exist; create it or choose another --outdir"

	mkdir -p "${outdir}" || die "could not create output directory: ${outdir}"
	log "Created ${outdir}"
}

# Set MERGED_HEX to the merged hex produced by the build (empty if none).
find_merged_hex() {
	local build_dir="$1" board="$2" candidate
	local -a hexes

	MERGED_HEX=""
	# Sysbuild names the file merged_<board>.hex with "/" replaced by "_".
	for candidate in "${build_dir}/merged.hex" "${build_dir}/merged_${board//\//_}.hex"; do
		if [[ -f "${candidate}" ]]; then
			MERGED_HEX="${candidate}"
			return 0
		fi
	done

	# Fall back to a single merged_*.hex (for example if the board name was normalized).
	hexes=("${build_dir}"/merged_*.hex)
	if [[ ${#hexes[@]} -eq 1 && -f "${hexes[0]}" ]]; then
		MERGED_HEX="${hexes[0]}"
	fi
}

# Copy the merged hex to OUTDIR and set MERGED_HEX to the copy.
copy_merged_hex_to_outdir() {
	local build_dir="$1" board="$2" sample_name="$3" outdir="$4" name_suffix="$5"
	local output_path="${outdir}/${sample_name}${board//\//}${name_suffix}.hex"

	find_merged_hex "${build_dir}" "${board}"
	[[ -n "${MERGED_HEX}" ]] ||
		die "merged hex not found under ${build_dir} (is SB_CONFIG_MERGED_HEX_FILES enabled?)"

	mkdir -p "${outdir}"
	cp -f "${MERGED_HEX}" "${output_path}"
	MERGED_HEX="${output_path}"
	log "Copied merged hex to ${output_path}"
}

run_build_sample() {
	[[ "${RUNNING_AS_SCRIPT}" == true ]] ||
		die "build must be run as a script, not sourced"

	local ncs_matter_dir ncs_version workspace samples_dir
	local sample_path board build_dir
	local cmake_args=("-DSB_CONFIG_MERGED_HEX_FILES=y")

	init_platform
	ncs_matter_dir="$(resolve_ncs_matter_path)"
	[[ -f "${ncs_matter_dir}/west.yml" ]] ||
		die "west manifest not found: ${ncs_matter_dir}/west.yml"
	ncs_version="$(parse_ncs_version "${ncs_matter_dir}/west.yml")"
	workspace="$(resolve_workspace "${ncs_version}")" ||
		die "SDK workspace not found; run ./scripts/setup.sh first"
	samples_dir="${ncs_matter_dir}/samples"

	ensure_nrfutil_sdk_manager
	verify_toolchain_for_version "${ncs_version}"
	verify_west_workspace "${workspace}"

	if [[ -z "${BUILD_SAMPLE}" ]]; then
		list_buildable_samples "${samples_dir}"
		return
	fi

	sample_is_valid "${samples_dir}" "${BUILD_SAMPLE}" ||
		die "unknown sample: ${BUILD_SAMPLE} (run '${PROG} build' to list samples)"

	if [[ "${BUILD_SAMPLE}" == "${LOCK_SAMPLE_NAME}" ]]; then
		ensure_lock_sample_symlink "${workspace}"
		[[ -f "${workspace}/${DOOR_LOCK_DIR}/west.yml" ]] ||
			die "west.yml not found in ${workspace}/${DOOR_LOCK_DIR}; run ./scripts/setup.sh first"
		WEST_MANIFEST_DIR="${DOOR_LOCK_DIR}"
		# The Door Lock manifest imports ncs-matter at a pinned release; west reads that
		# import from its manifest-rev ref (refs/heads/manifest-rev, or refs/west/manifest-rev
		# in newer west). Point both at the local checkout so the manifest resolves without
		# running west update (which would check out the release).
		vlog "pointing ${NCS_MATTER_DIR} manifest-rev at the local checkout HEAD"
		git -C "${workspace}/${NCS_MATTER_DIR}" update-ref refs/heads/manifest-rev HEAD &&
			git -C "${workspace}/${NCS_MATTER_DIR}" update-ref refs/west/manifest-rev HEAD ||
			die "failed to set manifest-rev in ${workspace}/${NCS_MATTER_DIR}"
	fi

	BUILD_MODE="${BUILD_MODE:-debug}"

	if [[ -n "${BUILD_NAME}" && -z "${BUILD_OUTDIR}" ]]; then
		die "--name requires --outdir"
	fi

	sample_path="${samples_dir}/${BUILD_SAMPLE}"
	board="${BUILD_BOARD}"
	if [[ -z "${board}" ]]; then
		board="$(sample_default_board "${sample_path}/sample.yaml" || true)"
	fi
	[[ -n "${board}" ]] || die "no default board found for ${BUILD_SAMPLE}; use --board"

	build_dir="${sample_path}/build"
	if [[ -n "${BUILD_OUTDIR}" ]]; then
		ensure_outdir "${BUILD_OUTDIR}"
	fi
	if [[ "${BUILD_MODE}" == "debug" ]]; then
		cmake_args+=("-D${BUILD_SAMPLE}_SNIPPET=diagnostic-logs;debug")
	else
		cmake_args+=("-DFILE_SUFFIX=release")
	fi

	vlog "building sample ${BUILD_SAMPLE} (${BUILD_MODE}) for ${board}"
	vlog "west build -p always -b ${board} -d ${build_dir} ${sample_path} -- ${cmake_args[*]}"

	run_in_toolchain_env "${ncs_version}" "${workspace}" \
		west build -p always -b "${board}" -d "${build_dir}" "${sample_path}" -- "${cmake_args[@]}"

	if [[ -n "${BUILD_OUTDIR}" ]]; then
		copy_merged_hex_to_outdir "${build_dir}" "${board}" "${BUILD_SAMPLE}" \
			"${BUILD_OUTDIR}" "${BUILD_NAME}"
	else
		find_merged_hex "${build_dir}" "${board}"
	fi

	cat <<EOF

Build complete.

Sample: ${BUILD_SAMPLE}
Board: ${board}
Configuration: ${BUILD_MODE}
Build directory: ${build_dir}

EOF

	if [[ -n "${MERGED_HEX}" ]]; then
		cat <<EOF
Flash the merged hex to the device:

  nrfutil device program --firmware "${MERGED_HEX}" \\
    --options chip_erase_mode=ERASE_RANGES_TOUCHED_BY_FIRMWARE,verify=VERIFY_READ \\
    && nrfutil device reset

If more than one DK is connected, list them and select the target by serial
number (add --serial-number to both commands):

  nrfutil device list
  nrfutil device program --serial-number <SERIAL_NUMBER> --firmware "${MERGED_HEX}" \\
    --options chip_erase_mode=ERASE_RANGES_TOUCHED_BY_FIRMWARE,verify=VERIFY_READ \\
    && nrfutil device reset --serial-number <SERIAL_NUMBER>

EOF
	fi
}

# ── west workspace ───────────────────────────────────────────────────────────

checkout_ncs_matter_revision() {
	local repo_dir="$1" revision="$2"

	verify_ncs_matter_checkout "${repo_dir}"

	vlog "checking out ncs-matter revision ${revision} in ${repo_dir}"
	git -C "${repo_dir}" fetch origin

	if git -C "${repo_dir}" show-ref --verify --quiet "refs/remotes/origin/${revision}"; then
		git -C "${repo_dir}" checkout "origin/${revision}"
	else
		git -C "${repo_dir}" checkout "${revision}"
	fi
}

read_west_manifest_path() {
	local config_file="$1/.west/config"

	[[ -f "${config_file}" ]] || return 1

	awk -F' = ' '
		/^\[manifest\]/ { in_manifest = 1; next }
		/^\[/ { in_manifest = 0 }
		in_manifest && $1 == "path" { print $2; exit }
	' "${config_file}"
}

write_west_manifest_path() {
	local config_file="$1/.west/config" manifest_path="$2" tmp_file

	[[ -f "${config_file}" ]] || return 1

	tmp_file="$(mktemp)"
	awk -v newpath="${manifest_path}" '
		/^\[manifest\]/ { in_manifest = 1; print; next }
		/^\[/ { in_manifest = 0 }
		in_manifest && $1 == "path" { print "path = " newpath; updated = 1; next }
		{ print }
		END { if (!updated) exit 1 }
	' "${config_file}" >"${tmp_file}" || {
		rm -f "${tmp_file}"
		return 1
	}

	mv "${tmp_file}" "${config_file}"
}

# Point west at the add-on in WEST_MANIFEST_DIR (ncs-matter, or the Door Lock
# add-on while building the lock sample).
ensure_west_manifest_path() {
	local workspace="$1" current

	[[ -d "${workspace}/.west" ]] || return 0

	current="$(read_west_manifest_path "${workspace}" 2>/dev/null || true)"
	if [[ "${current}" == "${WEST_MANIFEST_DIR}" ]]; then
		vlog "west manifest.path already ${WEST_MANIFEST_DIR}"
		return 0
	fi

	vlog "setting west manifest.path to ${WEST_MANIFEST_DIR}"
	write_west_manifest_path "${workspace}" "${WEST_MANIFEST_DIR}" ||
		die "failed to update west manifest.path in ${workspace}/.west/config"
}

# toolchain_launch VERSION WORKSPACE [-- ] COMMAND... | toolchain_launch VERSION WORKSPACE --shell
toolchain_launch() {
	local ncs_version="$1" workspace="$2"
	shift 2

	if [[ "$1" == "--shell" ]]; then
		set -- --shell
	else
		set -- -- "$@"
	fi

	nrfutil sdk-manager toolchain launch \
		--ncs-version "${ncs_version}" \
		--install-dir "${INSTALL_DIR}" \
		--chdir "${workspace}" \
		"$@"
}

run_in_toolchain_env() {
	local ncs_version="$1" workspace="$2"
	shift 2

	ensure_west_manifest_path "${workspace}"
	vlog "running in toolchain environment: $*"
	toolchain_launch "${ncs_version}" "${workspace}" "$@"
}

register_sdk_with_cmake() {
	local ncs_version="$1" workspace="$2"

	vlog "registering SDK with CMake (west zephyr-export)"
	if run_in_toolchain_env "${ncs_version}" "${workspace}" west zephyr-export; then
		return 0
	fi

	vlog "west zephyr-export failed; trying nrfutil sdk-manager sdk register"
	sdk_manager sdk register "${ncs_version}"
}

configure_west_workspace() {
	local ncs_version="$1" workspace="$2"

	[[ -d "${workspace}/${NCS_MATTER_DIR}" ]] ||
		die "west workspace missing and ${NCS_MATTER_DIR} is not cloned in ${workspace}"

	vlog "configuring west workspace for ${NCS_MATTER_DIR} inside toolchain environment"
	if [[ ! -d "${workspace}/.west" ]]; then
		vlog "initializing west workspace with ${NCS_MATTER_DIR} manifest"
		run_in_toolchain_env "${ncs_version}" "${workspace}" \
			west init -l "${NCS_MATTER_DIR}" --mf west.yml
	fi

	log "Running west update (first run may take 15-30+ minutes while updating Zephyr)..."
	run_in_toolchain_env "${ncs_version}" "${workspace}" west update

	register_sdk_with_cmake "${ncs_version}" "${workspace}"
}

launch_toolchain_shell() {
	local ncs_version="$1" workspace="$2"

	[[ "${RUNNING_AS_SCRIPT}" == true ]] ||
		die "--launch must be run as a script, not sourced"

	ensure_nrfutil_sdk_manager
	verify_toolchain_for_version "${ncs_version}"
	verify_west_workspace "${workspace}"
	ensure_west_manifest_path "${workspace}"

	toolchain_launch "${ncs_version}" "${workspace}" west topdir >/dev/null 2>&1 ||
		die "west workspace check failed in ${workspace}; run ./scripts/setup.sh first"

	log "Launching toolchain shell (NCS ${ncs_version}, workspace ${workspace})"
	log "West manifest: ${NCS_MATTER_DIR} (run 'west help' to verify extensions)"
	exec nrfutil sdk-manager toolchain launch \
		--ncs-version "${ncs_version}" \
		--install-dir "${INSTALL_DIR}" \
		--chdir "${workspace}" \
		--shell
}

run_launch_only() {
	local ncs_matter_src ncs_version workspace

	init_platform
	ncs_matter_src="$(user_ncs_matter_path)"
	verify_ncs_matter_checkout "${ncs_matter_src}"

	ncs_version="$(parse_ncs_version "${ncs_matter_src}/west.yml")"
	workspace="$(resolve_workspace "${ncs_version}")" ||
		die "SDK workspace not found; run ./scripts/setup.sh first"

	launch_toolchain_shell "${ncs_version}" "${workspace}"
}

# ── Cleanup ──────────────────────────────────────────────────────────────────

print_cleanup_warning() {
	local workspace="$1" ncs_version="$2"

	cat <<EOF

WARNING: This cleanup removes the Matter add-on workspace created by this script.

The following will be permanently deleted:

  - ${workspace}/${NCS_MATTER_DIR} workspace symlink (your ncs-matter checkout is kept)
  - ${workspace}/${NCS_MATTER_DIR}/samples/${LOCK_SAMPLE_NAME} symlink
  - ${workspace}/${DOOR_LOCK_DIR} repository clone
  - nRF Connect SDK ${ncs_version} installed by nrfutil sdk-manager
  - Toolchain for nRF Connect SDK ${ncs_version} (if not shared with other SDK versions)
  - SDK workspace at ${workspace} (if present)

Other files under ${INSTALL_DIR} that were not created by this script are not removed.

This action cannot be undone.

Type y to proceed:
EOF
}

reset_west_manifest() {
	local workspace="$1" manifest_path

	[[ -d "${workspace}/.west" ]] || return 0

	manifest_path="$(read_west_manifest_path "${workspace}" 2>/dev/null || true)"
	[[ "${manifest_path}" == "${NCS_MATTER_DIR}" || "${manifest_path}" == "${DOOR_LOCK_DIR}" ]] || return 0

	if [[ -d "${workspace}/nrf" ]]; then
		vlog "restoring west manifest path to nrf"
		write_west_manifest_path "${workspace}" "nrf" || true
	else
		vlog "removing west metadata at ${workspace}/.west"
		rm -rf "${workspace}/.west"
	fi
}

remove_path_if_exists() {
	if [[ -e "$1" ]]; then
		vlog "removing $1"
		rm -rf "$1"
	fi
}

run_cleanup() {
	[[ "${RUNNING_AS_SCRIPT}" == true ]] ||
		die "--cleanup must be run as a script, not sourced"

	local workspace ncs_version ncs_matter_src answer

	init_platform
	ncs_matter_src="$(user_ncs_matter_path)"
	verify_ncs_matter_checkout "${ncs_matter_src}"

	ncs_version="$(parse_ncs_version "${ncs_matter_src}/west.yml")"
	workspace="$(resolve_workspace "${ncs_version}" 2>/dev/null || true)"
	if [[ -z "${workspace}" ]]; then
		workspace="$(sdk_workspace_for_version "${ncs_version}")"
	fi

	print_cleanup_warning "${workspace}" "${ncs_version}"
	read -r answer
	[[ "${answer}" == "y" ]] || die "cleanup cancelled"

	ensure_nrfutil_sdk_manager

	sdk_manager_entry_status "${ncs_version}"
	if [[ "${HAVE_SDK}" == 1 || "${HAVE_TOOLCHAIN}" == 1 ]]; then
		vlog "uninstalling NCS ${ncs_version} SDK and toolchain via sdk-manager"
		sdk_manager uninstall "${ncs_version}"
	else
		vlog "NCS ${ncs_version} is not installed via sdk-manager"
	fi

	reset_west_manifest "${workspace}"
	remove_path_if_symlink "$(lock_sample_symlink_path "${ncs_matter_src}")" "lock sample"
	if [[ -L "${workspace}/${NCS_MATTER_DIR}" ]]; then
		remove_path_if_symlink "${workspace}/${NCS_MATTER_DIR}" "ncs-matter workspace"
	elif [[ -e "${workspace}/${NCS_MATTER_DIR}" ]]; then
		vlog "keeping existing ncs-matter path (not a symlink): ${workspace}/${NCS_MATTER_DIR}"
	fi
	remove_path_if_exists "${workspace}/${DOOR_LOCK_DIR}"

	if [[ "${workspace}" != "${INSTALL_DIR}" ]]; then
		remove_path_if_exists "${workspace}"
	fi

	printf '\nCleanup complete.\n\n'
}

# ── Setup ────────────────────────────────────────────────────────────────────

print_summary() {
	cat <<EOF

Setup complete.

Workspace: $2
ncs-matter: $3
NCS version: $1
ZEPHYR_BASE=$2/zephyr

Enter the toolchain environment:

  ${PROG} --launch

Build a sample:

  ${PROG} build [--debug|--release] [--outdir DIR] [--name SUFFIX] <sample>

List available samples:

  ${PROG} build

EOF
}

main() {
	parse_args "$@"

	if [[ "${COMMAND}" == "build" ]]; then
		run_build_sample
		return
	fi

	if [[ "${CLEANUP}" == true ]]; then
		run_cleanup
		return
	fi

	if [[ "${LAUNCH}" == true && "${REVISION_EXPLICIT}" == false ]]; then
		run_launch_only
	fi

	ensure_command curl
	ensure_command git

	local ncs_version workspace ncs_matter_src existing_workspace

	init_platform
	ncs_matter_src="$(user_ncs_matter_path)"

	vlog "default SDK install directory (${OS}): ${INSTALL_DIR}"
	vlog "using ncs-matter checkout: ${ncs_matter_src}"

	verify_ncs_matter_checkout "${ncs_matter_src}"

	ncs_version="$(parse_ncs_version "${ncs_matter_src}/west.yml")"
	existing_workspace="$(sdk_workspace_for_version "${ncs_version}")"
	[[ -d "${existing_workspace}" ]] || existing_workspace=""

	phase "Phase 1/5: Prepare ncs-matter checkout"
	remove_setup_symlinks "${ncs_matter_src}" "${existing_workspace}"
	checkout_ncs_matter_revision "${ncs_matter_src}" "${REVISION}"
	remove_lock_sample_path "${ncs_matter_src}"
	ncs_version="$(parse_ncs_version "${ncs_matter_src}/west.yml")"
	log "Using ncs-matter revision ${REVISION} (NCS ${ncs_version})"

	phase "Phase 2/5: Install nRF Util and J-Link"
	FORCE_INSTALL="${NRFUTIL_FORCE_INSTALL}"
	ensure_nrfutil_sdk_manager
	FORCE_INSTALL=false
	log "nRF Util and J-Link ready"

	phase "Phase 3/5: Install NCS ${ncs_version}"
	vlog "note: nrfutil may report a zephyr-export error during install; Phase 5 fixes this"
	ensure_ncs_and_toolchain "${ncs_version}"

	workspace="$(sdk_workspace_for_version "${ncs_version}")"
	[[ -d "${workspace}" ]] ||
		die "SDK workspace not found at ${workspace}; nrfutil sdk-manager install may have failed"

	export NCS_ROOT="${workspace}"
	export ZEPHYR_BASE="${workspace}/zephyr"
	export_jlink_path
	log "SDK workspace: ${workspace}"

	phase "Phase 4/5: Link workspace and add-ons"
	ensure_ncs_matter_workspace_link "${workspace}" "${ncs_matter_src}"
	clone_or_update_repo "${DOOR_LOCK_REPO}" "${workspace}/${DOOR_LOCK_DIR}" "${DOOR_LOCK_VERSION}"
	ensure_lock_sample_symlink "${workspace}"
	log "Workspace linked"

	phase "Phase 5/5: Configure west workspace"
	configure_west_workspace "${ncs_version}" "${workspace}"
	log "West workspace configured"

	print_summary "${ncs_version}" "${workspace}" "${ncs_matter_src}"

	if [[ "${LAUNCH}" == true ]]; then
		launch_toolchain_shell "${ncs_version}" "${workspace}"
	fi

	if [[ "${RUNNING_AS_SCRIPT}" == true ]]; then
		vlog "re-run with 'source ${SCRIPT_DIR}/setup.sh' to export ZEPHYR_BASE in your shell"
	fi
}

main "$@"
