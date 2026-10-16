"""
跨平台社群爬蟲與分析模組單元測試 (Multi-Platform Unit Tests)
"""

import unittest
from scrapers.multi_platform_scraper import MultiPlatformScraper, Platform
from analyzer import ViralPostAnalyzer
from workflow_example import load_targets_config, resolve_platforms

class MultiPlatformTests(unittest.TestCase):

    def test_platform_enum_resolution(self):
        self.assertEqual(Platform.from_str("x"), Platform.X)
        self.assertEqual(Platform.from_str("twitter"), Platform.X)
        self.assertEqual(Platform.from_str("threads"), Platform.THREADS)
        self.assertEqual(Platform.from_str("ig"), Platform.INSTAGRAM)
        self.assertEqual(Platform.from_str("instagram"), Platform.INSTAGRAM)
        self.assertEqual(Platform.from_str("fb"), Platform.FACEBOOK)
        self.assertEqual(Platform.from_str("facebook"), Platform.FACEBOOK)
        self.assertEqual(Platform.from_str("yt"), Platform.YOUTUBE)
        self.assertEqual(Platform.from_str("youtube"), Platform.YOUTUBE)
        self.assertEqual(Platform.from_str("reddit"), Platform.REDDIT)
        with self.assertRaises(ValueError):
            Platform.from_str("nonexistent_platform")

    def test_resolve_platforms(self):
        all_resolved = resolve_platforms("all")
        self.assertEqual(len(all_resolved), 6)
        partial = resolve_platforms("x,threads,reddit")
        self.assertEqual(len(partial), 3)
        self.assertIn(Platform.THREADS, partial)

    def test_multi_platform_account_fetching(self):
        scraper = MultiPlatformScraper()
        platforms = [Platform.X, Platform.THREADS, Platform.INSTAGRAM, Platform.FACEBOOK, Platform.YOUTUBE, Platform.REDDIT]
        for p in platforms:
            posts = scraper.fetch_account_posts(p, "test_target", max_posts=2)
            self.assertIsInstance(posts, list)
            self.assertGreater(len(posts), 0)
            self.assertIn("platform", posts[0])
            self.assertEqual(posts[0]["platform"], p.value)
            self.assertIn("text", posts[0])
            self.assertIn("likes", posts[0])

    def test_multi_platform_trending_search(self):
        scraper = MultiPlatformScraper()
        platforms = [Platform.X, Platform.THREADS, Platform.INSTAGRAM, Platform.FACEBOOK, Platform.YOUTUBE, Platform.REDDIT]
        for p in platforms:
            posts = scraper.search_trending_posts(p, "AI 創業", max_posts=2)
            self.assertIsInstance(posts, list)
            self.assertGreater(len(posts), 0)
            self.assertEqual(posts[0]["platform"], p.value)
            self.assertIn("text", posts[0])

    def test_platform_weighted_scoring(self):
        analyzer = ViralPostAnalyzer()
        # YouTube test with views
        yt_post = {"platform": "youtube", "likes": 1000, "replies": 100, "views": 10000}
        score_yt = analyzer.calculate_score(yt_post)
        self.assertEqual(score_yt, 1000 * 1.0 + 100 * 2.5 + 10.0 * 1.5)

        # Reddit test with upvotes & comments
        rd_post = {"platform": "reddit", "likes": 500, "replies": 50}
        score_rd = analyzer.calculate_score(rd_post)
        self.assertEqual(score_rd, 500 * 1.0 + 50 * 2.0)

    def test_load_targets_config_backward_compatibility(self):
        # Dictionary format
        cfg = load_targets_config("targets.example.json")
        self.assertIn("platforms", cfg)
        self.assertIn("x", cfg["platforms"])
        self.assertIn("threads", cfg["platforms"])

    def test_safe_float_and_scoring_resilience(self):
        from analyzer import _safe_float
        self.assertEqual(_safe_float(None), 0.0)
        self.assertEqual(_safe_float("1,500"), 1500.0)
        self.assertEqual(_safe_float("2.5K"), 2500.0)
        self.assertEqual(_safe_float("1.2M"), 1200000.0)
        self.assertEqual(_safe_float("invalid"), 0.0)

        analyzer = ViralPostAnalyzer()
        # Post with None and string fields
        post_with_none = {"platform": "x", "likes": None, "retweets": "1,200", "replies": "50"}
        score = analyzer.calculate_score(post_with_none)
        self.assertEqual(score, 0.0 * 1.0 + 1200.0 * 2.5 + 50.0 * 1.5)

    def test_export_and_postlens_interoperability(self):
        import tempfile
        import os
        from pathlib import Path
        from postlens.loaders import load_csv

        analyzer = ViralPostAnalyzer()
        test_posts = [
            {
                "platform": "threads",
                "author": "tester",
                "text": "Hello world post",
                "likes": 100,
                "retweets": 20,
                "replies": 10,
                "created_at": "2026-10-15T12:00:00Z"
            }
        ]
        analyzed = [analyzer.analyze_post_content(p) for p in test_posts]
        with tempfile.TemporaryDirectory() as tmpdir:
            json_p = os.path.join(tmpdir, "out.json")
            csv_p = os.path.join(tmpdir, "out.csv")
            analyzer.export_results(analyzed, json_p, csv_p)
            self.assertTrue(os.path.exists(csv_p))

            # Test postlens can load the exported CSV without error
            loaded_posts = load_csv(Path(csv_p))
            self.assertEqual(len(loaded_posts), 1)
            self.assertEqual(loaded_posts[0].likes, 100)
            self.assertEqual(loaded_posts[0].text, "Hello world post")

if __name__ == "__main__":
    unittest.main()
