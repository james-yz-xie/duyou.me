---
title:
  zh: "Harness Engineering 从精通到大师：2026 年，Agent 上生产的必修课"
  en: "Harness Engineering from Master to Grandmaster: The Essential Course for Production Agents in 2026"
description:
  zh: "入门 Harness Engineering 时，你关心的问题是 agent 能不能完成一个任务。大师级的问题是：agent 能不能连续跑 8 小时、跨越几十个 context window、在级联失败时自愈？"
  en: "Beginners ask if an agent can complete a task. Masters ask if it can run for 8 hours, span dozens of context windows, and self-heal during cascading failures."
date: "2026-05-07"
category: "AI Engineering"
tags: ["Harness Engineering", "Production Systems", "Long-running Agents", "Resilience"]
draft: false
author: "James Xie"
---

## 前言：从"能跑"到"能扛"

入门 Harness Engineering 时，你关心的问题是：agent 能不能完成一个任务？

精通之后，问题变成：agent 能不能可靠地完成一百个任务？

到了大师级，问题更硬：agent 能不能连续跑 8 小时、跨越几十个 context window、在级联失败时自愈、在成本可控的前提下交付？这不是理论问题，是生产环境每天都在发生的现实。

Anthropic 在 2026 年 4 月发布的长运行 agent 研究里讲得很直接：长周期任务失败的最常见原因，不是模型不够聪明，而是**每次新 context window 都是一次失忆**。模型忘了它之前在干什么、忘了已经尝试过什么、忘了哪些假设已经被推翻。没有 Harness 的结构化状态管理，agent 就像一个每过一小时就被敲一次头的工人——永远在重新理解问题。

这篇文章不谈入门知识。如果你还没读过《Harness Engineering 从入门到精通》，建议先看那篇。这篇假设你已经掌握了控制循环、工具层、护栏、记忆和可观测性，我们要聊的是**如何让这些组件在生产环境里扛住压力**。

---

## 第一章：大师思维——把 LLM 当作控制平面

### 1.1 五层稳定架构

现代 Harness 不是一堆胶水代码的集合，它有一套稳定的分层架构。这个架构来自 Anthropic 的生产实践、OpenAI Codex 的设计哲学，以及社区里大量失败案例的总结。五层分别是：

1. **Execution Runtime（执行运行时）**：事件循环、会话管理、检查点（checkpoint）、恢复机制。这是 Harness 的心跳。
2. **Context System（上下文系统）**：提示布局、产物引用、压缩策略、缓存纪律。这是 Harness 的呼吸系统——管理什么进肺、什么排出。
3. **Capability Surface（能力表面）**：内置工具、外部 MCP 服务器、技能（skills）、子 agent。这是 Harness 的手脚。
4. **Governance Layer（治理层）**：审批、钩子、允许/拒绝策略、沙箱、溯源。这是 Harness 的免疫系统。
5. **Surface/Protocol Adapters（适配层）**：CLI、IDE、Web UI、MCP、A2A。这是 Harness 的感官——和外部世界交互的接口。

这五层的顺序不是随意的。越往下越靠近确定性系统（Runtime、Context），越往上越靠近不确定性（LLM 推理）。**大师级 Harness 的核心原则是：把确定性的事从 LLM 手里拿回来，让 LLM 只干它擅长的事——推理和规划。**

### 1.2 神经符号分离

这个概念听起来学术，但意思很简单：**LLM 是控制平面（control plane），负责决策；Harness 是数据平面（data plane），负责执行。**

举个例子：agent 需要决定"要不要调用 write_file"。这个决策可以交给 LLM——它读上下文、理解目标、判断时机。但"write_file 的执行权限校验、路径合法性检查、备份创建、结果验证"这些必须交给 Harness 的确定性代码。LLM 可以建议写文件，但它不能绕过校验。

Anthropic 在 2026 年 4 月的 Managed Agents 架构里把这个分离做到了极致。他们把系统拆成三个独立的无状态组件：

- **Brain（大脑）**：Claude + Harness 控制逻辑
- **Hands（手脚）**：沙箱和工具执行环境
- **Session（会话）**：追加式事件日志

