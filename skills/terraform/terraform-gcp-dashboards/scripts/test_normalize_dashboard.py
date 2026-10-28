#!/usr/bin/env python3
"""Regression tests for normalize_dashboard.py.

Run with: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "normalize_dashboard.py")


def collapsible_dashboard(group):
    """Mosaic dashboard with a group tile spanning a chart tile."""
    return {
        "displayName": "Grouped",
        "mosaicLayout": {
            "columns": 48,
            "tiles": [
                {
                    "width": 48,
                    "height": 20,
                    "widget": {"title": "Group", "collapsibleGroup": group},
                },
                {
                    "width": 24,
                    "height": 16,
                    "widget": {"title": "Notes", "text": {"content": "hi"}},
                },
            ],
        },
    }


class NormalizeDashboardTest(unittest.TestCase):
    def run_script(self, data, *flags):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "dashboard.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            proc = subprocess.run(
                [sys.executable, "-I", SCRIPT, path, *flags],
                capture_output=True, text=True, check=False)
            with open(path, encoding="utf-8") as fh:
                written = json.load(fh)
        return proc, written

    def group_of(self, data):
        return data["mosaicLayout"]["tiles"][0]["widget"]

    def test_write_keeps_empty_collapsible_group(self):
        proc, written = self.run_script(collapsible_dashboard({}), "--write")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.group_of(written),
                         {"title": "Group", "collapsibleGroup": {}})

    def test_check_reports_empty_collapsible_group_canonical(self):
        proc, _ = self.run_script(collapsible_dashboard({}), "--check")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("canonical", proc.stderr)

    def test_collapsed_false_is_stripped_but_group_kept(self):
        proc, written = self.run_script(
            collapsible_dashboard({"collapsed": False}), "--write")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.group_of(written),
                         {"title": "Group", "collapsibleGroup": {}})

    def test_check_flags_collapsed_false(self):
        proc, _ = self.run_script(
            collapsible_dashboard({"collapsed": False}), "--check")
        self.assertEqual(proc.returncode, 1)

    def test_collapsed_true_is_kept(self):
        proc, _ = self.run_script(
            collapsible_dashboard({"collapsed": True}), "--check")
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
