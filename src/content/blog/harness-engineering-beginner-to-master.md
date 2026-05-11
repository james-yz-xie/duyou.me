---
title:
  zh: "Harness Engineering 从入门到精通：2026 年，AI 工程师的新必修课"
  en: "Harness Engineering from Beginner to Master: The New Essential Skill for AI Engineers in 2026"
description:
  zh: "当模型推理速度远超人类审查速度时，谁来保证产出的质量、安全和可控？Harness 就是答案——不是换更强的模型，而是给模型一个能可靠工作的环境。"
  en: "When model inference speed far exceeds human review speed, who ensures quality, safety, and control? Harness is the answer—not stronger models, but a reliable working environment for models."
date: "2026-05-06"
category: "AI Engineering"
tags: ["Harness Engineering", "Agent Architecture", "Production AI", "Control Systems"]
draft: false
author: "James Xie"
---

## 前言：速度太快，审查跟不上

2024 年，我们惊叹于 AI 写代码的速度。2026 年，问题变了：一个 agent 一天能产出过去一个团队一个月的代码变更量，但测试、安全审查、部署上线还是人肉速度。产出端在加速，审查端没跟上。这不是什么"革命"，这是一个实实在在的瓶颈。

Harness 的出现，就是为了解决这个具体问题：当模型推理速度远超人类审查速度时，谁来保证产出的质量、安全和可控？

答案不是换更强的模型。2026 年的数据已经说得很清楚：同一模型，改 Harness，成绩能涨十几个点；换模型，可能只涨两三个点。问题不在大脑，在大脑外面缺了一层东西。

这层东西，Anthropic 在 2026 年 4 月给了它一个名字：**Harness**。

---

## 第一章：为什么突然有个 Harness？

### 1.1 从 Prompt Engineering 到 Agent 工具

2024 年，写一个好 prompt 就是核心竞争力。ChatGPT 出来了，谁的 prompt 写得妙，谁的输出就好。那是一个 prompt craftsmanship 的年代——你花两小时打磨一段 system prompt，输出质量能翻一倍。

但 prompt 有一个天然的硬 ceiling：它是一次性输入，模型读完就忘。复杂任务需要状态、需要循环、需要工具调用、需要错误恢复——这些都不是 prompt 能承载的。

所以 2023 到 2024 年，agent 工具爆发了。AutoGPT、LangChain、CrewAI 一个接一个冒出来。大家第一次看到了"让 AI 自主行动"的可能性：给它一个目标，它自己规划步骤、调用搜索、读网页、写文件、执行代码。听起来很美好。

但实际用下来，问题很快暴露：

- **不可靠**：AutoGPT 跑十轮有八轮在兜圈子，最后要么死循环，要么给出一个完全跑偏的结果。
- **黑盒**：LangChain 的"Chain"抽象把控制流藏起来了。模型什么时候调了什么工具、为什么调、中间出了什么错——你很难搞清楚。
- **难以评估**：没有标准 benchmark，"感觉它变好了"不等于真的变好了。改一个 prompt，不知道整体成功率是升了还是降了。
- **难以复用**：每个 agent 都是一套独立的 prompt + 工具组合，换个项目要重新搭一遍。

Agent 工具解决了一个问题（让模型能动起来），但带来了三个新问题（不可靠、不可控、不可评估）。

### 1.2 从 Agent 工具到 Harness

2025 年，模型能力继续暴涨，但 agent 工具的瓶颈开始压倒模型能力的提升。Claude 3.5、GPT-4o、Gemini 1.5 Pro 之间的差距在缩小，基准测试上前几名的分数差从两位数缩到了个位数。换模型带来的提升，从 30% 降到了 3%。

但 agent 的问题没有因为模型变强而消失。恰恰相反——模型越强，agent 能做的事情越多，出错的后果也越严重。一个能自动写代码的 agent，写错了可能直接删库；一个能自动发邮件的 agent，发错了可能泄露商业机密。

2025 年底，工程圈意识到：**问题不在模型，在"包着模型的那一层"没有工程化。**