三者可以独立故障和替换。Brain 挂了？换一个新的，从 Session 日志恢复状态。Hands 被污染了？销毁容器，起一个干净的。这个架构让 p95 首 Token 时间（TTFT）下降了 90%——因为 Hands 的冷启动和 Brain 的推理可以并行。

关键洞察：**确定性越多，系统越可靠。** 如果你发现某个组件的行为依赖 LLM 的"判断"，而不是代码的"规则"，那这个组件还没有被 Harness 驯服。

---

## 第二章：长周期任务——跨越多个 Context Window

### 2.1 问题的本质：每次新窗口都是失忆

一个 context window 能装多少？2026 年的前沿模型已经到了 100 万甚至 200 万 token。但 token 多不等于记得住。研究表明，**当关键内容落在上下文窗口中间位置时，模型的指令遵循能力下降 30% 以上**。即使百万级窗口，长上下文中的信息也会被"稀释"——模型能读到，但不一定能用到。

更现实的问题是：一个复杂任务可能需要 8 小时、20 轮模型调用、上百次工具执行。没有任何一个上下文窗口能装下全程。Agent 必须在某个时刻"重启"——要么 compaction（压缩历史），要么 fresh restart（全新窗口）。这两种选择都有代价。

### 2.2 Anthropic 的解法：结构化交接

Anthropic 在 2026 年 4 月发布的长运行 agent 设计里，用了一个三段式接力：

1. **Initializer Agent**：一次性设置环境。读取项目结构、创建进度文件、初始化测试框架。这个 agent 只跑一次，把状态写入外部文件系统。
2. **Coding Agent**：增量推进。每次新窗口都从文件系统读取当前状态——feature list、git commit 历史、未通过的测试列表——然后继续工作。
3. **Evaluator Agent**：定期审查产出，给出反馈。

核心机制是**结构化交接工件（Structured Handoff Artifacts）**。不是让模型自己"记住"状态，而是把状态写成标准格式的文件：

```json
{
  "current_feature": "用户登录模块",
  "completed": ["数据库 schema", "API 路由"],
  "pending": ["前端表单", "JWT 验证"],
  "blockers": ["CORS 配置待确认"],
  "last_commit": "a1b2c3d",
  "test_status": "3/5 通过"
}
```

每次 Coding Agent 启动，第一件事就是读这个文件，而不是依赖对话历史。这样即使换了全新的 context window，agent 也能无缝接力。

### 2.3 检查点与恢复

长周期任务的另一个关键是**检查点（Checkpoint）**。就像玩游戏要存档一样，Harness 要在关键时刻保存状态，以便失败后恢复。

检查点的粒度很重要：

- **太粗**：只在任务结束时保存。如果中途失败，前功尽弃。
- **太细**：每次工具调用都保存。I/O 开销太大，拖慢速度。

最佳实践是**基于事件的检查点**：

- 完成一个子任务后保存
- 通过一组测试后保存
- 修改关键配置文件后保存
- 每隔 N 分钟强制保存一次

检查点的内容包括：

1. **会话状态**：当前的对话历史、变量值、临时文件
2. **文件系统快照**：关键文件的哈希值（不需要全量备份，只需记录变化）
3. **外部环境状态**：数据库版本、依赖包版本、环境变量

恢复时，Harness 先加载检查点，然后从最后一个成功的事件继续执行。这个过程对模型是透明的——它不知道自己"重启"过。

### 2.4 上下文压缩策略

当上下文窗口快满时，Harness 必须决定：哪些内容保留，哪些内容丢弃，哪些内容压缩。

常见的压缩策略：

#### 策略 1：滑动窗口（Sliding Window）

只保留最近 N 轮对话，更早的历史全部丢弃。

**优点**：简单高效  
**缺点**：可能丢掉重要的早期决策依据

**适用场景**：短期任务，历史信息不重要

#### 策略 2：摘要压缩（Summarization）

用一个小模型把长历史压缩成简短摘要，替换原始对话。

```python
# 原始对话（10000 tokens）
User: 帮我实现用户认证模块
Assistant: 好的，我需要...（长篇讨论）
...

# 压缩后（500 tokens）
Summary: 用户要求实现 JWT 认证。已完成数据库 schema 设计和 API 路由创建。下一步是实现前端表单和 token 验证逻辑。当前 blockers: CORS 配置。
```

