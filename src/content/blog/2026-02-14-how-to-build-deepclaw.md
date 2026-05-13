---
title:
  zh: "手把手教你部署 Deep-Claw：0成本打造你的本地'视觉打工人'"
  en: "Step-by-Step Guide to Deploying Deep-Claw: Build Your Local 'Vision Worker' at Zero Cost"
description:
  zh: "保姆级教程，带你从环境配置到模型部署，用 DeepSeek Janus-Pro 打造一个能看懂屏幕、自动执行任务的本地 AI 助手。"
  en: "A comprehensive tutorial guiding you from environment setup to model deployment, using DeepSeek Janus-Pro to build a local AI assistant that can understand screens and execute tasks automatically."
date: "2026-02-14"
category: "Practical Guide"
tags: ["DeepSeek", "Janus-Pro", "LocalAI", "Python", "Automation", "Tutorial"]
draft: false
author: "James Xie"
---

# 手把手教你部署 Deep-Claw：0成本打造你的本地“视觉打工人”

> 📌 **前言**: 昨天我们发布了“视觉智能体”的概念，后台被私信轰炸了。
> “DeepSeek 怎么连屏幕？”
> “Janus 是什么？”
> “不会写代码能不能用？”
> 别急。今天不谈虚的，直接上**工程级干货**。这是一篇完全可以在你周末花 2 小时复现的 Technical Guide。

---

## 🛠️ 准备工作：你的军火库

要打造 **Deep-Claw (深爪)**，你需要一台像样的电脑（建议 NVIDIA 显卡，显存 12G+ 体验最佳）。

**核心组件 (三大件)**:
1.  **大脑**: `DeepSeek-R1-Distill-Qwen-7B` (负责逻辑推理，轻量级)
2.  **眼睛**: `deepseek-ai/Janus-Pro-7B` (负责看懂屏幕)
3.  **手**: `Python + PyAutoGUI` (负责点击鼠标)

**为什么不用 GPT-4o？**
因为我们要做的是**完全本地化 (Local-First)**。
你的财务报表、你的内部系统截图，**一张都不会传到云端**。这是企业级安全的基本底线。

---

## 🚀 第一步：给电脑装上“眼睛” (部署 Janus-Pro)

DeepSeek 团队开源的 **Janus-Pro** 是目前最强的开源多模态模型之一。它不仅能看图，还能精准给出物体的坐标（这很关键，因为我们要点那一像素）。

**1. 安装环境**
```bash
# 建议使用 conda 隔离环境
conda create -n deepclaw python=3.10
conda activate deepclaw
pip install torch transformers pyautogui pillow
```

**2. 加载模型 (Python)**
新建一个 `vision_engine.py`:
```python
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

# 自动下载模型 (约 15GB，建议挂梯子或用 HF 镜像)
model_path = "deepseek-ai/Janus-Pro-7B"
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
model = model.to(torch.bfloat16).cuda().eval()

def see_screen(image_path, prompt):
    # 这里省略了复杂的 Tensor 处理代码，完整版见文末 GitHub 链接
    inputs = processor(text=prompt, images=image, return_tensors="pt").to("cuda")
    # ... 模型推理 ...
    return coordinates # 返回 [x, y]
```

---

## 🧠 第二步：连接“大脑” (Ollama + DeepSeek-R1)

这一步最简单。我们直接用 Ollama 运行 R1。

1.  下载 [Ollama](https://ollama.com).
2.  在终端运行:
    ```bash
    ollama run deepseek-r1:7b
    ```
    (对，稍微小一点的模型反应更快，适合做快速决策)

---

## ⚡️ 第三步：缝合！(Deep-Claw 主程序)

现在，我们要写一个 `agent.py` 把它们串起来。这就是所谓的 **"The Loop"**。

```python
import pyautogui
import requests
import time
from vision_engine import see_screen

def capture_screen():
    path = "current_screen.png"
    pyautogui.screenshot(path)
    return path

def ask_brain(context):
    # 调用本地 Ollama 接口
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": "deepseek-r1:7b",
        "prompt": f"Based on this screen state: {context}, what is the next step? Return JSON.",
        "stream": False
    })
    return response.json()['response']

# --- 主循环 ---
print("Deep-Claw 启动中... (按 Ctrl+C 终止)")
TASK = "把桌面上的 'Invoice.pdf' 移动到 'Done' 文件夹"

while True:
    # 1. 看 (Observe)
    screen = capture_screen()
    
    # 2. 找 (Locate)
    # 先让 Janus 帮我们找核心元素
    ocr_result = see_screen(screen, "Detect file icons and folder names")
    
    # 3. 想 (Decide)
    # 把视觉结果喂给 R1
    plan = ask_brain(f"Goal: {TASK}. Current Layout: {ocr_result}")
    # R1 可能会返回: {"action": "drag", "target": "Invoice.pdf", "destination": "Done"}
    
    # 4. 动 (Act)
    if "drag" in plan:
        # 获取具体坐标
        start_pos = see_screen(screen, "Invoice.pdf coordinates") 
        end_pos = see_screen(screen, "Done folder coordinates")
        
        pyautogui.moveTo(start_pos)
        pyautogui.dragTo(end_pos, duration=1.0)
        print("✅ Action Executed")
        break
    
    time.sleep(1)
```

### ⚠️ 关键难点：坐标对齐
大模型通常返回的是 `[0-1000]` 的归一化坐标。记住要在代码里把它映射回你的屏幕分辨率 (e.g., 2560x1440)。
`real_x = model_x / 1000 * screen_width`

---

## 💼 实战场景：它能干什么？

部署好这套系统后，它就是你的**全能数字实习生**。

1.  **内网数据搬运**:
    *   公司只有内网能访问 ERP 系统？没问题。Deep-Claw 在你本地运行，完全模拟人工点击。
    *   **场景**: 每天早上自动登录后台，截图销量数据，OCR 识别后填入 Excel 发给你。

2.  **敏感文件处理**:
    *   **场景**: 扫描合同 PDF，自动提取关键条款。
    *   **优势**: 以前你不敢用 GPT-4 因为怕泄密，现在 Janus + R1 就在你机箱里，网线拔了都能跑。

---

## 📝 结语

Deep-Claw 虽然简陋，但它代表了一种**权利的回归**。
我们不再依赖 OpenAI 的 API Key，不再受制于 Anthropic 的昂贵账单。
这是完全属于你自己的一套智能系统。它虽然现在只有像猫狗一样的智力（甚至有时候会点错），但它是**你的**猫狗。

**附件下载**:
*   [Deep-Claw-v0.1-Source.zip] (包含完整 Python 脚本与环境配置单)

---
*Mr. Xie AI Consulting | 2026-02-14*
