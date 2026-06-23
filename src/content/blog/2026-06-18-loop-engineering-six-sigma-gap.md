---
title:
  zh: "Loop Engineering 的本质：Agentic AI 的六西格玛缺口"
  en: "The Essence of Loop Engineering: The Six Sigma Gap in Agentic AI"
description:
  zh: "凌晨两点，coding agent 花了 4 小时、调用 127 次模型后宣布'任务完成'。三天后生产环境崩溃。这不是个例，而是当前 Agentic AI 系统的普遍困境。本文用制造业过程控制的思路，分析为什么大多数 loop 还没资格无人值守。"
  en: "At 2 AM, a coding agent spent 4 hours and made 127 model calls before declaring 'task complete'. Three days later, production crashed. This isn't an isolated case, but a common dilemma in current Agentic AI systems. This article uses manufacturing process control thinking to analyze why most loops aren't yet qualified for unattended operation."
date: "2026-06-18"
category: "AI Engineering"
tags: ["Loop Engineering", "Six Sigma", "Agent Architecture", "Process Control", "Quality Assurance"]
draft: false
author: "James Xie"
---

# Loop Engineering 的本质：Agentic AI 的六西格玛缺口

**作者：James Xie**

> 这是「Loop Engineering」系列的第一篇。
>
> 凌晨两点，coding agent 花了 4 小时、调用 127 次模型后宣布"任务完成"。三天后生产环境崩溃：agent 重命名了一个函数，只改了两处调用，第三处因为上下文窗口"看不到"而遗漏。127 个 99% 串在一起，整体正确率只有 36%。
>
> 这不是我编的数字。Lyzr 在 Six Sigma Agent 文档里算过：100 步工作流，每步 99%，累计成功率 36.6%。
>
> 这篇不是概念科普，而是一次工程复盘：用制造业过程控制的思路，看为什么大多数 loop 还没资格无人值守。

---

## 第一章：从 Prompt Engineering 到 Loop Engineering

过去两年，AI 工程化的叙事像爬楼梯一样清晰：

- 2024 年：Prompt Engineering。研究怎么把一次性提示词写好。
- 2025 年：Agent 工具爆发，模型能力也在暴涨，但工具链的瓶颈开始压倒模型带来的提升。工程师们忙着换模型、堆工具。
- 2026 年：先是 Harness Engineering（Anthropic 4 月命名），然后是 Loop Engineering（6 月命名）。问题从"单个 Agent 怎么跑"升级到"一群 Agent 任务怎么持续跑"。

我在 5 月份写的两篇 Harness Engineering 文章，核心论点是：**模型是公共资源，Harness 才是护城河。** 这个判断到今天仍然成立。但 Loop Engineering 把问题往上推了一层：

Harness 解决的是"一个 Agent 能不能可靠完成一个任务"。
Loop Engineering 解决的是"**一系列 Agent 任务能不能在没有人类在场的情况下，持续、可预测、可负担地运行**"。

Peter Steinberger 说：别再提示你的 Agent，去设计 loops。Boris Cherny 说：我的工作就是写 loops。Addy Osmani 把这套实践正式命名。Claude Code 和 Codex 推出了 `/goal`、`/loop`、Automations。所有人的注意力都集中在"从人提示 Agent 到系统提示 Agent"的转移上。

这个转移是真实的。但它带来了一个被忽略的问题：当 Agent 开始在没有人类在场的情况下持续运转，我们凭什么相信它的输出？

这就是 2026 年 6 月 Loop Engineering 热潮背后，那个没人愿意大声说出来的事实：我们不是在讨论一个已经成熟的工程学科，我们是在讨论一个**连基本质量控制都还没建立的新兴流水线**。

制造业在几十年前就回答过这个问题。答案不是"机器更聪明"，而是"流程被度量、被控制、被改进"。那就是六西格玛、精益生产、统计过程控制——一套让复杂系统从 craft 变成 discipline 的方法论。

Loop Engineering 现在正在同一条起跑线上。区别只是，今天的"产品"不是零件，而是代码、文档、决策和业务流程。

这篇文章想说的是：**Loop Engineering 的真正挑战，不是让 loop 跑起来，而是让 loop 的缺陷率低到可以无人值守。**

---

## 第二章：Loop Engineering 不是什么

一个新词火起来的时候，最危险的事就是每个人都把它往自己已有的产品上套。Loop Engineering 也不例外。在讨论它该是什么之前，先澄清四个它不是的东西。

**第一，不是每个 cron job 都叫 Loop Engineering。**

