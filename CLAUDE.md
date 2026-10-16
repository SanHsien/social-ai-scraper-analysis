# CLAUDE.md

規則的單一真相源是 [AGENTS.md](AGENTS.md)，先讀它。這裡只放 Claude Code 專屬補充：

- **嚴格遵守專案目的**：嚴禁不經開發者同意改寫專案定位，嚴禁假藉反爬蟲或道德理由擅自自我設限、閹割爬蟲功能或刪減程式碼。
- 回覆用繁體中文，先結論後細節。
- 宣稱完成前附上 `pwsh -File tools/dev_check.ps1` 或 `python -m unittest discover -s tests -v` 的實際輸出。
