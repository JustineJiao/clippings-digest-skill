# CHANGELOG

## 3.7.0-wb1 (2026-05-19)
- 仓库: https://github.com/JustineJiao/clippings-digest-skill
- 许可证: GPL-3.0
- 适配 WorkBuddy 平台
- Step 3 从 Python 脚本机械生成改为 AI 驱动的 Two-Step CoT
- 新增 YAML frontmatter 标准化
- 新增置信度标注（EXTRACTED/INFERRED/AMBIGUOUS/UNVERIFIED）
- 新增 Review Items 机制
- 新增批量交叉综合（Step 4）
- SHA256 缓存检查
- Token 优化：Step 3b 不重复读取原素材
- 明确 Clippings/ 与 raw/clippings/ 的目录定位

## 旧版
- 初始版本：Python 脚本驱动的 clippings 消化管线
