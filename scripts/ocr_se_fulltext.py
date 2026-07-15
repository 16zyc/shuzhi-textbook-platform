#!/usr/bin/env python3
"""全文OCR《软件工程 第3版》→ data/se_fulltext.json
每页渲染为图片 → Vision OCR → 按行聚合文本，并附加TOC书签结构。
"""
import fitz, json, os, sys, time, subprocess

PDF = '/Users/a1111/Desktop/数值平台/14043807.pdf'
OUT = '/Users/a1111/Desktop/数值平台/data/se_fulltext.json'
OCR_SCRIPT = '/Users/a1111/.agents/skills/desktop/ocr.py'
OCR_PY = os.path.expanduser('~/tools/ocr-env/bin/python3')
TMP_IMG = '/tmp/se_ocr_page.png'

def ocr_page(img_path):
    """调用 Vision OCR，返回 [(text, conf, bbox), ...]"""
    r = subprocess.run([OCR_PY, OCR_SCRIPT, img_path, '--bbox'],
                       capture_output=True, text=True, timeout=60)
    try:
        data = json.loads(r.stdout)
        return data.get('items', [])
    except Exception:
        return []

def main():
    doc = fitz.open(PDF)
    toc = doc.get_toc()  # [[level, title, page], ...]
    total = len(doc)
    print(f'开始OCR: {total}页, TOC {len(toc)}条')

    # 按 y 坐标排序聚合为行文本
    pages = []
    t0 = time.time()
    for i in range(total):
        page = doc[i]
        pix = page.get_pixmap(dpi=200)
        pix.save(TMP_IMG)
        items = ocr_page(TMP_IMG)
        # 按 y 排序，合并同一行
        items_sorted = sorted(items, key=lambda x: x.get('bbox', [0,0,0,0])[1])
        lines = []
        cur_y = None
        cur_line = []
        for it in items_sorted:
            y = it.get('bbox', [0,0,0,0])[1]
            if cur_y is None or abs(y - cur_y) < 15:
                cur_line.append(it.get('text', ''))
                cur_y = y if cur_y is None else cur_y
            else:
                if cur_line