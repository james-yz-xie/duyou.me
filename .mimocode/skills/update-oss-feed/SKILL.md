---
name: update-oss-feed
description: Update the GitHub open-source weekly feed by running the scout script, reading the generated briefing, updating bilingual Astro component data, and committing the changes.
---

# Update GitHub Open-Source Weekly Feed

## When to use
User says "更新 GitHub 开源热点" or asks to update the open source / OSS feed.

## Procedure

1. **Generate latest data** — Run the GitHub Trending scout script:
   ```bash
   cd "/Users/james/git/obsidian/MrXie GitHub Trending" && source venv/bin/activate && python scripts/scout.py
   ```
   Wait for completion. The script saves a structured briefing to its `Outputs/Briefings/` directory.

2. **Read the generated briefing**
   - Navigate to `/Users/james/git/obsidian/MrXie GitHub Trending/Outputs/Briefings/`
   - Find the most recent `Briefing_YYYY-MM-DD.md`
   - Read the full content

3. **Update the homepage component** `src/components/OpenSourceFeed.astro`
   - Replace the `topProjects` array with the top 3 trending projects from the briefing
   - Each project follows this exact structure:
     ```js
     {
       icon: '🤖',  // choose contextual emoji
       title: { zh: '中文标题：副标题', en: 'English Name: Subtitle' },
       stars: '⭐ X.Xk',
       summary: { zh: '中文摘要', en: 'English summary' },
       href: 'https://github.com/owner/repo'
     }
     ```
   - Update the date stamps at the bottom:
     - `最后更新：YYYY年MM月DD日` → today's date
     - `Last updated: Month DD, YYYY` → today's date

4. **Update the detail page** `src/pages/opensource.astro`
   - Update the sections array with ALL 4 categories from the briefing
   - Each section includes the full item list with repo links and descriptions
   - Update the date stamps identically to step 3

5. **Commit**
   ```bash
   git add src/components/OpenSourceFeed.astro src/pages/opensource.astro
   git commit -m "Update open source weekly feed to YYYY年MM月DD日"
   ```
   - Do NOT push (project rule: user does manual push)

## Rules
- Use `text-emerald-400` (翡翠绿) theme for visual distinction from AI feed (金色) — do not change
- Every project item must include the GitHub `href` link
- Bilingual content is mandatory: all `title` and `summary` fields need both `zh` and `en`
- Date format: zh uses `YYYY年MM月DD日`, en uses `Month DD, YYYY`
