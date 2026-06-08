---
title:
  zh: "RAG 从入门到精通：长上下文时代的能力边界与架构演进"
  en: "RAG from Beginner to Master: Capability Boundaries and Architecture Evolution in the Long Context Era"
date: "2026-05-18"
description:
  zh: "深度解析 RAG 在长上下文时代的定位变化，从入门实践到架构选型，再到异常检测场景的真实局限"
  en: "Deep analysis of RAG's positioning in the long context era, from beginner practices to architecture selection, and real limitations in anomaly detection scenarios"
category: "AI Architecture"
tags: ["RAG", "LLM", "Vector Database", "Knowledge Base"]
draft: false
author: "James Xie"
---

## 前言：RAG 的"中年危机"

2023 年，向量数据库是 AI 赛道最热的词。Pinecone 融资过亿，Weaviate、Qdrant、Milvus 一个接一个冒出来。每个做 LLM 应用的人都在问："我的知识库怎么接向量数据库？"

2024 年，RAG 成了标准架构。LLM + Embedding + Vector DB，这个公式被写进了无数技术方案。客服机器人、企业内部知识库、文档问答——RAG 似乎解决了一切"模型不知道"的问题。

2025 年，上下文窗口开始暴涨。Claude 3 给到 200K，Gemini 1.5 Pro 给到 200 万 token。一个声音开始弥漫："直接把所有文档塞进去不就行了，还要什么向量数据库？"

2026 年，这个问题有了答案。**RAG 没有死，但它的角色发生了根本性的迁移。**

长上下文没有杀死 RAG，但它撕掉了 RAG 的遮羞布——让我们看清了 RAG 真正的能力边界。RAG 在"已知问题 × 已知知识"的象限里依然是最优解，但在"未知问题 × 结构性异常"的象限里，它几乎无能为力。

这篇文章要说的，不是怎么搭一个 RAG 系统。是怎么**正确地认识 RAG、用好 RAG、并在它的边界之外找到补位方案**。

---

## 第一章：为什么突然有人问 RAG 还 work 不 work？

### 1.1 从 Prompt Engineering 到 RAG 的爆发

2023 年，写一个好 prompt 就是核心竞争力。但 prompt 有一个硬 ceiling：模型的知识截止在训练数据那一天，之后的世界它一无所知。

RAG 的出现解决了这个痛点：不把知识塞进模型权重里，而是存在外部数据库，用的时候按需检索。这相当于给 LLM 配了一个外置大脑——模型负责推理，RAG 负责供给知识。

2023 到 2024 年，RAG 架构爆发式增长。标配是：

```
用户提问 → Embedding 编码 → Vector DB 相似度检索 → Top-K 文档 → 塞进 Prompt → LLM 生成回答
```

这套架构简单、通用、效果好。客服问答、技术文档检索、企业内部知识库——这些标准化场景里，RAG 的成功率通常较高，但具体数字高度依赖文档质量和查询类型。

但问题很快暴露。

### 1.2 长上下文时代的冲击

2025 年，上下文窗口进入百万 token 时代。Gemini 1.5 Pro 的 200 万 token，相当于能一次性塞进去 3000 页 PDF。Claude 3 的 200K，也够塞下一本中等厚度的技术手册。

"还要向量数据库干嘛？直接把全部文档塞进 prompt，让模型自己找不就行了？"

这个说法在 2025 年反复出现，很多人信以为真。但运行一段时间后，数据说话了。

### 1.3 数据说话：RAG 和长上下文各有胜负

2025 年到 2026 年，几组大规模 benchmark 给出了清醒的回答。核心结论可以概括为一张表：

| 场景 | RAG 表现 | 长上下文表现 | 关键瓶颈 |
|------|---------|------------|---------|
| **单点事实检索**（如"SSL 证书怎么配"） | **好**（LaRA: 弱模型上优于 LC） | 好（强模型略优，但成本高 10-20 倍） | 注意力稀释 |
| **跨文档比较**（如"比较 A、B 产品差异"） | 差（Loong: Normal RAG 33.0 分） | **好**（Full Context 68.0 分） | 丢失全局上下文 |
| **多跳/时序/结构性推理**（如异常根因） | **很差**（KYC RAGAS: Context Recall 跌至 0.08） | 中等（但成本极高） | 检索不到结构性证据 |

三组数据指向同一个判断：

- **RAG 在"已知问题 × 已知知识"的象限里依然是最优解**——成本低、延迟低、来源可追溯。
- **RAG 在"复杂推理 × 结构性查询"的象限里系统性失效**——不是因为检索技术不够先进，而是因为问题本身就不适合用语义相似度来解决。

详细的数据分析留到第八章——那里我们会用这些 benchmark 来解释"为什么 RAG 在异常检测和根因分析中会失败"。


### 1.4 核心结论：RAG 的边界不是技术债务，是认知边界

三组测试指向同一个结论：

> **RAG 做得好的是"在已知知识里找已知问题的答案"。RAG 做不好的是"在已知知识里找未知问题的线索"——更不用说"在未知领域里探索未知问题"。**

长上下文解决的是"容量"问题。RAG 解决的是"精准性"和"选择性"问题。异常检测和根因分析需要的，是"因果推理"和"结构理解"——这两者都不是 RAG 的强项。

2026 年的正确认知：**RAG 没有过时，但被高估了能力边界。** 它的定位应该是"精准证据获取层"，而不是"万能知识引擎"。

---

## 第二章：入门——RAG 到底是什么

### 2.1 一个最小可运行的 RAG

说再多不如看代码。下面是一个最简 RAG 的骨架，不到 30 行 Python，展示核心流程：

```python
import numpy as np

class MinimalRAG:
    """最简 RAG：文档编码 → 向量存储 → 相似度检索 → 上下文生成"""
    
    def __init__(self, embed_fn, llm_fn):
        self.docs = []        # 原始文档片段
        self.vectors = []     # 向量表示
        self.embed_fn = embed_fn   # Embedding 函数
        self.llm_fn = llm_fn       # LLM 生成函数
    
    def add_documents(self, texts):
        """添加文档到知识库"""
        for text in texts:
            self.docs.append(text)
            self.vectors.append(self.embed_fn(text))
    
    def query(self, question, top_k=3):
        """检索 + 生成"""
        # 1. 把问题编码成向量
        q_vec = self.embed_fn(question)
        
        # 2. 计算相似度，找出最相关的 Top-K
        similarities = [np.dot(q_vec, d_vec) for d_vec in self.vectors]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        retrieved = [self.docs[i] for i in top_indices]
        
        # 3. 组装上下文，调用 LLM
        context = "\n\n".join([f"[文档 {i+1}] {doc}" for i, doc in enumerate(retrieved)])
        prompt = f"基于以下文档回答问题：\n\n{context}\n\n问题：{question}\n\n回答："
        
        return self.llm_fn(prompt)
```

