"""依賴新鮮度檢查的合約測試（全部離線）。

紅燈只有在「真的要有人看」時才有用。兩件事會讓它失準：每個月誤報直到沒人看，
以及把真正的落後消音。這裡釘住兩邊：依宣告精度比較，以及兩條有記錄的出口
（hold 與會自己過期的 deferral）。
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_dependency_freshness as checker  # noqa: E402


def _row(name="pandas", minimum="2.0.0", latest="3.1.0", hold="", deferrals=None):
    package = {
        "name": name,
        "minimum": minimum,
        "requirement": f"{name}>={minimum}",
        "source": "requirements.txt",
        "hold": hold,
        "kind": "pypi",
    }
    return checker.collect_status([package], lambda _name: latest, deferrals or {})[0]


class VersionComparison(unittest.TestCase):
    def test_comparison_uses_the_precision_the_declaration_states(self):
        self.assertFalse(checker.is_newer_version("7.4.0", "7"))
        self.assertTrue(checker.is_newer_version("8.0.0", "7"))
        self.assertTrue(checker.is_newer_version("7.4.0", "7.3"))
        self.assertFalse(checker.is_newer_version("7.3.2", "7.3"))

    def test_prerelease_suffix_does_not_count_as_newer(self):
        self.assertFalse(checker.is_newer_version("7.0.0rc1", "7.0.0"))

    def test_leading_v_is_stripped_for_action_tags(self):
        self.assertTrue(checker.is_newer_version("v7.1.0", "7.0.1"))


class Declarations(unittest.TestCase):
    def test_hold_marker_is_read_off_the_declaring_line(self):
        packages = checker.parse_requirements(
            "pandas>=2.0.0  # freshness-hold: pandas 3 needs Python 3.11\npydantic>=2.0.0\n",
            "requirements.txt",
        )
        holds = {p["name"]: p["hold"] for p in packages}
        self.assertEqual(holds["pydantic"], "")
        self.assertEqual(holds["pandas"], "pandas 3 needs Python 3.11")

    def test_extras_are_stripped_from_the_package_name(self):
        packages = checker.parse_requirements("scrapling[fetchers]>=0.3.0\n", "requirements.txt")
        self.assertEqual(packages[0]["name"], "scrapling")
        self.assertEqual(packages[0]["minimum"], "0.3.0")

    def test_the_real_requirements_file_is_checked(self):
        names = {p["name"].lower() for p in checker.load_direct_dependencies(ROOT)}
        self.assertIn("scrapling", names)
        self.assertIn("scrapegraphai", names)

    def test_every_real_requirement_declares_a_floor_or_a_hold(self):
        # A line with neither would be a permanent CHECK FAILED row.
        for package in checker.load_direct_dependencies(ROOT):
            self.assertTrue(package["minimum"] or package["hold"], package["requirement"])

    def test_real_workflow_pins_reach_the_report_including_codeql_subpaths(self):
        names = {p["name"] for p in checker.load_workflow_actions(ROOT)}
        self.assertIn("actions/checkout", names)
        self.assertIn("github/codeql-action/init", names)
        for package in checker.load_workflow_actions(ROOT):
            self.assertTrue(package["minimum"], package["requirement"])

    def test_subpath_actions_resolve_to_their_repository(self):
        self.assertEqual(checker.action_repository("github/codeql-action/init"), "github/codeql-action")


class Exits(unittest.TestCase):
    def test_an_aged_floor_asks_for_review(self):
        row = _row()
        self.assertTrue(row["outdated"])
        self.assertTrue(checker.needs_review(row))
        self.assertIn("REVIEW UPDATE", checker.render_markdown([row]))

    def test_a_held_floor_is_reported_but_does_not_ask_for_work(self):
        row = _row(hold="pandas 3 needs Python 3.11")
        self.assertFalse(checker.needs_review(row))
        self.assertIn("HELD: pandas 3 needs Python 3.11", checker.render_markdown([row]))

    def test_a_live_deferral_covers_the_row(self):
        row = _row(deferrals={"pandas": ("3.1", "reviewed, not now")})
        self.assertFalse(checker.needs_review(row))
        self.assertIn("DEFERRED at 3.1.0", checker.render_markdown([row]))

    def test_a_deferral_expires_once_the_release_moves_past_it(self):
        row = _row(latest="3.2.0", deferrals={"pandas": ("3.1", "reviewed, not now")})
        self.assertTrue(checker.needs_review(row))

    def test_an_unreadable_latest_is_a_failed_check_not_an_ok_row(self):
        row = _row(latest=None)
        self.assertTrue(row["check_failed"])

    def test_deferral_without_a_reviewed_release_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dependency-deferrals.json"
            path.write_text(
                json.dumps(
                    {
                        "deferrals": {
                            "kept": {"deferredLatest": "9.1", "reason": "reviewed, not now"},
                            "no-release": {"reason": "reviewed, not now"},
                            "no-reason": {"deferredLatest": "9.1"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(checker.load_deferrals(path), {"kept": ("9.1", "reviewed, not now")})

    def test_the_repos_own_deferrals_file_parses_and_every_entry_counts(self):
        path = ROOT / ".github" / "dependency-deferrals.json"
        raw = json.loads(path.read_text(encoding="utf-8"))["deferrals"]
        self.assertEqual(set(checker.load_deferrals(path)), {name.lower() for name in raw})

    def test_report_names_both_exits_and_does_not_offer_raising_the_floor(self):
        report = checker.render_markdown([_row()])
        self.assertIn("# freshness-hold:", report)
        self.assertIn("deferredLatest", report)
        self.assertIn("Raising it to silence the report is not an", report)


class Output(unittest.TestCase):
    def test_json_output_round_trips_and_flags_review_items(self):
        payload = json.loads(checker.render_json([_row()], [], None))
        self.assertEqual(payload["needs_review"], ["pandas"])
        self.assertFalse(payload["check_failed"])

    def test_github_output_marks_attention_for_a_failed_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            with mock.patch.dict("os.environ", {"GITHUB_OUTPUT": str(out)}):
                checker.write_github_output([_row(latest=None)], [], Path("r.md"))
            self.assertIn("needs_attention=true", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
