---
title:
  zh: "Agent 记忆工程入门到精通：为什么你的 Claude 上了 Production 就失忆？"
  en: "Agent Memory Engineering from Beginner to Master: Why Your Claude Loses Memory in Production"
description:
  zh: "Harness Engineering 三部曲第三篇。Anthropic 给 Claude 加了'做梦'功能整理记忆，但这恰恰说明 Agent 失忆是行业基础架构缺陷。从物理天花板、Context Window 限制，到记忆工程的实操解决方案。"
  en: "The third part of the Harness Engineering trilogy. Anthropic added a 'Dreaming' feature to Claude for memory organization, which precisely illustrates that agent amnesia is an industry-wide infrastructure flaw. From physical ceilings and context window limits to practical memory engineering solutions."
date: "2026-05-12"
category: "AI Engineering"
tags: ["Harness Engineering", "Agent Memory", "Production AI", "Context Management", "Claude"]
draft: false
author: "James Xie"
---

# Agent 记忆工程入门到精通：为什么你的 Claude 上了 Production 就失忆？

> 本文是 Harness Engineering 三部曲的第三篇。如果你还没读过前两篇，建议先快速浏览，因为我们会直接沿用那两篇文章的术语和架构。

---

## 引子：一个尴尬的事实

2026 年 5 月，Anthropic 给 Claude Managed Agents 加了一个听起来很浪漫的功能，叫「做梦」（Dreaming）。官方说法是：Agent 在空闲时自动整理记忆、识别模式，效率最高提升 6 倍。配套还发布了 Outcome Assessment（结果评估）和多 Agent 协作。

新闻稿写得很好。但读到这条消息的时候，我的第一反应不是兴奋，而是有点尴尬——**这件事我们早该做了。**

不是说我比 Anthropic 那帮人聪明。恰恰相反，他们终于把这个功能做进产品，恰恰说明了一个被长期忽视的事实：**Agent 失忆不是某个模型的 bug，是整个行业的基础架构缺陷。**

过去两年，所有人都在卷模型能力。SWE-bench 从 4% 干到 80%，GPQA 从 30% 冲到 94%，幻觉率一降再降。但当一个 Agent 真正跑上 Production，连续工作超过 3 小时、跨越十几个 context window、处理了上百次工具调用之后，它最常见的死法不是「犯蠢」，而是**失忆**——忘了自己在干什么、忘了哪些路已经试过、忘了哪些假设已经被推翻。

Anthropic 自己 4 月发布的长运行 Agent 研究报告里写得够直白：长周期任务失败的最常见原因，不是模型不够聪明，是**每次新 context window 都是一次失忆**。

这篇文章，我们就来聊 Agent 的记忆工程。不是学术综述，不是产品测评，是一篇从「为什么失忆」到「怎么治」的实操指南。你可以把它理解为 Harness Engineering 的上下文管理章节的一次大升级——从架构原理，走到代码实现。

---

## 第一章：入门——Agent 为什么会失忆？

要治失忆，先搞清楚病因。

### 1.1 物理天花板：Context Window 再大也不够

2026 年的前沿模型，context window 已经膨胀到 100 万甚至 200 万 token。听起来很吓人，对吧？但如果你的 Agent 需要连续运行 8 小时、执行 20 轮模型调用、触发上百次工具执行——没有任何一个窗口能装下全程。

做个简单算术：一次典型的代码编辑 Agent 会话，每轮可能消耗 5K-15K token（系统提示 + 文件内容 + 工具结果 + 历史对话）。按 10K/轮计算，20 轮就是 200K。如果你要求 Agent 同时处理多个文件、跑测试、查日志，这个数字轻松翻倍。

200 万 token 够吗？看起来够。但问题是：**Agent 不会等到窗口满了才出问题。**

### 1.2 「中间遗忘」：Long Context 的隐藏陷阱

有一个被很多人忽略的研究结论：当关键指令或信息落在上下文窗口的**中间位置**时，模型的指令遵循能力会下降 30% 以上。即使百万级窗口，长上下文中的信息也会被「稀释」——模型能「读到」，但不一定能「用到」。

这有点像你读一本 500 页的书。书的开头几页和结尾几页你记得最清楚，中间那 400 页说了什么，只有一个模糊的印象。LLM 也有同样的问题。所以哪怕你的窗口理论上能装 100 万 token，真正可靠利用的活跃记忆可能只有 20%。

### 1.3 任务漂移：Agent 会逐渐忘记「为什么要做这件事」

比「读不到」更隐蔽的问题是「忘了目标」。

长任务中，Agent 会「漂移」——逐渐偏离最初的目标，陷入局部优化。它可能在第 10 轮时花大量时间优化一个其实并不关键的函数，而忘了用户的原始需求是修复某个特定 bug。为什么会这样？因为原始目标被埋在了上下文的前半部分，Agent 最近的注意力被当下的局部问题占据了。

这就像一个工人进了仓库，本来要去拿某件工具，路上看到货架有点乱，开始整理货架，整理完又发现地面有灰，开始扫地。3 小时后，他忘了自己来仓库是干什么的。

