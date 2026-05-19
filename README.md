# clippings-digest-skill — Obsidian Clippings 笔记消化技能

> **将 Obsidian Web Clipper 采集的笔记自动消化到 llm-wiki 知识库。支持图片本地化、AI 驱动的 Two-Step CoT 深度分析。**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform: AI Agent](https://img.shields.io/badge/Platform-WorkBuddy-blue)]()
[![Version](https://img.shields.io/badge/version-3.7.0--wb1-green)]()
[![GitHub](https://img.shields.io/badge/GitHub-clippings--digest--skill-181717?logo=github)](https://github.com/JustineJiao/clippings-digest-skill)

---

## 📖 概述

**clippings-digest-skill** 是一个 AI Agent Skill，用于将 **Obsidian Web Clipper** 浏览器插件采集的网页笔记自动消化到 [llm-wiki](https://github.com/JustineJiao/llm-wiki-skill) 格式的知识库中。

### 完整工作流

```
浏览器中浏览网页
       │
       ▼
┌─────────────────┐
│ Obsidian Web     │  浏览器插件，一键 clip 网页到本地
│ Clipper 插件     │  支持文章、论文、推文、视频等
└────────┬────────┘
         │ 输出 .md 文件到 Obsidian Clippings 目录
         ▼
┌─────────────────┐
│ Obsidian         │  本地笔记管理
│ (可选)           │  可在 Obsidian 中预览/编辑 clippings
└────────┬────────┘
         │ Clippings/ 目录中的 .md 文件
         ▼
┌─────────────────┐
│ clippings-digest│  本技能：自动消化到知识库
│ skill           │  Step 1-5 完整管线
└────────┬────────┘
         │ wiki/sources/ + wiki/entities/
         ▼
┌─────────────────┐
│ llm-wiki 知识库   │  结构化、可搜索、可链接的知识体系
└─────────────────┘
```

### 核心特性

- **📥 Obsidian Web Clipper 集成** — 浏览器中一键采集，技能自动消化
- **🖼️ 图片本地化** — 自动下载外部图片到本地 attachments/
- **🧠 AI 驱动的 Two-Step CoT 分析** — 结构化分析 → 页面生成，Token 优化
- **📋 YAML frontmatter 标准化** — 统一格式的素材摘要页
- **🎯 置信度标注** — EXTRACTED / INFERRED / AMBIGUOUS / UNVERIFIED
- **📌 Review Items** — 不确定性信息自动生成待审项
- **🔗 批量交叉综合** — 批量消化后自动发现文件间关联

---

## 🚀 快速开始

### 前置要求

1. **WorkBuddy** — AI Agent 运行平台
2. **llm-wiki 知识库** — 已初始化的 llm-wiki 格式知识库
3. **Python 3.8+** — 用于图片下载和文本提取脚本
4. **Obsidian Web Clipper**（浏览器扩展）— 用于采集网页

### 浏览器端设置

1. 安装 [Obsidian Web Clipper](https://obsidian.md/clipper) 浏览器扩展
2. 在扩展中设置导出目录为知识库下的 `Clippings/` 文件夹
3. 浏览网页时点击扩展图标 → 选择模板 → **Clip page**

### 安装本技能

1. 将此 skill 目录放置到 WorkBuddy 的 skills 目录中
2. 编辑 `config/paths.json` 设置你的知识库路径
3. 在 WorkBuddy 中加载 clippings-digest skill

### 使用

说 **"消化玉米知识库中的clippings"** 或 **"消化clippings笔记"**，AI 会自动执行：

1. **Step 1**: 从 `Clippings/` 读取笔记 → 下载图片 → 搬到 `raw/clippings/`
2. **Step 2**: 提取 YAML frontmatter + 摘要 → `clippings_summary.json`
3. **Step 3**: AI 深度 Ingest（Two-Step CoT）→ 创建 source/entity 页
4. **Step 4**: 批量交叉综合 → 文件间关联发现
5. **Step 5**: 查看待审项（如有）

---

## 📋 目录结构

```
clippings-digest-skill/
├── SKILL.md                  # 核心技能文件（工作流定义）
├── README.md                 # 本文档
├── LICENSE                   # GPL-3.0
├── CHANGELOG.md              # 版本历史
├── config/
│   ├── paths.json            # 知识库路径配置（用户编辑）
│   └── entities.json         # 实体列表（可选参考）
├── scripts/
│   ├── digest_clippings.py   # Step 1: 图片本地化
│   ├── extract_clippings.py  # Step 2: 摘要提取
│   ├── create_sources.py     # (旧版) 批量生成 source 页
│   ├── create_entities.py    # (旧版) 批量生成 entity 页
│   └── list_clippings.py     # 查看辅助脚本
└── docs/
    └── SOURCES.md            # 引用来源文档
```

---

## ⚙️ 配置

编辑 `config/paths.json`：

```json
{
  "_note_clippings_dir": "要消化的原始Clippings导出文件（来源目录），处理后搬到raw_clippings",
  "_note_raw_clippings": "已图片本地化的文件存放目录（目标目录），等待Step 3 AI ingest",
  "vault_root": "./yourvault",
  "clippings_dir": "./yourvault/Clippings",
  "raw_clippings": "./yourvault/raw/clippings",
  "attachments": "./yourvault/attachments",
  "wiki_sources": "./yourvault/wiki/sources",
  "wiki_entities": "./yourvault/wiki/entities",
  "summary_json": "./yourvault/clippings_summary.json"
}
```

| 配置项 | 说明 |
|--------|------|
| `clippings_dir` | Obsidian Web Clipper 导出的原始 .md 文件目录（待消化） |
| `raw_clippings` | 图片本地化后搬入的目录（已预处理，待 AI ingest） |
| `attachments` | 图片附件存放目录 |
| `wiki_sources` | llm-wiki 素材摘要页目录 |
| `wiki_entities` | llm-wiki 实体页目录 |

---

## 🔬 技术架构

### Two-Step CoT

```
Step 1（分析）：读取 原文全文 + 现有 wiki → 结构化分析 JSON
Step 2（生成）：读取 Step 1 JSON + 已有页面（部分读取）→ wiki 页面
                         ^^^ 不重复读取原文（Token 节省）
```

### 工作流详情

| 步骤 | 输入 | 输出 | 方式 |
|------|------|------|------|
| Step 1 | `Clippings/` 中的 .md 文件 | 图片下载到 `attachments/`，文件搬到 `raw/clippings/` | Python 脚本 |
| Step 2 | `raw/clippings/*.md` | `clippings_summary.json` | Python 脚本 |
| Step 3a | clipping 全文 + wiki 上下文 | 结构化分析 JSON | AI Agent |
| Step 3b | 分析 JSON + 已有页面 | source/entity/topic 页 | AI Agent |
| Step 4 | 所有新页面 | 交叉关联 + 互链 + 主题更新 | AI Agent |
| Step 5 | `wiki/reviews/` | 用户确认待审项 | 交互 |

---

## 🤝 相关项目

- **[llm-wiki-skill](https://github.com/JustineJiao/llm-wiki-skill)** — 本技能依赖的 llm-wiki 知识库系统
- **[Obsidian Web Clipper](https://obsidian.md/clipper)** — 浏览器扩展，用于采集网页
- **[nashsu/llm_wiki](https://github.com/nashsu/llm_wiki)** — 基于 Karpathy 方法论的 llm-wiki 实现

---

## 📄 许可

[GNU General Public License v3.0](LICENSE) © 2026 JustineJiao
