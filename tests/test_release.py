# SPDX-License-Identifier: GPL-3.0-only

"""Release bookkeeping: the version lives in one place and the changelog has a slot for news.

`tools/release-check.sh` makes the per-release checks (tag, build, contents, fresh install);
these tests only keep the standing rules from drifting (docs/releasing.md).
"""

import re
import tomllib
import unittest
from pathlib import Path

import glra_midi

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseBookkeepingTests(unittest.TestCase):
    def test_version_is_plain_semver(self):
        self.assertRegex(glra_midi.__version__, SEMVER)

    def test_pyproject_reads_the_version_from_the_package(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertNotIn("version", project["project"])
        self.assertIn("version", project["project"]["dynamic"])
        self.assertEqual(
            project["tool"]["setuptools"]["dynamic"]["version"],
            {"attr": "glra_midi.__version__"},
        )

    def test_release_check_finds_the_version_line(self):
        # tools/release-check.sh reads the version with this exact pattern.
        text = (ROOT / "glra_midi" / "__init__.py").read_text()
        match = re.search(r'^__version__ = "(.*)"$', text, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), glra_midi.__version__)

    def test_changelog_has_an_unreleased_section(self):
        text = (ROOT / "CHANGELOG.md").read_text()
        self.assertRegex(text, r"(?m)^## \[Unreleased\]$")

    def test_changelog_release_headings_are_dated_semver(self):
        text = (ROOT / "CHANGELOG.md").read_text()
        for heading in re.findall(r"(?m)^## \[(?!Unreleased)(.*)$", text):
            self.assertRegex("## [" + heading, r"^## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