没有 Harness 的结构化状态管理，Agent 就像一个每过一小时就被敲一次头的工人——永远在重新理解问题。

---

## 第二章：进阶——记忆的四种形态

既然 Context Window 不够用，我们就得给 Agent 造一个「记忆系统」。但记忆不是单一的东西。理解记忆的分类，是设计记忆工程的第一步。

### 2.1 工作记忆（Working Memory）

工作记忆就是当前 Context Window 里的所有内容。它是 Agent 的「意识」，是模型正在进行推理时直接能访问到的信息。

**特点**：
- 访问速度最快（零延迟）
- 容量有限（受窗口限制）
- 内容在每次模型调用时被重新编码（可能变形或丢失细节）
- 没有持久性，窗口满了就会被挤出或压缩

**设计原则**：工作记忆里只放「现在需要的东西」。系统提示、当前任务描述、最近 3-5 轮对话、相关文件片段。其他的一律驱逐。

### 2.2 短期记忆（Short-term Memory）

短期记忆是最近若干轮的压缩摘要。它不等同于完整的历史对话，而是对工作记忆溢出部分的提炼。

**实现方式**：
- Compaction：把 10 轮对话压缩成一段结构化摘要
- Checkpoint：在关键节点保存状态快照
- 滚动窗口：保留最近 N 轮，丢弃更早的

**特点**：
- 访问速度较快（从内存或本地缓存读取）
- 容量中等（几千到几万 token 的摘要）
- 有有限持久性（跨会话保留，但可能定期清理）
- 关键信息被保留，细节被丢弃

类比人脑：你记得今天上午开了什么会、结论是什么，但不一定记得会议中某人说过的某句原话。

### 2.3 长期记忆（Long-term Memory）

长期记忆是外部化的结构化状态，不依赖模型的 Context Window。它通常以文件、数据库、日志的形式存在，Agent 需要显式读取才能使用。

**典型载体**：
- `AGENTS.md`：项目规范、约定、架构决策
- `progress.txt`：持续更新的任务进展日志
- `tests.json`：测试结果和失败记录
- `plan.md`：任务计划和当前优先级
- Git history：代码变更记录

**特点**：
- 访问速度较慢（需要 I/O 或工具调用）
- 容量几乎无限
- 持久性最强（写入磁盘或数据库）
- 需要 Agent 主动检索，不会自动出现在推理中

这是 Agent 记忆工程的基石。没有长期记忆，Agent 每次重启都是一张白纸。

### 2.4 外部知识（External Knowledge）

外部知识是 Agent 工作领域的事实性信息，不是 Agent 自己生成的经验，而是它需要查询的参考材料。

**典型载体**：
- 向量数据库（如 Chroma）：语义检索相关文档片段
- 知识图谱：实体关系和规则
- API 文档、代码库索引、业务规则库

**特点**：
- 访问速度取决于检索系统（RAG 延迟通常在几百毫秒到几秒）
- 容量理论上无限
- 内容通常静态或慢变（除非有更新机制）
- 需要精确的检索策略（query → 召回 → 重排序）

### 2.5 四种记忆的协作关系

一个健康的 Agent 记忆系统，应该像人脑一样让四种记忆各司其职：

```
工作记忆 ← 随时读取 ← 短期记忆（摘要）
    ↑                      ↑
   驱逐                  压缩
    ↓                      ↓
长期记忆 ← 显式写入 ← Agent 的运行产物
    ↑
   检索
    ↓
外部知识（RAG / 知识图谱）
```

关键原则：**不要让工作记忆承担它不该承担的责任**。它的角色是「现在正在用的」，不是「将来可能需要用的」。把后者放在短期或长期记忆中，需要时再召回。

---

## 第三章：进阶——上下文管理的四层策略

在第二篇 Harness Engineering 里，我们提出了四层上下文管理策略（Tier 0-3）加上 Fresh Restart（Tier 4）。这里我们重新梳理，并补充一些实战经验。

### 3.1 Tier 0：结构化输出默认

从第一行代码开始，Agent 的所有输出都应该是结构化的（JSON、YAML 或约定的文本格式）。

为什么？因为非结构化的自然语言输出，在 10 轮之后就会变成不可解析的噪音。你没法可靠地从中提取「上一轮做了什么」「结果是什么」「下一步该做什么」。结构化输出是后续所有压缩、摘要、状态重建的基础。

**最小可行约定**：

```json
{
  "action": "write_file",
  "target": "src/main.py",
  "reason": "修复第 42 行的空指针异常",
  "status": "success",
  "next_step": "运行测试验证修复"
}
```

不需要过度设计。一开始只要包含 action、reason、status、next_step 四个字段，后续按需扩展。

### 3.2 Tier 1：大结果立即驱逐

当工具返回超过 8K-16K token 等价物时，不要让它留在上下文里。立即写进 artifact 文件，上下文只保留一个引用：

```
[文件已写入: src/main.py (1,247 bytes)]
[测试结果已写入: tests_output.json (42 条记录)]
[日志已写入: build.log (8,391 行)]
```

