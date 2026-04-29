#!/bin/bash
# AI Arena 擂台赛 — 一键启动

echo "🥊 AI Arena 擂台赛"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查 LM Studio
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
  echo "✅ LM Studio 已连接"
else
  echo "⚠️  LM Studio 未连接"
  echo ""
  echo "请先启动 LM Studio："
  echo "  1. 下载 https://lmstudio.ai"
  echo "  2. 加载一个模型"
  echo "  3. 点击右上角 🟢 Local Server"
  echo "  4. 确认运行在 localhost:1234"
  echo ""
  echo "按回车继续（跳过 LM Studio 检查）..."
  read
fi

echo ""
echo "启动中..."
echo ""

# 同时启动 Astro 和 Arena 服务器
npm run dev:arena
