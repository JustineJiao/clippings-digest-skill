#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理 Obsidian Clippings 笔记中的外部图片：
1. 下载图片到本地 attachments/ 目录
2. 替换 Markdown 中的图片链接为本地路径
3. 将处理完的文件移动到 raw/clippings/ 目录

通用版：从 config/paths.json 读取路径配置
"""

import os
import re
import sys
import json
import shutil
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

# ============================================================
# 读取配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "paths.json"

with open(CONFIG_PATH, encoding="utf-8") as f:
    CFG = json.load(f)

WIKI_ROOT    = Path(CFG["vault_root"])
CLIPPINGS    = Path(CFG["clippings_dir"])
ATTACHMENTS  = Path(CFG["attachments"])
RAW_CLIPPINGS = Path(CFG["raw_clippings"])

# 超时（秒）
HTTP_TIMEOUT = 20
# User-Agent（避免部分服务器拒绝）
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Markdown 图片正则：![alt](url) 或 ![alt](url "title")
IMG_RE = re.compile(
    r'!\[([^\]]*)\]\((https?://[^)\s"]+)(?:\s+"[^"]*")?\)',
    re.IGNORECASE
)


# ============================================================
# 工具函数
# ============================================================
def url_to_filename(url: str, idx: int) -> str:
    """根据 URL 生成本地文件名（保留扩展名，用 MD5 做唯一前缀）"""
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    basename = url.split("?")[0].rstrip("/").split("/")[-1]
    ext = ""
    if "." in basename:
        ext = "." + basename.rsplit(".", 1)[-1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"):
            ext = ".png"
    else:
        ext = ".png"
    return f"{h}{ext}"


def download_image(url: str, dest: Path) -> bool:
    """下载图片到 dest，返回是否成功"""
    if dest.exists():
        return True   # 已存在，跳过
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = resp.read()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"    [WARN] 下载失败: {url}")
        print(f"           原因: {e}")
        return False


def process_file(md_path: Path) -> dict:
    """处理单个 Markdown 文件，返回统计信息"""
    content = md_path.read_text(encoding="utf-8")

    matches = IMG_RE.findall(content)
    total   = len(matches)
    ok      = 0
    fail    = 0

    if total > 0:
        new_content = content
        for idx, (alt, url) in enumerate(matches):
            fname   = url_to_filename(url, idx)
            dest    = ATTACHMENTS / fname
            local_link = f"attachments/{fname}"

            success = download_image(url, dest)
            if success:
                ok += 1
                # 精确替换当前这张图片的链接
                pattern = (
                    r'!\[' + re.escape(alt) +
                    r'\]\(' + re.escape(url) + r'(?:\s+"[^"]*")?\)'
                )
                replacement = f'![{alt}]({local_link})'
                new_content = re.sub(
                    pattern, replacement, new_content, count=1
                )
            else:
                fail += 1

        md_path.write_text(new_content, encoding="utf-8")

    # 移动到 raw/clippings/
    RAW_CLIPPINGS.mkdir(parents=True, exist_ok=True)
    dest_path = RAW_CLIPPINGS / md_path.name
    if dest_path.exists():
        dest_path.unlink()
    shutil.move(str(md_path), str(dest_path))

    return {
        "file": md_path.name,
        "total_images": total,
        "downloaded": ok,
        "failed": fail,
        "moved_to": str(dest_path),
    }


# ============================================================
# 主流程
# ============================================================
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    if not CLIPPINGS.exists():
        print(f"[ERROR] Clippings 目录不存在: {CLIPPINGS}")
        print("请编辑 config/paths.json 设置正确路径")
        sys.exit(1)

    md_files = sorted(CLIPPINGS.glob("*.md"))
    if not md_files:
        print(f"[INFO] {CLIPPINGS} 目录下没有 .md 文件")
        sys.exit(0)

    print(f"找到 {len(md_files)} 个 Clipping 文件")
    print(f"附件目录: {ATTACHMENTS}")
    print(f"目标目录: {RAW_CLIPPINGS}")
    print("=" * 70)

    all_stats = []
    for i, md_path in enumerate(md_files, 1):
        print(f"[{i:02d}/{len(md_files)}] 处理: {md_path.name[:60]}")
        stats = process_file(md_path)
        all_stats.append(stats)
        print(
            f"       图片: {stats['total_images']} 张, "
            f"成功: {stats['downloaded']}, "
            f"失败: {stats['failed']}"
        )

    # 汇总
    print("=" * 70)
    total_imgs  = sum(s["total_images"] for s in all_stats)
    total_ok    = sum(s["downloaded"]   for s in all_stats)
    total_fail  = sum(s["failed"]      for s in all_stats)
    total_moved = len(all_stats)
    print(f"完成! 处理文件: {total_moved}")
    print(f"      总图片: {total_imgs}")
    print(f"      下载成功: {total_ok}")
    print(f"      下载失败: {total_fail}")

    # 输出失败详情
    failed_files = [s for s in all_stats if s["failed"] > 0]
    if failed_files:
        print("\n--- 有图片下载失败的文件 ---")
        for s in failed_files:
            print(f"  {s['file']}: {s['failed']} 张失败")

    # 写入处理报告
    report_path = RAW_CLIPPINGS / "_digest_report.md"
    lines = [
        "# Clippings 批量处理报告\n",
        f"- 处理时间: {Path(__file__).stem}\n",
        f"- 处理文件: {total_moved} 个\n",
        f"- 图片总数: {total_imgs}\n",
        f"- 下载成功: {total_ok}\n",
        f"- 下载失败: {total_fail}\n",
        "\n## 文件详情\n\n",
        "| 文件名 | 图片数 | 成功 | 失败 |\n",
        "|--------|--------|------|------|\n"
    ]
    for s in all_stats:
        fname = s["file"][:60]
        lines.append(f"| {fname} | {s['total_images']} | {s['downloaded']} | {s['failed']} |\n")
    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()
