---
name: "clippings-digest"
version: 3.7.0-wb1
author: JustineJiao
license: GPL-3.0
repository: https://github.com/JustineJiao/clippings-digest-skill
description: "消化 Obsidian Clippings 笔记到 llm-wiki 知识库的完整工作流。支持图片本地化、AI 驱动的 Two-Step CoT 深度分析、YAML frontmatter 标准化、置信度标注、Review Items 机制。"
triggers:
  - "消化 clippings"
  - "消化XX知识库中的 clippings"
  - "消化clippings笔记"
  - "clippings digest"
  - "digest clippings"
---

# clippings-digest Skill

将 Obsidian Clippings 插件导出的 Markdown 笔记批量消化到 llm-wiki 格式知识库（v3.7+ 标准）。

## 适用场景

- Obsidian + Clippings 插件导出的 `.md` 笔记（含 YAML frontmatter：title / source / published / authors）
- 目标知识库为标准 llm-wiki 结构（`wiki/entities/`、`wiki/topics/`、`wiki/sources/`、`raw/`、`attachments/`）
- 需要自动下载笔记中的外部图片到本地 `attachments/`

## ⚠️ 目录定位（核心概念，不要混淆）

| 目录 | 配置键 | 内容 | 状态 |
|------|--------|------|------|
| `config/paths.json` 中的 `clippings_dir` | `clippings_dir` | Obsidian Clippings 插件**导出**的原始 `.md` 文件 | **待消化**（Step 1 的输入） |
| `config/paths.json` 中的 `raw_clippings` | `raw_clippings` | 经过 Step 1（图片本地化）后搬入的文件 | **已图片本地化，尚未 AI ingest**（Step 2 读取、Step 3 消化） |
| `wiki/sources/` | — | AI 生成的 source 摘要页 | **已消化完成** |

**理解要点**：
- `Clippings/` → 原始导出，还没动过 → **Step 1 从这里读，处理后搬到 `raw/clippings/`**
- `raw/clippings/` → 已经做了图片下载，但还没做 AI 分析 → **Step 2 读取摘要，Step 3 做 AI ingest**
- 一个 clipping 文件从 `Clippings/` 开始，经过 Step 1 → 到 `raw/clippings/` → 经过 Step 3 → 创建 `wiki/sources/` 页面，才算是"消化完成"

## 与 llm-wiki 的关系

本 skill 处理 clippings 的**特殊前置步骤**（图片本地化、YAML frontmatter 解析），核心分析环节**直接复用 llm-wiki 的 ingest 方法**：

| 阶段 | 方式 | 说明 |
|------|------|------|
| 图片下载 + 文本提取 | Python 脚本（确定性） | 无法 AI 化的机械步骤，保持脚本 |
| 知识分析 + 页面生成 | **Two-Step CoT（llm-wiki ingest）** | 复用 AI 驱动分析管线 |
| YAML frontmatter | 统一标准（llm-wiki 规范） | type/created/updated/sources/tags/aliases/confidence |
| 待审项 | Review Items（llm-wiki 机制） | 模糊信息自动生成待审 |
| 批量交叉 | Batch Cross-Synthesis（llm-wiki 机制） | 批次结束时发现跨文件关联 |

---

## 工作流总览

| 阶段 | 用途 | 自动化 |
|------|------|--------|
| **Step 0** | 选择知识库 + 路径配置 | 交互 |
| **Step 1** | 图片本地化 + 文件整理 | Python 脚本自动 |
| **Step 2** | 提取摘要文本 | Python 脚本自动 |
| **Step 3** | AI 深度 ingest（Two-Step CoT） | AI 驱动（核心） |
| **Step 4** | 批量交叉综合 | AI 驱动（结束时） |
| **Step 5** | 查看待审项（可选） | 交互 |

---

## Step 0：选择知识库

与之前逻辑一致：
- 已指定知识库名称 → 直接使用
- 未指定 → 询问用户
- 更新 `config/paths.json` 中的路径配置

## Step 1：图片本地化 — `scripts/digest_clippings.py`

**输入**：`config/paths.json` 中 `clippings_dir` 指向的目录（即 `Clippings/`）中的原始 `.md` 文件
**输出**：图片下载到 `attachments/`，文件搬到 `raw/clippings/`

扫描 `clippings_dir`（即知识库根目录下的 `Clippings/` 目录）中的原始笔记文件：
1. 扫描笔记中的外部图片链接，下载到 `attachments/`
2. 替换 Markdown 中的图片链接为本地路径
3. 将处理完的文件**搬到** `raw/clippings/` 目录

> **不要搞混**：Step 1 只在 `Clippings/` 目录中读取，不会碰 `raw/clippings/` 中的已有文件。

