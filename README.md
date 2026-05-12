# Duyou.me 项目维护指南

## 项目概述

谢灵江的个人网站，托管在 Cloudflare Pages，使用 Astro + Tailwind CSS 构建。

**仓库**: https://github.com/james-yz-xie/duyou.me.git
**域名**: https://duyou.me

---

## 维护规范 (AI Agent Rules)

- **禁止自动执行 `git push`**：AI Agent 仅负责代码修改与 `git commit`。所有 `git push` 动作必须由用户在手动审查代码后执行，以控制发布节奏。
- **路径规范**：优先使用项目根目录下的相对路径，避免写死绝对路径（除非是访问特定的外部 Obsidian 知识库）。
- **最小化改动原则**：每次更新只做必要的最小改动，避免一次性引入过多复杂功能，确保稳定性。

---

## 快速命令

```bash
# 本地开发
npm run dev

# 构建
npm run build

# 部署（推送到 GitHub，Cloudflare 自动部署）
git add -A && git commit -m "message"
```

---

## 内容更新

### 发布 Solo 日志 (博客)

博客位置：`src/content/blog/`
配置文件：`src/content/config.ts`

**内容来源**：用户口述或即兴感悟

**规范**：
- **文件名**：使用 kebab-case (如 `my-new-post.md`)
- **Frontmatter**：必须包含 `title` (zh/en), `description` (zh/en), `date`, `category`, `tags`, `draft`, `author`。
- **语言**：正文默认使用中文，Metadata 需提供中英双语。

**用户交互口令**：`发布博客`

---

### 更新 AI 前沿情报

内容来源：
- **AI Briefings**: `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Briefings/`

**注意**：仅包含外部情报（来自 Briefings），不包含原创文章。原创文章在"核心成果"页面展示。

**步骤**：
1. 阅读 Briefings 目录下的最新简报
2. 更新首页前沿情报摘要：`src/components/WeeklyFeed.astro`
3. 更新情报详情页：`src/pages/briefings.astro`
4. 分类按 Scout Agent 格式：工业界巨头、学术界前沿、社区与工程
5. **每条简报必须添加外部来源链接**（如 `Google →`、`arXiv →`、`OpenAI →`）
6. 提交：`git add -A && git commit -m "Update AI feed"`

**用户交互口令**：`更新 AI 前沿情报`

---

### 更新 GitHub 开源热点

开源内容来源：
- **GitHub Trending 独立监控项目**: `/Users/james/git/obsidian/MrXie GitHub Trending/`

**注意**：开源热点专栏统一使用 `text-emerald-400` (翡翠绿) 主题，以便与传统 AI 前沿情报 (金色) 形成视觉区隔。

**日常完整运维工作流 (End-to-End)**：
1. **生成最新情报数据**：
   打开终端环境执行独立项目的抓取脚本，让 Gemini 大模型自动分析：
   ```bash
   cd "/Users/james/git/obsidian/MrXie GitHub Trending"
   source venv/bin/activate
   python scripts/scout.py
   ```
   *注：运行结束后，结构化简报会自动保存在其内部的 `Outputs/Briefings/` 目录下。*

2. **更新前台门户网页**：
   - 阅读刚才生成的 Markdown 简报文件。
   - 打开 `src/components/OpenSourceFeed.astro`，把“首要信号/趋势总结”以及Top项目的卡片更新上去。
   - 打开 `src/pages/opensource.astro`，将四大分类和完整的仓库详细名单全量更新进此页面库中。

3. **提交与全网自动部署**：
   ```bash
   git add -A && git commit -m "Update open source feed"
   ```

**用户交互口令**：`更新 GitHub 开源热点`

---

### 更新时间线

时间线位置：`src/components/Timeline.astro`

**内容来源**：用户口述新里程碑

**格式**：
- 左右交替布局
- 标题 + 日期 + 描述
- 按时间顺序排列

**用户指令**：`更新时间线`

---

### 更新个人介绍

