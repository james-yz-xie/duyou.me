#!/bin/bash
# Duyou.me 定时任务一键安装/更新 - 只需运行这一条命令！
# 用法: ./scripts/install-schedule.sh

set -e

PLIST="com.duyoume.weekly-feed-updater.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST"

echo "🚀 正在安装/更新 Duyou.me 定时任务..."

# 卸载旧任务（如果存在）
launchctl unload "$DEST" 2>/dev/null || true

# 复制新配置
cp "scripts/$PLIST" "$DEST"

# 加载新任务
launchctl load "$DEST"

# 验证
if launchctl list | grep -q "com.duyoume"; then
    echo "✅ 安装成功！每天下午 1:00 自动更新周报"
    echo "📊 查看状态: launchctl list | grep duyoume"
    echo "📝 查看日志: tail -f /tmp/duyou-feeds-update.log"
else
    echo "❌ 安装失败，请检查错误信息"
    exit 1
fi
