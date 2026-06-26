---
name: publish-blog
description: Publish a new blog article by creating the markdown file with correct bilingual frontmatter, validating metadata, and staging for commit.
---

# Publish Blog Article

## When to use
User says "发布博客" or asks to write/publish a blog article.

## Procedure

1. **Determine the article content**
   - Content may come from user dictation, Obsidian Knowledge Base sync, or the sync-kb-to-blog script
   - If user references the Knowledge Base, check `/Users/james/git/obsidian/MrXie AI consulting/Knowledge_Base/` for source material

2. **Create the markdown file** in `src/content/blog/`
   - File naming: kebab-case, optionally date-prefixed (e.g., `2026-06-18-loop-engineering.md` or `agent-memory-engineering.md`)
   - Frontmatter must contain ALL required fields:

   ```yaml
   ---
   title:
     zh: "中文标题"
     en: "English Title"
   date: "YYYY-MM-DD"
   description:
     zh: "中文描述（1-2句话）"
     en: "English description (1-2 sentences)"
   category: "Category Name"
   tags: ["tag1", "tag2"]
   draft: false
   author: "谢灵江"
   ---
   ```

3. **Validate the article**
   - Run: `node scripts/check-blog-posts.cjs`
   - Confirm all required fields are present
   - Confirm `draft: false` for publishing

4. **Stage for commit**
   - Run: `node scripts/publish-blog-posts.cjs`
   - This auto-detects new articles, validates, adds `draft: false`, and runs `git add`
   - Alternatively, manually: `git add src/content/blog/<filename>.md`

5. **Commit**
   ```bash
   git commit -m "feat: 发布新文章：中文标题"
   ```
   - Do NOT push (project rule)

6. **If adding a series** (multiple related articles published together):
   - Commit each article individually, or commit as a batch with message:
     `feat: 发布《系列名》系列N篇文章`
   - After articles are committed, update timeline if milestones warrant it (see `update-timeline` skill)

7. **If updating the timeline** alongside a blog release:
   - Edit `src/components/Timeline.astro` to add the new milestone entry
   - Commit together or separately (user preference)

## Required frontmatter fields
| Field | Required | Notes |
|-------|----------|-------|
| `title.zh` | YES | 中文标题 |
| `title.en` | YES | English Title |
| `date` | YES | Format: YYYY-MM-DD |
| `draft` | YES | false = published, true = draft |
| `author` | YES | Author name |
| `description.zh` | Recommended | 中文描述 |
| `description.en` | Recommended | English description |
| `category` | Recommended | Article category |
| `tags` | Recommended | Tag array |

## Rules
- Article body defaults to Chinese (中文)
- Metadata must be bilingual (zh + en)
- Use `draft: true` initially during writing, switch to `false` when ready to publish
- Minimum viable check: run `check-blog-posts.cjs` before committing
