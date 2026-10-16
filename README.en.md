English | [中文版](README.md)

# AI Social Post Scraper & Viral Topic Analysis Pipeline

Inspired by the Threads discussion (Source: `https://www.threads.com/share/_jV5NQ2xs/`, by `@aistart_up`).

Core Objective: **"Automatically scrape the recent posts of 100 top X (Twitter) accounts, analyze which topics, hooks, and formats perform best, and generate actionable viral copywriting guides."**

This repository provides both **automated live web scraping (bypassing anti-bot / Cloudflare protections without paid API keys)** and **offline statistical analysis and reporting (`postlens`)**.

---

## 1. Architecture

```
[Target List: 100 X Accounts (targets.json)]
                │
                ▼ Bypass Cloudflare, Turnstile, Fingerprinting & DOM Changes
         【Scrapling】
                │  - StealthyFetcher anti-detection headless browser
                │  - Adaptive Locators (self-healing DOM element selectors)
                ▼
         【Agent Reach】
                │  - Zero-API-cost social data gateway for AI Agents (X / Reddit / YouTube)
                │  - Integrates local sessions, RSS feeds, and multi-route fallback
                ▼
        【ScrapeGraphAI】
                │  - Prompt-based scraping (semantic graph extraction)
                │  - Supports local Ollama (Llama 3, Qwen 2.5) or cloud LLMs
                ▼
    [Viral Topic Analyzer & Report Engine (analyzer.py / postlens)]
                │  - Weighted engagement scoring (Likes + Retweets*2.5 + Replies*1.5)
                │  - Filter top 10%–20% viral posts and extract: Category, Hook Style, Viral Factors, Imitation Guide
                ▼
[Output: results.json & viral_insights.csv / postlens Markdown Report]
```

---

## 2. Core Scraping Tools

### 1. Scrapling
- **Role**: High-resilience, adaptive Python web scraping framework.
- **Pain Point Solved**: Traditional scrapers break when websites update CSS classes or DOM layouts. X also employs strict Cloudflare Turnstile anti-bot checks.
- **Key Features**:
  - **StealthyFetcher**: Built-in browser fingerprint spoofing to bypass modern anti-bot protections.
  - **Adaptive Locators (`adaptive=True`)**: Stores element fingerprints to relocate elements dynamically when layouts change.
  - **Resource Blocking**: Speeds up scraping 3–5x with `block_ads=True` and `disable_resources=True`.

### 2. Agent Reach (`agent-reach`)
- **Role**: Unified social data gateway for AI coding agents (Claude Code, Cursor, Windsurf, etc.).
- **Pain Point Solved**: Official X API costs thousands of dollars monthly.
- **Key Features**:
  - **Zero Official API Cost**: Combines local authenticated cookies (`browser-cookie3`), RSS feeds, and lightweight crawlers.
  - **Cross-Platform**: Covers X (Twitter), Reddit, YouTube transcripts, GitHub, and more.

### 3. ScrapeGraphAI
- **Role**: LLM-driven knowledge graph scraper ("Scrape by asking").
- **Pain Point Solved**: Eliminates the need to write fragile XPath/Regex rules for each page.
- **Key Features**:
  - **Declarative Extraction**: Provide a natural language prompt (e.g. *"Extract all post texts, likes, retweets, and categorize the topics"*).
  - **Local Privacy**: Runs with local Ollama models (Llama 3, Qwen 2.5) for free, private extraction.

---

## 3. Directory Structure

```
social-ai-scraper-analysis/
├── scrapers/                     # Web scraper modules
│   ├── __init__.py
│   ├── scrapling_scraper.py      # Scrapling StealthyFetcher & adaptive parser
│   ├── agent_reach_scraper.py    # Agent Reach zero-API social interface
│   └── scrapegraph_analyzer.py   # ScrapeGraphAI declarative extraction
├── analyzer.py                   # Scoring, hook classification & viral analysis
├── workflow_example.py           # End-to-end executable pipeline
├── targets.example.json          # Monitored accounts list
├── requirements.txt              # Scraping and AI dependencies
├── postlens/                     # Zero-dependency local reporting engine
│   ├── __init__.py
│   ├── analysis.py               # Statistics, grouping, percentile calculations
│   ├── loaders.py                # CSV, JSON, X Archive loaders
│   └── report.py                 # Markdown report generator
├── examples/                     # Sample datasets
├── tests/                        # Test suite
└── README.md
```

---

## 4. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Scrapling stealth browser binaries
scrapling install

# Install Playwright drivers
playwright install
```

---

## 5. Usage

### Mode A: Automated Live Scraping & Viral Analysis
Run the integrated pipeline to fetch target accounts, score engagement, and analyze top viral topics:
```bash
python workflow_example.py
```

Options:
```bash
# Specify Scrapling engine with proxy
python workflow_example.py --engine scrapling --proxy http://127.0.0.1:7890 --max-posts 10

# Use Agent Reach channel
python workflow_example.py --engine agent-reach

# Custom targets and output file
python workflow_example.py --targets targets.example.json --output-csv viral_insights.csv
```

### Mode B: Offline Dataset Analysis (`postlens`)
If you have an exported CSV, JSON, or X account archive (`tweets.js`), analyze it offline with zero external dependencies:
```bash
python -m postlens analyze examples/sample_posts.csv --rules rules.example.json --out out
```
Outputs:
- `out/report.md`: Markdown report grouped by topic, hook, and time slot.
- `out/posts_scored.csv`: Scored posts with percentiles.
- `out/summary.json`: Structured grouping statistics.

---

## 6. Testing & Quality Verification

Run the test suite and dev checks:
```bash
python -m unittest discover -s tests -v
python tools/check_links.py
python workflow_example.py
```

Windows check:
```powershell
pwsh -File tools/dev_check.ps1
```

---

## 7. License

[MIT](LICENSE)