这就是 RAG 的全部精髓：**编码、存储、检索、生成**。没有黑魔法。你完全可以从零写一个。

### 2.2 RAG 不是 Vector DB，也不是简单检索

新手最容易混淆的三个概念：

|        | Embedding                       | Vector DB                          | RAG                         |
| ------ | ------------------------------- | ---------------------------------- | --------------------------- |
| 是什么    | 把文本变成向量的模型                      | 存储和检索向量的数据库                        | 完整的系统（检索 + 生成）              |
| 解决什么问题 | 语义压缩                            | 高维向量相似度搜索                          | 让 LLM 基于外部知识回答问题            |
| 常见产品   | OpenAI text-embedding, BGE, M3E | Pinecone, Milvus, Qdrant, Weaviate | 上面所有 + LLM +  orchestration |

**Vector DB ≠ RAG。** 向量数据库只是 RAG 系统中的一个存储层。RAG 的真正价值在于**检索策略**和**上下文组装**——怎么检索、检索什么、怎么把检索结果塞进 prompt，这些决定了最终输出的质量。

### 2.3 和长上下文"直接塞"的根本区别

| 维度 | 长上下文全量塞入 | RAG |
|------|----------------|-----|
| 成本结构 | O(n) 按 token 线性增长 | O(1) 检索固定成本 + 短上下文生成 |
| 实时性 | 静态快照（prompt 构建时冻结） | 动态更新（索引可实时重建） |
| 精准控制 | 弱（全部输入，无前置过滤） | 强（精确控制检索范围、策略、来源） |
| 多源异构 | 受限（主要是文本） | 灵活（可融合结构化数据、图、时序） |
| 来源可追溯 | 弱（不知道用了文档的哪部分） | 强（明确引用来源，可审计） |
| 注意力效率 | 低（关键信息被稀释） | 高（只送入最相关的片段） |

**关键洞察：长上下文是"大仓库"，RAG 是"精准供应链"。** 两者不是替代关系，是互补关系。

---

## 第三章：入门——你的第一个 RAG

### 3.1 选一个具体的任务

不要上来就想"帮我查所有文档"这种模糊目标。选一个边界清晰、可验证的任务。

> 任务示例：读取一份产品 FAQ 文档 → 用户问"退款多久到账？" → 系统检索相关段落 → 给出准确回答，并标注来源。

这个任务有明确的输入、可预期的输出、一眼能验证的成败标准。

### 3.2 准备文档：分块策略决定检索质量

RAG 的第一步不是写代码，是**怎么切文档**。切得好不好，直接决定检索质量。

最常见的错误：按固定长度切（比如每 512 token 切一块）。这样会把一个完整的段落拦腰斩断：

```
原始文本：
"退款处理流程如下：第一步，用户提交申请；第二步，客服审核；
第三步，财务确认；第四步，原路退回。通常情况下，退款会在 3-7 个工作日到账。"

错误切分（每 20 字切一块）：
块 1: "退款处理流程如下：第一步，用户提交"
块 2: "申请；第二步，客服审核；第三步，财"
块 3: "务确认；第四步，原路退回。通常情况下"
```

块 1 和块 2 单独被检索到时，语义都不完整。模型拿到这些碎片，根本无法回答"退款流程是什么"。

**正确的起步策略**：

1. **按语义边界切**：以段落、小节、列表项为边界，保持语义完整性。
2. **块大小 200-500 token**：太小则丢失上下文，太大则检索精度下降。
3. **相邻块重叠 20%**：比如块 A 覆盖段落 1-3，块 B 覆盖段落 3-5，重叠的段落 3 作为"桥梁"保证连续性。

```python
def chunk_text(text, max_tokens=300, overlap_tokens=50):
    """按段落边界切分，保持语义完整"""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para_tokens = len(para) // 4  # 粗略估算
        if current_length + para_tokens > max_tokens and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            # 保留最后一段作为重叠
            current_chunk = current_chunk[-1:] if overlap_tokens > 0 else []
            current_length = len(current_chunk[0]) // 4 if current_chunk else 0
        current_chunk.append(para)
        current_length += para_tokens
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks
```

### 3.3 写检索循环

检索的核心就三个参数：

- **Top-K**：返回多少个最相关的片段。K 太小会漏掉关键信息，K 太大会让 prompt 膨胀、注意力稀释。起步建议 **K=3-5**。
- **相似度阈值**：低于某个分数的文档直接丢弃，防止噪声进入上下文。起步建议 **cosine similarity > 0.7**。
- **元数据过滤**：在向量搜索之前，先用元数据（文档类型、时间、权限）过滤，缩小搜索空间。

```python
def retrieve(self, query, top_k=5, min_score=0.7, metadata_filter=None):
    """带过滤和阈值控制的检索"""
    # 1. 元数据预过滤
    candidates = self.docs
    if metadata_filter:
        candidates = [d for d in candidates 
                      if all(d.meta.get(k) == v for k, v in metadata_filter.items())]
    
    # 2. 向量相似度计算
    q_vec = self.embed_fn(query)
    scored = []
    for doc in candidates:
        score = cosine_similarity(q_vec, doc.vector)
        if score >= min_score:
            scored.append((score, doc))
    
    # 3. 排序返回 Top-K
    scored.sort(reverse=True)
    return [doc for _, doc in scored[:top_k]]
```

### 3.4 上下文组装：怎么塞很关键

检索到的文档片段，怎么组织进 prompt，直接影响模型理解。

**差的组装**：
```
文档1: [一段文字]
文档2: [一段文字]
文档3: [一段文字]
问题：[用户问题]
```