Agent 工具给了模型手脚，但没有给模型缰绳。Harness 就是这把缰绳——不是限制模型能力，而是让模型能力变得可靠、可控、可评估。

Prompt Engineering 是"告诉模型做什么"。Agent 工具是"给模型手脚让它动起来"。Harness Engineering 是"给模型一个能可靠工作的环境"。

### 1.3 数据说话：Harness 比模型更重要

2026 年初，几组公开数据让工程圈醒了过来。

**LangChain**，2026 年 2 月。同一模型 GPT-5.2-Codex，不换模型，只改 Harness——system prompts、tool routing、verification loops。Terminal-Bench 2.0 的分数从 52.8% 拉到 66.5%，涨了 13.7 分，排名从 Top 30 冲进 Top 5。

**Vercel**，2026 年 3 月。把 agent 身上挂的工具从二十个砍到四个，砍掉 80%。结果成功率从 80% 跳到 100%，token 消耗减半，延迟从 724 秒降到 141 秒。同一模型，问题出在工具设计。

**Anthropic 内部**，Claude Code 框架的 15 项任务评估。代码质量平均分从 49.5 提升到 79.3，提升 60%。而且任务越难差距越大——基础任务涨 23.8 分，进阶涨 29.6 分，专家级涨 36.2 分。

**Princeton CORE-Bench**：同一模型，不同的 scaffold（脚手架），得分 42% 对 78%。

这些数字指向同一个结论：**模型能力在收敛，Harness 设计在分化**。2025 年大家都在选模型，2026 年工程师已经在卷 Harness。

### 1.4 Harness 的工作模式：不是矿工，是流水线

很多人（包括某些 AI）把 Harness 想象成"分布式挖矿"——一堆 agent 像矿工一样各自竞争，用"Proof of Inference"达成共识。这完全是虚构的。Harness 的工作模式不是竞争，是**协作流水线**。

一个典型的 Harness 包含以下组件：

1. **Control Loop（控制循环）**：持续调用模型，管理会话状态，处理工具返回
2. **Tool Router（工具路由）**：把模型的函数调用请求路由到正确的执行器
3. **Guardrails（护栏）**：权限校验、沙箱隔离、审批流程
4. **Memory System（记忆系统）**：短期上下文管理、长期记忆检索、状态持久化
5. **Observability（可观测性）**：日志、追踪、指标、告警

等式很简单：

> **Agent = Model + Harness**

模型是桌上的赌注，大家都能用。Harness 才是你的护城河。

---

## 第二章：Harness 的核心组件

### 2.1 控制循环：Agent 的心跳

控制循环是 Harness 的核心引擎。它的职责很简单：

```python
while not task_complete:
    # 1. 构建当前上下文
    context = build_context(history, tools, state)
    
    # 2. 调用模型
    response = llm.chat(context)
    
    # 3. 解析响应
    if response.has_tool_call:
        # 执行工具
        result = execute_tool(response.tool_call)
        history.append(result)
    else:
        # 最终答案
        return response.text
    
    # 4. 检查终止条件
    if should_stop(history):
        break
```

看起来简单，但魔鬼在细节里：

- **上下文构建**：哪些历史要保留？哪些要压缩？哪些要丢弃？
- **工具执行**：超时怎么处理？失败怎么重试？副作用怎么回滚？
- **终止判断**：什么时候算完成？什么时候算死循环？

Anthropic 的 Claude Code 用了三层控制循环：

1. **外层循环**：管理整个任务的生命周期（初始化 → 执行 → 验证 → 交付）
2. **中层循环**：管理单个子任务的执行（规划 → 编码 → 测试 → 修复）
3. **内层循环**：管理单次模型调用（提示构建 → 推理 → 工具调用 → 结果整合）

每层循环都有自己的状态机、超时策略和错误处理。这种分层设计让 Claude Code 能在长周期任务中保持稳定。

### 2.2 工具路由：从混乱到秩序

早期 agent 工具的问题是"太多太乱"。AutoGPT 默认挂了 20+ 个工具，模型经常不知道该用哪个，或者用错了顺序。

