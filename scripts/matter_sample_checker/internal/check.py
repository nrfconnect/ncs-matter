#
# Copyright (c) 2026 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause

from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from internal.utils.defines import LEVELS, MatterSampleCheckerResult

ProgressHandler = Callable[[str, str], None]


@dataclass
class MatterCheckerConfig:
    config_file: dict
    sample_path: Path
    nrf_path: Path
    verbose: bool = False
    skip: bool = False
    expected_years: list[int] | None = None
    allowed_names: list[str] | None = None
    live_progress: bool = False
    progress_handler: ProgressHandler | None = field(default=None, repr=False)


class MatterSampleTestCase:
    def __init__(self):
        self.config: MatterCheckerConfig
        self.sample_name = ""
        self.result: list[MatterSampleCheckerResult] = []

    def run(self, config: MatterCheckerConfig) -> list[MatterSampleCheckerResult]:
        """
        Run the test case.

        This method is called to run the test case.
        It will prepare the test case, run the check and return the result.
        """
        # save config
        self.config = config
        self.sample_name = config.sample_path.name if config.sample_path else ""

        # Prepare the test case
        self.prepare()

        # display the name of the check
        self.info(f"\n=== {self.name()} check ===")
        if self.config.skip:
            self.info("✅ Check skipped")
            return self.result
        try:
            # run the check
            self.check()
        except Exception as e:
            self.issue(str(e))
        finally:
            check_issues = [result for result in self.result if result.level == LEVELS["issue"]]
            check_warnings = [result for result in self.result if result.level == LEVELS["warning"]]

            if not check_issues and not check_warnings:
                self.info("✅ No issues found")
            else:
                if check_issues:
                    self._print_result_summary("FAILURES", check_issues, marker="❌")
                    self.info(f"❌ {len(check_issues)} Issues found")
                if check_warnings:
                    self._print_result_summary("WARNINGS", check_warnings, marker="⚠️")
                    self.info(f"⚠️ {len(check_warnings)} Warnings found")
        return self.result

    def _print_result_summary(
        self,
        heading: str,
        items: list[MatterSampleCheckerResult],
        *,
        marker: str,
    ) -> None:
        """Re-print check failures/warnings in a compact block easy to spot in CI logs."""
        self.info("")
        self.info("!" * 60)
        self.info(f"{marker} {heading} in {self.name()} ({len(items)}):")
        for index, item in enumerate(items, start=1):
            self.info(f"  [{index}] {item.message}")
        self.info("!" * 60)
        self.info("")

    def _emit(self, level: str, message: str) -> None:
        self.result.append(MatterSampleCheckerResult(level=level, message=message))
        if self.config.progress_handler is not None:
            self.config.progress_handler(level, message)

    def issue(self, message: str):
        self._emit(LEVELS["issue"], message)

    def warning(self, message: str):
        self._emit(LEVELS["warning"], message)

    def info(self, message: str):
        self._emit(LEVELS["info"], message)

    def debug(self, message: str):
        self._emit(LEVELS["debug"], message)

    @abstractmethod
    def prepare(self):
        """
        Prepare the test case.

        This method is called before running the check.
        Implement here all the logic and variables that are needed for the check,
        but are not part of the check body
        """
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the test case.

        This name will be displayed in the output.
        """
        raise NotImplementedError

    @abstractmethod
    def check(self):
        """
        Run the check.

        This method is called to run the check.
        Implement here the logic of the check.

        Return a MatterSampleTestCaseResult object with the issues, warnings, info and debug lists.
        """
        raise NotImplementedError