**优点**：保留关键信息，大幅减少 token  
**缺点**：摘要可能丢失细节，小模型可能理解偏差

**适用场景**：中长期任务，需要保留决策脉络

#### 策略 3：选择性保留（Selective Retention）

根据重要性评分，只保留高价值的内容：

- **高价值**：用户的明确要求、关键决策、错误修复方案
- **中价值**：一般的讨论过程、尝试过的方案
- **低价值**：寒暄、重复的确认、失败的尝试

**优点**：精准保留有用信息  
**缺点**：需要额外的评分模型，增加复杂度

**适用场景**：复杂任务，信息密度不均匀

#### 策略 4：分层存储（Tiered Storage）

结合以上三种策略，形成三层存储：

- **热层（Hot）**：最近 5 轮对话，完整保留
- **温层（Warm）**：过去 50 轮对话，摘要压缩
- **冷层（Cold）**：更早的历史，索引化存储，按需检索

**优点**：平衡性能和完整性  
**缺点**：实现复杂，需要管理多层存储

**适用场景**：超长周期任务（数天甚至数周）

大师级 Harness 会根据任务类型动态选择压缩策略。例如：

- 代码生成任务 → 选择性保留（保留关键决策）
- 数据分析任务 → 摘要压缩（保留结论）
- 调试任务 → 滑动窗口（只看最近的错误）

### 2.5 跨窗口一致性保证

长周期任务的最大挑战是**一致性**：如何保证第 1 小时的决策和第 8 小时的行动不矛盾？

解决方案：

#### 方案 1：全局约束文件

维护一个全局约束文件（如 `constraints.json`），记录不可违背的规则：

```json
{
  "architecture_decisions": [
    "使用 PostgreSQL 而非 MySQL",
    "采用 REST API 而非 GraphQL",
    "前端使用 React 而非 Vue"
  ],
  "coding_standards": [
    "所有函数必须有类型注解",
    "禁止使用全局变量",
    "单元测试覆盖率 >= 80%"
  ],
  "security_policies": [
    "所有用户输入必须校验",
    "密码必须加盐哈希",
    "敏感数据不得写入日志"
  ]
}
```

每次新窗口启动，Harness 先把这个文件注入上下文，确保模型不会违背之前的决策。

#### 方案 2：决策日志

记录所有关键决策及其理由：

```
[2026-05-07 10:23] Decision: Use JWT for authentication
Reason: Stateless, scalable, widely supported
Alternatives considered: Session-based (rejected due to scaling issues), OAuth2 (rejected due to complexity)
```

当模型要做相关决策时，Harness 先查询决策日志，如果已有决策，直接告知模型"之前已决定使用 JWT"，避免重复决策或矛盾决策。

#### 方案 3：冲突检测

在每次模型输出后，Harness 运行冲突检测：

- 新生成的代码是否符合之前的架构决策？
- 新的 API 设计是否与已有 API 风格一致？
- 新的安全策略是否与现有策略冲突？

检测到冲突时，Harness 可以：

1. **自动修复**：如果冲突可以自动解决（如代码格式不一致），直接修复
2. **请求澄清**：如果冲突需要人工判断，暂停并请求用户澄清
3. **回滚**：如果冲突严重，回滚到上一个检查点

---

## 第三章：容错与自愈——让 Agent 永不宕机

### 3.1 错误分类与处理策略

不是所有错误都一样。大师级 Harness 会把错误分类，并采取不同的处理策略：

#### 类别 1：瞬时错误（Transient Errors）

**特征**：暂时性问题，重试可能成功

**例子**：
- 网络超时
- API 速率限制（429）
- 临时服务不可用（503）

**处理策略**：指数退避重试

```python
def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = min(2 ** attempt + random.random(), 60)
            time.sleep(wait_time)
```

#### 类别 2：永久性错误（Permanent Errors）

**特征**：根本性问题，重试无效

**例子**：
- 参数错误（400）
- 认证失败（401）
- 资源不存在（404）

**处理策略**：立即失败，向上层报告

不要浪费时间在永久性错误上重试。立即停止，记录错误详情，通知上层控制器。

#### 类别 3：语义错误（Semantic Errors）

**特征**：工具执行成功，但结果不符合预期

