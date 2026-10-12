/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "nfc_commissioning/nfc_unpowered_commissioning.h"

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include <zephyr/shell/shell.h>
#include <zephyr/sys/util.h>

static int shell_printf(struct NfcCommissioningShellOut *out, const char *fmt, ...)
{
	va_list args;
	int ret;

	if ((out == NULL) || (out->print == NULL)) {
		return -1;
	}

	va_start(args, fmt);
	ret = out->print(out->ctx, fmt, args);
	va_end(args);

	return ret;
}

static void print_help(int (*print)(void *ctx, const char *fmt, va_list args), void *ctx)
{
	size_t count = 0;
	const struct NfcCommissioningShellCommand *commands = NfcCommissioningShellGetCommands(&count);
	struct NfcCommissioningShellOut out = { .print = print, .ctx = ctx };

	shell_printf(&out, "%s\r\n", NfcCommissioningShellGetHelpHeader());
	for (size_t i = 0; i < count; i++) {
		shell_printf(&out, "  %-14s %s\r\n", commands[i].name, commands[i].help);
	}
}

int NfcCommissioningShellExec(int argc, char **argv, int (*print)(void *ctx, const char *fmt, va_list args), void *ctx)
{
	size_t count = 0;
	const struct NfcCommissioningShellCommand *commands = NfcCommissioningShellGetCommands(&count);
	struct NfcCommissioningShellOut out = { .print = print, .ctx = ctx };

	if ((argc == 0) || (argv[0] == NULL)) {
		print_help(print, ctx);
		return 0;
	}

	for (size_t i = 0; i < count; i++) {
		if (strcmp(argv[0], commands[i].name) == 0) {
			return commands[i].handler(&out, argc - 1, &argv[1]);
		}
	}

	shell_printf(&out, "Unknown command: %s\r\n", argv[0]);
	print_help(print, ctx);
	return -EINVAL;
}

static int nfc_shell_vprint(void *ctx, const char *fmt, va_list args)
{
	const struct shell *sh = static_cast<const struct shell *>(ctx);
	char line[256];
	int len;

	len = vsnprintf(line, sizeof(line), fmt, args);
	if (len < 0) {
		return len;
	}

	shell_fprintf(sh, SHELL_NORMAL, "%s", line);
	return len;
}

static int cmd_nfc(const struct shell *sh, size_t argc, char **argv)
{
	int ret;

	if (argc <= 1) {
		print_help(nfc_shell_vprint, (void *)sh);
		return 0;
	}

	ret = NfcCommissioningShellExec((int)argc - 1, &argv[1], nfc_shell_vprint, (void *)sh);
	return (ret == 0) ? 0 : -EINVAL;
}

SHELL_CMD_REGISTER(nfc, NULL, "NFC tag commissioning commands", cmd_nfc);