Vercel 在 2026 年 3 月的实验证明：**工具越少越好**。他们把 agent 的工具从 20 个砍到 4 个核心工具：

1. `read_file` - 读取文件内容
2. `write_file` - 写入文件内容
3. `run_command` - 执行 shell 命令
4. `search_codebase` - 搜索代码库

结果：
- 成功率：80% → 100%
- Token 消耗：减少 50%
- 延迟：724 秒 → 141 秒（降低 80%）

为什么？因为**工具设计的本质是约束**。工具越多，模型的决策空间越大，出错概率越高。好的 Harness 不是给模型更多工具，而是给模型更清晰的工具边界。

工具路由的关键原则：

1. **最小化工具集**：只保留必要的工具，砍掉冗余
2. **明确的工具契约**：每个工具的输入/输出格式必须严格定义
3. **工具组合而非嵌套**：避免工具调用工具，保持扁平结构
4. **确定性优先**：能用代码实现的逻辑，不要交给模型判断

### 2.3 护栏：安全不是可选项

Harness 的护栏（Guardrails）是生产环境和玩具项目的分水岭。没有护栏的 agent 就像一个没有刹车的赛车——跑得再快也没用。

护栏分为三层：

#### 第一层：预防性护栏（Preventive）

在模型行动之前拦截危险操作：

- **权限校验**：模型想删除文件？先检查是否有写权限
- **路径白名单**：模型想访问 `/etc/passwd`？拒绝，只允许访问项目目录
- **资源限制**：模型想运行 `rm -rf /`？拦截，检测到危险命令立即终止

#### 第二层：检测性护栏（Detective）

在模型行动之后检查结果：

- **输出验证**：模型生成的代码能通过编译吗？单元测试过了吗？
- **副作用审计**：模型修改了哪些文件？有没有意外删除重要文件？
- **成本监控**：这次任务花了多少 token？超过预算了吗？

#### 第三层：纠正性护栏（Corrective）

发现问题后自动修复：

- **自动回滚**：如果模型的操作导致测试失败，自动 git revert
- **降级策略**：如果模型连续 3 次调用失败，切换到备用模型或人工介入
- **告警通知**：检测到异常行为（如大量文件删除），立即发送告警

Anthropic 的 Managed Agents 把护栏做到了极致：所有工具执行都在沙箱容器中进行，容器的生命周期由 Harness 管理，模型无法直接访问宿主机。即使模型被"越狱"，也只能在沙箱里折腾，不会影响外部系统。

### 2.4 记忆系统：对抗遗忘

LLM 的最大弱点是**失忆**。每次新对话都是一个全新的开始，模型不记得之前说过什么、做过什么。

Harness 的记忆系统解决这个问题，分为三层：

#### 短期记忆（Short-term Memory）

- **上下文窗口**：最近 N 轮对话的历史
- **工作区状态**：当前打开的文件、正在运行的进程、环境变量
- **临时变量**：本次会话中产生的中间结果

短期记忆的特点是**快但易失**。它存在内存里，会话结束就清空。

#### 中期记忆（Mid-term Memory）

- **会话摘要**：把长对话压缩成关键点列表
- **任务进度**：当前任务的完成百分比、已完成的子任务、待办事项
- **决策日志**：模型做出的关键决策及其理由

中期记忆的特点是**结构化且可检索**。它存在数据库或文件系统中，可以跨会话访问。

#### 长期记忆（Long-term Memory）

- **知识库**：项目文档、API 规范、最佳实践
- **用户偏好**：用户的编码风格、常用工具、禁忌事项
- **历史经验**：过去类似任务的成功/失败案例

长期记忆的特点是**持久且语义化**。它通常用向量数据库存储，支持语义搜索。

记忆系统的设计原则：

1. **分层存储**：不同生命周期的数据放在不同的存储层
2. **按需加载**：不要一次性把所有记忆塞进上下文，根据当前任务动态检索
3. **定期清理**：过期的记忆要归档或删除，避免污染上下文
4. **可追溯性**：每条记忆的来源和时间戳都要记录，方便审计