如果你写了一个脚本，每天凌晨 3 点触发一次 Agent，这不叫 Loop Engineering。这叫定时任务。Loop Engineering 的关键不是"定时触发"，而是**触发之后，系统能否自主地判断任务是否完成、是否出错、是否该停止**。没有验证和终止条件的循环，只是无限重试的高级版。

**第二，不是用了 /goal 或 /loop 命令就自动进入 Loop Engineering。**

Claude Code 的 `/goal` 和 `/loop`，OpenAI Codex 的 Automations，这些是很好的**原语**（primitive），但原语不等于方法论。就像有了螺丝刀不等于你会修表。大多数人用 `/goal` 的方式，只是换了个入口发更长的 prompt 而已。真正的 Loop Engineering 发生在命令背后：你怎么定义完成条件？怎么设计验证器？怎么控制成本和风险？

**第三，不是多 Agent 就叫 Loop Engineering。**

三个 Agent 互相调用、一个 Orchestrator 调度五个 Worker，这听起来很 Loop，但如果它们之间没有清晰的误差隔离和状态传递机制，那只是一个**分布式的错误放大器**。我在 Harness Engineering 第二篇里写过：多 Agent 编排有六种模式，每种都有自己的"死法"。Loop Engineering 要解决的不是"怎么让多个 Agent 一起跑"，而是"怎么让多个 Agent 一起跑之后，系统的可靠性不崩溃"。

**第四，不是自动化就等于 Loop Engineering。**

传统 RPA 也是自动化的，但它执行的是 predefined 步骤，没有自主判断。Loop Engineering 里的 loop 必须包含**决策**——感知状态、评估结果、决定是否继续。如果一个流程的每一步都是固定的，那它是 automation；如果它在运行时根据反馈调整自己的下一步，那它才进入 Loop Engineering 的范畴。

这四个"不是"，指向同一个"是"：

> **Loop Engineering 是一种针对 Agentic 系统的过程控制方法论。**

它关心的不是 loop 能不能跑起来，而是 loop 跑起来之后的**可靠性、可测性、可控性**。

---

## 第三章：六西格玛给 Loop Engineering 的一记耳光

六西格玛（Six Sigma）是一个被制造业讲烂了的概念。它的核心指标只有一个：**每百万次机会中的缺陷数**（DPMO, Defects Per Million Opportunities）。

- 1 Sigma：约 690,000 DPMO
- 2 Sigma：约 308,000 DPMO
- 3 Sigma：约 66,800 DPMO
- 4 Sigma：约 6,210 DPMO
- 5 Sigma：约 233 DPMO
- 6 Sigma：3.4 DPMO

银行核心系统、航空电子、医疗设备，通常要求 5–6 Sigma。丰田生产线的某些环节，甚至追求 7 Sigma。

那么 Agentic AI 现在在什么水平？

我们先看一组相对硬的 benchmark。你之前 Harness Engineering 文章里引用的数字：

- LangChain Terminal-Bench：同一模型，只改 Harness，成功率从 52.8% 提升到 66.5%
- Anthropic Claude Code 15 项任务：代码质量从 49.5 分提升到 79.3 分
- Princeton CORE-Bench：同一模型不同 scaffold，42% 对 78%
- Vercel：把 20 个工具砍到 4 个，成功率从 80% 跳到 100%

这些数字里有一个共同区间：**复杂 Agent 任务的成功率，往往在 50%–80% 之间。** 换句话说，每跑 10 次，可能有 2 到 5 次出各种问题。

Corvair.ai 最近把这个现象套到 Six Sigma 框架里，给出了一个相当刺耳的启发式评估——

> **如果把复杂多步 Agent 流程的"成功率"粗暴地映射成 sigma 水平，它大约落在 1.5–2.5 Sigma 之间。**

这个映射不是精密测量，更像是一种警告：企业级关键系统要求 5–6 Sigma，而当前 Agent 循环的可靠性可能还差着两到三个数量级。

当然，这个对比本身有点不公平。Agentic 任务的"失败"定义，和制造业零件尺寸超差不是一回事。但正因为定义还不清晰，问题才更严重——**很多人根本不知道自己 loop 的"缺陷率"是多少**。

为什么差距这么大？

因为 Agent 不是确定性程序。它是概率性推理 + 外部工具 + 状态变化的混合体。每一步都引入随机性。而随机性会叠加，不是线性叠加，是**乘法叠加**。