**好的组装**：
```
你是一位产品支持专家。请基于以下参考文档回答问题。
如果文档中没有相关信息，请明确说明"根据现有文档无法回答"。

[参考文档]
来源：退款政策 V2.3，第 3 节
内容：退款处理流程为：用户提交申请 → 客服审核（1-2 工作日）→ 财务确认 → 原路退回。通常 3-7 个工作日到账，具体取决于支付渠道。

来源：常见问题，条目 #14
内容：如果超过 7 个工作日仍未到账，请检查：1) 原支付渠道是否支持退款；2) 银行卡是否已过期。

[用户问题]
退款多久到账？
```

**组装原则**：
1. **标注来源**：文档名、章节、版本——让回答可追溯。
2. **结构化分隔**：用明确的标记（`[来源]`、`[内容]`）分隔，不要让模型自己猜。
3. **注入指令**：明确告诉模型"如果文档里没有，就说不知道"——减少幻觉。

### 3.5 检查点：你入门了

如果你的 RAG 满足以下条件，恭喜，你入门了：

- [ ] 文档按语义边界分块，不是固定长度硬切
- [ ] 有 Top-K 和相似度阈值控制，不是返回所有结果
- [ ] 上下文组装有来源标注和结构化分隔
- [ ] 有基本的幻觉防护（"文档中没有则明确说明"）
- [ ] 跑通了一个完整 workflow，输入问题 → 检索 → 生成 → 一眼验证回答质量

到这里，你已经写了一个比市面上 80% 的"RAG demo"更靠谱的东西。

---

## 第四章：进阶——RAG 的五大核心组件

入门之后，你会发现"能跑通"和"能上线"之间差着五个核心组件。它们共同决定 RAG 在生产环境里的可靠性。

### 4.1 文档处理与分块（Chunking）

分块不是一次性操作，是一个流水线：

```
原始文档 → 格式解析（PDF/Word/HTML/Markdown）→ 文本清洗 → 语义分块 → 元数据提取 → 向量化 → 入库
```

**进阶分块策略：**

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 固定长度 | 均匀文档（如小说） | 简单、均匀 | 语义断裂 |
| 段落边界 | 结构化文档（FAQ、手册） | 语义完整 | 段落长度差异大 |
| 递归切分 | 层次文档（论文、报告） | 保留层级结构 | 实现复杂 |
| 语义切分 | 任意长文 | 按意义边界切 | 需要额外模型 |
| Agent 切分 | 复杂多模态 | 智能决策切分点 | 成本高 |

**生产环境建议**：从"段落边界 + 重叠"开始，遇到瓶颈再升级。

### 4.2 Embedding 模型选择

Embedding 模型是 RAG 的"感官系统"——它决定了你的文档在向量空间里怎么分布、怎么被检索到。

2026 年的选择格局：

| 模型 | 维度 | 语言 | 特点 |
|------|------|------|------|
| text-embedding-3-large (OpenAI) | 3072 | 多语言 | 通用性强，成本高 |
| BGE-M3 (BAAI) | 1024 | 多语言 | 开源，支持稀疏+密集混合 |
| GTE-Qwen2-7B (Alibaba) | 3584 | 中英最优 | 长文本，中文场景首选 |
| E5-Mistral-7B (Microsoft) | 4096 | 多语言 | 检索精度高，推理成本高 |

**选型铁律**：不要只看 benchmark 分数，要看**你的文档类型**和**查询类型**的匹配度。一个医学文档库用通用 embedding，效果可能还不如用一个在医学语料上微调过的中等模型。

### 4.3 检索策略：从相似度到智能召回

基础检索是"单个向量查询 → 近似最近邻（ANN）搜索"。生产环境里，这远远不够。

**层次化检索策略：**

**第一层：粗排（召回）**
- 用轻量 Embedding + ANN 快速召回 Top-100
- 目标：不漏掉任何可能相关的文档

**第二层：精排（重排序）**
- 用更强的 cross-encoder 或重排序模型对 Top-100 重新打分
- 目标：把真正相关的文档排到前面

**第三层：过滤**
- 元数据过滤（时间、权限、文档类型）
- 相似度阈值过滤
- 去重（同一文档的不同 chunk 只保留最相关的一个）

```python
# 两层检索示例
def advanced_retrieve(query, top_k=5):
    # 第一层：Embedding 快速召回
    q_vec = embed_light(query)
    candidates = vector_db.ann_search(q_vec, top_k=100)
    
    # 第二层：Cross-encoder 精排
    pairs = [(query, doc.text) for doc in candidates]
    scores = reranker.predict(pairs)
    
    # 排序 + 过滤
    ranked = sorted(zip(scores, candidates), reverse=True)
    return [doc for score, doc in ranked if score > 0.7][:top_k]
```

**混合检索（Hybrid Search）**：向量相似度 + 关键词匹配（BM25）结合。向量擅长语义匹配，BM25 擅长精确术语匹配。两者结合，召回率能提升 15-30%。

### 4.4 上下文组装（Context Assembly）

检索到的文档怎么塞进 prompt，是 RAG 最容易被忽视的高杠杆环节。

**问题：检索到 5 个 chunk，但总长度超过了模型的上下文限制，怎么办？**

**策略一：截断（Truncation）**
- 按相关性排序，从高分往低分塞，塞满为止
- 简单，但可能把长文档的关键尾部截掉

**策略二：摘要压缩（Summarization）**
- 先用一个轻量模型把每个 chunk 压缩成一句话摘要
- 只把摘要塞进主 prompt，需要细节时再读原文

**策略三：层次化上下文（Hierarchical Context）**
- 文档 → 摘要 → 关键段落
- 先给模型看摘要列表，让它决定需要深入哪些文档

```python
def assemble_context(docs, max_tokens=4000):
    """智能上下文组装：优先保留高相关度内容，低相关度内容压缩"""
    context_parts = []
    used_tokens = 0
    
    for i, doc in enumerate(docs):
        # 第一个文档最相关，保留完整内容
        if i == 0:
            entry = format_full(doc)
        # 第二个文档保留，但限制长度
        elif i == 1:
            entry = format_truncated(doc, max_len=500)
        # 其余只保留摘要
        else:
            entry = format_summary(doc)
        
        entry_tokens = estimate_tokens(entry)
        if used_tokens + entry_tokens > max_tokens:
            break
        
        context_parts.append(entry)
        used_tokens += entry_tokens
    
    return "\n\n".join(context_parts)
```

### 4.5 生成后处理：引用标注与幻觉检测