Agent 如果需要查看完整内容，可以通过工具显式读取。但默认情况下，工作记忆里只有「这个操作发生过」的信息，而不是完整结果。

**经验值**：大多数工具调用结果里，Agent 真正需要用于下一步决策的信息不超过 10%。剩下的 90% 都是噪音。

### 3.3 Tier 2：延迟驱逐

当上下文用到 80-90% 的安全可用窗口时，触发延迟驱逐。把旧的 bulky 输入/结果替换为引用，保留「这个操作发生过」的元信息。

和 Tier 1 的区别：Tier 1 是「一见大结果就驱逐」，Tier 2 是「窗口快满时才驱逐历史」。Tier 1 是激进的，Tier 2 是保守的。

**触发阈值**：不要等 100%。留 10-20% 的 buffer，因为一次模型调用的输出本身也可能消耗大量 token。如果你等到 95% 才驱逐，下一轮可能直接溢出。

### 3.4 Tier 3：压缩/摘要（Compaction）

当延迟驱逐也不够时，你需要 Compaction——把历史对话总结成一段结构化摘要，替换原始对话。

**摘要里必须保留什么**：
- 原始目标（用户最初的需求）
- 已达成状态（完成了什么、通过了哪些测试）
- 未完成任务（还有什么没做、卡在什么地方）
- 关键决策（为什么选了方案 A 而不是 B）
- 产物引用（生成的文件、修改的代码位置）
- 下一步建议（如果继续，该做什么）

**摘要里可以丢弃什么**：
- 完整的工具输出（保留引用即可）
- 失败尝试的细节（保留「尝试了 X，失败，原因 Y」即可）
- 中间推理过程（保留结论即可）

Compaction 的质量直接决定 Agent 失忆的严重程度。一个糟糕的摘要会让 Agent 忘记关键约束，一个精准的摘要能让 Agent 在重启后立刻回到正轨。

### 3.5 Tier 4：全新窗口重启（Fresh Restart）

有时候，压缩也不够。当任务跨度太长、历史太混乱、或者 Agent 明显漂移时，最好的策略是**彻底重启**——丢弃全部上下文，从外部化状态重建。

**适合场景**：
- 任务有清晰的外部化状态（文件、测试、代码）
- Agent 已经明显漂移，继续在当前上下文里纠偏成本更高
- 当前上下文已经被错误信息污染（比如 Agent 陷入了错误的假设，后续所有推理都建立在这个错误之上）

**重建流程**：
1. Agent 读取 AGENTS.md，理解项目规范
2. 读取 progress.txt，了解已完成和待办
3. 读取 git diff，了解代码变更
4. 读取失败的测试，了解当前卡点
5. 基于这些信息重新制定计划，进入新窗口

代价是：重建需要时间，前几轮可能效率较低。但好处是：摆脱了历史包袱，以一个干净的视角重新审视问题。

### 3.6 决策树：什么时候用哪一层？

```
工具返回 > 8K token? 
  → 是 → Tier 1（立即驱逐）
  → 否 → 上下文用量 > 80%?
      → 是 → 历史里有可压缩的 bulky 内容?
          → 是 → Tier 2（延迟驱逐）
          → 否 → Tier 3（Compaction）
      → 否 → 继续正常工作

Agent 明显漂移 / 上下文被污染 / 任务跨度 > 2 小时?
  → 是 → Tier 4（Fresh Restart）
  → 否 → 继续当前策略
```

---

## 第四章：精通——注意力锚定（Attention Anchoring）

四层策略解决的是「怎么在窗口有限的情况下保留信息」。但它们解决不了一个更隐蔽的问题：**Agent 记得住信息，但用不对。**

### 4.1 什么是任务漂移？

假设用户让 Agent 重构一个模块。Agent 开始工作，读了代码，发现某个函数写法很丑，开始优化。优化完发现这个函数依赖的另一个服务也有问题，开始改服务接口。改完接口发现下游调用方全部报错，开始修调用方。3 小时后，Agent 花了大量时间在边缘问题上，而用户最初要求的重构只完成了 20%。

这就是任务漂移。Agent 的注意力被当下的局部问题捕获，逐渐丢失了全局视角。

### 4.2 注意力锚定的原理

解决方法是**定期在上下文中重写计划/任务状态**，把「现在最重要的是什么」放在上下文末尾——模型注意力最集中的位置。

具体做法：每隔 N 轮（或每次执行完一个子任务后），Agent 生成一段「当前状态摘要」，插入到上下文的尾部。这段摘要强制回答三个问题：

1. **原始目标**：用户最初让我做什么？
2. **当前进度**：已经完成了什么？还剩什么？
3. **下一步优先级**：如果不考虑任何干扰，现在最该做什么？

这段摘要就像一个锚，把 Agent 的注意力定期拉回主线。

### 4.3 Claude Code 的 progress.txt 模式

Claude Code 的实现方式很简洁：维护一个 `progress.txt` 文件，每次完成一个有意义的工作单元后更新它。文件格式大概是：

