#!/bin/bash

# ============================================================
# IHDS Daily View Fetcher - 卸载脚本
# ============================================================

PLIST_FILE="com.ihds.dailyview.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "============================================================"
echo "IHDS Daily View Fetcher - 卸载程序"
echo "============================================================"
echo ""

# 1. 停止并卸载定时任务
echo "⏹️  停止定时任务..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_FILE" 2>/dev/null || true
echo "   ✅ 定时任务已停止"

# 2. 删除 plist 文件
echo "🗑️  删除配置文件..."
rm -f "$LAUNCH_AGENTS_DIR/$PLIST_FILE"
echo "   ✅ 配置文件已删除"

echo ""
echo "============================================================"
echo "✨ 卸载完成!"
echo "============================================================"
echo ""
echo "注意: 脚本文件和生成的内容未被删除，如需删除请手动处理。"
echo ""