**例子**：
- 模型调用了正确的工具，但传了错误的参数
- 代码能运行，但逻辑有误
- 测试通过，但功能不完整

**处理策略**：验证 + 反馈循环

```python
result = execute_tool(tool_call)
if not validate_result(result, expected_schema):
    # 告诉模型哪里错了，让它修正
    feedback = generate_feedback(result, expected_schema)
    return retry_with_feedback(feedback)
```

#### 类别 4：系统性错误（Systemic Errors）

**特征**：Harness 本身的问题，不是模型或工具的问题

**例子**：
- 内存泄漏
- 死锁
- 资源耗尽

**处理策略**：优雅降级 + 告警

立即切换到备用模式（如离线模式、简化模式），同时发送告警给运维团队。

### 3.2 级联失败防护

在复杂的 Harness 中，一个组件的失败可能引发连锁反应，导致整个系统崩溃。这就是**级联失败（Cascading Failure）**。

防护策略：

#### 策略 1：熔断器（Circuit Breaker）

当一个组件连续失败 N 次后，熔断器打开，暂时停止调用该组件，给它恢复的时间。

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        if self.state == "OPEN":
            if time.now() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

#### 策略 2：舱壁隔离（Bulkhead Isolation）

把系统分成多个独立的舱壁，一个舱壁的失败不会影响其他舱壁。

例如：
- 每个用户会话有独立的资源配额（CPU、内存、API 调用次数）
- 不同类型的任务使用不同的线程池
- 关键任务和非关键任务分开部署

这样即使用户 A 的任务耗尽了资源，用户 B 的任务仍能正常运行。

#### 策略 3：负载 shedding（Load Shedding）

当系统过载时，主动拒绝部分请求，保护核心功能。

例如：
- 优先级低的任务排队等待
- 非关键的工具调用暂时禁用
- 降低采样率（如只记录 10% 的日志）

目标是**宁可部分失败，不要全部崩溃**。

### 3.3 自愈机制

最高级的容错是**自愈（Self-healing）**——系统检测到问题后，自动修复，无需人工介入。

#### 自愈场景 1：工具失败

**问题**：模型调用 `run_command` 执行 `npm install`，但失败了（网络问题）。

**自愈流程**：
1. 检测到失败（返回码非 0）
2. 分析错误日志（发现是网络超时）
3. 自动重试（切换镜像源，如从 npmjs.org 切换到淘宝镜像）
4. 如果重试成功，继续执行
5. 如果重试失败，记录错误并通知用户

#### 自愈场景 2：状态不一致

**问题**：文件系统状态和 Harness 记录的状态不一致（如模型手动删除了某个文件）。

**自愈流程**：
1. 定期检查点验证（对比实际文件系统和预期状态）
2. 检测到不一致
3. 尝试自动修复（如重新生成缺失的文件）
4. 如果无法自动修复，回滚到上一个一致的检查点

#### 自愈场景 3：模型陷入循环

**问题**：模型反复尝试同一个方案，每次都失败，但不知道换思路。

**自愈流程**：
1. 检测循环模式（相同工具调用重复 N 次）
2. 中断循环
3. 生成元认知提示："你已经在同一个问题上卡住了。请反思：是不是方向错了？有没有其他方法？"
4. 强制模型切换到备选方案

#### 自愈场景 4：资源泄漏

**问题**：Harness 运行时间长了，内存占用越来越高（可能有内存泄漏）。

**自愈流程**：
1. 监控内存使用趋势
2. 超过阈值时触发垃圾回收
3. 清理不再需要的会话状态
4. 如果仍然过高，重启 Harness（从检查点恢复）

### 3.4 优雅降级

当某些功能不可用时，Harness 应该降级到简化模式，而不是完全崩溃。

降级层次：

1. **Level 0：全功能模式**
   - 所有工具可用
   - 完整记忆系统
   - 高级可观测性

2. **Level 1：受限模式**
   - 部分工具禁用（如外部 API 调用）
   - 简化的记忆检索
   - 基础日志

3. **Level 2：离线模式**
   - 仅本地工具可用（读写文件、运行本地命令）
   - 无外部依赖
   - 最小化日志

4. **Level 3：只读模式**
   - 只能读取和分析，不能修改
   - 提供诊断报告
   - 等待人工干预

降级触发条件：