RAG 的最后一道防线是**让模型的回答可验证**。

**引用标注（Citation）**：
模型生成回答时，要求在关键事实后标注来源文档。不是"根据文档"这种模糊说法，是精确到文档名和段落。

> "退款通常在 3-7 个工作日到账[退款政策 V2.3, 第 3 节]。如果超过 7 天未到账，建议检查原支付渠道[常见问题, 条目 #14]。"

**幻觉检测**：
即使有了 RAG，模型仍然可能"脑补"——在检索到的文档基础上编造不存在的信息。

检测方法：
1. **事实一致性检查**：用 NLI（自然语言推理）模型判断回答中的每个断言是否被检索文档支持。
2. **来源覆盖检查**：回答中的每个关键事实，必须能在检索文档中找到对应。
3. **不确定性标注**：对于无法验证的陈述，模型应明确标注"此信息未在参考文档中找到"。

---

## 第五章：进阶——RAG 设计的三大铁律

从海量案例里能总结出三条普适原则。它们不来自某篇论文，来自一次次失败后的共识。

### 铁律一：Chunk 不是越小越好

很多人以为 chunk 越小，检索精度越高。错。

Chunk 太小的问题：
- **语义断裂**：一个完整的概念被切成碎片，每个碎片单独看都没有意义。
- **上下文丢失**："退款流程"和"退款时效"是两个 chunk，但用户问"退款要多久"时，检索到的可能是"退款流程"的 chunk——里面只说了"第一步提交申请"，没说具体时间。
- **检索噪声**：小 chunk 数量多，ANN 搜索容易返回大量低相关度结果。

**Chunk 太大的问题**：
- **检索精度下降**：一个 2000 token 的 chunk 可能包含 10 个不同主题，Embedding 会被"平均化"，导致任何查询的相似度都不高。
- **上下文膨胀**：Top-5 chunk 塞满 prompt，留给生成回答的空间不够。

**黄金区间**：对于大多数文档，**200-500 token** 是一个合理的起步点。然后观察检索质量，逐步调整。

### 铁律二：在 LLM 场景下，检索精度 > 召回率

传统信息检索的格言是"宁可错杀，不可放过"——高召回率优先。但 RAG 的场景不同。

**LLM 的注意力机制对噪声极其敏感。** 你检索到 10 个 chunk，其中 3 个是相关的、7 个是噪声，模型会被那 7 个噪声带偏。实验数据显示（基于多个生产环境 RAG 系统的经验估算）：

- Top-K 结果全相关 → 回答准确率通常在 90% 左右
- Top-K 里混入噪声文档 → 回答准确率显著下降
- 检索结果中相关文档比例越低 → 模型被噪声带偏的概率越高

**宁可少给，不要给错。** 这也是重排序（Reranking）如此重要的原因——宁可只返回 3 个高置信度的文档，也不要返回 10 个良莠不齐的文档。

### 铁律三：先优化检索，最后再调 prompt

回答质量不好时，大多数人的第一反应是改 prompt。加一段"请注意..."、换个措辞、加个例子。这是 2024 年的思维惯性。

2026 年的正确做法：**先检查检索层。**

1. **检索到的文档对吗？** 用同样的查询直接看 Top-K 结果，是不是你想要的文档？
2. **相似度分数合理吗？** 最高分是不是显著高于其他？还是所有文档分数都差不多（说明 embedding 没有区分度）？
3. **Chunk 边界对吗？** 检索到的 chunk 是不是包含了回答需要的全部信息？
4. **上下文组装合理吗？** 文档是按重要性排序的吗？有没有把关键信息截掉？
5. **元数据过滤生效吗？** 是不是返回了过期的文档？或者用户无权查看的文档？

确认检索层没问题后，最后再调 prompt。Prompt 是最后一道微调，不是第一道。

---

## 第六章：精通——RAG 的四种架构模式

入门和进阶解决的是"怎么把 RAG 做对"。精通解决的是"面对不同场景，选什么架构"。2026 年的 RAG 已经不是单一模式，而是一个谱系。

### 6.1 Naive RAG：一个向量数据库就够了

最简模式，也是 90% 项目的起点：

```
用户查询 → Embedding → ANN 检索 Top-K → 塞进 Prompt → LLM 生成
```

**适合场景**：文档量 < 1 万页、查询类型单一、答案通常在单个文档内、对延迟要求不苛刻。

**什么时候该升级**：当 Naive RAG 在你的 eval 集上准确率明显低于预期（例如连续多个测试用例失败），且你已经确认检索结果是正确的（问题出在模型理解层面），就该考虑更复杂的架构。

### 6.2 Advanced RAG：给检索加翅膀

在 Naive RAG 基础上增加三层优化：

**查询重写（Query Rewriting）**：
用户的问题往往不适合直接检索。"这玩意怎么用？"这种模糊查询，Embedding 无法有效匹配。

解法：用一个小模型先把用户问题改写成适合检索的表述。

```
用户："这玩意怎么用？"
Rewrite："产品安装步骤和首次使用配置指南"
```

**多路召回（Multi-Route Retrieval）**：
同时用多种检索方式召回候选，然后合并去重：
- 向量相似度召回（语义匹配）
- BM25 关键词召回（精确术语匹配）
- 图遍历召回（知识图谱中的关联实体）

**重排序（Reranking）**：
用 cross-encoder 对多路召回的结果统一重排，把真正相关的文档推到前面。

```python
def advanced_rag_pipeline(query):
    # 1. 查询重写
    rewritten = query_rewriter.rewrite(query)
    
    # 2. 多路召回
    vec_results = vector_db.search(rewritten, top_k=20)
    bm25_results = keyword_index.search(rewritten, top_k=20)
    
    # 3. 合并去重
    candidates = deduplicate(vec_results + bm25_results)
    
    # 4. Cross-encoder 重排
    pairs = [(query, doc.text) for doc in candidates]
    scores = reranker.score(pairs)
    ranked = sort_by_score(candidates, scores)
    
    # 5. 取 Top-5 生成
    return llm.generate(query, context=ranked[:5])
```

**Advanced RAG 的典型收益**：在跨文档推理场景，准确率通常比 Naive RAG 有明显提升（重排序和多路召回能有效减少噪声）。成本增加主要来自重排序模型的推理开销。

### 6.3 Modular RAG：路由决定一切

