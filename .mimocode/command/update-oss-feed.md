---
description: "Run GitHub Trending scout, read the generated OSS briefing, update OpenSourceFeed.astro + opensource.astro, then commit."
agent: build
---

Update the GitHub open-source weekly feed.

Follow the `update-oss-feed` skill:
1. Run the scout script: `cd "/Users/james/git/obsidian/MrXie GitHub Trending" && source venv/bin/activate && python scripts/scout.py`
2. Read the latest generated briefing from `Outputs/Briefings/`
3. Update `src/components/OpenSourceFeed.astro` (topProjects array + date stamps)
4. Update `src/pages/opensource.astro` (full sections + date stamps)
5. Commit with message: `Update open source weekly feed to <today's date in Chinese>`
6. Do NOT push — user does manual push
