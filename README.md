# IHDS Daily View Fetcher

> 每天自动抓取 [IHDS Daily View](https://ihdschool.com/the-daily-view) 内容，生成中英文双语 Markdown 文件。

## ✨ 功能特点

- 🌐 自动抓取 IHDS 每日视图网页内容
- 📷 下载 Gate 图片和 Rave Mandala 到本地
- 🤖 使用 DeepSeek API 自动翻译成繁体中文
- 📝 生成美观的双语 Markdown 文件
- ⏰ 支持 macOS LaunchAgent 定时任务

## 📁 项目结构

```
ihds/
├── src/                           # 源代码
│   ├── __init__.py
│   └── ihds/
│       ├── __init__.py            # 模块入口
│       └── fetcher.py             # 核心抓取逻辑
├── scripts/                       # 脚本
│   ├── setup.sh                   # 安装定时任务
│   └── uninstall.sh               # 卸载定时任务
├── config/                        # 配置文件
│   └── com.ihds.dailyview.plist   # macOS LaunchAgent 配置
├── output/                        # 输出目录
│   └── daily_views/
│       ├── 2026-01-06-54.1/       # 按日期-Gate.Line 组织
│       │   ├── daily_view_2026-01-06_en.md
│       │   ├── daily_view_2026-01-06_zh.md
│       │   └── images/
│       ├── latest_en.md           # 最新英文版
│       └── latest_zh.md           # 最新中文版
├── logs/                          # 日志目录
├── main.py                        # 程序入口
├── requirements.txt               # Python 依赖
├── .gitignore                     # Git 忽略规则
└── README.md                      # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 运行程序

```bash
python3 main.py
```

### 3. 安装定时任务（每天早上 8 点自动运行）

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## ⚙️ 配置说明

### DeepSeek API Key

程序默认使用内置的 API Key。如需更换：

```bash
# 方式一：命令行参数
python3 main.py --api-key YOUR_API_KEY

# 方式二：环境变量
export DEEPSEEK_API_KEY=YOUR_API_KEY
python3 main.py
```

### 自定义输出目录

```bash
python3 main.py --output-dir /path/to/output
```

## 📋 定时任务管理

```bash
# 查看任务状态
launchctl list | grep ihds

# 启动任务
launchctl load ~/Library/LaunchAgents/com.ihds.dailyview.plist

# 停止任务
launchctl unload ~/Library/LaunchAgents/com.ihds.dailyview.plist

# 卸载定时任务
./scripts/uninstall.sh
```

## 📄 输出文件说明

每天生成的 Markdown 文件保存在独立的日期目录中，命名格式：
- 目录：`YYYY-MM-DD-{Gate}.{Line}` (例如: `2026-01-06-54.1`)
- 文件：`daily_view_YYYY-MM-DD_{lang}.md`

包含内容：
- 📅 日期信息
- 🖼️ Gate 图片
- 📖 Gate 标题、副标题和描述
- ✨ Cross 信息
- 🌙 Line 详细信息（Exaltation / Detriment）
- 🔮 Rave Mandala 图

## 🔧 技术栈

- Python 3.8+
- requests - HTTP 请求
- beautifulsoup4 - HTML 解析
- DeepSeek API - 翻译服务

## 📜 许可

仅供个人学习使用。内容版权归 IHDS 所有。