当查询类型多样化时，单一的检索策略不够用了。Modular RAG 的核心思想是：**先判断查询类型，再路由到对应的检索模块。**

```
用户查询
    ↓
[Router] 判断查询类型
    ↓
    ├─→ 事实查询 → 直接检索文档库
    ├─→ 比较查询 → 多文档并行检索 + 对比模板
    ├─→ 流程查询 → 检索步骤文档 + 顺序组装
    ├─→ 数值查询 → 检索表格/数据库 + 精确提取
    └─→ 开放查询 → 先检索背景知识，再生成推理
```

**Router 怎么实现？**

最简单的方式是分类器（几类查询类型，轻量模型做分类）。更高级的方式是让 LLM 自己判断——把查询扔给一个小模型，让它输出需要的检索策略。

```python
def route_query(query):
    """查询路由：根据问题类型选择检索策略"""
    prompt = f"""分析以下查询的类型，只输出标签：
    - factual: 需要查找具体事实
    - comparative: 需要比较多个事物
    - procedural: 需要步骤或流程
    - numerical: 需要精确数字
    - open: 需要推理和综合
    
    查询：{query}
    类型："""
    
    query_type = small_llm.generate(prompt).strip()
    
    strategies = {
        'factual': direct_retrieval,
        'comparative': multi_doc_parallel,
        'procedural': step_wise_retrieval,
        'numerical': structured_data_retrieval,
        'open': background_then_reason
    }
    
    return strategies.get(query_type, direct_retrieval)(query)
```

### 6.4 Agentic RAG：让 Agent 决定什么时候检索、检索什么

RAG 的最高形态不是更好的检索引擎，而是**把检索作为 Agent 的工具之一**。

在传统 RAG 里，检索是固定的第一步。在 Agentic RAG 里，Agent 自己决定：

- 这个问题需要检索吗？（还是我能直接回答？）
- 如果需要，检索什么？（关键词、文档类型、时间范围）
- 检索到结果后，需要二次检索吗？（结果不够，需要深入某个子主题）

```python
# Agentic RAG 的工具定义
retrieval_tools = [
    {
        "name": "search_knowledge_base",
        "description": "在知识库中搜索与查询相关的文档",
        "parameters": {
            "query": "搜索关键词",
            "doc_type": "可选，限定文档类型（faq/policy/manual）",
            "time_range": "可选，限定时间范围"
        }
    },
    {
        "name": "read_document",
        "description": "读取指定文档的完整内容",
        "parameters": {"doc_id": "文档ID"}
    },
    {
        "name": "answer_directly",
        "description": "如果已有足够信息，直接回答用户",
        "parameters": {"answer": "回答内容", "citations": "引用来源"}
    }
]

# Agent 循环
def agentic_rag(user_query):
    context = []
    for step in range(max_steps):
        response = llm.plan(user_query, context, tools=retrieval_tools)
        
        if response.action == "answer_directly":
            return response.answer
        
        elif response.action == "search_knowledge_base":
            results = search(**response.parameters)
            context.append({"tool": "search", "results": results})
        
        elif response.action == "read_document":
            doc = read_doc(response.parameters["doc_id"])
            context.append({"tool": "read", "content": doc})
```

**Agentic RAG 的核心优势**：
- **按需检索**：简单问题不检索，直接回答，省 token。
- **深度检索**：复杂问题可以多次检索、逐步深入。
- **工具组合**：检索可以和计算、代码执行、API 调用等其他工具组合。

### 6.5 选型建议

| 维度 | Naive RAG | Advanced RAG | Modular RAG | Agentic RAG |
|------|-----------|--------------|-------------|-------------|
| 文档规模 | < 1 万页 | 1-10 万页 | 10 万页以上 | 任意 |
| 查询类型 | 单一 | 中等多样 | 高度多样 | 高度多样 + 需要推理 |
| 准确率（经验估算） | ~70-85% | ~85-92% | ~88-94% | ~90-95%（波动大） |
| 延迟 | 低 | 中 | 中 | 高（多轮） |
| 成本 | 低 | 中 | 中 | 高 |
| 维护复杂度 | 低 | 中 | 高 | 很高 |
| **最佳场景** | 快速原型、内部工具 | 生产级知识库 | 企业级多业务线 | 研究型、探索型任务 |

**一句话建议**：

- 想周末搭一个能用的知识库问答 → **Naive RAG**
- 公司要上线客服系统，准确率要求 90%+ → **Advanced RAG**
- 多个业务部门共用一套系统，查询类型差异大 → **Modular RAG**
- Agent 需要自主探索、多步推理、工具组合 → **Agentic RAG**

**最重要的一点**：不管选哪种架构，RAG 的**原理**是相通的——分块、Embedding、检索、组装、生成。学会原理，换架构只是换编排方式。

---

## 第七章：精通——高级模式与前沿探索

掌握了四种架构后，你可以开始探索一些前沿模式。它们不是每个项目都需要，但在特定场景下能带来质的飞跃。

### 7.1 GraphRAG：当关系比文本更重要

标准 RAG 的问题是：它只能找到**语义相似**的文档，但找不到**逻辑关联**的文档。

场景：用户问"张三负责的项目的退款政策是什么？"
- 标准 RAG：检索"退款政策"→ 返回政策文档。但不知道"张三负责的项目"是哪个。
- GraphRAG：在知识图谱中查询 `张三 --负责→ 项目A --适用政策→ 退款政策 V2.3` → 精确定位到具体政策。

**GraphRAG 的核心流程**：

1. **构建阶段**：从文档中提取实体和关系，构建知识图谱。
   ```
   实体：张三（人）、项目A（项目）、退款政策 V2.3（文档）
   关系：张三-负责-项目A，项目A-适用政策-退款政策 V2.3
   ```

2. **检索阶段**：
   - 先用 Embedding 检索相关实体和文档
   - 再在图谱中做邻居扩展（找到关联的实体和文档）
   - 把图谱子图 + 相关文档一起送进 LLM

3. **生成阶段**：LLM 基于文本内容 + 图谱结构做推理

**GraphRAG 的收益**：在需要跨实体关联查询的场景（组织架构、项目关系、产品依赖），Microsoft Research 的 GraphRAG 系统报告了相比基线 RAG 的显著改进，尤其是在全局理解类问题上。

