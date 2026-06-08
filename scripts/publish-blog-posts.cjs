#!/usr/bin/env node

/**
 * Blog Post Publisher
 * 自动检测并发布新的博客文章
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BLOG_DIR = path.join(__dirname, '../src/content/blog');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
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
    const keyMatch = line.match(/^(\w+):\s*(.*)/);
    if (keyMatch && !isInMultiline) {
      if (currentKey) {
        frontmatter[currentKey] = currentValue.trim();
      }
      currentKey = keyMatch[1];
      currentValue = keyMatch[2];
      
      if (currentValue === '|' || currentValue === '>') {
        isInMultiline = true;
        currentValue = '';
      }
    } else if (currentKey) {
      if (isInMultiline) {
        if (line.match(/^\w+:/) && !line.startsWith('  ')) {
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
  
  if (currentKey) {
    frontmatter[currentKey] = currentValue.trim();
  }
  
  return frontmatter;
}

function checkArticle(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const frontmatter = parseFrontmatter(content);
  
  if (!frontmatter) {
    return { valid: false, issues: ['❌ 缺少 Frontmatter'], published: false };
  }
  
  const issues = [];
  
  // Check required fields
  if (!frontmatter.title) issues.push('❌ 缺少标题');
  if (!frontmatter.date) issues.push('❌ 缺少日期');
  if (!frontmatter.description) issues.push('⚠️  缺少描述');
  if (!frontmatter.category) issues.push('⚠️  缺少分类');
  if (!frontmatter.tags) issues.push('⚠️  缺少标签');
  if (!frontmatter.author) issues.push('⚠️  缺少作者');
  
  // Check draft status
  const isPublished = frontmatter.draft === 'false' || frontmatter.draft === false;
  
  return { 
    valid: issues.length === 0, 
    issues, 
    published: isPublished,
    frontmatter 
  };
}

function getGitStatus() {
  try {
    const output = execSync('git status --porcelain', { cwd: path.join(__dirname, '..'), encoding: 'utf-8' });
    return output.trim().split('\n').filter(line => line.includes('src/content/blog/'));
  } catch (error) {
    return [];
  }
}

function getNewFiles() {
  const gitStatus = getGitStatus();
  const newFiles = [];
  
  gitStatus.forEach(line => {
    if (line.startsWith('??')) {
      const filePath = line.substring(3).trim();
      if (filePath.startsWith('src/content/blog/') && filePath.endsWith('.md')) {
        newFiles.push(filePath);
      }
    }
  });
  
  return newFiles;
}

function getModifiedFiles() {
  const gitStatus = getGitStatus();
  const modifiedFiles = [];
  
  gitStatus.forEach(line => {
    if (line.startsWith(' M') || line.startsWith('M ')) {
      const filePath = line.substring(2).trim();
      if (filePath.startsWith('src/content/blog/') && filePath.endsWith('.md')) {
        modifiedFiles.push(filePath);
      }
    }
  });
  
  return modifiedFiles;
}

function addDraftField(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Check if draft field already exists
  if (content.includes('draft:')) {
    return false;
  }
  
  // Add draft: false before the closing ---
  const updatedContent = content.replace(/^(---)$/m, 'draft: false\n$1');
  fs.writeFileSync(filePath, updatedContent, 'utf-8');
  
  return true;
}

function main() {
  log('\n📝 博客文章发布助手', colors.cyan);
  log('=' .repeat(60), colors.cyan);
  
  // Check for new files
  const newFiles = getNewFiles();
  const modifiedFiles = getModifiedFiles();
  
  if (newFiles.length === 0 && modifiedFiles.length === 0) {
    log('\n✅ 没有检测到新的或修改的博客文章', colors.green);
    log('');
    return;
  }
  
  // Process new files
  if (newFiles.length > 0) {
    log(`\n🆕 发现 ${newFiles.length} 篇新文章:`, colors.magenta);
    
    newFiles.forEach(file => {
      const filePath = path.join(__dirname, '..', file);
      const { valid, issues, published, frontmatter } = checkArticle(filePath);
      
      log(`\n  📄 ${path.basename(file)}`, colors.blue);
      
      if (!valid) {
        log(`  ❌ 验证失败:`, colors.red);
        issues.forEach(issue => log(`     ${issue}`, colors.red));
        return;
      }
      
      if (!published) {
        log(`  📤 准备发布...`, colors.yellow);
        
        // Add draft: false
        const added = addDraftField(filePath);
        if (added) {
          log(`  ✅ 已添加 draft: false`, colors.green);
        }
        
        // Stage the file
        try {
          execSync(`git add "${file}"`, { cwd: path.join(__dirname, '..') });
          log(`  ✅ 已添加到 git`, colors.green);
        } catch (error) {
          log(`  ❌ Git 添加失败: ${error.message}`, colors.red);
        }
      } else {
        log(`  ✅ 已经是发布状态`, colors.green);
      }
    });
  }
  
  // Process modified files
  if (modifiedFiles.length > 0) {
    log(`\n✏️  发现 ${modifiedFiles.length} 篇修改的文章:`, colors.magenta);
    
    modifiedFiles.forEach(file => {
      const filePath = path.join(__dirname, '..', file);
      const { valid, issues, published } = checkArticle(filePath);
      
      log(`\n  📄 ${path.basename(file)}`, colors.blue);
      
      if (!valid) {
        log(`  ⚠️  验证问题:`, colors.yellow);
        issues.forEach(issue => log(`     ${issue}`, colors.yellow));
      } else {
        log(`  ✅ 验证通过`, colors.green);
      }
      
      if (!published) {
        log(`  📤 准备发布...`, colors.yellow);
        const added = addDraftField(filePath);
        if (added) {
          log(`  ✅ 已添加 draft: false`, colors.green);
          try {
            execSync(`git add "${file}"`, { cwd: path.join(__dirname, '..') });
            log(`  ✅ 已添加到 git`, colors.green);
          } catch (error) {
            log(`  ❌ Git 添加失败: ${error.message}`, colors.red);
          }
        }
      }
    });
  }
  
  // Summary
  log('\n' + '='.repeat(60), colors.cyan);
  log('📊 操作摘要', colors.cyan);
  log('=' .repeat(60), colors.cyan);
  log(`新文章: ${newFiles.length}`, colors.blue);
  log(`修改文章: ${modifiedFiles.length}`, colors.blue);
  
  if (newFiles.length > 0 || modifiedFiles.length > 0) {
    log('\n💡 提示:', colors.yellow);
    log('  运行以下命令提交更改:', colors.yellow);
    log(`  git commit -m "feat: 发布 ${newFiles.length + modifiedFiles.length} 篇博客文章"`, colors.cyan);
    log(`  git push`, colors.cyan);
  }
  
  log('');
}

main();
