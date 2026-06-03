#!/usr/bin/env node

/**
 * Resume Sync Script
 * Updates sync timestamp in resume page
 * Usage: npm run sync-resume
 */

const fs = require('fs');
const path = require('path');

// Paths
const WEBSITE_RESUME_PATH = path.join(__dirname, '../src/pages/resume.astro');

console.log('📄 Updating resume sync timestamp...\n');

// Check if file exists
if (!fs.existsSync(WEBSITE_RESUME_PATH)) {
  console.error(`❌ Resume page not found: ${WEBSITE_RESUME_PATH}`);
  process.exit(1);
}

// Read current template
let template = fs.readFileSync(WEBSITE_RESUME_PATH, 'utf-8');

// Update last modified date
const now = new Date();
const syncComment = `<!-- Last synced from Obsidian: ${now.toISOString()} -->`;

// Check if sync comment exists
if (template.includes('<!-- Last synced')) {
  template = template.replace(/<!-- Last synced[^>]*-->/, syncComment);
  console.log('✅ Updated existing sync timestamp');
} else {
  template = syncComment + '\n' + template;
  console.log('✅ Added new sync timestamp');
}

// Write back
fs.writeFileSync(WEBSITE_RESUME_PATH, template, 'utf-8');

console.log(`✨ Resume sync completed!`);
console.log(`📍 Updated: ${WEBSITE_RESUME_PATH}`);
console.log(`🕐 Sync time: ${now.toLocaleString()}\n`);