**GraphRAG 的成本**：需要额外的图谱构建和维护，实体抽取和关系识别本身就需要一个 NLP pipeline。

### 7.2 Self-RAG：让模型自己判断是否需要检索

传统 RAG 的问题是：不管问题多简单，都要先检索一遍。很多简单问题（"你们公司叫什么名字？"），模型直接从训练记忆里就能回答，根本不需要检索。

Self-RAG 的解决思路：**模型在生成每个 token 时，自主决定"我现在需要检索吗？"**

```
模型生成："我们公司的退款政策是..."
          ↑ 这里模型判断：我需要检索吗？
          → [需要] → 触发检索 → 把检索结果加入上下文 → 继续生成
          → [不需要] → 直接生成
```

Self-RAG 训练模型输出特殊的 reflection token：
- `Retrieve`：是否需要检索？（Yes/No）
- `IsRel`：检索到的文档是否相关？（Relevant/Irrelevant）
- `IsSup`：生成的内容是否被文档支持？（Supported/Contradicted）
- `IsUse`：生成的内容是否有用？（Useful/Not Useful）

**收益**：在简单问题上省掉不必要的检索，在复杂问题上保证检索的深度。Self-RAG 论文报告整体 token 成本显著降低，同时准确率持平或略有提升。

### 7.3 RAPTOR：层次化摘要检索

标准 RAG 的分块策略有一个根本矛盾：
- **小块**：检索精度高，但丢失全局上下文。
- **大块**：保留上下文，但检索精度低。

RAPTOR（Recursive Abstractive Processing for Tree-Organized Retrieval）的解法：**构建一棵摘要树**。

```
                    [整本手册的摘要]
                   /                \
        [第1-5章摘要]              [第6-10章摘要]
         /        \                 /         \
    [章1摘要]  [章2摘要]       [章6摘要]   [章7摘要]
      /            \             /             \
  [段落1] ... [段落N]       [段落1] ... [段落N]
```

**检索时自顶向下**：
1. 先在最上层摘要中匹配，定位到相关章节。
2. 再在该章节的子摘要中匹配，定位到相关段落。
3. 最后读取原始段落。

**收益**：既保留了全局上下文（高层摘要），又保持了检索精度（底层 chunk）。在长文档（书籍、论文集、大型手册）场景下，效果尤其明显。

### 7.4 多模态 RAG：不只是文本

RAG 的原始假设是"文档 = 文本"。但真实世界的知识不只存在于文本中：

- **表格**：产品规格表、财务报表、实验数据
- **图表**：架构图、流程图、趋势图
- **图像**：产品照片、扫描件、截图
- **视频**：教程、会议录像

多模态 RAG 的思路：**统一的多模态 Embedding 空间**。

```python
# 多模态检索流程
def multimodal_retrieve(query):
    # 查询编码（文本）
    q_vec = multimodal_embed(text=query)
    
    # 候选召回（跨模态）
    candidates = []
    candidates += text_index.ann_search(q_vec, top_k=10)
    candidates += table_index.ann_search(q_vec, top_k=5)
    candidates += image_index.ann_search(q_vec, top_k=5)
    
    # 重排序
    ranked = rerank_by_modality_relevance(candidates, query)
    
    # 组装多模态上下文
    context = {
        'texts': [c for c in ranked if c.modality == 'text'],
        'tables': [c for c in ranked if c.modality == 'table'],
        'images': [c for c in ranked if c.modality == 'image']
    }
    
    return llm.generate(query, multimodal_context=context)
```

**多模态 RAG 的典型场景**：
- 产品支持：用户上传一张报错截图，系统检索相关的文档和解决方案。
- 医疗诊断：结合病历文本、检验报告表格、医学影像做综合检索。
- 工程设计：检索 CAD 图纸、技术规范文本、材料参数表。

---

## 第八章：精通——RAG 在异常检测和根因分析中的真实局限

前面七章讲的是 RAG 怎么做好。这一章讲的是**RAG 在什么场景下根本做不好**——这也是你最初关心的问题。

### 8.1 异常检测：为什么 RAG 会系统性失效

让我们回到一个具体的场景：支付系统出现了重复打款。你有一个 RAG 系统，索引了所有的技术文档、运维手册、历史工单。

用户问："为什么会出现重复打款？"

RAG 的检索流程：
1. 将"重复打款"编码为 query embedding
2. 在向量空间中寻找最近邻
3. 返回 Top-K 最相似的文档片段

它会返回什么？

> "退款流程说明：用户发起退款请求 → 系统校验订单状态 → 原路退回支付渠道 → 更新订单状态为已退款"
>
> "常见问题：退款到账时间通常为 1-7 个工作日"
>
> "历史工单 #2847：用户反映退款未到账，经排查为支付渠道延迟..."

这些都是**语义上最相似**的内容。但它们对于解决"重复打款"这个问题，**几乎毫无价值**。

**根本原因：异常事件在向量空间中的分布决定了 RAG 会系统性漏检。**

| | 正常事件 | 异常事件 |
|---|---------|---------|
| 频率 | 高频 → 向量空间高密度区域 | 低频/首次 → 向量空间稀疏区域 |
| 文档覆盖 | 充分描述 → 检索命中率高 | 缺失或间接描述 → 检索命中率低 |
| 语义特征 | 明确、标准 → Embedding 压缩损失小 | 隐晦、结构性 → Embedding 压缩损失大 |
| 关联模式 | 独立发生 → 单文档可回答 | 级联/涌现 → 需要多文档关联推理 |

Embedding 模型学的是**常态世界的语义分布**。异常事件的 embedding 在向量空间里是孤立点——它离所有正常文档都很远，但又没有足够的相似异常文档来形成聚类。ANN 搜索天生倾向于返回高密度区域的"正常模式变体"。

**但这不是理论推测——benchmark 已经用真实数据量化了这个崩溃过程。**

以上关于"异常事件在向量空间中是孤立点"的分析，如果只是直觉，说服力有限。2025-2026 年公开发表的几组评估，恰好验证了一条清晰的衰减曲线：**查询越需要跨时间、跨文档、跨实体的结构性关联，RAG 的检索质量就越差。**

**第一层验证：从"找事实"到"跨文档比较"，准确率断崖下跌**

