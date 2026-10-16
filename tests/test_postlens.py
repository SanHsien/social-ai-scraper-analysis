from __future__ import annotations

import contextlib
import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from postlens import analysis, loaders, report  # noqa: E402
from postlens.cli import main  # noqa: E402
from postlens.models import Post  # noqa: E402

FIXTURES = Path(__file__).with_name("fixtures")


def post(text="hello", likes=0, replies=0, reposts=0, quotes=0, views=None, when="2026-09-01T00:00:00Z"):
    return Post(id=text, created_at=loaders.parse_datetime(when), text=text, likes=likes,
                replies=replies, reposts=reposts, quotes=quotes, views=views)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="postlens-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue() + err.getvalue()


class DateTests(unittest.TestCase):
    def test_formats(self):
        utc = timezone.utc
        self.assertEqual(loaders.parse_datetime("2026-09-01T08:00:00+08:00"),
                         datetime(2026, 9, 1, 0, 0, tzinfo=utc))
        self.assertEqual(loaders.parse_datetime("2026-09-01T00:00:00Z"), datetime(2026, 9, 1, tzinfo=utc))
        self.assertEqual(loaders.parse_datetime("2026-09-01 00:00:00"), datetime(2026, 9, 1, tzinfo=utc))
        self.assertEqual(loaders.parse_datetime("1788220800"), datetime(2026, 9, 1, tzinfo=utc))
        self.assertEqual(loaders.parse_datetime("Tue Sep 01 00:00:00 +0000 2026"),
                         datetime(2026, 9, 1, tzinfo=utc))
        with self.assertRaises(ValueError):
            loaders.parse_datetime("yesterday")


class LoaderTests(TempDirCase):
    def test_csv_aliases_and_missing_views(self):
        p = self.tmp / "a.csv"
        p.write_text("post_id,Timestamp,content,like_count,comments,shares\n"
                     "x1,2026-09-01T00:00:00Z,hi,\"1,200\",3,4\n", encoding="utf-8")
        [x] = loaders.load(p)
        self.assertEqual((x.id, x.text, x.likes, x.replies, x.reposts, x.quotes, x.views),
                         ("x1", "hi", 1200, 3, 4, 0, None))

    def test_csv_errors_name_the_row(self):
        p = self.tmp / "bad.csv"
        p.write_text("id,date,likes\n1,2026-09-01,5\n2,2026-09-02,-1\n", encoding="utf-8")
        with self.assertRaisesRegex(loaders.DataError, r"bad\.csv:3: likes is negative"):
            loaders.load(p)
        p.write_text("id,likes\n1,5\n", encoding="utf-8")
        with self.assertRaisesRegex(loaders.DataError, r"bad\.csv:2: missing created_at"):
            loaders.load(p)

    def test_json_list_and_data_wrapper(self):
        rows = [{"id": "1", "timestamp": "2026-09-01T00:00:00Z", "text": "t", "likes": 2, "views": 100}]
        for name, payload in (("list.json", rows), ("wrapped.json", {"data": rows})):
            p = self.tmp / name
            p.write_text(json.dumps(payload), encoding="utf-8")
            [x] = loaders.load(p)
            self.assertEqual((x.likes, x.views), (2, 100))

    def test_x_archive(self):
        posts = loaders.load(FIXTURES / "tweets.js")
        self.assertEqual(len(posts), 3)
        self.assertEqual((posts[0].likes, posts[0].reposts, posts[0].views), (42, 7, None))
        self.assertTrue(posts[1].is_repost)
        self.assertFalse(posts[0].is_repost)

    def test_x_archive_rejects_other_js(self):
        p = self.tmp / "other.js"
        p.write_text("console.log(1)", encoding="utf-8")
        with self.assertRaisesRegex(loaders.DataError, "not an X archive"):
            loaders.load(p)

    def test_non_utf8_file_names_the_file(self):
        p = self.tmp / "big5.csv"
        p.write_bytes("id,date,text\n1,2026-09-01,中文\n".encode("cp950"))
        with self.assertRaisesRegex(loaders.DataError, r"big5\.csv: not UTF-8"):
            loaders.load(p)

    def test_unknown_extension(self):
        p = self.tmp / "data.txt"
        p.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(loaders.DataError, "pass --format"):
            loaders.load(p)


