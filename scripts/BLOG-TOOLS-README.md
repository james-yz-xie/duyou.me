# 博客文章管理工具

## 概述

这两个脚本帮助你管理和发布博客文章，自动检查元数据完整性并发布新文章。

## 脚本说明

### 1. check-blog-posts.cjs - 博客文章状态检查器

**功能：**
- 检查所有博客文章的元数据完整性
- 验证必需字段（标题、日期、描述、分类、标签、作者）
- 检查中英文双语支持
- 显示每篇文章的发布状态和字数统计
- 生成详细的统计报告

**使用方法：**
```bash
node scripts/check-blog-posts.cjs
```

**输出示例：**
```
📝 博客文章状态检查器
============================================================

找到 23 篇博客文章

1. ✅ agent-memory-engineering.md
   📤 已发布 | 字数: 22,665
   📅 日期: 2026-05-11

...

📊 统计摘要
============================================================
总文章数: 23
✅ 有效文章: 23
❌ 有问题文章: 0
📤 已发布: 23
📝 草稿: 0

🎉 所有文章状态良好！
```

### 2. publish-blog-posts.cjs - 博客文章发布助手

**功能：**
- 自动检测新的博客文章文件
- 自动检测修改的博客文章
- 验证文章元数据
- 自动添加 `draft: false` 字段
- 自动将文章添加到 git
- 提供提交和推送建议

**使用方法：**
```bash
node scripts/publish-blog-posts.cjs
```

**工作流程：**
1. 在 `src/content/blog/` 目录创建新的 `.md` 文件
2. 运行 `node scripts/publish-blog-posts.cjs`
3. 脚本会自动：
   - 检测新文件
   - 验证元数据
   - 添加 `draft: false`
   - 执行 `git add`
4. 根据提示运行 `git commit` 和 `git push`

## 博客文章元数据要求

每篇博客文章必须包含以下 Frontmatter：

```yaml
---
title:
  zh: "中文标题"
  en: "English Title"
date: "YYYY-MM-DD"
description:
  zh: "中文描述"
  en: "English description"
category: "分类名称"
tags: ["标签1", "标签2"]
draft: false
author: "作者姓名"
---
```

### 必需字段
- ✅ `title.zh` - 中文标题
- ✅ `title.en` - 英文标题
- ✅ `date` - 发布日期（格式：YYYY-MM-DD）
- ✅ `draft` - 发布状态（false = 已发布，true = 草稿）
- ✅ `author` - 作者姓名

### 推荐字段
- ⚠️ `description.zh` - 中文描述
- ⚠️ `description.en` - 英文描述
- ⚠️ `category` - 文章分类
- ⚠️ `tags` - 文章标签数组

## 最佳实践

### 创建新文章

1. **复制模板**
```bash
cp src/content/blog/template.md src/content/blog/my-new-post.md
```

2. **编辑元数据**
```yaml
---
title:
  zh: "我的新文章标题"
  en: "My New Post Title"
date: "2026-06-04"
description:
  zh: "文章的中文描述"
  en: "English description of the post"
category: "AI Engineering"
tags: ["AI", "Tutorial"]
draft: true  # 先设为 true，完成后再改为 false
author: "Your Name"
---
```

3. **编写内容**
```markdown
## 引言

文章内容...

## 正文

更多内容...

## 结论

总结...
```

4. **发布文章**
```bash
# 修改 draft 为 false
# 运行发布脚本
node scripts/publish-blog-posts.cjs

# 提交更改
git commit -m "feat: 发布新文章：我的新文章标题"
git push
```

### 定期检查

建议定期运行检查脚本，确保所有文章状态正常：

```bash
# 每周检查一次
node scripts/check-blog-posts.cjs
```

### 批量修复

如果发现多篇文章有问题，可以：

1. 运行检查脚本查看问题
2. 手动修复有问题的文章
3. 再次运行检查脚本确认
4. 运行发布脚本提交更改

## 常见问题

### Q: 如何设置文章为草稿？

A: 将 `draft` 字段设置为 `true`：
```yaml
draft: true
```

### Q: 文章没有显示在博客列表中？

A: 检查以下几点：
1. `draft` 是否为 `false`
2. 元数据是否完整
3. 运行 `check-blog-posts.cjs` 查看是否有错误

### Q: 如何修改文章日期？

A: 直接修改 Frontmatter 中的 `date` 字段：
```yaml
date: "2026-06-04"  # 修改为你想要的日期
```

### Q: 可以只发布部分文章吗？

A: 可以。发布脚本只会处理新文件或修改过的文件。你可以：
1. 只创建/修改要发布的文章
2. 运行发布脚本
3. 提交时只包含这些文章

## 自动化建议

### Git Hook（可选）

可以在 `.git/hooks/pre-commit` 中添加检查：

```bash
#!/bin/bash
echo "📝 检查博客文章..."
node scripts/check-blog-posts.cjs
```

### CI/CD 集成

在 GitHub Actions 或其他 CI/CD 工具中添加检查步骤：

```yaml
- name: Check blog posts
  run: node scripts/check-blog-posts.cjs
```

## 技术支持

如有问题或建议，请提交 Issue 或联系维护者。
