# Gemini Agent Protocols

This file defines specific workflows for AI agents operating in this codebase.

## 📝 Blog Publishing Protocol
When asked to "add a blog post" or "publish a new solo log", follow these steps:

1. **Path**: Always create the file in `src/content/blog/{slug}.md`.
2. **Filename**: Use kebab-case for the filename (e.g., `my-new-post.md`).
3. **Frontmatter Schema**: Must strictly follow the `src/content/config.ts` definition:
   - `title`: Object with `zh` and `en`.
   - `description`: Object with `zh` and `en`.
   - `date`: Current date in `YYYY-MM-DD` format.
   - `category`: String (e.g., "Daily", "Tech", "Life").
   - `tags`: Array of strings.
   - `draft`: Boolean (default `false`).
   - `author`: Default to "James Xie".
4. **Content**: 
   - Write the main content in Markdown. 
   - If not specified, write in Chinese (the user's primary language for solo logs).
   - Ensure a clear structure with H2/H3 headers.

### Example Frontmatter
```yaml
---
title:
  zh: "标题"
  en: "Title"
description:
  zh: "描述"
  en: "Description"
date: "2026-04-23"
category: "Daily"
tags: ["tag1"]
draft: false
author: "James Xie"
---
```
