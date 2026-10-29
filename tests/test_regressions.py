"""第二輪深度掃描找到的缺陷的重現測試（全部離線）。"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analyzer import ViralPostAnalyzer
from postlens import analysis, loaders
from postlens.cli import main as postlens_main
from scrapers.agent_reach_scraper import AgentReachScraper
from scrapers.scrapling_scraper import ScraplingSocialScraper

ROOT = Path(__file__).resolve().parent.parent


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, name: str, text: str) -> Path:
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p


class AgentReachMetricTests(unittest.TestCase):
    def test_safe_int_parses_unit_strings(self):
        s = AgentReachScraper()
        self.assertEqual(s._safe_int("1,200"), 1200)
        self.assertEqual(s._safe_int("2.5K"), 2500)
        self.assertEqual(s._safe_int("1.2M"), 1200000)
        self.assertEqual(s._safe_int("3B"), 3000000000)
        self.assertEqual(s._safe_int("n/a"), 0)
        self.assertEqual(s._safe_int("1.2.3"), 0)

    def test_normalize_accepts_string_metrics(self):
        rows = AgentReachScraper()._normalize_agent_reach_data(
            [{"text": "hi", "likes": "1.5K", "retweet_count": "2K", "reply_count": "30"}], "u")
        self.assertEqual((rows[0]["likes"], rows[0]["retweets"], rows[0]["replies"]), (1500, 2000, 30))


class ScraplingMetricTests(unittest.TestCase):
    def test_malformed_metric_text_is_zero_not_crash(self):
        s = ScraplingSocialScraper()
        self.assertEqual(s._extract_metric("1.2.3"), 0)
        self.assertEqual(s._extract_metric("."), 0)
        self.assertEqual(s._extract_metric("1.2K"), 1200)


class JsonRowShapeTests(TempDirCase):
    def test_non_object_rows_raise_data_error(self):
        for payload in ([1, 2], ["text"], [None], {"data": [[1]]}):
            p = self.write("p.json", json.dumps(payload))
            with self.assertRaises(loaders.DataError, msg=payload):
                loaders.load(p)

    def test_cli_reports_instead_of_traceback(self):
        p = self.write("p.json", "[1, 2]")
        self.assertEqual(postlens_main(["analyze", str(p), "--out", str(self.tmp / "o")]), 2)


class RulesShapeTests(TempDirCase):
    def test_string_keywords_and_patterns_are_rejected(self):
        for payload in (
            {"topics": {"x": {"keywords": "AI"}}},
            {"hooks": {"x": {"patterns": "^為什麼"}}},
            {"topics": ["x"]},
            {"weights": [1]},
            {"weights": {"likes": float("nan")}},
            {"weights": {"likes": True}},
            ["not", "an", "object"],
        ):
            p = self.write("r.json", json.dumps(payload))
            with self.assertRaises(ValueError, msg=payload):
                analysis.load_rules(p)

    def test_cli_reports_bad_rules_shape(self):
        data = self.write("d.json", json.dumps([{"created_at": "2026-01-01T00:00:00Z", "text": "a"}]))
        rules = self.write("r.json", json.dumps(["x"]))
        self.assertEqual(postlens_main(["analyze", str(data), "--rules", str(rules),
                                        "--out", str(self.tmp / "o")]), 2)


class AnalyzerRobustnessTests(unittest.TestCase):
    def test_none_text_does_not_crash(self):
        r = ViralPostAnalyzer().analyze_post_content({"text": None, "platform": "x"})
        self.assertIn("topic_category", r)

    def test_hook_skips_leading_blank_lines(self):
        a = ViralPostAnalyzer()
        self.assertEqual(a._detect_hook_style("\n\n為什麼多數人都錯了\n內文"), a._detect_hook_style("為什麼多數人都錯了\n內文"))

    def test_short_ascii_keyword_needs_word_boundary(self):
        a = ViralPostAnalyzer()
        self.assertNotEqual(a._detect_category("I said hello, maintain the plan by email"), "AI 工具評測與技術架構")
        self.assertEqual(a._detect_category("New AI tools for developers"), "AI 工具評測與技術架構")
        self.assertEqual(a._detect_category("今天用 ai 寫程式"), "AI 工具評測與技術架構")
        for text in ("OpenAI released GPT-5", "AIGC trend", "AI2 model", "GenAI roadmap",
                     "#AItools", "#GenerativeAI", "#OpenSourceAI", "AIart", "AIagent", "devtools",
                     "#AIArt", "#AINews", "AIOps", "#aiart", "#ainews", "#aiagent"):
            self.assertEqual(a._detect_category(text), "AI 工具評測與技術架構", text)

    def test_generated_ids_are_stable_across_processes(self):
        code = (
            "import sys, tempfile, os\n"
            "from analyzer import ViralPostAnalyzer\n"
            "d = tempfile.mkdtemp()\n"
            "p = {'platform': 'x', 'author': 'a', 'text': 'same text', 'likes': 1, 'created_at': '2026-01-01T00:00:00Z'}\n"
            "ViralPostAnalyzer().export_results([p], os.path.join(d, 'o.json'), os.path.join(d, 'o.csv'))\n"
            "print(open(os.path.join(d, 'o.csv'), encoding='utf-8-sig').read().splitlines()[1].split(',')[0])\n"
        )
        outs = set()
        for seed in ("1", "2", "3"):
            r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                               env={**__import__("os").environ, "PYTHONHASHSEED": seed}, check=True)
            outs.add(r.stdout.strip())
        self.assertEqual(len(outs), 1, outs)


class WorkflowTests(TempDirCase):
    def test_postlens_failure_is_not_reported_as_success(self):
        import workflow_example as wf
        out = self.tmp / "r.json"
        argv = ["workflow_example.py", "--mode", "trending", "--query", "q", "--platforms", "x",
                "--max-posts", "1", "--output-json", str(out), "--output-csv", str(self.tmp / "v.csv"),
                "--run-postlens"]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch("postlens.cli.main", return_value=2), \
                mock.patch("builtins.print") as pr, \
                mock.patch.object(wf.logger, "warning") as warn:
            wf.main()
        printed = " ".join(str(c.args[0]) for c in pr.call_args_list if c.args)
        self.assertNotIn("報表已生成", printed)
        self.assertTrue(warn.called)

    def test_headless_can_be_disabled(self):
        import workflow_example as wf
        with mock.patch.object(sys, "argv", ["w", "--no-headless"]):
            self.assertFalse(wf.parse_args().headless)
        with mock.patch.object(sys, "argv", ["w"]):
            self.assertTrue(wf.parse_args().headless)


class CliOutputErrorTests(TempDirCase):
    def test_unwritable_out_dir_exits_2(self):
        data = self.write("d.json", json.dumps([{"created_at": "2026-01-01T00:00:00Z", "text": "a"}]))
        blocker = self.write("blocker", "x")  # 檔案擋在輸出目錄的位置
        self.assertEqual(postlens_main(["analyze", str(data), "--out", str(blocker / "sub")]), 2)


class MarkdownUrlTests(unittest.TestCase):
    def test_url_with_parentheses_or_spaces_keeps_link_intact(self):
        from datetime import datetime, timezone
        from postlens import report
        from postlens.models import Post
        p = Post(id="1", created_at=datetime(2026, 1, 1, tzinfo=timezone.utc), text="hello",
                 url="https://en.wikipedia.org/wiki/Foo_(bar) baz")
        analysis.analyze([p], analysis.Rules())
        md = report.markdown([p], analysis.Rules(), timezone.utc, 0, "s")
        self.assertIn("(https://en.wikipedia.org/wiki/Foo_%28bar%29%20baz)", md)


class UnknownMetricsTests(unittest.TestCase):
    """抓不到的互動數必須是 None，不能寫死或推算出數字。"""

    METRICS = ("likes", "retweets", "replies")

    def test_scrapling_text_fallback_does_not_invent_metrics(self):
        page = mock.Mock(text="這是一段足夠長的段落文字，用來通過三十字元的長度門檻，內容本身不含任何互動數。\n\n"
                              "第二段同樣夠長的文字，用來確認不同順位的段落也不會被推算出互動數字。")
        posts = ScraplingSocialScraper()._parse_from_page_text(page, "u", 5)
        self.assertEqual(len(posts), 2)
        for p in posts:
            for m in self.METRICS:
                self.assertIsNone(p[m], m)

    def test_threads_live_scrape_does_not_invent_metrics(self):
        from scrapers.multi_platform_scraper import MultiPlatformScraper
        el = mock.Mock(text="這是一則足夠長的 Threads 貼文內文，用來通過長度門檻。")
        page = mock.Mock()
        page.css.return_value = [el]
        fetchers = mock.Mock()
        fetchers.StealthyFetcher.fetch.return_value = page
        scraper = MultiPlatformScraper()
        scraper.scrapling._scrapling_available = True
        with mock.patch.dict(sys.modules, {"scrapling": mock.Mock(), "scrapling.fetchers": fetchers}):
            posts = scraper._fetch_threads_account("someone", 3)
        self.assertEqual(posts[0]["source"], "scrapling_threads")
        for m in self.METRICS:
            self.assertIsNone(posts[0][m], m)

    def test_unknown_metrics_flow_through_analysis_and_export(self):
        import os
        a = ViralPostAnalyzer()
        posts = [{"platform": "threads", "author": "a", "text": "no numbers here", "likes": None,
                  "retweets": None, "replies": None, "created_at": "2026-01-01T00:00:00Z"},
                 {"platform": "threads", "author": "b", "text": "has numbers", "likes": 10,
                  "retweets": 1, "replies": 2, "created_at": "2026-01-02T00:00:00Z"}]
        ranked = a.rank_and_filter(posts, top_ratio=1.0, min_count=2)
        self.assertEqual(ranked[0]["author"], "b")
        self.assertEqual(ranked[1]["engagement_score"], 0.0)
        analyzed = [a.analyze_post_content(p) for p in ranked]
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        a.export_results(analyzed, str(d / "o.json"), str(d / "o.csv"))
        self.assertIsNone(json.loads((d / "o.json").read_text(encoding="utf-8"))[1]["likes"])
        self.assertEqual(len(loaders.load_csv(d / "o.csv")), 2)

    def test_format_metric_shows_unknown(self):
        import workflow_example as wf
        self.assertEqual(wf.format_metric(None), "未取得")
        self.assertEqual(wf.format_metric(0), "0")
        self.assertEqual(wf.format_metric(1200), "1200")


class ScrapeGraphConfigTests(unittest.TestCase):
    def test_ollama_custom_url_passed_as_base_url(self):
        """以最新版 scrapegraphai 支援的 base_url 鍵名斷言設定被傳入 SmartScraperGraph。"""
        from scrapers.scrapegraph_analyzer import ScrapeGraphExtractor

        mock_smart_scraper_cls = mock.MagicMock()
        mock_smart_scraper = mock.MagicMock()
        mock_smart_scraper.run.return_value = {"summary": "ok"}
        mock_smart_scraper_cls.return_value = mock_smart_scraper

        mock_graphs = mock.MagicMock()
        mock_graphs.SmartScraperGraph = mock_smart_scraper_cls

        with mock.patch.dict(sys.modules, {
            "scrapegraphai": mock.MagicMock(),
            "scrapegraphai.graphs": mock_graphs,
        }):
            extractor = ScrapeGraphExtractor(
                llm_model="ollama/llama3.2",
                ollama_url="http://custom-ollama:11434"
            )
            extractor._scrapegraph_available = True
            extractor.extract_from_url_or_html("https://example.com", "抽取重點")

            self.assertTrue(mock_smart_scraper_cls.called)
            config = mock_smart_scraper_cls.call_args.kwargs.get("config", {})
            llm_config = config.get("llm", {})
            self.assertEqual(llm_config.get("base_url"), "http://custom-ollama:11434")
            self.assertNotIn("ollama_url", llm_config)


class AgentReachImportTests(unittest.TestCase):
    def test_agent_reach_uses_runner_entrypoint_when_channel_available(self):
        """修前因 import agent_reach.channels.twitter 失敗走備援；修後走真實 runner.run 入口。"""
        mock_agent_reach = mock.MagicMock()
        mock_runner = mock.MagicMock()
        mock_manifests = mock.MagicMock()

        mock_manifest = mock.MagicMock()
        mock_manifests.get.return_value = mock_manifest

        mock_envelope = mock.MagicMock()
        mock_envelope.to_dict.return_value = {
            "channel": "x",
            "items": [
                {
                    "text": "真實貼文內容",
                    "engagement": {"likes": 50, "retweets": 10, "replies": 5},
                    "created_at": "2026-10-29T12:00:00Z",
                }
            ]
        }
        mock_runner.run.return_value = mock_envelope

        with mock.patch.dict(sys.modules, {
            "agent_reach": mock_agent_reach,
            "agent_reach.runner": mock_runner,
            "agent_reach.manifest": mock_manifests,
        }):
            mock_agent_reach.runner = mock_runner
            mock_agent_reach.manifest = mock_manifests

            scraper = AgentReachScraper()
            scraper.cli_available = False
            results = scraper.fetch_tweets("testuser", count=5)

            mock_manifests.get.assert_called_with("twitter")
            mock_runner.run.assert_called_once_with(mock_manifest, query="testuser", params={"limit": 5})
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["text"], "真實貼文內容")
            self.assertEqual(results[0]["likes"], 50)
            self.assertEqual(results[0]["retweets"], 10)
            self.assertEqual(results[0]["replies"], 5)
            self.assertEqual(results[0]["source"], "agent_reach")

    def test_agent_reach_reports_unavailable_when_channel_missing(self):
        """當 agent-reach 安裝但無 twitter/x 頻道時，明確回報不可用並切換至備援資料。"""
        mock_agent_reach = mock.MagicMock()
        mock_runner = mock.MagicMock()
        mock_manifests = mock.MagicMock()

        class MockManifestError(Exception):
            pass

        mock_manifests.ManifestError = MockManifestError
        mock_manifests.get.side_effect = MockManifestError("no channel named 'twitter'")

        with mock.patch.dict(sys.modules, {
            "agent_reach": mock_agent_reach,
            "agent_reach.runner": mock_runner,
            "agent_reach.manifest": mock_manifests,
        }):
            mock_agent_reach.runner = mock_runner
            mock_agent_reach.manifest = mock_manifests

            scraper = AgentReachScraper()
            scraper.cli_available = False
            with self.assertLogs("scrapers.agent_reach_scraper", level="WARNING") as cm:
                results = scraper.fetch_tweets("testuser", count=5)

            self.assertFalse(mock_runner.run.called)
            self.assertTrue(any("不可用" in log for log in cm.output))
            self.assertEqual(len(results), 1)
            self.assertIn("多數人還在用官方貴得離譜的 API", results[0]["text"])


if __name__ == "__main__":
    unittest.main()
