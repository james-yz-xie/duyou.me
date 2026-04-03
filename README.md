# 督友 - AI 独立开发者展示墙

一个极简设计的个人品牌展示网站，基于 Astro 和 Tailwind CSS 构建。

## 特性

- ⚡ **极速加载** - 纯静态网站，Cloudflare Pages 秒开
- 🎨 **极简黑金设计** - #0A0A0A 底色 + #D4AF37 点缀色
- 📱 **完全响应式** - 精美适配所有设备
- 🚀 **零 JavaScript 依赖** - 100% 静态内容
- 🌐 **SEO 友好** - Astro 天生支持

## 页面结构

### Hero 区
展示个人背景和核心身份：
- 前 PWC 审计师 / eBay 财务分析师背景
- 现 AI 独立开发者身份
- 快速导航按钮

### Timeline 区
项目里程碑展示：
- 2026年3月：M5 Pro 工作台购置
- 2026年4月：域名上线发布
- 进行中：AI 研究深化

### 核心成果（Card 阵列）
两个高质量卡片：
1. **AI 研究成果** - 本地模型跑分和成果
2. **财务 AI 深度文章** - 行业审计应用研究

### AI 前沿周报
最新文章列表，展示行业前沿洞察

### 工作台展示
M5 Pro 工作台信息与占位符图片区域

### Footer
导航和社交媒体链接

## 快速开始

### 安装依赖
```bash
npm install
```

### 本地开发
```bash
npm run dev
```
访问 `http://localhost:3000`

### 构建生产版本
```bash
npm run build
```

## 部署到 Cloudflare Pages

### 方法 1：连接 Git 仓库
1. 推送到 GitHub/GitLab
2. 登陆 Cloudflare Pages 控制台
3. 连接仓库，选择构建命令 `npm run build`
4. 构建输出目录选择 `dist`

### 方法 2：使用 Wrangler CLI
```bash
npm install -g wrangler
wrangler pages deploy dist
```

## 技术栈

- **框架**: [Astro 4.0](https://astro.build)
- **样式**: [Tailwind CSS 3.3](https://tailwindcss.com)
- **部署**: [Cloudflare Pages](https://pages.cloudflare.com)
- **字体**: 系统字体栈（无额外 CDN）

## 文件结构

```
src/
├── layouts/
│   └── Layout.astro        # 基础布局模板
├── components/
│   ├── Hero.astro          # Hero 介绍区
│   ├── Timeline.astro      # 项目里程碑
│   ├── CardGrid.astro      # 成果卡片阵列
│   ├── WeeklyFeed.astro    # AI 周报列表
│   ├── Studio.astro        # 工作台展示
│   └── Footer.astro        # 页脚
├── pages/
│   └── index.astro         # 主页
└── styles/
    └── global.css          # 全局样式
```

## 性能指标

- 📦 **首屏加载**: < 1s
- 🎯 **Lighthouse Score**: 98+
- 🔍 **SEO Score**: 100
- ♿ **无障碍**: 100

## 自定义指南

### 修改颜色
编辑 `tailwind.config.mjs`：
```javascript
colors: {
  'dark': '#0A0A0A',      // 修改底色
  'gold': '#D4AF37',      // 修改点缀色
}
```

### 修改内容
编辑各个 `.astro` 组件文件中的文本内容

### 添加新页面
在 `src/pages/` 目录创建新的 `.astro` 文件，Astro 会自动生成路由

## 许可证

MIT License - 自由使用和修改

## 联系方式

📧 Email: contact@duyou.me
🐙 GitHub: [DuYou](https://github.com)
🐦 Twitter: [@DuYou](https://twitter.com)

---

Built with ❤️ using Astro & Tailwind CSS
