#!/usr/bin/env node

/**
 * Sync Knowledge Base Articles to Blog
 * 从 Obsidian Knowledge Base 同步文章到博客系统
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const KB_DIR = '/Users/james/git/obsidian/MrXie AI consulting/Knowledge_Base';
const BLOG_DIR = path.join(__dirname, '../src/content/blog');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

function generateSlug(filename, title) {
  // Try to extract date from filename first
  const dateMatch = filename.match(/^(\d{4}-\d{2}-\d{2})_/);
  if (dateMatch) {
    // Use date + simplified title
    const date = dateMatch[1];
    // For Chinese titles, use pinyin or just use the date
    // Since we can't easily convert Chinese to pinyin, let's use a different approach
    const cleanTitle = title
      .replace(/[《》]/g, '')
      .replace(/[：:]/g, '-')
      .substring(0, 30); // Limit length
    
    return `${date}-${cleanTitle}`;
  }
  
  // Fallback: use English-friendly slug
  return title
    .toLowerCase()
    .replace(/[\u4e00-\u9fa5]/g, '') // Remove Chinese characters
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .substring(0, 50);
}

function extractDateFromFilename(filename) {
  const match = filename.match(/^(\d{4}-\d{2}-\d{2})_/);
  return match ? match[1] : null;
}

function createFrontmatter(title, date, category, tags, description) {
  return `---
title:
  zh: "${title}"
  en: "${title}"
date: "${date}"
description:
  zh: "${description || 'AI 架构与工程实践深度解析'}"
  en: "${description || 'Deep dive into AI architecture and engineering practices'}"
category: "${category}"
tags: ${JSON.stringify(tags)}
draft: false
author: "James Xie"
---

`;
}

function syncArticle(filename) {
  const sourcePath = path.join(KB_DIR, filename);
  const content = fs.readFileSync(sourcePath, 'utf-8');
  
  // Extract metadata
  const title = extractTitle(content);
  const date = extractDateFromFilename(filename);
  
  if (!title) {
    log(`❌ ${filename}: 无法提取标题`, colors.red);
    return false;
  }
  
  if (!date) {
    log(`❌ ${filename}: 无法提取日期`, colors.red);
    return false;
  }
  
  // Generate slug
  const slug = generateSlug(filename, title);
  const targetFilename = `${slug}.md`;
  const targetPath = path.join(BLOG_DIR, targetFilename);
  
  // Check if already exists
  if (fs.existsSync(targetPath)) {
    log(`⚠️  ${filename}: 已存在 (${targetFilename})`, colors.yellow);
    return false;
  }
  
  // Determine category and tags based on content
  let category = 'AI Engineering';
  let tags = ['AI', 'Architecture'];
  let description = '';
  
  if (content.includes('第一篇') || content.includes('系列第一篇')) {
    category = 'AI Engineering';
    tags = ['AI', 'Software Engineering', 'Architecture', 'Best Practices'];
    description = '《大模型不是魔法》系列第一篇：证明经典软件工程原则在 AI 时代依然有效';
  } else if (content.includes('第二篇') || content.includes('系列第二篇')) {
    category = 'AI Architecture';
    tags = ['AI', 'LLM Gateway', 'Agent', 'Production', 'Cost Optimization'];
    description = '《大模型不是魔法》系列第二篇：从原则到模式，AI 系统的工程化落地实践';
  } else if (content.includes('第三篇') || content.includes('系列第三篇') || content.includes('终章')) {
    category = 'AI Architecture';
    tags = ['AI', 'Architecture', 'Evolution', 'Uncertainty', 'Design Patterns'];
    description = '《大模型不是魔法》系列第三篇：当基础设施成熟后，架构师的不可替代性在哪里';
  }
  
  // Create frontmatter
  const frontmatter = createFrontmatter(title, date, category, tags, description);
  
  // Remove the title line from content (already in frontmatter)
  const bodyContent = content.replace(/^#\s+.+$/m, '').trim();
  
  // Write to blog directory
  const fullContent = frontmatter + bodyContent;
  fs.writeFileSync(targetPath, fullContent, 'utf-8');
  
  log(`✅ ${filename} → ${targetFilename}`, colors.green);
  log(`   📅 日期: ${date}`, colors.cyan);
  log(`   📂 分类: ${category}`, colors.cyan);
  log(`   🏷️  标签: ${tags.join(', ')}`, colors.cyan);
  
  return true;
}

function main() {
  log('\n📝 Knowledge Base 文章同步工具', colors.cyan);
  log('=' .repeat(60), colors.cyan);
  
  // Get recent articles (last 7 days)
  const files = fs.readdirSync(KB_DIR)
    .filter(f => f.endsWith('.md') && !f.includes('WeChat') && !f.includes('_Archived'))
    .sort()
    .reverse();
  
  // Also check _Archived files from last week
  const archivedFiles = fs.readdirSync(KB_DIR)
    .filter(f => f.endsWith('_Archived.md'))
    .sort()
    .reverse();
  
  const allFiles = [...files, ...archivedFiles];
  
  log(`\n找到 ${allFiles.length} 篇文章\n`, colors.blue);
  
  let syncedCount = 0;
  
  allFiles.forEach(filename => {
    const sourcePath = path.join(KB_DIR, filename);
    const stats = fs.statSync(sourcePath);
    const modifiedTime = stats.mtime;
    
    // Only process files modified in the last 7 days
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    if (modifiedTime > sevenDaysAgo) {
      if (syncArticle(filename)) {
        syncedCount++;
      }
    }
  });
  
  log('\n' + '='.repeat(60), colors.cyan);
  log('📊 同步摘要', colors.cyan);
  log('=' .repeat(60), colors.cyan);
  log(`同步文章数: ${syncedCount}`, colors.blue);
  
  if (syncedCount > 0) {
    log('\n💡 提示:', colors.yellow);
    log('  运行以下命令提交更改:', colors.yellow);
    log(`  git add src/content/blog/*.md`, colors.cyan);
    log(`  git commit -m "feat: 同步 ${syncedCount} 篇 Knowledge Base 文章到博客"`, colors.cyan);
    log(`  git push`, colors.cyan);
  } else {
    log('\n✅ 没有需要同步的新文章', colors.green);
  }
  
  log('');
}

main();
