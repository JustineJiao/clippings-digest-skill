# SOURCES.md — 引用来源与灵感

本文档列出了 clippings-digest-skill 设计过程中引用的所有来源。

---

## 🔥 核心来源

### 1. JustineJiao/llm-wiki-skill

- **来源**: https://github.com/JustineJiao/llm-wiki-skill
- **说明**: 本技能依赖的 llm-wiki 知识库系统，ingest/query/digest 等方法论复用自 llm-wiki
- **贡献**: Two-Step CoT、YAML frontmatter 标准、置信度系统、Review Items 机制

### 2. Obsidian Web Clipper

- **来源**: https://obsidian.md/clipper
- **说明**: 浏览器扩展，将网页一键保存为 Markdown 笔记
- **贡献**: 本技能处理的数据来源，Clippings/ 目录中的 .md 文件由该插件生成

### 3. nashsu/llm_wiki

- **来源**: https://github.com/nashsu/llm_wiki
- **作者**: nashsu
- **贡献**: 基于 Karpathy 方法论的 llm-wiki 实现，工作流设计的参考

### 4. Karpathy's llm-wiki

- **来源**: https://github.com/karpathy/llm-wiki
- **作者**: Andrej Karpathy
- **贡献**: 核心理念和方法论

---

## 🛠️ 工具依赖

- **WorkBuddy** — https://www.codebuddy.cn/docs/workbuddy/Overview — AI Agent 运行平台
- **Python 3** — 图片下载和文本提取脚本
- **markitdown** — https://github.com/microsoft/markitdown — 文件格式转换（可选）

---

## 📝 版本说明

| 版本 | 日期 | 主要变化 |
|------|------|---------|
| 3.7.0-wb1 | 2026-05-19 | 适配 WorkBuddy，Two-Step CoT |
| 旧版 | 2025 | Python 脚本驱动版 |
