# 🚀 Duyou.me 周报自动更新系统 - 快速开始指南

## 📸 一分钟快速上手

### 方式一：使用安装向导（推荐新手）

```bash
cd /Users/james/git/duyou.me
./scripts/setup-auto-update.sh
```

这个交互式脚本会引导您完成所有设置步骤！

### 方式二：手动设置

#### Step 1: 测试运行

```bash
cd /Users/james/git/duyou.me
chmod +x scripts/auto-update-feeds.sh
./scripts/auto-update-feeds.sh --dry-run
```

#### Step 2: 执行更新

```bash
# 更新所有内容
./scripts/auto-update-feeds.sh --both

# 或仅更新 AI 情报
./scripts/auto-update-feeds.sh --ai-only

# 或仅更新开源热点
./scripts/auto-update-feeds.sh --oss-only
```

#### Step 3: 设置定时任务

**选项 A: launchd（macOS 推荐）**

```bash
# 一键安装
cp scripts/com.duyoume.weekly-feed-updater.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# 验证
launchctl list | grep duyoume
```

**选项 B: cron**

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每周一上午9点更新）
0 9 * * 1 cd /Users/james/git/duyou.me && ./scripts/auto-update-feeds.sh --both >> /tmp/duyou-feeds-update.log 2>&1
```

## 🎯 常用场景

### 场景 1: 我想每天自动更新

```bash
# 使用 launchd，编辑 plist 文件中的 StartCalendarInterval
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>2</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>

# 重新加载
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
```

### 场景 2: 我只想在周一更新

默认配置就是每周一上午 9 点，无需修改！

### 场景 3: 我想立即测试定时任务

```bash
# 使用 launchd
launchctl start com.duyoume.weekly-feed-updater

# 或使用脚本的预览模式
./scripts/auto-update-feeds.sh --dry-run
```

### 场景 4: 我想查看更新日志

```bash
# 实时查看
tail -f /tmp/duyou-feeds-update.log

# 查看最近 50 行
tail -n 50 /tmp/duyou-feeds-update.log

# 查看错误日志
tail -f /tmp/duyou-feeds-update-error.log
```

### 场景 5: 我想暂停自动更新

```bash
# launchd
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# cron
crontab -e
# 在任务行前加 # 注释掉
```

### 场景 6: 我想完全删除定时任务

```bash
# launchd
launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
rm ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist

# cron
crontab -r
```

## 🔍 故障排查速查表

| 问题 | 解决方案 |
|------|----------|
| 权限被拒绝 | `chmod +x scripts/auto-update-feeds.sh` |
| 找不到 Python | 检查虚拟环境路径是否正确 |
| Git 推送失败 | 检查网络连接和 SSH key |
| 任务不执行 | 检查 launchd/cron 状态和日志 |
| 日期未更新 | 确认脚本有写权限 |

## 📊 监控仪表板命令

```bash
# 创建监控别名（添加到 ~/.zshrc 或 ~/.bash_profile）
alias duyou-status='echo "=== Duyou.me 更新状态 ===" && tail -5 /tmp/duyou-feeds-update.log 2>/dev/null || echo "暂无日志"'
alias duyou-errors='tail -20 /tmp/duyou-feeds-update-error.log 2>/dev/null || echo "无错误"'
alias duyou-schedule='launchctl list | grep duyoume || echo "未找到定时任务"'

# 使用后
source ~/.zshrc

# 现在可以运行
duyou-status
duyou-errors
duyou-schedule
```

## 💡 高级技巧

### 技巧 1: 自定义更新时间

编辑 `com.duyoume.weekly-feed-updater.plist`，修改时间配置。

### 技巧 2: 邮件通知

在 crontab 顶部添加：
```
MAILTO=your-email@example.com
```

### 技巧 3: 多个时间表

launchd 支持数组形式的多个时间点：
```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key><integer>9</integer>
        <key>Minute</key><integer>0</integer>
        <key>Weekday</key><integer>1</integer>
    </dict>
    <dict>
        <key>Hour</key><integer>20</integer>
        <key>Minute</key><integer>0</integer>
        <key>Weekday</key><integer>4</integer>
    </dict>
</array>
```

### 技巧 4: 条件执行

修改脚本，添加条件判断：
```bash
# 仅在联网时执行
if ping -c 1 github.com &>/dev/null; then
    # 执行更新
else
    echo "网络不可用，跳过更新"
fi
```

## 🎓 学习资源

- **完整文档**: `cat scripts/README-AUTO-UPDATE.md`
- **launchd 手册**: `man launchd.plist`
- **cron 手册**: `man crontab`
- **项目 README**: `cat README.md`

---

**需要帮助？** 查看详细文档或联系维护者。