这就是 Six Sigma 要解决的问题：不是让每一步都做到 100%——那不可能——而是让整个过程的变异被控制在可接受的范围内，并且**先知道变异有多大**。

---

## 第四章：三层 Sigma 约束链

Corvair 把 Agentic 系统的质量拆成三层，这个框架非常值得一偷。但需要先说明：**这三层不是精确测量，而是帮助我们定位瓶颈的概念透镜**。

### Data Sigma：输入数据的质量

Agent 不是从零开始思考的。它读取代码库、文档、数据库、API 返回、CI 日志。这些输入的质量，决定了 Agent 输出的上限。

制造业有个老话："garbage in, garbage out"。Agentic AI 把这个道理放大了十倍，因为 Agent 会主动调用工具去获取输入。如果 RAG 返回了错误的文档、如果 CI 日志被截断、如果数据库字段含义不明，Agent 会基于错误输入做出错误决策，而且因为它的"自信"，它会继续执行下去。

一个企业里未经治理的数据源——混合了结构化表、非结构化文档、实时 API 和临时文件——很难给 Agent 提供稳定可信的输入。Corvair 用"低于 3.5 Sigma"来形容这种状态，意思是：输入层本身就可能是整个系统里最薄弱的环节。

### Process Sigma：流程本身的可重复性

给定同样的输入，Agent 能不能稳定地产生同样的输出？

传统软件可以。Agent 不行。温度参数、上下文窗口滑动、工具返回顺序、模型版本更新，都会让结果变化。同一个 prompt，昨天跑过，今天可能不过。

Process Sigma 衡量的就是这种稳定性。从我们前面引用的 benchmark 来看，复杂 Agent 任务的端到端成功率在 50%–80% 之间波动。用 sigma 语言粗略映射，大致落在 1.5–2.5 Sigma 区间。

这个区间不是权威结论，而是一个**起点**——它告诉你：在把 Loop 投入无人值守生产之前，你至少得知道这个数字是什么。

### Agent Sigma：多 Agent 协作时的有效质量

当多个 Agent 串行或并行工作时，误差会传递和放大。一个 Agent 的小错，会成为下一个 Agent 的输入偏差。如果三个 Agent 各以 95% 准确率工作，串联后的整体准确率只有 86%。五个串联，只有 77%。

Agent Sigma 永远不可能超过 Process Sigma，Process Sigma 又受 Data Sigma 限制。所以 Corvair 的这句话仍然成立：**"你不能用 3 Sigma 的数据、5 Sigma 的流程和 2 Sigma 的 Agent，跑出一个 6 Sigma 的业务。"**

最弱的那一环，决定天花板。

这个三层约束链，画成图只是一张漂亮的幻灯片。真正有用的是把它变成一份**控制清单**。下面这张表用了一个"每日 CI 失败自动修复 Loop"当例子，把三层约束翻译成可检查、可改进的工程动作：

| 层级 | 瓶颈是什么 | 典型检查项 | 改进动作 |
|---|---|---|---|
| Data Sigma | 输入数据质量差 | CI 日志是否完整？Issue 描述是否可解析？代码索引是否新鲜？ | 加日志重试、给 Issue 加必填字段、缩短索引周期 |
| Process Sigma | 流程不可重复 | 端到端成功率多少？同输入两次运行是否一致？死循环/超时率多少？ | 固定模型版本、加 no-progress detector、设迭代上限 |
| Agent Sigma | 多 Agent 误差传递 | 是否有独立 verifier？子 Agent 输出是否结构化？错误是否级联？ | Maker-Checker 分离、强制 JSON schema、加 circuit breaker |

这张表的价值不是给出一个通用模板，而是展示一种思考方式：**每一层都要有自己的度量、缺陷定义和改进动作**。如果你只优化 Agent 层，但 Data 层一团糟，那就像给一条漏水的管道加压——越用力，漏得越多。

---

## 第五章：复合误差

让我把那个 99% 的例子再展开一点，因为这是 Loop Engineering 所有焦虑的源头。

假设你的 Agent 工作流有 100 个逻辑步骤，每步准确率都是 99%。看起来很高吧？比一个普通程序员手动操作还稳。

但累计成功率是：

> 0.99^100 = 36.6%

也就是说，**跑一次，有六成概率失败**。

如果你把每步准确率提升到 99.5%：

> 0.995^100 = 60.6%

好了一些，但仍然不到三分之二。

要达到 90% 的累计成功率，每步准确率需要达到 99.9%。要达到 99%，每步需要 99.99%。

这个数字意味着什么？