## Step 2：提取摘要 — `scripts/extract_clippings.py`

**输入**：`raw/clippings/` 中的 `.md` 文件（即已从 `Clippings/` 搬入的、图片已本地化的文件）
**输出**：`clippings_summary.json`（包含所有 raw/clippings 中文件的 YAML frontmatter + 摘要）

读取 `raw/clippings/*.md`，解析 YAML frontmatter，提取 `## Abstract` 段落，输出 `clippings_summary.json`。

---

## Step 3：AI 深度 Ingest（核心改造）

**输入**：`raw/clippings/` 中**尚未创建对应 source 页面**的 clipping 文件
**输出**：`wiki/sources/`、`wiki/entities/`、`wiki/topics/` 页面

### 确定待消化范围

Step 3 开始前，先排查 `raw/clippings/` 中的文件哪些还没创建 source 页面：

1. 读取 `raw/clippings/` 中所有 `.md` 文件的文件名
2. 读取 `wiki/sources/` 中所有 source 页面的 YAML frontmatter，提取 `sources` 字段
3. 对比：`raw/clippings/` 中文件名出现在任何 source 页面的 `sources` 字段 → 已消化，跳过
4. 未出现在任何 `sources` 字段中的文件 → **待消化**

> `raw/clippings/` 中的文件只是经过了 Step 1 图片本地化，不一定已经 AI ingest 了。需要逐一检查是否已有对应 source 页面。

### 上下文加载

读取知识库的 `purpose.md`、`index.md`（概要部分）和 `.wiki-schema.md` 作为全局上下文。

### SHA256 缓存检查

对每个 clipping 文件计算 SHA256 哈希，检查 `.wiki-cache.json`。
- 命中 → 跳过，0 Token 消耗
- 未命中 → 进入 Two-Step 流程

### Step 3a：结构化分析（对应 llm-wiki Step 1）

**输入**：clipping 全文 + `purpose.md` + 现有 wiki 上下文
**输出**：JSON 分析结果（不持久化，仅在本流程传递）

```json
{
  "source_summary": "论文一句话概括",
  "entities": [
    {"name": "THP9", "type": "gene", "relevance": "high",
     "confidence": "EXTRACTED", "evidence": "原文表述：'THP9 is a key gene...'"}
  ],
  "topics": [{"name": "玉米高蛋白育种", "importance": "high"}],
  "connections": [
    {"from": "THP9", "to": "O2", "type": "调控关系",
     "confidence": "INFERRED", "evidence": "两基因在同一代谢通路"}
  ],
  "categories": ["基因组选择与AI育种"],
  "review_items": [
    {"type": "create_page | deep_research | skip",
     "description": "不确定实体分类",
     "reason": "原文表述含糊",
     "suggested_queries": ["THP9 基因功能 玉米"]}
  ]
}
```

**置信度规则**（与 llm-wiki 一致）：
| 标注 | 含义 | evidence 要求 |
|------|------|--------------|
| `EXTRACTED` | 原文直接陈述 | 必须，≤50字摘录 |
| `INFERRED` | 从多处原文推断 | 必须，推理依据 |
| `AMBIGUOUS` | 原文表述不清 | 可选 |
| `UNVERIFIED` | 来自 AI 背景知识 | 可选 |

**标题自动分类**：沿用原版 `categorize()` 逻辑，按标题关键词匹配已知类别。

### Step 3b：页面生成（对应 llm-wiki Step 2）

**输入**：Step 3a 分析结果 JSON（**不是原素材全文**，节省 Token）+ 需要更新的已有页面（部分读取）
**输出**：标准 llm-wiki 格式的 wiki 页面

**生成内容**：

1. **Source 页面**（`wiki/sources/{日期}-{短标题}.md`）
   - 标准化 YAML frontmatter：
     ```yaml
     ---
     type: source
     title: <论文标题>
     created: YYYY-MM-DD
     updated: YYYY-MM-DD
     source_url: <source 字段>
     source_type: clippings
     confidence: EXTRACTED
     sources: [raw/clippings/<文件名>]
     tags: [<分类标签>]
     aliases: []
     images: <N>
     image_paths: []
     ---
     ```
   - 内容：核心摘要、关键实体、核心观点（含置信度标注）、分类标签

2. **Entity 页面**（`wiki/entities/`）
   - 已有实体 → 追加新信息，更新"不同素材中的观点"
   - 新实体 → 创建标准化页面（包含标准化 YAML frontmatter）
   - 新实体但 `confidence: AMBIGUOUS` → 不直接创建页面，生成 **Review Item**