- 外部服务不可用 → 降到 Level 1
- 网络连接断开 → 降到 Level 2
- 检测到安全威胁 → 降到 Level 3

关键原则：**降级时要明确告知用户当前模式和限制**，避免用户期望与实际不符。

---

## 第四章：成本控制——让 Agent 经济可行

### 4.1 成本构成分析

生产环境的 Agent 成本主要来自三部分：

1. **模型推理成本**：Token 消耗 × 单价
2. **基础设施成本**：计算资源、存储、网络
3. **运维成本**：监控、告警、人工干预

其中模型推理成本通常占 60-80%，是优化的重点。

### 4.2 Token 优化策略

#### 策略 1：提示压缩

减少不必要的提示内容：

- 移除冗余的系统指令
- 使用缩写和符号代替长文本
- 合并相似的示例

**效果**：可以减少 20-30% 的 prompt token

#### 策略 2：智能缓存

缓存常见的问答对和工具调用结果：

```python
cache = {}

def cached_llm_call(prompt):
    cache_key = hash(prompt)
    if cache_key in cache:
        return cache[cache_key]
    
    result = llm.chat(prompt)
    cache[cache_key] = result
    return result
```

**效果**：对于重复性任务，可以减少 50% 以上的 token 消耗

#### 策略 3：模型路由

根据任务难度选择不同的模型：

- 简单任务（如代码格式化）→ 用小模型（如 GPT-3.5）
- 中等任务（如代码生成）→ 用中等模型（如 Claude 3 Sonnet）
- 复杂任务（如架构设计）→ 用大模型（如 Claude 3 Opus）

**效果**：可以在保持质量的前提下，降低 40-60% 的成本

#### 策略 4：批量处理

把多个小任务合并成一个大任务，一次性调用模型：

```python
# 反例：逐个处理
for file in files:
    result = llm.chat(f"Review this file: {file}")

# 正例：批量处理
batch_prompt = "Review these files:\n" + "\n".join(files)
results = llm.chat(batch_prompt)
```

**效果**：减少 API 调用次数，降低固定开销

### 4.3 预算控制

#### 硬预算（Hard Budget）

设定绝对上限，超过即停止：

```python
MAX_COST_PER_TASK = 10.0  # 美元

def execute_task(task):
    cost_tracker = CostTracker()
    
    while not task.is_complete():
        if cost_tracker.total_cost > MAX_COST_PER_TASK:
            raise BudgetExceededError(f"Task exceeded budget: ${cost_tracker.total_cost}")
        
        step_result = execute_step(task, cost_tracker)
        task.update(step_result)
```

#### 软预算（Soft Budget）

设定预警线，超过时提醒但不一定停止：

```python
WARNING_THRESHOLD = 0.8  # 80%
CRITICAL_THRESHOLD = 0.95  # 95%

def check_budget(cost_tracker, budget):
    ratio = cost_tracker.total_cost / budget
    
    if ratio > CRITICAL_THRESHOLD:
        alert_admin(f"Critical: Task at {ratio*100:.1f}% of budget")
        return "STOP"
    elif ratio > WARNING_THRESHOLD:
        alert_admin(f"Warning: Task at {ratio*100:.1f}% of budget")
        return "CONTINUE_WITH_CAUTION"
    else:
        return "CONTINUE"
```

#### 动态预算

根据任务价值和复杂度动态调整预算：

```python
def calculate_budget(task):
    base_budget = 5.0
    
    # 根据任务类型调整
    if task.type == "CRITICAL":
        base_budget *= 3
    elif task.type == "EXPERIMENTAL":
        base_budget *= 0.5
    
    # 根据历史数据调整
    historical_avg = get_historical_cost(task.type)
    if historical_avg:
        base_budget = max(base_budget, historical_avg * 1.2)
    
    return base_budget
```

### 4.4 ROI 评估

不是所有任务都值得用 Agent。大师级 Harness 会评估 ROI（投资回报率）：

```
ROI = (自动化收益 - Agent 成本) / Agent 成本
```

**自动化收益**包括：
- 节省的人工时间 × 人力成本
- 提高的质量（减少返工）
- 加快的速度（提前上线带来的收益）