SPD-RAG (Kartal et al., 2026) 在 Loong benchmark（Wang et al., 2024）上的实验最能说明问题。Loong 的每道题平均涉及 11 个文档，测试"在多文档中找到并综合信息"的能力——这和"支付系统重复打款"需要跨模块排查的场景是同一类问题。

在需要全局比较的 Clustering 任务中：

| 方案 | Avg Score (0-100) |
|------|-------------------|
| Full Context（Gemini 2.5 Pro） | **68.0** |
| SPD-RAG（分片并行 + 合并） | **58.1** |
| Normal RAG | **33.0** |
| Agentic RAG（迭代检索） | **32.8** |

Normal RAG 和 Agentic RAG 几乎一样差。为什么？因为标准检索只能按"语义相似度"返回局部片段，它**天生就不具备"结构性比较"的能力**——不知道文档 A 的退款逻辑和文档 B 的幂等性校验之间存在冲突。即使 Agent 迭代检索，如果每次检索的驱动力还是"语义近似"，它永远看不到全局。

**第二层验证：从"跨文档"到"跨时间/跨实体"，Context Recall 跌至 0.08**

如果说 Loong 证明了"跨文档比较"是 RAG 的软肋，那么金融合规领域的 RAGAS 评估（arXiv 2025）则证明了"跨时间、跨对手的结构性追踪"是 RAG 的噩梦。

研究人员评估了一个 GraphRAG Agent 在不同难度查询上的 Context Recall（检索到了多少比例的相关证据）：

| 查询难度 | 类型 | Context Recall |
|---------|------|----------------|
| Level 1 | 直接事实检索（"客户 X 的国籍是？"） | **1.00** |
| Level 2 | 单跳关系（"客户 X 持有哪些账户？"） | **0.85+** |
| Level 3 | 多跳推理（"客户 X 通过哪些中间人转账？"） | **0.46** |
| Level 4-5 | 时序/行为/叙事推理 | **0.38-0.79** |
| Transaction | 交易级细粒度时序 + 对手方追踪 | **0.08** |

注意最后一条：Transaction 级别——需要追踪资金流向、时序依赖、对手方关系——系统只检索到了 **8%** 的相关证据。

这和"支付系统重复打款"的根因分析高度相似：**都不是"找一个事实"，而是"追踪一个跨时间、跨组件、跨状态的因果链条"。RAG 的语义相似度检索，对这种任务几乎完全失明。**

**第三层验证：即使强行把正确答案塞进上下文，模型也可能理解不了**

这就引出了最深层的问题。Zhang et al. (2024) 做了一个"残酷实验"：人为把 100% 相关的文档片段塞进上下文（Oracle Retrieval），排除检索失误的干扰，只看模型能不能基于正确信息给出正确答案。

结果：QA 任务仍有 **6.9%** 失败率，代码生成任务失败率高达 **12%**。

这说明什么？**异常检测和根因分析的挑战，不只是"检索不到"，更是"即使检索到了，模型也无法在碎片化、跨文档、甚至矛盾的证据中构建正确的因果链"。**

**三层验证叠加起来的结论：**

```
第一层：跨文档比较 → RAG 丢失全局上下文（Loong: 33.0 vs 68.0）
    ↓
第二层：跨时间/跨实体追踪 → RAG 检索崩溃（RAGAS: Context Recall 0.08）
    ↓
第三层：即使检索完美 → 模型理解仍有硬 ceiling（Oracle: 6.9%-12% 失败率）
```

这不是某个 embedding 模型不够好、某个向量数据库不够快的问题。这是**架构层面的不匹配**——用"语义相似度"解决"结构性异常"，就像用温度计测血压，工具和目标不在一个维度上。

> **一句话总结：RAG 检索到的是"别人怎么描述过类似问题"，但异常检测需要的往往是"这个问题为什么从未被描述过"——而当问题确实被描述过时，RAG 也未必能把它和当前症状正确地关联起来。**

### 8.2 根因分析：RAG 的三重盲区

根因分析（Root Cause Analysis, RCA）比异常检测更进一步——它需要构建"为什么会出问题"的因果链。RAG 在这里有三重盲区。

#### 盲区一：根因往往不在文档里

系统的根因通常是**动态行为**的产物，而不是**静态文档**的描述。

- 两个独立部署的服务在特定时序下产生竞态条件
- 一个配置变更与旧版本客户端的兼容性问题
- 负载均衡算法在特定流量模式下的边缘行为
- 第三方 API 的静默行为变更

这些事情**从未被任何人写成文档**。RAG 检索的是已记录的知识，而根因往往藏在系统运行的 emergent behavior 中。

#### 盲区二：语义相似 ≠ 故障相似

即使文档里描述过类似问题，RAG 也不一定能找到它——因为**故障的相似性和语义的相似性不是一回事**。

两个故障可能在日志表现上完全不同（语义不相似），但根因完全相同（比如都是某个底层库的线程安全问题）。Embedding 模型无法捕捉这种跨语义的结构性关联。

举个例子：
- 故障 A 的日志："timeout while connecting to payment gateway"
- 故障 B 的日志："duplicate transaction detected in settlement batch"

这两段日志的语义相似度很低，但根因可能是同一个：数据库连接池配置不当，导致请求在超时后重试，既产生了连接超时（故障 A 的表现），又产生了重复交易（故障 B 的表现）。

RAG 的 Embedding 会把这两个故障分到向量空间的不同角落，永远不会同时被检索到。

#### 盲区三：缺乏假设-验证的推理闭环

真正的根因分析是一个**假设驱动的探索过程**：

```
观察症状 → 构建假设 → 定向检索证据 → 验证/否定假设 → 修正假设 → 循环
```

标准 RAG 是单次检索：你问一个问题，它给一批文档。它不参与假设的迭代 refinement，不做证据的交叉验证，不评估不同解释的概率。

**RAG 给你的是答案的候选集，不是因果的推理链。**

### 8.3 从 RAG 到 World Model：升级路径

承认 RAG 的局限，不等于放弃 RAG。答案是**在它的边界之外补位**。

**分层架构：长上下文作为工作记忆，RAG 作为精准证据获取，World Model 作为方向指引。**