### 2.5 可观测性：看见黑盒内部

没有可观测性的 Harness 就像没有仪表盘的飞机——你不知道飞得怎么样，也不知道什么时候会坠毁。

可观测性包含三个维度：

#### Logging（日志）

记录发生了什么：

```json
{
  "timestamp": "2026-05-06T10:23:45Z",
  "event": "tool_call",
  "tool": "write_file",
  "arguments": {"path": "src/main.py", "content": "..."},
  "result": "success",
  "duration_ms": 234,
  "token_usage": {"prompt": 1234, "completion": 567}
}
```

日志的关键是**结构化**。不要用自由文本，要用 JSON 或类似格式，方便后续分析。

#### Tracing（追踪）

记录因果链：

```
Task: Implement user authentication
├─ Subtask: Design database schema
│  ├─ Tool call: write_file (schema.sql)
│  └─ Result: Success
├─ Subtask: Create API endpoints
│  ├─ Tool call: write_file (auth.py)
│  ├─ Tool call: run_command (pytest)
│  └─ Result: Failed (test error)
│     └─ Retry: Fix test, rerun
│        └─ Result: Success
└─ Subtask: Write documentation
   └─ ...
```

追踪的关键是**层级关系**。每个事件都要有 parent_id，形成树状结构。

#### Metrics（指标）

量化系统表现：

- **成功率**：任务完成率、工具调用成功率
- **效率**：平均任务时长、Token 消耗、成本
- **质量**：代码通过率、用户满意度、返工率
- **可靠性**：平均无故障时间（MTBF）、恢复时间（MTTR）

指标的关键是**趋势分析**。单点数值没有意义，要看长期趋势。

---

## 第三章：Harness 的设计模式

### 3.1 单一职责模式（Single Responsibility）

每个 Harness 组件只做一件事，并做好。

**反例**：一个"万能工具"既能读文件、又能写文件、还能执行命令、还能搜索代码。

**正例**：四个独立工具，每个工具职责明确：
- `read_file`：只读文件，不做其他事
- `write_file`：只写文件，不做其他事
- `run_command`：只执行命令，不做其他事
- `search_codebase`：只搜索代码，不做其他事

好处：
- 更容易测试
- 更容易调试
- 更容易替换实现
- 更容易理解行为

### 3.2 失败快速模式（Fail Fast）

尽早发现错误，而不是等到最后才爆发。

**实现方式**：

1. **前置校验**：在执行工具之前，先检查参数合法性
2. **增量验证**：每完成一个子任务，立即验证结果
3. **超时保护**：任何操作都有超时限制，超时立即终止
4. **断言检查**：在关键节点插入断言，确保状态符合预期

**例子**：

```python
def write_file(path, content):
    # 前置校验
    if not is_safe_path(path):
        raise SecurityError(f"Unsafe path: {path}")
    
    if not validate_content(content):
        raise ValidationError("Invalid content format")
    
    # 执行写入
    with open(path, 'w') as f:
        f.write(content)
    
    # 后置验证
    if not verify_write(path, content):
        raise IntegrityError("Write verification failed")
```

### 3.3 幂等性模式（Idempotency）

同样的操作执行多次，结果应该一致。

**为什么重要**：

- 网络抖动可能导致重试
- 模型可能重复调用同一个工具
- 用户可能手动触发重新执行

**实现方式**：

1. **检查是否存在**：写入文件前，先检查文件是否已存在且内容相同
2. **使用唯一标识**：给每个操作分配 UUID，重复的 UUID 直接跳过
3. **事务性操作**：使用数据库事务或文件系统原子操作

**例子**：

```python
def write_file(path, content):
    # 如果文件已存在且内容相同，跳过
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing = f.read()
        if existing == content:
            return "Skipped (already exists)"
    
    # 否则写入
    with open(path, 'w') as f:
        f.write(content)
    return "Written"
```

### 3.4 观察者模式（Observer）

所有关键事件都发出通知，订阅者可以监听并做出反应。