Hero 组件：`src/components/Hero.astro`
页脚：`src/components/Footer.astro`
页面标题：`src/pages/index.astro`

---

### 更新核心成果

核心成果位置：`src/components/CardGrid.astro`

**内容来源**：`/Users/james/git/obsidian/MrXie AI consulting/Knowledge_Base/`

**两个卡片**：
1. **AI 研究成果**：展示已发布的公众号文章，从 Knowledge_Base 目录获取
2. **财务 AI 深度文章**：待发布，标注"敬请期待"

**用户指令**：`更新核心成果`

---

### 更新 Upwork AI 工作情报

页面位置：`src/pages/upwork-ai-jobs.astro`
导航链接：在 Header.astro 中配置

**内容来源**：Upwork 平台 AI 相关工作数据

**规范**：
- 采用简洁的 HTML 结构，避免复杂的 sections 数组
- 包含 3 个主要部分：市场概览、热门岗位与薪资、热门技能增长
- 保持双语支持（中文/英文）
- 左侧金色边框卡片布局
- 导航栏显示完整文字 "Upwork AI"

**用户指令**：`更新 Upwork AI 情报`

---

## 内容来源路径

| 内容 | 路径 |
|------|------|
| AI 研究成果（已发布文章） | `/Users/james/git/obsidian/MrXie AI consulting/Knowledge_Base/` |
| AI 咨询 Briefings | `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Briefings/` |
| AI 咨询 Articles | `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Articles/` |
| GitHub Trending 监控 | `/Users/james/git/obsidian/MrXie GitHub Trending/` |
| AI 养生公司 | `/Users/james/git/obsidian/MrXie AI养生公司` |
| 个人简历 | `/Users/james/git/obsidian/MrXie AI resume/谢灵江_简历_Base.md` |

---

## 项目结构

```
src/
├── components/
│   ├── Hero.astro           # 首页个人介绍
│   ├── Timeline.astro       # 项目里程碑
│   ├── WeeklyFeed.astro     # 周报摘要（首页）
│   ├── OpenSourceFeed.astro # 开源热点摘要（首页）
│   ├── CardGrid.astro       # 核心成果卡片网格
│   ├── Footer.astro         # 页脚
│   └── ...
├── pages/
│   ├── index.astro          # 首页
│   ├── briefings.astro      # AI 前沿情报详情页
│   ├── opensource.astro     # GitHub 开源热点详情页
│   ├── upwork-ai-jobs.astro # Upwork AI 工作情报页
│   ├── achievements.astro   # 核心成果页
│   ├── agents.astro         # AI Agent 导航页
│   ├── blog/                # Solo 日志（博客）
│   │   ├── index.astro      # 博客列表
│   │   └── [slug].astro     # 博客文章详情
│   └── ...
├── content/
│   ├── blog/                # 博客 Markdown 文件
│   └── config.ts            # 内容配置
└── layouts/
    └── Layout.astro         # 页面布局
```

---

## 网站页面清单

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | `/` | 个人介绍 + 最新动态 |
| AI Agent 导航 | `/agents` | AI 工具推荐和导航 |
| 开源热点 | `/opensource` | GitHub Trending 监控 |
| 前沿情报 | `/briefings` | AI 行业资讯简报 |
| Upwork AI | `/upwork-ai-jobs` | Upwork AI 工作情报 |
| Solo 日志 | `/blog` | 个人博客文章 |
| 核心成果 | `/achievements` | 项目成果展示 |
| 时间线 | `/timeline` | 发展历程 |
| 交付服务 | `/delivery` | 企业服务介绍 |
| 斗鱼小程序 | `/duyou` | 小程序介绍 |
| Arena | `/arena` | AI 竞技场 |
| Agent PK | `/agent-pk` | Agent 对战 |

---

## 用户背景

- eBay 前技术负责人，20年支付领域经验
- 两项美国机器学习专利（图神经网络异常检测）
- 公众号：谢先生的AI深析札记
- 视频号：黄帝内经每天趣味一分钟