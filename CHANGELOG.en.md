English | [中文版](CHANGELOG.md)

# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), newest first.

## 2026-10-16

### Added

- `postlens`: reads CSV / JSON / X archive `tweets.js`, computes engagement score, engagement rate and percentile, classifies topics and hooks from a rules file, and writes `report.md`, `posts_scored.csv`, `summary.json`.
- `rules.example.json`, fictional sample data and its generator `examples/make_sample.py`.
- Tests (stdlib `unittest`, 21 cases), `tools/dev_check.ps1`, GitHub Actions (Windows + Ubuntu Python 3.10 / 3.13).
- Bilingual README, MIT license, `.gitattributes`, `.editorconfig`.

### Removed

- The old README's descriptions and install steps for tools that bypass anti-bot and Cloudflare protection.
- `targets.example.json` (listed real personal accounts) and `workflow_example.py`, which only printed text.