3. **Review Items**（当存在 `review_items` 时）
   - 按 `wiki/reviews/review-{日期}-{序号}.md` 格式写入
   - 参考 llm-wiki `templates/review-template.md`

4. **更新 wiki 元数据**
   - 更新 `.wiki-cache.json`
   - 追加 `log.md` 记录

### 处理模式

| 场景 | 模式 |
|------|------|
| 单篇 clipping | 标准 Two-Step（分析 → 生成） |
| 批量 2-5 篇 | 组内 Two-Step（每篇分析→生成），组件完成后统一存入 |
| 批量 > 5 篇 | 每 5 篇一组，组内独立分析→生成，组间暂停汇报进度 |

### 关于 Step 2 → Step 3 的数据流

Step 2（extract_clippings.py）的输出 `clippings_summary.json` 是 Step 3（AI Ingest）的**参考信息**，但不是唯一输入。Step 3 的 AI 分析引擎在判断一个 clipping 是否已消化时，**主要依据 `wiki/sources/` 中已有 source 页面的 `sources` 字段**：

- 遍历 `raw/clippings/` 中的文件
- 对每个文件，检查 `wiki/sources/` 下是否有 source 页面的 `sources` 字段指向该文件路径
- 已指向 → 跳过（已消化）
- 未指向 → 进入 Two-Step 流程

这确保即使 `clippings_summary.json` 过期或丢失，Step 3 仍能正确识别待消化文件。

---

## Step 4：批量交叉综合（新增）

所有 clipping 处理完后执行，与 llm-wiki batch-ingest 的交叉综合机制一致。

**输入**：本次 batch 中所有新创建的 source 页面 + entity 页面
**输出**：

1. **实体间互链**：在 entity 页面的"相关实体"中补充 batch 内互链
2. **主题页面更新**：创建/更新 `wiki/topics/` 下的主题页，汇总本 batch 相关素材
3. **index.md 更新**：在所有分类下添加新条目，更新统计数字
4. **图谱触发**：更新 `graph-data.json` 中的 4-Signal 相关性数据（如有）
5. **log.md 记录**：`## {日期} batch-cross-synthesis | digest {N} 个 clippings`

---

## Step 5：查看待审项（新增）

如果有 Review Items 生成，询问用户是否查看：

> "消化过程中产生了 {N} 个待审项（不确定性/需要确认），要不要现在看看？"

用户选择查看时，读取 `wiki/reviews/` 目录中 `status: pending` 的页面，展示给用户处理。

---

## 注意事项

1. **Python 脚本**（Step 1-2）保持原样，它们处理的是确定性机械任务，不需要 AI
2. **Two-Step 流程**（Step 3）直接复用 llm-wiki 方法论，但针对性优化 clipping 场景（论文摘要解析、基因名提取、分类标注）
3. **Token 节省**：Step 3b 不再读取 clipping 全文，只读 Step 3a 的分析 JSON + 相关已有页面（部分读取）
4. **缓存**：SHA256 缓存跳过未变更文件，重复运行不重复消耗
5. **图片下载失败**：同原版，失败时保持链接不变，不阻塞流程
6. **重复运行安全**：所有步骤都检查目标文件是否已存在

## 文件结构

```
clippings-digest/
├── SKILL.md              # 本文件
├── config/
│   ├── paths.json        # 路径配置（用户编辑）
│   └── entities.json    # 实体列表（可选，仅用于参考）
└── scripts/
    ├── digest_clippings.py   # Step 1
    ├── extract_clippings.py  # Step 2
    └── list_clippings.py     # 查看辅助
```

## 常见问题

**Q: Clippings 没有 YAML frontmatter 怎么办？**
A: 脚本会尽量从正文提取标题。建议在 Obsidian 中安装 Clippings 插件，它会自动添加 frontmatter。

**Q: 图片下载全部失败？**
A: 检查网络连接，部分网站需要设置代理。可编辑 `digest_clippings.py` 中的 `UA` 变量伪装浏览器。

**Q: 如何修改分类规则？**
A: 分类逻辑从 Python 脚本移到了 AI 分析的提示中。不想要某类时，在分析时告诉 AI 忽略即可。

**Q: 想跳过 AI 分析直接用旧方式？**
A: 可以临时改为手动运行原有的 `create_sources.py` 和 `create_entities.py` 脚本，但生成的页面不含标准化 YAML frontmatter 和置信度标注。

## 适用场景

- Obsidian + Clippings 插件导出的 `.md` 笔记（含 YAML frontmatter：title / source / published / authors）
- 目标知识库为标准 llm-wiki 结构（`wiki/entities/`、`wiki/topics/`、`wiki/sources/`、`raw/`、`attachments/`）
- 需要自动下载笔记中的外部图片到本地 `attachments/`

