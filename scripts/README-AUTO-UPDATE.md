# Duyou.me 周报自动更新系统

## 📋 概述

本系统提供自动化的 AI 前沿情报和 GitHub 开源热点周报更新功能，支持定时执行和手动触发。

## 🚀 快速开始

### 1. 赋予脚本执行权限

```bash
cd /Users/james/git/duyou.me
chmod +x scripts/auto-update-feeds.sh
```

### 2. 测试运行（预览模式）

```bash
./scripts/auto-update-feeds.sh --dry-run
```

这将显示将要执行的操作，但不会实际提交更改。

### 3. 手动执行更新

```bash
# 更新所有内容
./scripts/auto-update-feeds.sh --both

# 仅更新 AI 情报
./scripts/auto-update-feeds.sh --ai-only

# 仅更新开源热点
./scripts/auto-update-feeds.sh --oss-only
```

## ⏰ 设置定时任务

macOS 提供了两种定时任务方式：**launchd**（推荐）和 **cron**。

### 方式一：使用 launchd（推荐）

#### 安装定时任务

```bash
# 1. 复制配置文件到 launchd 目录
cp scripts/com.duyoume.weekly-feed-updater.plist ~/Library/LaunchAgents/

# 2. 加载任务
launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# 3. 验证任务已加载
launchctl list | grep duyoume
```

#### 管理任务

```bash
# 查看任务状态
launchctl list | grep duyoume

# 立即执行一次（测试用）
launchctl start com.duyoume.weekly-feed-updater

# 停止任务
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# 重新启动任务
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# 完全删除任务
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
rm ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
```

#### 自定义执行时间

编辑 `com.duyoume.weekly-feed-updater.plist` 文件中的 `StartCalendarInterval` 部分：

```xml
<!-- 每周一上午 9:00 -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
    <key>Weekday</key>
    <integer>1</integer>  <!-- 1=周一, 7=周日 -->
</dict>
```

常用时间配置示例：

```xml
<!-- 每天凌晨 2:00 -->
<dict>
    <key>Hour</key>
    <integer>2</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>

<!-- 每周三和周日下午 8:00 -->
<array>
    <dict>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>3</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>7</integer>
    </dict>
</array>
```

### 方式二：使用 cron

#### 安装定时任务

```bash
# 1. 编辑 crontab.example，取消注释您需要的任务
vim scripts/crontab.example

# 2. 安装 crontab
crontab scripts/crontab.example

# 3. 验证任务已安装
crontab -l
```

#### 管理任务

```bash
# 查看当前任务
crontab -l

# 编辑任务
crontab -e

# 删除所有任务
crontab -r
```

## 📊 日志管理

### 查看日志

```bash
# 查看最新日志
tail -f /tmp/duyou-feeds-update.log

# 查看错误日志
tail -f /tmp/duyou-feeds-update-error.log

# 查看最近 50 行
tail -n 50 /tmp/duyou-feeds-update.log
```

### 清理旧日志

```bash
# 手动清理 7 天前的日志
find /tmp -name "duyou-*.log" -mtime +7 -delete

# 或添加到 crontab 自动清理（每周日凌晨）
0 0 * * 0 find /tmp -name "duyou-*.log" -mtime +7 -delete
```

## 🔧 故障排查

### 问题 1：脚本执行失败

```bash
# 1. 检查脚本权限
ls -l scripts/auto-update-feeds.sh

# 2. 重新赋予执行权限
chmod +x scripts/auto-update-feeds.sh

# 3. 检查依赖
./scripts/auto-update-feeds.sh --help
```

### 问题 2：GitHub Trending 抓取失败

```bash
# 1. 手动测试抓取脚本
cd "/Users/james/git/obsidian/MrXie GitHub Trending"
source venv/bin/activate
python scripts/scout.py
deactivate

# 2. 检查 Python 环境
which python
python --version

# 3. 检查虚拟环境
ls -la "/Users/james/git/obsidian/MrXie GitHub Trending"/venv/bin/activate
```

### 问题 3：Git 提交失败

```bash
# 1. 检查 Git 配置
git config user.name
git config user.email

# 2. 检查远程仓库
git remote -v

# 3. 手动测试提交流程
cd /Users/james/git/duyou.me
git status
git add -A
git commit -m "Test commit"
git push
```

### 问题 4：launchd 任务不执行

```bash
# 1. 检查任务是否加载
launchctl list | grep duyoume

# 2. 查看 launchd 日志
log show --predicate 'process == "launchd"' --last 1h | grep duyoume

# 3. 重新加载任务
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# 4. 检查 plist 文件语法
plutil -lint ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
```

## 📝 命令行选项

```bash
./scripts/auto-update-feeds.sh [选项]

选项：
  --ai-only      仅更新 AI 前沿情报
  --oss-only     仅更新开源热点
  --both         同时更新两者（默认）
  --dry-run      预览模式，不实际提交
  --help         显示帮助信息
```

## 🎯 最佳实践

### 1. 首次设置流程

```bash
# Step 1: 测试脚本
./scripts/auto-update-feeds.sh --dry-run

# Step 2: 手动执行一次
./scripts/auto-update-feeds.sh --both

# Step 3: 验证网站更新
open https://duyou.me

# Step 4: 设置定时任务（选择 launchd 或 cron）
cp scripts/com.duyoume.weekly-feed-updater.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# Step 5: 监控第一次自动执行
tail -f /tmp/duyou-feeds-update.log
```

### 2. 推荐的更新频率

- **AI 前沿情报**: 每天或每 2-3 天更新一次
- **开源热点**: 每周 1-2 次（周一和周四）
- **综合更新**: 每周一上午（适合周报节奏）

### 3. 监控建议

```bash
# 创建监控脚本
cat > ~/bin/check-duyoume-updates.sh << 'EOF'
#!/bin/bash
LOG_FILE="/tmp/duyou-feeds-update.log"
if [ -f "$LOG_FILE" ]; then
    LAST_UPDATE=$(tail -1 "$LOG_FILE" | grep -o "[0-9]\{4\}年[0-9]\{2\}月[0-9]\{2\}日")
    echo "最后更新: $LAST_UPDATE"
else
    echo "未找到日志文件"
fi
EOF

chmod +x ~/bin/check-duyoume-updates.sh

# 添加到每日提醒
echo "0 10 * * * ~/bin/check-duyoume-updates.sh" >> ~/.crontab.backup
```

## 🔐 安全注意事项

1. **不要将敏感信息硬编码在脚本中**
2. **定期检查日志文件**，确保没有泄露敏感信息
3. **使用 SSH key 认证**进行 Git 推送，避免密码暴露
4. **限制脚本权限**：`chmod 755 scripts/auto-update-feeds.sh`

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件：`/tmp/duyou-feeds-update.log`
2. 运行预览模式：`./scripts/auto-update-feeds.sh --dry-run`
3. 检查 README.md 中的更新流程说明
4. 查看项目 issues 或联系维护者

## 🔄 版本历史

- **v1.0.0** (2026-05-01): 初始版本
  - 支持 AI 情报和开源热点自动更新
  - 提供 launchd 和 cron 两种定时方式
  - 完整的日志记录和错误处理
  - 预览模式和灵活的选择性更新

---

**祝您使用愉快！** 🎉
