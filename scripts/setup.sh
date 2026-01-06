#!/bin/bash

# ============================================================
# IHDS Daily View Fetcher - 安装脚本
# ============================================================

set -e

# 获取项目根目录（scripts 的上一级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_FILE="com.ihds.dailyview.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "============================================================"
echo "IHDS Daily View Fetcher - 安装程序"
echo "============================================================"
echo ""
echo "📍 项目目录: $PROJECT_ROOT"
echo ""

# 1. 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip3 install -r "$PROJECT_ROOT/requirements.txt" --quiet
echo "   ✅ 依赖安装完成"
echo ""

# 2. 创建必要目录
echo "📁 创建目录结构..."
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/output/daily_views"
echo "   ✅ 目录创建完成"
echo ""

# 3. 设置脚本执行权限
echo "🔐 设置执行权限..."
chmod +x "$PROJECT_ROOT/main.py"
echo "   ✅ 权限设置完成"
echo ""

# 4. 配置定时任务
echo "📝 配置定时任务..."

# 创建 LaunchAgents 目录（如果不存在）
mkdir -p "$LAUNCH_AGENTS_DIR"

# 复制 plist 文件到 LaunchAgents
cp "$PROJECT_ROOT/config/$PLIST_FILE" "$LAUNCH_AGENTS_DIR/"
echo "   ✅ 配置文件已复制到 $LAUNCH_AGENTS_DIR"
echo ""

# 5. 加载定时任务
echo "⏰ 加载定时任务..."

# 先尝试卸载已存在的任务（忽略错误）
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_FILE" 2>/dev/null || true

# 加载新任务
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_FILE"
echo "   ✅ 定时任务已加载（每天早上 8:00 执行）"
echo ""

# 6. 测试运行
echo "============================================================"
echo "🧪 是否立即运行一次测试？(y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 正在运行测试..."
    python3 "$PROJECT_ROOT/main.py"
fi

echo ""
echo "============================================================"
echo "✨ 安装完成!"
echo "============================================================"
echo ""
echo "📋 使用说明:"
echo "   - 定时任务将每天早上 8:00 自动运行"
echo "   - 生成的文件保存在: $PROJECT_ROOT/output/daily_views/"
echo "   - 日志文件保存在: $PROJECT_ROOT/logs/"
echo ""
echo "🔧 管理命令:"
echo "   - 手动运行: python3 $PROJECT_ROOT/main.py"
echo "   - 查看任务状态: launchctl list | grep ihds"
echo "   - 停止任务: launchctl unload $LAUNCH_AGENTS_DIR/$PLIST_FILE"
echo "   - 启动任务: launchctl load $LAUNCH_AGENTS_DIR/$PLIST_FILE"
echo ""