意味着**单点优化已经不够了**。你再怎么换更强的模型，也不可能把每一步都推到 99.99%。GPT-6 也做不到，因为问题的根源不是模型能力，而是**步骤太多了**。

制造业在 1980 年代就明白了这个道理。摩托罗拉当年推动 Six Sigma，不是因为他们的工人变强了，而是因为他们意识到：复杂产品由成千上万个工序组成，如果每个工序都允许一定缺陷，最终产品几乎必然有缺陷。唯一的解法，是把整个系统的缺陷率当作一个系统问题来管理，而不是单个工序的问题。

Loop Engineering 现在站在同一个路口。

---

## 第六章：为什么"换模型"不是答案

每当 Agent 失败，很多人的第一反应是：换更强的模型。

这个直觉在 2024 年是对的。当时 GPT-4 和 Claude 之间的差距确实能决定任务成败。但到了 2026 年，模型能力已经收敛。Claude、GPT、Gemini 在常见 coding 任务上的差距，往往只有几个百分点。

更重要的是：**模型能力的提升，无法对抗复合误差的指数衰减。**

假设你通过换模型，把每步准确率从 99% 提升到 99.5%。在 100 步工作流里，累计成功率从 36.6% 提升到 60.6%。这是 24 个百分点的提升，看起来不错。但如果是 200 步呢？0.995^200 = 36.7%。你又回到了原点。

模型越强，Agent 能做的事越多。Agent 能做的事越多，步骤就越多。步骤越多，复合误差越严重。**更强的模型，可能只是在更快地制造更复杂的失败。**

这也是为什么我把 Harness Engineering 称为"护城河"而不是"升级包"。Harness 做的不是让模型更聪明，而是让模型的聪明变得可控。Loop Engineering 要继承这个思路，但它需要比 Harness 多一样东西：**过程度量**。

没有度量，就没有改进。没有西格玛水平的概念，Loop Engineering 就永远只是 vibe coding 的高级版。

---

## 第七章：制造业教给 Loop Engineering 的三件事

六西格玛不是唯一的方法论，但它代表了一种思维模式。Loop Engineering 要成熟，必须借走制造业的三件东西。

### 第一，把"完成"重新定义成"在规格内"

制造业不会说"这个零件做完了"。它会问："这个零件的尺寸、硬度、表面粗糙度，是不是都在规格范围内？"

Agentic 系统现在太爱说"做完了"。Agent 跑完一轮，告诉你"测试通过"，但你真的知道它做了什么吗？测试覆盖了哪些路径？有没有修改不该改的文件？有没有引入新的依赖？

Loop Engineering 需要建立**完成规格**（Done Criteria）：不是 Agent 自己说完成，而是一组外部可验证的条件必须全部满足。这些条件要写得像制造业的质检单一样具体：

- 所有单元测试通过
- 类型检查无错误
- 没有修改非目标文件
- 新增代码覆盖率不低于 X%
- 依赖变更经过人工确认

只有这些条件全部绿，才叫一次"良品"输出。

### 第二，用控制图而不是快照看质量

制造业不会只看一个产品合不合格，它会画控制图，看过程是不是稳定。

Loop Engineering 也需要自己的控制图。Digital Applied 在 5 月份发布的一套 10-KPI 面板，就是一个很好的起点：

- **Completion rate**：多少比例的循环真正跑完了
- **Stage abandonment**：多少循环在中途放弃
- **Retry depth**：平均每步重试多少次
- **Cost per success**：每次成功输出的真实成本
- **Human-in-the-loop frequency**：多久需要人工介入一次
- **Eval-fail rate**：评估层拒绝的比例
- **Drift signals**：输出质量是否随时间漂移
- **Incident frequency**：由 Agent 引发的事故数量

这些指标的核心价值，不是告诉你"这次跑得好不好"，而是告诉你"**这个过程是不是在控制之内**"。

### 第三，冗余和验证比聪明更可靠

Lyzr 的 Six Sigma Agent 提供了一个很反直觉的方案：不用大模型，用很多个小模型。

他们的逻辑是：把任务拆成极小的原子步骤，然后让 5 个便宜的小模型对每个步骤做共识投票。即使每个小模型的准确率只有 95%（比大模型差），5 个投票后的系统错误率可以降到 0.11%。如果投票有分歧，再动态增加到 13 个模型，把错误率推到 Six Sigma 级别。

这个思路和制造业的"防错"（Poka-Yoke）一模一样：不依赖工人的绝对专注，而是设计一个系统，让错误很难发生，或者很容易被捕获。

