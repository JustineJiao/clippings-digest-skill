#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出 raw/clippings/ 中所有文件，显示标题和来源域名
通用版：从 config/paths.json 读取路径
"""

import sys, re
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

# ============================================================
# 读取配置
# ============================================================
SCRIPT_DIR  = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "paths.json"
with open(CONFIG_PATH, encoding="utf-8") as f:
    CFG = json.load(f)

RAW_CLIP = Path(CFG["raw_clippings"])


def main():
    if not RAW_CLIP.exists():
        print(f"[ERROR] raw/clippings 目录不存在: {RAW_CLIP}")
        sys.exit(1)

    files = sorted(RAW_CLIP.glob('*.md'))
    # 过滤掉下划线开头的报告文件
    files = [f for f in files if not f.name.startswith('_')]

    print(f'raw/clippings 中共 {len(files)} 个文件\n')
    for f in files:
        text = f.read_text(encoding='utf-8')
        # 解析 frontmatter
        title_m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', text, re.M)
        source_m = re.search(r'^source:\s*["\']?(.*?)["\']?\s*$', text, re.M)
        title = title_m.group(1).strip('"\'') if title_m else f.stem
        source = source_m.group(1).strip('"\'') if source_m else ''
        domain_m = re.search(r'https?://([^/]+)', source)
        domain = domain_m.group(1) if domain_m else 'unknown'
        print(f'[{domain[:28]}] {title[:70]}')


if __name__ == '__main__':
    main()
