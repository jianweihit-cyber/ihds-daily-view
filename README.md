# IHDS Daily View Fetcher

> 每天自动抓取 [IHDS Daily View](https://ihdschool.com/the-daily-view) 内容，生成中英文双语 Markdown 文件。

## ✨ 功能特点

- 🌐 自动抓取 IHDS 每日视图网页内容
- 📷 下载 Gate 图片和 Rave Mandala 到本地
- 🤖 使用 DeepSeek API 自动翻译成繁体中文
- 📝 生成美观的双语 Markdown 文件
- 🎨 自动生成 AI 绘图提示词（用于 Leonardo.AI / Midjourney）
- ⏰ 支持 macOS LaunchAgent 定时任务
- 🚀 支持 GitHub Actions 自动运行 + 邮件通知

## 📁 项目结构

```
ihds/
├── src/                              # 源代码
│   └── ihds/
│       ├── __init__.py               # 模块入口
│       ├── fetcher.py                # 核心抓取逻辑
│       └── image_generator.py        # Leonardo.AI 集成（备用）
├── scripts/                          # 脚本
│   ├── setup.sh                      # 安装本地定时任务
│   └── uninstall.sh                  # 卸载定时任务
├── config/                           # 配置文件
│   └── com.ihds.dailyview.plist      # macOS LaunchAgent 配置
├── .github/workflows/                # GitHub Actions
│   └── daily_view.yml                # 自动抓取工作流
├── output/                           # 输出目录
│   ├── Gate_Rave_Mandala_Collection/ # 64个闘门图片收藏
│   └── daily_views/
│       ├── 2026-01-10-54.6/          # 按日期-Gate.Line 组织
│       │   ├── daily_view_xxx_en.md
│       │   ├── daily_view_xxx_zh.md
│       │   └── ai_prompt_xxx.txt     # AI 绘图提示词
│       ├── latest_en.md
│       ├── latest_zh.md
│       └── latest_ai_prompt.txt
├── logs/                             # 日志目录
├── main.py                           # 程序入口
├── requirements.txt                  # Python 依赖
└── README.md
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

### 3. 设置自动运行

**方式 A：macOS 本地定时任务**
```bash
./scripts/setup.sh
```

**方式 B：GitHub Actions（推荐）**
见下方 [GitHub Actions 配置](#-github-actions-自动运行)

## ☁️ GitHub Actions 自动运行

### 功能
- ⏰ 每天北京时间 8:00 自动运行
- 📥 自动抓取并提交到仓库
- 📧 完成后发送邮件通知
- 🔄 支持手动触发

### 配置步骤

1. **推送代码到 GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/ihds.git
   git push -u origin main
   ```

2. **设置 Secrets**（仓库 Settings → Secrets and variables → Actions）

   | Secret 名称 | 说明 | 示例 |
   |-------------|------|------|
   | `DEEPSEEK_API_KEY` | DeepSeek 翻译 API Key | `sk-xxx...` |
   | `EMAIL_USERNAME` | Gmail 邮箱地址 | `your@gmail.com` |
   | `EMAIL_PASSWORD` | Gmail 应用专用密码 | `xxxx xxxx xxxx xxxx` |
   | `EMAIL_TO` | 接收通知的邮箱 | `your@email.com` |

3. **获取 Gmail 应用专用密码**
   - 访问 https://myaccount.google.com/apppasswords
   - 创建新的应用专用密码
   - 复制 16 位密码（格式：`xxxx xxxx xxxx xxxx`）

4. **启用 GitHub Actions**
   - 仓库 → Actions → 允许运行工作流

5. **手动测试**
   - Actions → IHDS Daily View Fetcher → Run workflow

## ⚙️ 配置说明

### DeepSeek API Key

```bash
# 命令行参数
python3 main.py --api-key YOUR_API_KEY

# 环境变量
export DEEPSEEK_API_KEY=YOUR_API_KEY
python3 main.py
```

### 生成 AI 绘图海报（需要 Leonardo API）

```bash
# 使用 Leonardo.AI 自动生成海报
python3 main.py --generate-image --leonardo-key YOUR_KEY
```

## 📋 本地定时任务管理

```bash
# 查看任务状态
launchctl list | grep ihds

# 启动/停止任务
launchctl load ~/Library/LaunchAgents/com.ihds.dailyview.plist
launchctl unload ~/Library/LaunchAgents/com.ihds.dailyview.plist

# 卸载
./scripts/uninstall.sh
```

## 📄 输出文件说明

每天生成的文件：

| 文件 | 说明 |
|------|------|
| `daily_view_xxx_en.md` | 英文版 Markdown |
| `daily_view_xxx_zh.md` | 繁体中文版 Markdown |
| `ai_prompt_xxx.txt` | AI 绘图提示词（用于手动生成海报） |

目录命名格式：`YYYY-MM-DD-{Gate}.{Line}`（例如：`2026-01-10-54.6`）

## 🎨 AI 绘图使用

每天自动生成 `ai_prompt_xxx.txt` 文件，包含：
- 英文提示词（可直接复制到 Leonardo.AI / Midjourney）
- 负面提示词
- 推荐设置
- 参考图片路径

## 🔧 技术栈

- Python 3.8+
- requests - HTTP 请求
- beautifulsoup4 - HTML 解析
- DeepSeek API - 翻译服务
- GitHub Actions - 自动化运行

## 📜 许可

仅供个人学习使用。内容版权归 IHDS 所有。
