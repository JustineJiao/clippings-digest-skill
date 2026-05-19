#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量从 raw/clippings 读取笔记的核心信息，生成 clippings_summary.json
通用版：从 config/paths.json 读取路径
"""

import sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

# ============================================================
# 读取配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "paths.json"
with open(CONFIG_PATH, encoding="utf-8") as f:
    CFG = json.load(f)

RAW_CLIP   = Path(CFG["raw_clippings"])
SUMMARY_P  = Path(CFG["summary_json"])


# ============================================================
# 工具函数
# ============================================================
def parse_frontmatter(text):
    """解析 YAML frontmatter，返回 (fm_dict, body_text)"""
    fm = {}
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return fm, text
    block = m.group(1)
    body  = text[m.end():]
    # title
    t = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', block, re.M)
    if t: fm['title'] = t.group(1).strip('"\'')
    # source
    s = re.search(r'^source:\s*["\']?(.*?)["\']?\s*$', block, re.M)
    if s: fm['source'] = s.group(1).strip('"\'')
    # published
    p = re.search(r'^published:\s*([\d-]+)', block, re.M)
    if p: fm['published'] = p.group(1)
    # authors
    authors = re.findall(r'- "\[\[([^\]]+)\]\]"', block)
    if not authors:
        authors = re.findall(r'- \[\[([^\]]+)\]\]', block)
    fm['authors'] = authors
    # description
    d = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', block, re.M)
    if d: fm['description'] = d.group(1).strip('"\'')
    return fm, body


def extract_abstract(body):
    """提取 ## Abstract 段落，失败则取正文前 500 字"""
    m = re.search(r'## Abstract\s*\n+(.*?)(?=\n## |\Z)', body, re.DOTALL)
    if m:
        text = m.group(1).strip()
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        return text[:1500]
    # fallback
    cleaned = re.sub(r'!\[.*?\]\(.*?\)', '', body).strip()
    return cleaned[:500]


# ============================================================
# 主流程
# ============================================================
def main():
    if not RAW_CLIP.exists():
        print(f"[ERROR] raw/clippings 目录不存在: {RAW_CLIP}")
        sys.exit(1)

    results = []
    for md_path in sorted(RAW_CLIP.glob('*.md')):
        if md_path.name.startswith('_'):
            continue
        text = md_path.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(text)
        title = fm.get('title', md_path.stem)
        abstract = extract_abstract(body)
        if not abstract:
            abstract = '(无摘要)'

        results.append({
            'file':      md_path.name,
            'title':     title,
            'source':    fm.get('source', ''),
            'published': fm.get('published', ''),
            'authors':   fm.get('authors', []),
            'abstract':  abstract,
        })

    # 保存汇总 JSON
    with open(SUMMARY_P, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'已提取 {len(results)} 篇笔记摘要')
    print(f'汇总文件: {SUMMARY_P}')
    print()
    for r in results:
        year = (r['published'][:4] if r['published'] else '????')
        print(f"[{year}] {r['title'][:70]}")
        if r['authors']:
            shown = ', '.join(r['authors'][:3])
            if len(r['authors']) > 3:
                shown += ' ...'
            print(f"       作者: {shown}")
        print()


if __name__ == '__main__':
    main()