class AnalysisTests(unittest.TestCase):
    def test_score_uses_weights(self):
        p = post(likes=10, replies=2, reposts=1, quotes=1)
        self.assertEqual(analysis.score(p, analysis.DEFAULT_WEIGHTS), 10 + 3 + 2 + 2)
        self.assertEqual(analysis.score(p, {"likes": 0, "replies": 1, "reposts": 0, "quotes": 0}), 2)

    def test_engagement_rate_needs_views(self):
        a, b, c = post(likes=10, views=100), post(likes=10), post(likes=10, views=0)
        analysis.analyze([a, b, c], analysis.Rules())
        self.assertAlmostEqual(a.engagement_rate, 0.1)
        self.assertIsNone(b.engagement_rate)
        self.assertIsNone(c.engagement_rate)

    def test_percentile_ranks_with_ties(self):
        self.assertEqual(analysis.percentile_ranks([1, 2, 2, 3]), [0.0, 50.0, 50.0, 100.0])
        self.assertEqual(analysis.percentile_ranks([5]), [100.0])

    def test_rules_classify_topics_and_first_line_hook(self):
        rules = analysis.load_rules(ROOT / "rules.example.json")
        p = post("免費的 Claude 測試清單\n你會用嗎？")
        analysis.classify(p, rules)
        self.assertEqual(p.topics, ["AI 工具實測", "程式開發"])
        self.assertEqual(p.hook, "資源分享")  # 只看第一行，第二行的問號不算
        q = post("今天天氣很好")
        analysis.classify(q, rules)
        self.assertEqual((q.topics, q.hook), ([analysis.UNCATEGORIZED], analysis.OTHER_HOOK))

    def test_bad_rules_are_rejected(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for payload, message in (
                ({"weights": {"stars": 1}}, "unknown weight"),
                ({"weights": {"likes": -1}}, "non-negative"),
                ({"topics": {"x": {}}}, "no keywords or patterns"),
                ({"hooks": {"x": {"patterns": ["("]}}}, "invalid pattern"),
            ):
                p = tmp / "r.json"
                p.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    analysis.load_rules(p)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_filter_excludes_reposts_and_dates(self):
        a, b, c = post("a", when="2026-09-01T00:00:00Z"), post("b", when="2026-09-10T00:00:00Z"), post("c")
        c.is_repost = True
        since = loaders.parse_datetime("2026-09-05T00:00:00Z")
        self.assertEqual([p.text for p in analysis.filter_posts([a, b, c], None, None, False)], ["a", "b"])
        self.assertEqual([p.text for p in analysis.filter_posts([a, b, c], since, None, False)], ["b"])
        self.assertEqual(len(analysis.filter_posts([a, b, c], None, None, True)), 3)

    def test_group_stats_flags_small_samples_last(self):
        posts = [post(f"big{i}", likes=1) for i in range(5)] + [post("tiny", likes=100)]
        analysis.analyze(posts, analysis.Rules())
        stats = analysis.group_stats(posts, lambda p: "small" if p.text == "tiny" else "big")
        self.assertEqual([s.name for s in stats], ["big", "small"])
        self.assertTrue(stats[1].small_sample)
        self.assertFalse(stats[0].small_sample)

    def test_hour_and_weekday_use_offset(self):
        p = post(when="2026-09-06T17:30:00Z")  # 週日 17:30 UTC = 週一 01:30 +08:00
        tz = analysis.parse_offset("+08:00")
        self.assertEqual(analysis.weekday_key(tz)(p), "週一")
        self.assertEqual(analysis.hour_key(tz)(p), "00–03 時")
        with self.assertRaises(ValueError):
            analysis.parse_offset("Asia/Taipei")


class CliTests(TempDirCase):
    def test_sample_end_to_end(self):
        out = self.tmp / "out"
        code, log = self.cli("analyze", str(ROOT / "examples" / "sample_posts.csv"),
                             "--rules", str(ROOT / "rules.example.json"), "--out", str(out))
        self.assertEqual(code, 0, log)
        md = (out / "report.md").read_text(encoding="utf-8")
        self.assertIn("## 依主題", md)
        self.assertIn("UTC+08:00", md)
        self.assertIn("| AI 工具實測 | 6 |", md)
        with (out / "posts_scored.csv").open(encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 36)
        scores = [float(r["score"]) for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["posts"], 36)

    def test_x_archive_excludes_reposts_and_notes_missing_views(self):
        out = self.tmp / "out"
        code, log = self.cli("analyze", str(FIXTURES / "tweets.js"), "--out", str(out))
        self.assertEqual(code, 0, log)
        self.assertIn("analyzed 2 of 3 posts", log)
        md = (out / "report.md").read_text(encoding="utf-8")
        self.assertIn("另排除轉發 1 篇", md)
        self.assertIn("本資料沒有曝光數", md)

    def test_until_date_uses_offset(self):
        out = self.tmp / "out"
        # 2026-09-04 23:30 UTC = 09-05 07:30 +08:00，所以 --until 2026-09-05 會排除它
        code, log = self.cli("analyze", str(FIXTURES / "tweets.js"), "--until", "2026-09-05", "--out", str(out))
        self.assertEqual(code, 0, log)
        self.assertIn("analyzed 1 of 3 posts", log)

    def test_empty_result_exit_1_and_bad_input_exit_2(self):
        code, _ = self.cli("analyze", str(FIXTURES / "tweets.js"), "--since", "2030-01-01",
                           "--out", str(self.tmp / "o"))
        self.assertEqual(code, 1)
        code, log = self.cli("analyze", str(self.tmp / "missing.csv"))
        self.assertEqual(code, 2)
        self.assertIn("input file not found", log)

    def test_markdown_escapes_pipes(self):
        p = post("a | b", likes=1)
        analysis.analyze([p], analysis.Rules())
        md = report.markdown([p], analysis.Rules(), timezone.utc, 0, "x")
        self.assertIn("a \\| b", md)


class SampleDataTests(unittest.TestCase):
    def test_sample_is_reproducible(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copy(ROOT / "examples" / "make_sample.py", tmp / "make_sample.py")
            import runpy
            with contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(tmp / "make_sample.py"), run_name="__main__")
            self.assertEqual((tmp / "sample_posts.csv").read_bytes(),
                             (ROOT / "examples" / "sample_posts.csv").read_bytes())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