**应用场景**：

- **审计**：记录所有敏感操作
- **告警**：检测到异常行为时通知管理员
- **自动化**：某些事件触发自动化流程（如代码提交后自动运行 CI）

**实现方式**：

```python
class EventBus:
    def __init__(self):
        self.listeners = {}
    
    def subscribe(self, event_type, callback):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def emit(self, event_type, data):
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(data)

# 使用
bus = EventBus()
bus.subscribe("tool_call", audit_logger.log)
bus.subscribe("error", alert_manager.notify)

# 发射事件
bus.emit("tool_call", {"tool": "write_file", "path": "..."})
```

### 3.5 策略模式（Strategy）

同一个接口，不同的实现策略，可以动态切换。

**应用场景**：

- **模型选择**：根据任务难度选择不同的模型
- **重试策略**：根据错误类型选择不同的重试方式
- **记忆检索**：根据查询类型选择不同的检索算法

**实现方式**：

```python
class RetryStrategy:
    def should_retry(self, error, attempt_count):
        raise NotImplementedError

class ExponentialBackoff(RetryStrategy):
    def should_retry(self, error, attempt_count):
        if attempt_count > 5:
            return False
        wait_time = 2 ** attempt_count
        time.sleep(wait_time)
        return True

class ImmediateRetry(RetryStrategy):
    def should_retry(self, error, attempt_count):
        return attempt_count < 3

# 使用
strategy = ExponentialBackoff()
for attempt in range(10):
    try:
        result = call_llm(prompt)
        break
    except Error as e:
        if not strategy.should_retry(e, attempt):
            raise
```

---

## 第四章：Harness 的评估与优化

### 4.1 评估指标体系

评估 Harness 的好坏，不能只看"能不能完成任务"，要看多个维度：

#### 功能性指标

- **任务完成率**：成功完成的任务数 / 总任务数
- **工具调用准确率**：正确的工具调用数 / 总工具调用数
- **代码通过率**：通过测试的代码比例

#### 效率指标

- **平均任务时长**：从开始到完成的平均时间
- **Token 消耗**：每个任务的平均 token 用量
- **成本**：每个任务的平均成本（美元）

#### 质量指标

- **代码质量评分**：静态分析工具的评分
- **用户满意度**：用户对结果的评分
- **返工率**：需要人工修正的比例

#### 可靠性指标

- **平均无故障时间（MTBF）**：两次故障之间的平均时间
- **平均恢复时间（MTTR）**：从故障发生到恢复的平均时间
- **错误率**：单位时间内的错误次数

### 4.2 A/B 测试框架

优化 Harness 不能靠直觉，要靠数据。A/B 测试是黄金标准。

**实施步骤**：

1. **定义假设**：例如"减少工具数量能提高成功率"
2. **设计实验**：A 组用 20 个工具，B 组用 4 个工具
3. **随机分组**：将任务随机分配到 A 组或 B 组
4. **收集数据**：记录每组的成功率、时长、成本
5. **统计分析**：使用 t-test 或 chi-square 检验差异显著性
6. **决策**：如果 B 组显著优于 A 组，采用 B 组配置

**注意事项**：

- 样本量要足够大（至少 100 个任务）
- 任务难度要均衡分布
- 排除外部因素干扰（如模型版本变化）
- 多次实验验证稳定性

### 4.3 常见优化方向

根据 2026 年的实践经验，以下优化方向最有效：

#### 优化工具设计

- **减少工具数量**：砍掉冗余工具，保留核心工具
- **简化工具接口**：参数越少越好，避免复杂嵌套
- **增强工具文档**：每个工具要有清晰的示例和说明

#### 优化提示工程

- **结构化提示**：使用模板化的提示格式，保持一致性
- **思维链引导**：要求模型逐步推理，而不是直接给答案
- **自我反思**：让模型检查自己的输出，发现错误

#### 优化记忆管理

- **智能压缩**：使用摘要算法压缩长历史
- **相关性检索**：只检索与当前任务相关的记忆
- **定期清理**：删除过期和无用的记忆