**决策规则**：
- ROI > 5：强烈推荐自动化
- ROI 2-5：值得尝试
- ROI < 2：暂不自动化，等待模型成本下降

例如：
- 代码审查：ROI 很高（节省高级工程师时间），适合自动化
- 一次性脚本：ROI 很低（人工写更快），不适合自动化

---

## 第五章：安全与合规——生产环境的底线

### 4.1 沙箱隔离

所有工具执行必须在沙箱中进行，防止模型恶意操作。

沙箱类型：

#### 类型 1：进程沙箱

使用操作系统级别的隔离：

- Linux：namespace + cgroups
- macOS：sandbox-exec
- Windows：Job Objects

**优点**：轻量，性能好  
**缺点**：隔离程度有限，可能被逃逸

#### 类型 2：容器沙箱

使用 Docker 或 containerd：

```python
import docker

client = docker.from_env()
container = client.containers.run(
    "python:3.11-slim",
    command="python script.py",
    volumes={"/host/project": "/workspace"},
    network_disabled=True,  # 禁用网络
    mem_limit="512m",       # 内存限制
    cpu_quota=50000,        # CPU 限制（50%）
    remove=True             # 执行后删除
)
```

**优点**：隔离性好，易于管理  
**缺点**：启动慢，资源开销大

#### 类型 3：虚拟机沙箱

使用 Firecracker 或 gVisor：

**优点**：最强隔离，几乎不可能逃逸  
**缺点**：最重，启动最慢

选择原则：
- 开发环境 → 进程沙箱
- 测试环境 → 容器沙箱
- 生产环境 → 虚拟机沙箱（或容器 + 严格策略）

### 4.2 权限最小化

每个工具和 agent 只拥有完成任务所需的最小权限。

**实践**：

1. **文件系统权限**：
   - 只读访问项目目录
   - 禁止访问 `/etc`、`/home` 等敏感目录
   - 临时文件写入专用目录

2. **网络权限**：
   - 默认禁用外网访问
   - 白名单机制：只允许访问必要的 API
   - 内部服务只能通过内网访问

3. **系统调用权限**：
   - 禁用危险系统调用（如 `ptrace`、`mount`）
   - 限制进程数量
   - 限制文件描述符数量

### 4.3 审计与溯源

所有操作必须可审计、可溯源。

**审计日志内容**：

```json
{
  "timestamp": "2026-05-07T14:23:45Z",
  "session_id": "sess_abc123",
  "agent_id": "agent_xyz789",
  "action": "tool_call",
  "tool": "write_file",
  "arguments": {"path": "/project/src/main.py"},
  "result": "success",
  "user_context": {
    "user_id": "user_001",
    "ip_address": "192.168.1.100",
    "request_id": "req_def456"
  },
  "compliance_tags": ["GDPR", "SOC2"]
}
```

**溯源能力**：

- 任何输出都能追溯到具体的模型调用
- 任何文件修改都能追溯到具体的工具调用
- 任何决策都能追溯到具体的上下文

这对于合规审计至关重要。例如 GDPR 要求"被遗忘权"——用户要求删除数据时，你必须能找到并删除所有相关数据，包括 agent 生成的中间文件、日志、缓存。

### 4.4 合规检查

Harness 必须内置合规检查机制：

#### 数据隐私

- 检测 PII（个人身份信息）泄露
- 自动脱敏敏感数据
- 加密存储和传输

#### 代码合规

- 检测开源许可证冲突
- 扫描安全漏洞（CVE）
- 检查代码规范符合性

#### 行业合规

- 金融：PCI DSS、SOX
- 医疗：HIPAA
- 欧洲：GDPR

大师级 Harness 会根据部署环境自动加载相应的合规模块。

---

## 第六章：团队协作——多人多 Agent 协作

### 6.1 多 Agent 架构

复杂任务通常需要多个 agent 协作。常见的架构模式：

#### 模式 1：主从架构（Master-Worker）

一个主 agent 负责任务分解和协调，多个 worker agent 执行子任务。

```
Master Agent
├─ Worker 1: 前端开发
├─ Worker 2: 后端开发
├─ Worker 3: 数据库设计
└─ Worker 4: 测试编写
```

**优点**：结构清晰，易于管理  
**缺点**：主 agent 成为瓶颈

#### 模式 2：对等架构（Peer-to-Peer）

