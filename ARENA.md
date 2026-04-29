# 🥊 AI Arena — AI 擂台赛

在 duyou.me 上实时对比两个 AI 模型的回答。

## 快速开始

### 1. 启动 LM Studio

1. 下载安装 [LM Studio](https://lmstudio.ai)
2. 加载你喜欢的模型
3. 点击右上角 **🟢 Local Server** 启动本地 API 服务
4. 确认运行在 `localhost:1234`

### 2. 启动项目

```bash
cd /Users/james/git/duyou.me

# 安装依赖
npm install

# 同时启动 Astro + Arena 服务器
npm run dev:arena
```

访问 http://localhost:4321/arena

### 3. 开始擂台赛

1. 选择两个模型（A 和 B）
2. 输入问题
3. 点击 **开始擂台赛** 🥊
4. 两个模型并行回答，实时流式输出

## 架构

```
用户浏览器
    │
    ▼
Astro 页面 (/arena)
    │
    ▼
Arena Server (:3456) ──→ LM Studio (:1234)
    │                              │
    │  SSE 流式返回               │  API 请求
    │         ┌──────────────────┘
    ▼         ▼
模型 A 回答  模型 B 回答
```

## 技术细节

- **后端**: Hono + Node Server（独立进程）
- **前端**: Astro + 内联 JS
- **流式**: SSE (Server-Sent Events)
- **请求**: 并行发送，同时等待两个模型

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LM_STUDIO_URL` | `http://localhost:1234` | LM Studio API 地址 |
| `PORT` | `3456` | Arena 服务器端口 |

## 常见问题

### LM Studio 未连接？
- 确认 LM Studio 已启动
- 确认 Local Server 已开启（右上角 🟢）
- 确认端口是 1234

### 模型加载失败？
- 在 LM Studio 中加载一个模型
- 刷新页面自动检测

## 未来扩展

- [ ] 多模型对比（3+）
- [ ] 历史记录
- [ ] 评分/投票
- [ ] 云端 API 混合对比
- [ ] 对话模式（多轮）
