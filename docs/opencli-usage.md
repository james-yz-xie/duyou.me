# 🚀 OpenCLI 使用大全：从入门到精通

OpenCLI 的核心理念是 **"让任何网站都成为你的 CLI"**。它能够复用 Chrome 浏览器的登录状态，无需复杂的 API Key 配置，通过 AI 驱动的自动化技术实现高效的数据抓取和交互。

---

## 1. 快速开始

### 安装
```bash
# 全局安装（推荐）
npm install -g @jackwener/opencli

# 检查安装是否成功
opencli list
```

### 环境要求
1. **Chrome 浏览器**：确保浏览器已登录目标网站。
2. **OpenCLI 扩展**：在 Chrome 中加载 `opencli-browser-bridge` 扩展（开发者模式加载解压后的插件）。
3. **保持运行**：执行命令时，OpenCLI 会自动与后台扩展通信，无需手动启动 Daemon。

---

## 2. 核心使用模式

通用语法：`opencli <站点> <命令> [参数] [选项]`

*   **格式控制**：`-f` 或 `--format` 支持 `table` (默认), `json`, `yaml`, `md`, `csv`。
*   **数量限制**：`--limit N` 限制返回条数。
*   **静默/详细模式**：`-v` 查看详细日志。

---

## 3. 热门工具使用指南与实例

### 🔍 搜索与学术研究
| 工具 | 常用命令 | 例子 |
| :--- | :--- | :--- |
| **Google** | `search`, `news` | `opencli google search "DeepSeek-V3"` |
| **arXiv** | `search`, `paper` | `opencli arxiv search "LLM agents" --limit 5` |
| **Wikipedia** | `search`, `summary` | `opencli wikipedia summary "OpenAI"` |
| **Google Scholar** | `search` | `opencli google-scholar search "Transformer architecture"` |

### 📱 社交媒体交互
| 工具 | 常用命令 | 例子 |
| :--- | :--- | :--- |
| **Twitter/X** | `trending`, `post`, `search` | `opencli twitter post "Hello from OpenCLI!"` |
| **Reddit** | `hot`, `subreddit`, `read` | `opencli reddit hot --subreddit programming` |
| **Instagram** | `profile`, `followers` | `opencli instagram profile elonmusk` |
| **微博** | `hot`, `search`, `post` | `opencli weibo hot` (查看热搜) |

### 📺 视频与内容社区
| 工具 | 常用命令 | 例子 |
| :--- | :--- | :--- |
| **Bilibili** | `hot`, `search`, `subtitle` | `opencli bilibili subtitle --bvid BV1xxx` (下字幕) |
| **YouTube** | `search`, `transcript` | `opencli youtube transcript "视频链接" --lang zh-Hans` |
| **小红书** | `search`, `note`, `download` | `opencli xiaohongshu download "笔记链接"` |
| **豆瓣** | `search`, `top250`, `movie-hot` | `opencli douban movie-hot` |

### 🤖 AI 助手 (对话与研究)
| 工具 | 常用命令 | 例子 |
| :--- | :--- | :--- |
| **ChatGPT** | `ask`, `new`, `model` | `opencli chatgpt ask "解释量子纠缠"` |
| **Gemini** | `ask`, `deep-research` | `opencli gemini deep-research "2024 AI 趋势"` |
| **NotebookLM** | `list`, `open`, `summary` | `opencli notebooklm summary` (对当前笔记本做总结) |
| **豆包** | `ask`, `history` | `opencli doubao ask "帮我写一段 Rust 代码"` |

### 📝 通用网页采集 (神器)
*   **任意网页转 Markdown**：
    ```bash
    opencli web read --url "https://example.com/article" --output ./docs/
    ```
*   **微信公众号下载**：
    ```bash
    opencli weixin download --url "微信文章链接"
    ```

---

## 4. 桌面应用操控 (Cursor/Notion)

OpenCLI 支持通过 CDP 协议操控基于 Electron 的桌面应用。

*   **Cursor**：
    ```bash
    opencli cursor ask "给这段代码加单元测试"
    opencli cursor export  # 导出当前聊天记录为 Markdown
    ```
*   **Notion**：
    ```bash
    opencli notion search "会议纪要"
    opencli notion write "今天天气不错" # 追加内容到当前页面
    ```
*   **Discord**：
    ```bash
    opencli discord-app send "Hello Team!"
    ```

---

## 5. 高级技巧：多标签管理

当你需要同时操作多个页面时，可以使用 **Tab Targeting**：

1.  **获取 Tab ID**：`opencli browser tab list`
2.  **指定 Tab 执行**：
    ```bash
    # 在特定的页面执行点击
    opencli browser click 3 --tab <TargetID>
    ```
3.  **切换默认 Tab**：`opencli browser tab select <TargetID>`

---

## 6. 管理与维护

*   **诊断连接**：`opencli doctor` (检查浏览器插件是否连接成功)。
*   **查看所有工具**：`opencli list`。
*   **自动修复**：如果某个网站改版导致命令失效，运行 `OPENCLI_DIAGNOSTIC=1 opencli <原命令>`，系统会尝试自动诊断并修复适配器。

---

**💡 小贴士**：
*   执行 `🌐 Browser` 类命令前，请确保 Chrome 是**可见**的（不要最小化到托盘，但可以放在后台）。
*   利用 `-f json` 配合 `jq` 工具，可以轻松地将 OpenCLI 集成到你的自动化脚本中。
