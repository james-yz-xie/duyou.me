---
name: update-timeline
description: Add a new milestone entry to the project timeline component with bilingual content.
---

# Update Timeline

## When to use
User says "更新时间线" or asks to add a milestone/event to the timeline.

## Procedure

1. **Read current timeline** — Open `src/components/Timeline.astro`
2. **Understand the existing structure** — Items are in a chronological array with alternating left/right layout
3. **Add new entry** — Insert in correct chronological position:
   ```js
   {
     title: { zh: '中文里程碑标题', en: 'English Milestone Title' },
     date: { zh: '2026 年 M 月', en: 'Month 2026' },
     description: { zh: '中文描述', en: 'English description' },
     icon: '🚀'  // choose contextual emoji
   }
   ```
4. **Commit**
   ```bash
   git add src/components/Timeline.astro
   git commit -m "Update timeline: YYYY年M月 里程碑标题"
   ```
   - Do NOT push

## Rules
- Entries are sorted chronologically (newest at bottom or top depending on current convention)
- Bilingual content required for `title`, `date`, and `description`
- Right-aligned entries are left-aligned and vice versa (alternating layout)
- Keep descriptions concise (1-2 sentences)
