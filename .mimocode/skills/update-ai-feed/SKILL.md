---
name: update-ai-feed
description: Update the AI frontier weekly feed by reading the latest Obsidian briefing, translating highlights into bilingual Astro component data, and committing the changes.
---

# Update AI Frontier Weekly Feed

## When to use
User says "更新 AI 前沿情报" or asks to update the AI feed / briefings page.

## Procedure

1. **Read the latest briefing**
   - Navigate to `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Briefings/`
   - Find the most recent `Briefing_YYYY-MM-DD.md` file (sorted by date, newest first)
   - Read the full briefing content

2. **Update the homepage component** `src/components/WeeklyFeed.astro`
   - Replace the `highlights` array with the top 5-8 most significant items from the briefing
   - Each item follows this exact structure:
     ```js
     {
       title: { zh: '中文标题', en: 'English Title' },
       date: { zh: '2026 年 M 月 D 日', en: 'Month D, 2026' },
       summary: { zh: '中文摘要', en: 'English summary' },
       links: [{ label: 'Source →', href: 'https://...' }]
     }
     ```
   - Update the date stamps at the bottom of the file:
     - `最后更新：YYYY年MM月DD日` → today's date
     - `Last updated: Month DD, YYYY` → today's date

3. **Update the detail page** `src/pages/briefings.astro`
   - Update the `sections` array with the full categorized content
   - Categories follow the Scout Agent format: 工业界巨头 / 顶级媒体 / 学术界前沿 / 社区与工程
   - Include ALL items from the briefing (not just highlights)
   - Each item MUST have an external source link (e.g., `Google →`, `arXiv →`, `OpenAI →`)
   - Update the date stamps identically to step 2

4. **Commit**
   ```bash
   git add src/components/WeeklyFeed.astro src/pages/briefings.astro
   git commit -m "Update AI frontier weekly feed to YYYY年MM月DD日"
   ```
   - Do NOT push (project rule: user does manual push)

## Rules
- Only include external intelligence from Briefings, not original articles
- Every briefing item must include at least one external source link
- Bilingual content is mandatory: all `title` and `summary` fields need both `zh` and `en`
- Date format in component: zh uses `YYYY 年 M 月 D 日`, en uses `Month D, YYYY`
- Use the gold/amber color theme (already in CSS) — do not change visual styling