```markdown
# 任务：重构 auth 模块

## 已完成
- [x] 提取了 PasswordService 接口
- [x] 将 bcrypt 逻辑移入服务层
- [x] 单元测试全部通过

## 待办
- [ ] 更新 API 文档
- [ ] 检查下游调用方是否需要适配
- [ ] 跑集成测试

## 当前卡点
无。但注意到 UserController 里有段重复代码，可能值得后续清理。

## 下一步
跑集成测试，确认没有破坏现有功能。
```

每次模型调用前，这段内容被注入到系统提示的末尾。Agent 即使读了一万行代码和日志，也不会忘记主线任务是什么。

### 4.4 自己实现：一个极简的锚定模块

你可以用不到 50 行 Python 实现一个注意力锚定模块：

```python
class AttentionAnchor:
    def __init__(self, target: str, checkpoint_every: int = 5):
        self.original_target = target
        self.progress = []
        self.todo = []
        self.blockers = []
        self.step_count = 0
        self.checkpoint_every = checkpoint_every
    
    def update(self, action: str, result: str):
        self.step_count += 1
        self.progress.append(f"- {action}: {result}")
        if self.step_count % self.checkpoint_every == 0:
            return self.anchor_text()
        return None
    
    def anchor_text(self) -> str:
        lines = [
            "【注意力锚定】",
            f"原始目标: {self.original_target}",
            f"已执行步数: {self.step_count}",
            "最近进展:",
            *self.progress[-5:],
            "当前卡点:",
            *(self.blockers or ["无"]),
            "下一步建议: 请基于原始目标和最近进展，判断当前行动是否偏离主线。"
        ]
        return "\n".join(lines)
```

把这个模块接入你的 Harness 控制循环，每隔固定步数把 `anchor_text()` 的返回值注入到上下文中。成本几乎为零，效果立竿见影。

---


## 第五章：精通——Checkpoint 与可恢复性

注意力锚定解决的是「别忘目标」，但它不解决另一个更硬的问题：**如果 Agent 中途崩溃，怎么恢复？**

### 5.1 为什么需要 Checkpoint？

生产环境里，Agent 崩溃的原因五花八门：API 超时、模型 rate limit、工具执行出错、甚至宿主进程被系统杀掉。如果一个 Agent 已经跑了 2 小时、执行了 50 轮，崩溃后一切从头再来——这不仅是浪费 token，在很多场景下是不可接受的（比如正在部署服务、正在修改关键数据库）。

Checkpoint 的核心思想是：**在关键操作前后保存状态快照，崩溃后从最近的快照恢复。**

### 5.2 Checkpoint 的触发时机

不是所有操作都值得 Checkpoint。触发时机通常有三类：

**A. 副作用操作前后**
- 写文件之前：保存当前计划，如果写崩了可以回滚
- 写文件之后：保存新文件的内容 hash，后续可以验证一致性
- 调用外部 API 之前：保存请求参数
- 调用外部 API 之后：保存响应摘要

**B. 阶段性目标完成时**
- 每完成一个子任务，保存进度
- 每通过一轮测试，保存测试状态
- 每完成一个文件的重构，保存重构摘要

**C. 定时触发**
- 每 N 分钟或每 M 轮自动保存一次
- 适合长运行任务，防止「什么都不做的时候崩溃」

### 5.3 Checkpoint 里该存什么？

一个最小可用的 Checkpoint 包含：

```json
{
  "timestamp": "2026-05-08T14:32:11Z",
  "session_id": "sess_abc123",
  "checkpoint_id": "cp_007",
  "target": "重构 auth 模块",
  "completed_steps": [
    {"step": 1, "action": "读取 auth.py", "status": "done"},
    {"step": 2, "action": "提取 PasswordService", "status": "done"}
  ],
  "pending_steps": [
    {"step": 3, "action": "更新 API 文档", "status": "pending"},
    {"step": 4, "action": "跑集成测试", "status": "pending"}
  ],
  "artifact_hashes": {
    "src/auth.py": "sha256:abc...",
    "tests/test_auth.py": "sha256:def..."
  },
  "context_summary": "已完成 PasswordService 提取，bcrypt 逻辑已移入服务层。单元测试通过。下一步是更新文档和跑集成测试。",
  "last_action": "write_file",
  "last_action_target": "src/auth.py",
  "error_state": null
}
```

核心原则：**存能让 Agent「重建上下文」的最小信息，而不是全量数据。** 代码本身在 git 里，文件内容在磁盘上，Checkpoint 里只存引用和摘要。

### 5.4 幂等性设计

Checkpoint 的价值不仅在于「恢复」，还在于**重试**。如果一个操作失败了，Agent 从 Checkpoint 恢复后，可能会重试同一个操作。如果那个操作不是幂等的，重试就会出乱子。

**幂等性规则**：
- 文件写入：先写临时文件，验证通过后再原子替换目标文件
- API 调用：请求里带 idempotency key，服务端识别重复请求
- 数据库操作：用事务包裹，失败时回滚
- 测试执行：只读操作天然幂等，写操作需要沙箱隔离