#### 优化错误处理

- **分类错误**：区分可恢复错误和不可恢复错误
- **针对性重试**：不同错误类型采用不同重试策略
- **优雅降级**：失败时提供备选方案，而不是直接崩溃

---

## 第五章：Harness 的未来趋势

### 5.1 标准化接口

2026 年，Harness 领域开始出现标准化趋势：

- **MCP（Model Context Protocol）**：Anthropic 推出的工具通信协议，让不同 Harness 可以共享工具
- **A2A（Agent-to-Agent）**：agent 之间的通信协议，支持多 agent 协作
- **OpenTelemetry for AI**：AI 系统的可观测性标准

标准化的好处是**互操作性**。今天你用 Claude Code，明天换 Cursor，后天换 Windsurf，只要它们都遵循 MCP，你的工具就可以无缝迁移。

### 5.2 自适应 Harness

未来的 Harness 不再是静态配置，而是**动态自适应**：

- **自动调参**：根据任务类型自动调整温度、top_p 等参数
- **动态工具选择**：根据当前上下文动态加载/卸载工具
- **智能路由**：根据模型表现动态切换模型
- **自学习**：从历史数据中学习最优策略

Anthropic 已经在实验"Meta-Harness"——一个能自动生成和优化 Harness 配置的 agent。它通过分析数千个任务的执行数据，找出最优的工具组合、提示模板和重试策略。

### 5.3 形式化验证

随着 Harness 在关键领域的应用（如医疗、金融、自动驾驶），**形式化验证**变得越来越重要：

- **安全性证明**：数学证明 Harness 不会执行危险操作
- **活性证明**：证明 Harness 最终会完成任务，不会死锁
- **一致性证明**：证明 Harness 的状态转换是一致的

这不是学术研究，已经有公司在生产环境中使用形式化验证工具（如 TLA+、Coq）来验证 Harness 的正确性。

### 5.4 人机协作新模式

Harness 不是要取代人类，而是要**增强人类**：

- **人在环路（Human-in-the-Loop）**：关键决策由人类审批，日常操作由 agent 执行
- **渐进式自动化**：从辅助模式（人类主导，agent 建议）逐步过渡到自主模式（agent 主导，人类监督）
- **可解释性**：Harness 要能解释自己的决策过程，让人类理解为什么这么做

未来的软件工程师不是"写代码的人"，而是"设计 Harness 的人"。你不再亲自写每一行代码，而是设计一个能让 agent 可靠写代码的系统。

---

## 结语：Harness 是新的编程范式

2026 年，Harness Engineering 已经从"可选技能"变成"必备技能"。

回顾历史：

- 1970 年代：结构化编程成为主流
- 1990 年代：面向对象编程成为主流
- 2010 年代：函数式编程复兴
- 2020 年代：Prompt Engineering 兴起
- **2026 年：Harness Engineering 成为主流**

每一次范式转移，都伴随着生产力的飞跃。Harness Engineering 也不例外。

学会 Harness Engineering，你不是在学一个新工具，而是在掌握一种新的思维方式：

- **从"如何让模型更聪明"转向"如何让系统更可靠"**
- **从"一次性交互"转向"持续协作"**
- **从"黑盒魔法"转向"透明工程"**

这才是 2026 年 AI 工程师的真正竞争力。

---

## 延伸阅读

1. [Anthropic: Long-running agents design patterns](https://www.anthropic.com/research/long-running-agents)
2. [LangChain: Building reliable agents](https://python.langchain.com/docs/concepts/)
3. [Vercel: Agent tool design best practices](https://vercel.com/blog/agent-tool-design)
4. [OpenAI: Codex evaluation framework](https://openai.com/research/codex)
5. [Princeton: CORE-Bench benchmark](https://core-bench.princeton.edu/)

---

**关于作者**：James Xie，前 eBay 技术负责人，20 年支付领域经验，两项美国机器学习专利持有者。专注于 AI 工程化、Agent 架构设计和企业 AI 落地。公众号「谢先生的 AI 深析札记」。