```
┌─────────────────────────────────────┐
│  World Model（系统理解、因果推理）      │  ← 方向指引：先建模型，再有目标地检索
├─────────────────────────────────────┤
│  Agent Loop（假设生成、策略选择）        │  ← 决策中枢：reason → retrieve → validate
├─────────────────────────────────────┤
│  RAG（精准检索、证据获取）              │  ← 信息输入：从"retrieve then reason" 
│                                      │     变为 "reason then retrieve"
├─────────────────────────────────────┤
│  Long Context（工作记忆、多轮累积）      │  ← 上下文容器
└─────────────────────────────────────┘
```

**升级路径一：RAG + Knowledge Graph（结构增强）**

把向量相似性和图结构结合起来。当标准 RAG 返回"退款流程文档"时，图谱增强的 RAG 可以沿着"退款服务 → 支付网关 → 幂等性校验 → 重试机制"的链路，定位到更可能出问题的组件。

**升级路径二：Hypothesis-Driven RAG（方向性检索）**

不再是一次性检索，而是先基于系统模型生成假设，再有目标地检索验证。

```
系统模型: "支付流程包含 A→B→C 三个环节"
假设 1: "问题出在 B→C 的幂等性校验"
    → 定向检索 B 服务的配置、C 服务的日志格式、幂等性实现代码
假设 2: "问题出在重试风暴"
    → 定向检索重试策略配置、熔断器状态、QPS 监控
```

**关键转变：从 "retrieve then reason" 到 "reason then retrieve"。**

**升级路径三：World Model + RAG（因果检索）**

终极形态是在检索之前，先有一个对目标系统的**世界模型**——它的组件、接口、状态机、不变量约束。基于这个世界模型，Agent 可以：

1. 识别观察到的行为与模型预期的偏差
2. 生成关于偏差来源的结构化假设
3. 将假设转化为精准的检索查询（代码、配置、日志模式）
4. 用检索结果验证或修正世界模型

**这不是传统意义上的 RAG 了。RAG 在这里退化为一个精准证据获取工具，而认知的核心转移到了世界模型的构建和因果推理上。**

### 8.4 一句话总结

> **RAG 在"已知问题 × 已知知识"的象限里是最优解。在"未知问题 × 结构性异常"的象限里，纯 RAG 基本不 work。未来的系统不是用 RAG 替代推理，而是用 RAG 增强推理——但推理的方向必须由世界模型和因果理解来指引。**

---

## 第九章：常见陷阱（反面教材）

### 陷阱一：文档越多越好

把公司十年来的所有文档全部塞进向量数据库，以为量大了覆盖率就高。错。

**陈旧文档是噪声源。** 过期的 API 文档、废弃的流程说明、旧版本的政策——这些文档被检索到时，模型会基于错误信息生成回答，反而降低准确率。

**正确做法**：建立文档生命周期管理。过期文档标记为 deprecated，检索时过滤或降权。定期重建索引，只保留有效文档。

### 陷阱二：Chunk 越小越好

已经在第五章讲过了，但值得再强调一次。Chunk 太小会导致语义断裂、上下文丢失、检索噪声。200-500 token 是大多数场景的黄金区间。

### 陷阱三：只看相似度分数

相似度分数高不等于文档有用。一个文档可能因为包含了查询中的关键词而得分很高，但它的内容实际上并没有回答用户的问题。

**正确做法**：在评估 RAG 质量时，核心指标不是"检索相似度"，而是**端到端回答准确率**。准备 20-50 个标注好的测试用例，每次改系统后跑一遍，看回答正确率有没有提升。

### 陷阱四：忽视元数据过滤

所有文档混在一起检索，不管文档类型、版本、权限、时间。这会导致：
- 检索到测试环境的文档，而不是生产环境的
- 检索到过期版本的政策，而不是最新版
- 检索到用户无权查看的内部文档

**正确做法**：每个 chunk 都要带上丰富的元数据（来源文档、版本、时间、文档类型、权限级别），检索前先过滤。

### 陷阱五：不做幻觉检测

以为有了 RAG 就不会有幻觉。错。RAG 只能减少幻觉，不能消除幻觉。模型仍然可能在检索文档的基础上编造不存在的信息，或者把两个文档的信息错误拼接。

**正确做法**：在生成后加一层事实一致性检查。最简单的方法：要求模型在回答中标注每个关键事实的来源，然后人工或自动验证这些来源是否确实支持该事实。

### 陷阱六：一个 Embedding 模型打天下

用一个通用 Embedding 模型处理所有类型的文档。技术文档、产品说明、法律合同、客服对话——这些文档的语义特征差异很大，通用模型在所有类型上都只是"够用"。

**正确做法**：如果某个文档类型的查询量特别大，考虑在该类型语料上微调一个专用 Embedding 模型，或者用领域适配层（domain adapter）做迁移。

---

## 第十章：结语

2024 年拼 Embedding 模型，2025 年拼向量数据库，2026 年拼 RAG 架构设计。

Embedding 模型是公共资源，BGE、GTE、E5——大家都能用。向量数据库也是公共资源，Pinecone、Milvus、Qdrant——选型差异不大。**差距在哪？在检索策略设计得好不好、分块策略精不精、上下文组装到不到位、幻觉检测严不严。**

RAG 没有过时。在 FAQ、客服、文档问答、标准化流程查询这些场景里，它仍然是最成熟、最经济、最可控的解决方案。

但 RAG 的能力边界也必须被清醒地认识：

> **它擅长"在已知里找已知"，不擅长"在已知里找未知"，更不擅长"在未知里探索未知"。**

相似性不是因果性。检索不是推理。已知不是全部。

当"让模型知道更多"已经足够时，RAG 是最好的工具。当"让模型理解系统为什么坏"成为需求时，你需要的是 World Model、因果推理、假设驱动的探索——RAG 只是这个更宏大架构中的一个证据获取层。

**别再问"RAG 还 work 吗"。问："RAG 在我的场景里 work 在哪里，不 work 在哪里？在不 work 的地方，用什么补位？"**

去建更好的检索。

但别忘了，检索的终点是推理，推理的终点是理解。

---

## 参考来源

- Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020
- Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey", 2024
- Microsoft Research, "GraphRAG: A modular graph-based Retrieval-Augmented Generation system", 2024
- Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection", 2023
- Sarthi et al., "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval", 2024
- Anthropic Research, "Building effective RAG systems", 2025
- LangChain Blog, "RAG from scratch: a comprehensive guide", 2025
- Pinecone Blog, "Advanced RAG techniques: A practitioner's guide", 2025