### 5.5 可恢复的任务图

对于复杂任务，建议把任务分解成一个**任务图**（task graph），每个节点是一个子任务，边是依赖关系。Checkpoint 里保存的是「任务图当前状态」——哪些节点已完成、哪些正在执行、哪些还没开始。

恢复时，Agent 读取任务图状态，从第一个未完成的节点继续。已完成节点的产物已经在外部化状态里（文件、数据库记录），不需要重做。

```python
class RecoverableTaskGraph:
    def __init__(self, tasks: list[Task]):
        self.tasks = {t.id: t for t in tasks}
        self.status = {t.id: "pending" for t in tasks}
    
    def checkpoint(self) -> dict:
        return {
            "task_status": self.status,
            "completed_artifacts": [
                t.output_artifacts for t in self.tasks.values()
                if self.status[t.id] == "done"
            ]
        }
    
    def resume(self, checkpoint: dict):
        self.status = checkpoint["task_status"]
        next_task = next(
            (t for t in self.tasks.values() 
             if self.status[t.id] == "pending" 
             and all(self.status[dep] == "done" for dep in t.dependencies)),
            None
        )
        return next_task
```

这个模式在 LangGraph 2.0 里已经内置了（Checkpoint-resume、持久化层），但如果你用自定义 Harness，自己实现也不复杂。

---

## 第六章：精通——多 Agent 场景下的记忆同步

单 Agent 的记忆管理已经够复杂了。多 Agent 协作时，问题会指数级放大。

### 6.1 为什么多 Agent 容易失忆？

当一个任务被拆给多个 Agent 处理时，每个 Agent 都有自己的上下文窗口。信息在 Agent 之间传递时，面临两个难题：

**A. 传全量上下文太贵**
- 如果 Agent A 把全部 100K token 的上下文传给 Agent B，B 的窗口可能直接被占满，没有空间做自己的工作
- 多 Agent 并行时，总 token 消耗可能翻倍

**B. 传摘要又丢信息**
- 如果只传一段摘要，B 可能丢失关键细节——比如 A 尝试过的失败方案、A 发现的隐藏约束
- 摘要的质量决定了 B 会不会「重复踩坑」

### 6.2 Infinite Handoff Loops：失忆的终极形态

第二篇文章里我们提过一个死法：**无限移交循环**。Agent A 转给 B，B 转给 C，C 又转回 A。没有人对任务负责，每个人都在 replan。

这个死法的根因往往是**上下文丢失**。A 把任务交给 B 时，没有说清楚「为什么交给你」「我已经做了什么」「别做什么」。B 接过来后重新理解问题，得出了和 A 不同的结论，于是把任务交给 C。C 看到上下文更少了，做出了更离谱的判断，又交回给 A。

### 6.3 移交协议：Handoff 时必须传递什么？

每次 Agent 间移交，必须包含以下信息：

```json
{
  "handoff_from": "agent_a",
  "handoff_to": "agent_b",
  "original_target": "重构 auth 模块",
  "why_this_agent": "B 擅长 API 文档编写和测试策略",
  "completed_work": [
    {"action": "提取 PasswordService", "result": "成功，单元测试通过"}
  ],
  "known_constraints": [
    "不能破坏现有 JWT token 格式",
    "下游 mobile-app 依赖 auth 模块的接口签名"
  ],
  "failed_attempts": [
    {"attempt": "直接用 bcrypt 替换 argon2", "reason": "argon2 是项目标准，不能改"}
  ],
  "current_state": "代码已修改，单元测试通过，待补文档和集成测试",
  "success_criteria": "集成测试通过 + API 文档更新",
  "termination_condition": "当集成测试全部通过时，任务完成，不再移交"
}
```

关键字段是 `failed_attempts` 和 `termination_condition`。前者防止下一个 Agent 重复踩坑，后者防止无限循环。

### 6.4 共享状态 vs 隔离状态

多 Agent 有两种记忆架构：

**共享状态**：所有 Agent 读写同一个状态存储（比如同一个 SQLite 数据库、同一个文件目录）。优点是信息不会丢失，缺点是可能产生竞态条件（两个 Agent 同时修改同一个文件）。

**隔离状态**：每个 Agent 有自己的工作区，通过明确的移交协议交换信息。优点是干净、可预测，缺点是信息可能不同步。

**建议**：默认用隔离状态，只在必要时通过受控接口共享状态。共享状态的设计原则：
- 只共享「产物」（文件、数据库记录），不共享「过程」（中间推理）
- 共享状态用乐观锁或版本号控制，避免竞态
- 每个 Agent 只对自己创建的文件有写权限，对其他 Agent 的文件只读

---

## 第七章：精通——Anthropic「做梦」功能的解剖

聊完通用原理，我们来看 Anthropic 这次推出的「做梦」功能。这不是产品测评，而是从一个工程师的角度，推测它的实现逻辑和适用边界。

### 7.1 官方功能概述

Anthropic 给 Claude Managed Agents 加了三个功能：

