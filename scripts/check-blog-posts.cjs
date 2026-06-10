#!/usr/bin/env node

/**
 * Blog Post Status Checker and Publisher
 * 检查所有博客文章的状态，确保元数据完整且已发布
 */

const fs = require('fs');
const path = require('path');

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

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  
  const frontmatter = {};
  const lines = match[1].split('\n');
  let currentKey = null;
  let currentValue = '';
  let isInMultiline = false;
  
  for (const line of lines) {
    // Check for key: value pattern
    const keyMatch = line.match(/^(\w+):\s*(.*)/);
    if (keyMatch && !isInMultiline) {
      // Save previous key-value pair
      if (currentKey) {
        frontmatter[currentKey] = currentValue.trim();
      }
      currentKey = keyMatch[1];
      currentValue = keyMatch[2];
      
      // Check if this is a multiline value (starts with | or >)
      if (currentValue === '|' || currentValue === '>') {
        isInMultiline = true;
        currentValue = '';
      }
    } else if (currentKey) {
      if (isInMultiline) {
        // For multiline values, check if we've reached the end
        if (line.match(/^\w+:/) && !line.startsWith('  ')) {
          // New top-level key found
          frontmatter[currentKey] = currentValue.trim();
          const keyMatch = line.match(/^(\w+):\s*(.*)/);
          currentKey = keyMatch[1];
          currentValue = keyMatch[2];
          isInMultiline = false;
        } else {
          currentValue += '\n' + line;
        }
      } else {
        currentValue += '\n' + line;
      }
    }
  }
  
  // Save last key-value pair
  if (currentKey) {
    frontmatter[currentKey] = currentValue.trim();
  }
  
  return frontmatter;
}

function checkArticle(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const frontmatter = parseFrontmatter(content);
  const filename = path.basename(filePath);
  
  const issues = [];
  const stats = {
    filename,
    hasFrontmatter: !!frontmatter,
    titleZh: false,
    titleEn: false,
    descriptionZh: false,
    descriptionEn: false,
    date: false,
    category: false,
    tags: false,
    draft: false,
    author: false,
    wordCount: 0,
  };
  
  if (!frontmatter) {
    issues.push('❌ 缺少 Frontmatter');
    return { stats, issues, valid: false };
  }
  
  // Check title
  if (frontmatter.title) {
    // Title can be a multiline YAML object with zh and en keys
    const titleLines = frontmatter.title.split('\n');
    titleLines.forEach(line => {
      const zhMatch = line.match(/zh:\s*["'](.+)["']/);
      const enMatch = line.match(/en:\s*["'](.+)["']/);
      if (zhMatch) stats.titleZh = true;
      if (enMatch) stats.titleEn = true;
    });
    
    if (!stats.titleZh) issues.push('⚠️  缺少中文标题');
    if (!stats.titleEn) issues.push('⚠️  缺少英文标题');
  } else {
    issues.push('❌ 缺少标题');
  }
  
  // Check description
  if (frontmatter.description) {
    const descLines = frontmatter.description.split('\n');
    descLines.forEach(line => {
      const zhMatch = line.match(/zh:\s*["'](.+)["']/);
      const enMatch = line.match(/en:\s*["'](.+)["']/);
      if (zhMatch) stats.descriptionZh = true;
      if (enMatch) stats.descriptionEn = true;
    });
    
    if (!stats.descriptionZh) issues.push('⚠️  缺少中文描述');
    if (!stats.descriptionEn) issues.push('⚠️  缺少英文描述');
  } else {
    issues.push('⚠️  缺少描述');
  }
  
  // Check date
  if (frontmatter.date) {
    stats.date = true;
  } else {
    issues.push('❌ 缺少日期');
  }
  
  // Check category
  if (frontmatter.category) {
    stats.category = true;
  } else {
    issues.push('⚠️  缺少分类');
  }
  
  // Check tags
  if (frontmatter.tags) {
    stats.tags = true;
  } else {
    issues.push('⚠️  缺少标签');
  }
  
  // Check draft status
  if (frontmatter.draft !== undefined) {
    stats.draft = frontmatter.draft === 'false' || frontmatter.draft === false;
  } else {
    issues.push('⚠️  未设置 draft 状态');
  }
  
  // Check author
  if (frontmatter.author) {
    stats.author = true;
  } else {
    issues.push('⚠️  缺少作者');
  }
  
  // Count words (rough estimate)
  const bodyContent = content.replace(/^---[\s\S]*?---/, '').trim();
  stats.wordCount = bodyContent.length;
  
  return { stats, issues, valid: issues.length === 0 };
}

function main() {
  log('\n📝 博客文章状态检查器', colors.cyan);
  log('=' .repeat(60), colors.cyan);
  
  const files = fs.readdirSync(BLOG_DIR)
    .filter(f => f.endsWith('.md'))
    .sort();
  
  log(`\n找到 ${files.length} 篇博客文章\n`, colors.blue);
  
  const results = {
    total: files.length,
    valid: 0,
    invalid: 0,
    published: 0,
    draft: 0,
    issues: []
  };
  
  files.forEach((file, index) => {
    const filePath = path.join(BLOG_DIR, file);
    const { stats, issues, valid } = checkArticle(filePath);
    
    const statusIcon = valid ? '✅' : '❌';
    const publishStatus = stats.draft ? '📤 已发布' : '📝 草稿';
    
    log(`${index + 1}. ${statusIcon} ${file}`, valid ? colors.green : colors.red);
    log(`   ${publishStatus} | 字数: ${stats.wordCount.toLocaleString()}`, colors.yellow);
    
    if (stats.date) {
      // Extract date from frontmatter
      const content = fs.readFileSync(filePath, 'utf-8');
      const dateMatch = content.match(/date:\s*["']([^"']+)["']/);
      if (dateMatch) {
        log(`   📅 日期: ${dateMatch[1]}`, colors.cyan);
      }
    }
    
    if (issues.length > 0) {
      log(`   问题:`, colors.red);
      issues.forEach(issue => log(`     ${issue}`, colors.red));
      results.issues.push({ file, issues });
      results.invalid++;
    } else {
      results.valid++;
    }
    
    if (stats.draft) {
      results.published++;
    } else {
      results.draft++;
    }
    
    console.log('');
  });
  
  // Summary
  log('\n' + '='.repeat(60), colors.cyan);
  log('📊 统计摘要', colors.cyan);
  log('=' .repeat(60), colors.cyan);
  log(`总文章数: ${results.total}`, colors.blue);
  log(`✅ 有效文章: ${results.valid}`, colors.green);
  log(`❌ 有问题文章: ${results.invalid}`, colors.red);
  log(`📤 已发布: ${results.published}`, colors.green);
  log(`📝 草稿: ${results.draft}`, colors.yellow);
  
  if (results.issues.length > 0) {
    log('\n⚠️  需要修复的文章:', colors.red);
    results.issues.forEach(({ file, issues }) => {
      log(`  • ${file}:`, colors.red);
      issues.forEach(issue => log(`    ${issue}`, colors.red));
    });
  } else {
    log('\n🎉 所有文章状态良好！', colors.green);
  }
  
  log('');
}

main();