Loop Engineering 的成熟标志，不是 Agent 变得多聪明，而是**系统变得多不容易出错**。

---

## 第八章：Loop Engineering 的"道"

Loop Engineering 这个词会火，会退烧，会被下一个 buzzword 取代。但它指向的问题不会消失：

> **当 AI 系统开始代替人做复杂决策时，如何保证这些系统的输出是可预测、可验证、可改进的？**

术语是"可道之道"，会不断更新；真正不变的是对复杂系统进行过程治理的需求。

这个问题不是 AI 独有的。制造业经历过，金融业经历过，航空业经历过。它们的答案也不是"更聪明的工人"，而是"**更好的流程、更好的度量、更好的控制**".

六西格玛、精益生产、TQM、SPC（统计过程控制），这些方法论在各自的时代都不是炫技，而是**让复杂系统从 artisan craft 变成 industrial discipline**。

Loop Engineering 正在走同一条路。今天我们看到的那些 loop 框架、/goal 命令、automation 工具，只是这条路上的早期工具。真正成熟的 Loop Engineering，会看起来像一套**针对 Agentic 系统的过程控制方法论**：

- 定义 CTQ（Critical to Quality）
- 建立 DPMO 基线
- 用 DMAIC 持续改进
- 设计防错和冗余
- 用控制图监控过程稳定性
- 把人工介入点当作控制阀，而不是拐杖

---

## 第九章：结语

2026 年 6 月，所有人都在讨论 Loop Engineering。这是一个好现象，说明行业意识到了下一个瓶颈在哪。

但我担心的是，这个概念会在三个月内被滥用。每一个 cron job 都会被称为 loop，每一次自动重试都会被称为 loop engineering，每一篇营销文都会告诉你"只要用我们的工具，就能实现自治"。

如果 Loop Engineering 只是换个名字卖 automation，那它不会有任何进步。

真正的 Loop Engineering，应该像制造业的 Six Sigma 一样无聊：不是关于"Agent 能做多酷的事"，而是关于"**Agent 做的事，能不能稳定地达到规格**".

你可以用 99% 准确率的 Agent，但只要步骤够多，它就是一场赌博。

你可以设计一个看起来很聪明的 loop，但只要没有度量、没有控制、没有防错，它就是一台会自己运转的缺陷制造机。

Loop Engineering 的下一课，不是怎么写更复杂的 loop。

是**怎么让 loop 的缺陷率，从十万分之一，降到百万分之一**。

---

## 系列预告

这篇文章是 Loop Engineering 系列的第一篇，讲的是问题本身：为什么 Agent 循环的可靠性，和企业级生产质量之间还隔着两到三个数量级。

下一篇会进入测量层：**《如何测量一个 Loop：从 Vibe 指标到过程指标》**。我会把 Agentic 流程的健康指标和制造业的 SPC 思路结合起来，给出一套适合个人或小团队落地的 Loop 度量框架。

第三篇会进入改进层：**《如何把 Loop 从 1 Sigma 推到 4 Sigma》**。核心不是换更强的模型，而是任务分解、独立验证、共识冗余和人工接管点的设计。

---

> **金句卡片**
>
> - "127 个 99% 串在一起，整体正确率是 36%。"
> - "你不能用 3 Sigma 的数据、5 Sigma 的流程和 2 Sigma 的 Agent，跑出一个 6 Sigma 的业务。"
> - "更强的模型，可能只是在更快地制造更复杂的失败。"
> - "Loop Engineering 的成熟标志，不是 Agent 变得多聪明，而是系统变得多不容易出错。"
> - "真正的 Loop Engineering 应该像 Six Sigma 一样无聊：不是关于 Agent 能做多酷的事，而是关于 Agent 做的事能不能稳定地达到规格。"

---

## 参考来源

- Addy Osmani, "Loop Engineering", 2026-06-07
- Peter Steinberger, X post on loops vs prompting, 2026-06-07
- Boris Cherny, Anthropic Claude Code commentary, June 2026
- Corvair.ai, "Six Sigma for Agentic AI", 2026
- Lyzr.ai, "Six Sigma (6σ) Agent", 2026-04-21
- Digital Applied, "Agentic Workflow Completion Metrics: Pipeline Health 2026", 2026-05-12
- Agiflow, "Optimise Cost and Speed of Agentic Workflow", 2024-08-03
- James Xie, "Harness Engineering 从入门到精通", 2026-05-06
- James Xie, "Harness Engineering 从精通到大师", 2026-05-07