1. **Dreaming（做梦）**：Agent 在空闲时自动整理记忆、识别模式，效率最高提升 6 倍
2. **Outcome Assessment**：自动评估任务完成质量
3. **多 Agent 协作**：复杂任务自动拆分到多个 Agent

### 7.2 Dreaming 的技术推测

Anthropic 没有公开 Dreaming 的技术细节，但从描述和效果推测，它大概率是一个**异步后台整理线程**：

**触发条件**：Agent 进入空闲状态（等待用户输入、等待外部 API 响应、或任务间歇期）。

**处理内容**：
- 把最近 N 轮的对话历史压缩成结构化摘要
- 识别重复出现的模式（比如「这个错误已经第三次出现了」）
- 标记重要信息（比如「用户反复强调不能改接口签名」）
- 清理过期信息（比如「临时调试日志可以丢弃」）
- 更新长期记忆索引（比如「把这个知识点加入领域知识库」）

**输出产物**：
- 一个更紧凑的上下文表示（替代原始对话）
- 一个更新的记忆索引（供后续检索）
- 可能的「洞察」提示（比如「注意到你总是先做 X 再做 Y，其实可以并行」）

**为什么叫「做梦」**：因为它发生在 Agent 的「非工作时段」，就像人睡觉时大脑整理白天记忆一样。

### 7.3 Dreaming 解决了什么问题？

它本质上是一个**自动化的 Tier 3 Compaction + 注意力锚定**。解决三个痛点：

1. **手工压缩太累**：之前需要开发者自己写 Compaction 逻辑，Dreaming 把这件事自动化了
2. **压缩质量不稳定**：手工写的摘要模板往往太死板，Dreaming 用模型自己总结，质量更高
3. **上下文膨胀速度减缓**：如果 Agent 每空闲一次就整理一次记忆，窗口被占满的频率大大降低

### 7.4 Dreaming 的边界

但 Dreaming 不是万能药。它有几个明显的局限：

**A. 只在空闲时工作**
- 如果 Agent 连续高强度运行（比如每分钟都在调用工具），Dreaming 没有机会触发
- 长任务中仍然需要显式的 Checkpoint 和 Fresh Restart

**B. 整理质量取决于「整理者」**
- Dreaming 本身也是用模型做的压缩，如果原始上下文已经混乱，整理结果也可能混乱
- 它无法「创造」信息，只能「提炼」信息。如果关键信息已经在上下文中丢失，Dreaming 找不回来

**C. 多 Agent 场景下作用有限**
- Dreaming 整理的是单个 Agent 的上下文，不解决 Agent 之间的信息同步问题
- 如果 Agent A 的「梦」里没有包含「已经试过的失败方案」，Agent B 仍然会重复踩坑

**D. 长期记忆仍然需要外部化**
- Dreaming 整理后的记忆仍然存在 Claude 的内部状态里，跨会话不一定保留
- 真正的长期记忆还是需要 AGENTS.md、progress.txt、数据库这些外部载体

### 7.5 对我们自建 Harness 的启示

Anthropic 做这件事，说明**记忆管理已经从「可选优化」变成「刚需基础设施」**。如果你在用开源模型或本地 LLM 自建 Agent，现在就该把记忆工程加入 Roadmap。

好消息是：Dreaming 的核心逻辑不复杂。用 Qwen 3.6 35B 或 Gemma 4 26B 在本地跑一个「整理摘要 + 模式识别」的后台任务，完全可行。下一章我们会给一个最小可行实现。

---

## 第八章：实战——用本地 LLM 搭建轻量级记忆系统

理论聊够了，我们来写代码。

### 8.1 硬件与模型选择

我的日常基准环境：
- **硬件**：Apple M5 Pro / 64GB RAM，通过 LM Studio 本地推理
- **日常模型**：Qwen 3.6 35B A3B（日常 driver），Gemma 4 26B A4B（深度 review）

这两个模型的强项是：**激活参数量适中（推理速度快），但质量足以处理记忆整理这类中等复杂度任务。** 不需要 GPT-5.5 或 Claude Opus 来做摘要，本地模型完全够用，而且成本为零。

### 8.2 架构设计

我们用一个最简架构实现四记忆协作：

```
工作记忆 → Python 变量（当前 context window 内容）
短期记忆 → SQLite（压缩摘要）
长期记忆 → 文件系统（AGENTS.md, progress.txt）
外部知识 → Chroma（向量检索）
```

核心组件就一个 `AgentMemory` 类，大概 200 行 Python。

### 8.3 核心代码