所有 agent 地位平等，通过消息队列通信。

```
Agent 1 ←→ Message Queue ←→ Agent 2
   ↑                              ↓
   └──────←──────────────────────┘
```

**优点**：去中心化，可扩展性好  
**缺点**：协调复杂，可能出现冲突

#### 模式 3：流水线架构（Pipeline）

Agent 按顺序排列，每个 agent 的输出是下一个 agent 的输入。

```
Planner → Coder → Reviewer → Tester → Deployer
```

**优点**：职责明确，易于调试  
**缺点**：线性执行，速度慢

### 6.2 通信协议

Agent 之间如何通信？2026 年有两个主流协议：

#### MCP（Model Context Protocol）

Anthropic 推出的标准协议，用于 agent 和工具之间的通信。

**特点**：
- 基于 JSON-RPC
- 支持同步和异步调用
- 统一的错误处理

**示例**：

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "src/main.py"}
  }
}

// 响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": "print('Hello, World!')"
  }
}
```

#### A2A（Agent-to-Agent）

新兴的 agent 间通信协议，支持更复杂的协作模式。

**特点**：
- 支持订阅/发布模式
- 支持广播和组播
- 内置身份验证和加密

### 6.3 冲突解决

多个 agent 同时工作时，可能出现冲突：

**冲突类型 1：资源竞争**

两个 agent 同时修改同一个文件。

**解决方案**：
- 文件锁机制
- 乐观并发控制（检测冲突后合并）
- 分区策略（不同 agent 负责不同文件）

**冲突类型 2：决策冲突**

Agent A 决定使用 PostgreSQL，Agent B 决定使用 MySQL。

**解决方案**：
- 优先级机制（某些 agent 有更高决策权）
- 投票机制（多数决）
- 仲裁 agent（专门解决冲突）

**冲突类型 3：目标冲突**

Agent A 要优化性能，Agent B 要优化可读性，两者矛盾。

**解决方案**：
- 明确权衡标准（如"性能优先，可读性其次"）
- 分阶段优化（先保证可读性，再优化性能）
- 人工介入（让用户决定）

### 6.4 协作最佳实践

1. **明确角色边界**：每个 agent 的职责要清晰，避免重叠
2. **标准化接口**：agent 之间的输入/输出格式要统一
3. **共享状态管理**：使用集中式的状态存储，避免状态不一致
4. **异步通信**：尽量使用异步消息，避免阻塞
5. **监控协作效率**：跟踪 agent 之间的等待时间、冲突次数等指标

---

## 结语：Harness Engineering 是新的软件工程

2026 年，软件工程正在经历范式转移：

- **过去**：工程师写代码，计算机执行
- **现在**：工程师设计 Harness，Agent 写代码，计算机执行

Harness Engineering 不是"辅助工具"，它是**新的编程范式**。

掌握 Harness Engineering，意味着你掌握了：

1. **系统设计能力**：设计可靠、可扩展、可维护的 agent 系统
2. **风险控制能力**：在生产环境中安全地部署 agent
3. **成本优化能力**：让 agent 在经济上可行
4. **团队协作能力**：协调多个 agent 高效工作

这才是 2026 年 AI 工程师的核心竞争力。

未来的软件公司会有两种工程师：

- **Harness Engineers**：设计和管理 agent 系统
- **Domain Experts**：提供领域知识和业务逻辑

传统的"程序员"角色会逐渐消失，取而代之的是"Agent Orchestrator"（Agent 编排者）。

你，准备好了吗？

---

## 延伸阅读

1. [Anthropic: Long-running agents design patterns](https://www.anthropic.com/research/long-running-agents)
2. [Anthropic: Managed Agents architecture](https://www.anthropic.com/news/managed-agents)
3. [Model Context Protocol specification](https://modelcontextprotocol.io/)
4. [OpenAI: Swarm multi-agent framework](https://github.com/openai/swarm)
5. [Microsoft: AutoGen multi-agent conversations](https://microsoft.github.io/autogen/)

---

**关于作者**：James Xie，前 eBay 技术负责人，20 年支付领域经验，两项美国机器学习专利持有者。专注于 AI 工程化、Agent 架构设计和企业 AI 落地。公众号「谢先生的 AI 深析札记」。
