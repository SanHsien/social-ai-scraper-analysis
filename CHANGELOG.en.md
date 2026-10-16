English | [中文版](CHANGELOG.md)

# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), newest first.

## 2026-10-17

### Added

- Fully restored and implemented the web scraper suite (`scrapers/`):
  - `scrapling_scraper.py`: Scrapling integration with `StealthyFetcher` (anti-bot & Cloudflare Turnstile bypass) and `adaptive=True` self-healing element locators.
  - `agent_reach_scraper.py`: Agent Reach integration for zero-API-cost social platform data extraction (X / Reddit / YouTube).
  - `scrapegraph_analyzer.py`: ScrapeGraphAI integration for prompt-based semantic extraction with local Ollama or cloud LLMs.
- Fully implemented end-to-end executable `workflow_example.py` replacing the previous print-only skeleton, supporting CLI flags, proxies, batch scraping, and viral hook extraction.
- Implemented `analyzer.py` for weighted engagement scoring, top 20% viral filtering, topic categorization, and imitation guide generation, exporting to `results.json` and `viral_insights.csv`.
- Restored `targets.example.json` and added `requirements.txt`.
- Fixed Windows 11 console CP950 Unicode encoding issue.
- Updated `README.md`, `README.en.md`, and `AGENTS.md` to remove anti-scraping restrictions and support both automated online scraping and offline `postlens` reporting.
- Added non-negotiable governance rule across `AGENTS.md`, `CLAUDE.md`, `README.md`, and `README.en.md` strictly prohibiting AI Agents from altering project scope, downgrading core features, or imposing self-restrictions without developer consent.
- Expanded architecture across all mainstream social platforms: X (Twitter), Threads, Instagram, Facebook, YouTube, and Reddit.
- Implemented dual modes: "Target Account Monitoring (Account Mode)" and broad "Trending Discovery Mode" for searching viral content across platforms by keyword or topic.
- Added `scrapers/multi_platform_scraper.py` and unit test suite `tests/test_multi_platform.py` (31 passing tests).
- Added comprehensive repository code review document `REVIEW.md`.

### Fixed

- Fixed missing `created_at` in `viral_insights.csv` causing `postlens` to fail with DataError.
- Fixed conversion exceptions in `analyzer.py` and `agent_reach_scraper.py` when metrics are `None` or formatted strings.
- Removed hardcoded 3-account limit per platform in `workflow_example.py` by adding `--max-targets` and `--run-postlens`.
- Fixed unescaped URL query parameters in social trending search.
- Fixed non-standard datetime outputs in fallback scrapers.

## 2026-10-16

### Added

- `postlens`: reads CSV / JSON / X archive `tweets.js`, computes engagement score, engagement rate and percentile, classifies topics and hooks from a rules file, and writes `report.md`, `posts_scored.csv`, `summary.json`.
- `rules.example.json`, fictional sample data and its generator `examples/make_sample.py`.
- Tests (stdlib `unittest`, 23 cases), `tools/dev_check.ps1`, GitHub Actions (Windows + Ubuntu Python 3.10 / 3.13).
- Bilingual README, MIT license, `.gitattributes`, `.editorconfig`.

### Fixed

- Python 3.10 could not read the Graph/Threads API `+0000` offset format.
- 10-digit Unix seconds in `--since` / `--until` were mistaken for a date-only value and shifted by `--utc-offset`.
- `inf` counts and non-UTF-8 files now produce an error naming the file and row (exit 2).