```python
import sqlite3, json, hashlib
from datetime import datetime
from typing import List, Dict, Optional

class AgentMemory:
    """轻量级 Agent 记忆系统。支持四层记忆 + Compaction + Checkpoint."""
    
    def __init__(self, db_path: str = ".agent_memory.db"):
        self.db = sqlite3.connect(db_path)
        self._init_tables()
        self.working_buffer: List[Dict] = []  # 工作记忆
        self.anchor = None  # 注意力锚定
    
    def _init_tables(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS short_term (
                id INTEGER PRIMARY KEY,
                session TEXT,
                summary TEXT,
                timestamp TEXT,
                priority REAL DEFAULT 0.5
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY,
                session TEXT,
                checkpoint TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS long_term (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated TEXT
            );
        """)
        self.db.commit()
    
    # ========== 工作记忆 ==========
    def add_turn(self, role: str, content: str, metadata: Optional[dict] = None):
        self.working_buffer.append({
            "role": role,
            "content": content,
            "meta": metadata or {},
            "ts": datetime.utcnow().isoformat()
        })
    
    def working_memory(self, max_items: int = 10) -> str:
        """返回格式化的工作记忆内容。"""
        recent = self.working_buffer[-max_items:]
        lines = []
        for item in recent:
            lines.append(f"[{item['role']}] {item['content'][:500]}")
        return "\n".join(lines)
    
    # ========== 短期记忆（Compaction）==========
    def compact(self, session: str, llm_summarize_fn) -> str:
        """用 LLM 把当前工作记忆压缩成摘要，存入 SQLite。"""
        if len(self.working_buffer) < 3:
            return "暂无需压缩。"
        
        raw = "\n".join(
            f"{t['role']}: {t['content']}" for t in self.working_buffer
        )
        prompt = f"""将以下 Agent 执行记录压缩成结构化摘要。
保留：原始目标、已完成工作、关键决策、未完成任务、失败尝试、产物引用。
丢弃：完整工具输出、中间推理过程。

记录：
{raw[:8000]}

输出 JSON 格式：
{{"goal": "...", "completed": [...], "decisions": [...], "pending": [...], "artifacts": [...]}}"""
        
        summary = llm_summarize_fn(prompt)
        
        self.db.execute(
            "INSERT INTO short_term (session, summary, timestamp) VALUES (?, ?, ?)",
            (session, summary, datetime.utcnow().isoformat())
        )
        self.db.commit()
        
        # 清空工作记忆（已压缩部分）
        self.working_buffer = []
        return summary
    
    def recent_summaries(self, session: str, limit: int = 3) -> List[str]:
        cur = self.db.execute(
            "SELECT summary FROM short_term WHERE session=? ORDER BY id DESC LIMIT ?",
            (session, limit)
        )
        return [r[0] for r in cur.fetchall()]
    
    # ========== 长期记忆 ==========
    def write_long_term(self, key: str, value: str):
        self.db.execute(
            """INSERT INTO long_term (key, value, updated) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated""",
            (key, value, datetime.utcnow().isoformat())
        )
        self.db.commit()
    
    def read_long_term(self, key: str) -> Optional[str]:
        cur = self.db.execute("SELECT value FROM long_term WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None
    
    # ========== Checkpoint ==========
    def save_checkpoint(self, session: str, state: dict):
        self.db.execute(
            "INSERT INTO checkpoints (session, checkpoint, timestamp) VALUES (?, ?, ?)",
            (session, json.dumps(state, ensure_ascii=False), datetime.utcnow().isoformat())
        )
        self.db.commit()
    
    def load_latest_checkpoint(self, session: str) -> Optional[dict]:
        cur = self.db.execute(
            "SELECT checkpoint FROM checkpoints WHERE session=? ORDER BY id DESC LIMIT 1",
            (session,)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None
    
    # ========== 注意力锚定 ==========
    def set_anchor(self, target: str, progress: List[str], blockers: List[str]):
        self.anchor = {
            "target": target,
            "progress": progress,
            "blockers": blockers,
            "updated": datetime.utcnow().isoformat()
        }
    
    def anchor_text(self) -> str:
        if not self.anchor:
            return ""
        a = self.anchor
        return f"""【注意力锚定】
原始目标: {a['target']}
当前进度: {', '.join(a['progress'])}
当前卡点: {', '.join(a['blockers']) or '无'}
更新时间: {a['updated']}
提醒: 请确认当前行动是否偏离主线。"""
    
    # ========== 构建完整上下文 ==========
    def build_context(self, session: str, include_anchor: bool = True) -> str:
        parts = []
        
        # 1. 注意力锚定
        if include_anchor:
            parts.append(self.anchor_text())
        
        # 2. 长期记忆（项目规范）
        conventions = self.read_long_term("conventions")
        if conventions:
            parts.append(f"【项目规范】\n{conventions}")
        
        # 3. 短期记忆（最近摘要）
        summaries = self.recent_summaries(session, limit=2)
        if summaries:
            parts.append("【历史摘要】\n" + "\n---\n".join(summaries))
        
        # 4. 工作记忆（最近交互）
        parts.append("【当前对话】\n" + self.working_memory(max_items=8))
        
        return "\n\n".join(parts)
```

### 8.4 使用方式

