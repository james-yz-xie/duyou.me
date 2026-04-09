# Duyou.me 项目维护指南

## 项目概述

谢灵江的个人网站，托管在 Cloudflare Pages，使用 Astro + Tailwind CSS 构建。

**仓库**: https://github.com/james-yz-xie/duyou.me.git
**域名**: https://duyou.me

---

## 快速命令

```bash
# 本地开发
npm run dev

# 构建
npm run build

# 部署（推送到 GitHub，Cloudflare 自动部署）
git add -A && git commit -m "message" && git push
```

---

## 内容更新

### 更新周报

周报内容来源：
- **Briefings**: `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Briefings/`
- **Articles**: `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Articles/`

**步骤**：
1. 阅读 Briefings 目录下的最新简报
2. 更新首页周报摘要：`src/components/WeeklyFeed.astro`
3. 更新周报详情页：`src/pages/briefings.astro`
4. 分类按 Scout Agent 格式：工业界巨头、学术界前沿、社区与工程
5. **每条周报必须添加链接**（三种情况）：
   - 有外部来源：添加原始信源链接（如 `Google →`、`arXiv →`、`OpenAI →`）
   - 原创深度文章：标注 `深度解析 →` 链接到 `/briefings`
   - 进行中项目：标注 `进行中` 状态
6. 提交推送：`git add -A && git commit -m "Update weekly feed" && git push`

**用户指令**：`更新周报`

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

## 内容来源路径

| 内容 | 路径 |
|------|------|
| AI 研究成果（已发布文章） | `/Users/james/git/obsidian/MrXie AI consulting/Knowledge_Base/` |
| AI 咨询 Briefings | `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Briefings/` |
| AI 咨询 Articles | `/Users/james/git/obsidian/MrXie AI consulting/Outputs/Articles/` |
| AI 养生公司 | `/Users/james/git/obsidian/MrXie AI养生公司` |
| 个人简历 | `/Users/james/git/obsidian/MrXie AI resume/谢灵江_简历_Base.md` |

---

## 项目结构

```
src/
├── components/
│   ├── Hero.astro        # 首页个人介绍
│   ├── Timeline.astro    # 项目里程碑
│   ├── WeeklyFeed.astro  # 周报摘要（首页）
│   ├── Footer.astro      # 页脚
│   └── ...
├── pages/
│   ├── index.astro       # 首页
│   └── briefings.astro   # 周报详情页
└── layouts/
    └── Layout.astro      # 页面布局
```

---

## 用户背景

- eBay 前技术负责人，20年支付领域经验
- 两项美国机器学习专利（图神经网络异常检测）
- 公众号：谢先生的AI深析札记
- 视频号：黄帝内经每天趣味一分钟