```python
# 初始化
mem = AgentMemory()

# 设置锚定
mem.set_anchor(
    target="重构 auth 模块",
    progress=["已提取 PasswordService", "bcrypt 逻辑已移入服务层"],
    blockers=[]
)

# 记录对话轮次
mem.add_turn("user", "继续更新 API 文档")
mem.add_turn("assistant", "已读取 auth.md，发现文档和代码不同步...")

# 窗口快满时压缩
if token_count > 60000:  # 假设 80% 的 75K 窗口
    mem.compact(session="sess_001", llm_summarize_fn=local_llm)

# 保存 Checkpoint
mem.save_checkpoint("sess_001", {
    "target": "重构 auth 模块",
    "completed": ["提取 PasswordService"],
    "next": "更新 API 文档",
    "file_hashes": {"src/auth.py": "sha256:abc..."}
})

# 构建给模型的完整上下文
context = mem.build_context("sess_001")
response = local_llm(context + "\n\n【用户输入】继续")
```

### 8.5 为什么没有外部知识（RAG）？

为了控制复杂度，上面的代码没有集成 Chroma 或向量检索。如果你的 Agent 需要查文档、查代码库，可以在 `build_context()` 里加一步：

```python
# 伪代码：在 build_context 里加入 RAG
from chromadb import Client
documents = chroma_client.query(query_texts=[user_input], n_results=3)
parts.append("【相关文档】\n" + format_documents(documents))
```

RAG 的延迟通常在几百毫秒，对于非实时任务完全可以接受。

---

## 第九章：实战——落地检查清单

最后，一个务实的检查清单。你的 Agent 是否需要记忆工程？可以从这 4 个信号判断：

### 信号 1：任务持续时间
- **不需要**：单次对话 < 5 轮，总耗时 < 10 分钟
- **建议做**：单次对话 > 20 轮，或总耗时 > 1 小时
- **必须做**：总耗时 > 4 小时，或需要跨会话恢复

### 信号 2：工具调用密度
- **不需要**：每轮对话最多 1-2 次工具调用
- **建议做**：每轮对话 3-5 次工具调用，且工具返回结果 > 4K token
- **必须做**：每轮对话 > 5 次工具调用，或需要连续修改多个文件

### 信号 3：任务复杂度
- **不需要**：单步任务（翻译一段文字、生成一个函数）
- **建议做**：多步任务（写代码 + 跑测试 + 修 bug + 补文档）
- **必须做**：长时程任务（重构模块、多文件迁移、持续集成调试）

### 信号 4：可靠性要求
- **不需要**：个人实验、POC、一次性脚本
- **建议做**：团队内部工具、自动化工作流
- **必须做**：生产环境、面向客户的 Agent、涉及数据修改的操作

### 渐进落地路径

如果你确认需要记忆工程，不要一次性做全套。按这个顺序：

**第 1 周：注意力锚定**
- 只实现 `set_anchor()` 和 `anchor_text()`
- 每次模型调用前把锚定文本注入上下文
- 效果：Agent 不再漂移

**第 2-3 周：大结果驱逐 + 延迟驱逐**
- 工具返回 > 8K 时立即写入文件
- 窗口用量 > 80% 时驱逐历史
- 效果：窗口不再频繁溢出

**第 4-5 周：Compaction + Checkpoint**
- 加入压缩摘要和状态保存
- 崩溃后能恢复到最近状态
- 效果：长任务可存活

**第 6 周+：多 Agent 移交协议**
- 如果你有多 Agent 场景，再补移交协议
- 单 Agent 场景不需要这一步

---

## 结语：记忆是 Agent 的氧气

写这篇文章的时候，我想起一个老比喻。

早期的人工智能研究，把智能等同于「推理能力」——会不会下棋、会不会证明定理、会不会解数学题。后来的深度学习浪潮，把智能等同于「模式识别」——认猫认狗、语音识别、机器翻译。

今天的 Agent 热潮，正在把智能等同于「工具使用」——会不会调用 API、会不会写代码、会不会查数据库。

但所有这些视角都漏掉了一件事：**记忆**。没有记忆，推理是断片的，模式识别是一次性的，工具使用是重复的。记忆不是智能的某个子模块，记忆是智能的**基础设施**。

Anthropic 推出「做梦」功能，本质上是在承认：即使是 Claude 这样顶级的模型，如果没有外部记忆系统的支持，上了 Production 也会失忆。这不是 Claude 的弱点，这是所有 LLM 的共性。

对我们这些自己搭 Agent 的工程师来说，这意味着两件事：

第一，**别指望模型替你记住一切**。Context Window 是工作记忆，不是硬盘。学会设计外部记忆系统，是 Agent Engineering 的必修课。

第二，**记忆工程不需要等到项目变大才做**。从第一天开始，就给 Agent 配一个 SQLite 数据库、一个 progress.txt、一个注意力锚定模块。成本几乎为零，但能帮你避开 80% 的长任务失败。

记忆是 Agent 的氧气。没有它，Agent 活不过几个回合。

---

*本文是 Harness Engineering 三部曲的第三篇，完结。*

*参考资料：*
- *Anthropic, "Long-running Agent Research", 2026-04*
- *Fivetran, "2026 Agentic AI Readiness Index", 2026-05*
- *LangGraph 2.0 Documentation, Checkpoint & Resume*
- *Claude Code Internal Patterns (publicly documented)*
- *Atkinson-Shiffrin Memory Model (human cognitive architecture)*
