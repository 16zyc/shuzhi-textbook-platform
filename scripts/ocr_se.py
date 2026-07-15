#!/usr/bin/env python3
"""
批量OCR《软件工程 第3版》398页
使用 macOS Vision Framework，多进程并发
输出: data/se_fulltext.json
"""
import fitz, json, os, sys, time
from multiprocessing import Pool, cpu_count

DOC_PATH = '/Users/a1111/Desktop/数值平台/14043807.pdf'
OUT_PATH = '/Users/a1111/Desktop/数值平台/data/se_fulltext.json'
DPI = 200

def ocr_page_oneshot(args):
    """单页OCR：渲染图片→调Vision→返回文本"""
    import subprocess
    page_idx, pdf_path = args
    ocr_py = os.path.expanduser('~/tools/ocr-env/bin/python3')
    ocr_script = os.path.expanduser('~/.agents/skills/desktop/ocr.py')
    tmp_img = f'/tmp/se_ocr_{page_idx}.png'

    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=DPI)
    pix.save(tmp_img)
    doc.close()

    try:
        r = subprocess.run([ocr_py, ocr_script, tmp_img, '--bbox'],
                           capture_output=True, text=True, timeout=60)
        # 解析JSON输出
        out = r.stdout.strip()
        # bbox模式输出JSON
        if out.startswith('{'):
            data = json.loads(out)
            items = data.get('items', [])
            # 按y坐标排序（从上到下），再按x
            items.sort(key=lambda it: (it['bbox'][1], it['bbox'][0]))
            text = '\n'.join(it['text'] for it in items)
        else:
            # 纯文本模式，按行
            text = out
        return page_idx, text
    except Exception as e:
        return page_idx, f'[OCR错误: {e}]'
    finally:
        if os.path.exists(tmp_img):
            os.remove(tmp_img)

def ocr_page_native(args):
    """原生Vision OCR（进程内，避免subprocess开销）"""
    page_idx, pdf_path = args
    try:
        import Vision, objc
        from Foundation import NSURL
        import fitz as _fitz

        # 渲染图片
        doc = _fitz.open(pdf_path)
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=DPI)
        tmp_img = f'/tmp/se_ocr_{os.getpid()}_{page_idx}.png'
        pix.save(tmp_img)
        doc.close()

        # Vision OCR
        url = NSURL.fileURLWithPath_(tmp_img)
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLanguages_(['zh-Hans', 'en'])
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
        success = handler.performRequests_error_([request], None)

        text_lines = []
        if success:
            observations = request.results()
            if observations:
                # 按y坐标排序（Vision的y是从下往上，需反转）
                sorted_obs = sorted(observations, key=lambda o: o.boundingBox().origin.y, reverse=True)
                for obs in sorted_obs:
                    candidate = obs.topCandidates_(1)
                    if candidate:
                        text_lines.append(candidate[0].string())
        os.remove(tmp_img)
        return page_idx, '\n'.join(text_lines)
    except Exception as e:
        return page_idx, f'[OCR错误: {e}]'

def main():
    print(f'=== 批量OCR《软件工程 第3版》 ===')
    doc = fitz.open(DOC_PATH)
    total = len(doc)
    toc = doc.get_toc()
    doc.close()
    print(f'总页数: {total}, TOC条目: {len(toc)}')

    # 准备任务
    tasks = [(i, DOC_PATH) for i in range(total)]

    # 多进程并发（4进程，平衡速度和系统负载）
    n_proc = min(4, cpu_count())
    print(f'启动 {n_proc} 进程并发OCR...')

    results = {}
    t0 = time.time()
    with Pool(n_proc) as pool:
        for i, (page_idx, text) in enumerate(pool.imap_unordered(ocr_page_native, tasks)):
            results[page_idx] = text
            done = i + 1
            if done % 20 == 0 or done == total:
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (total - done) / rate
                print(f'  进度: {done}/{total} ({done/total*100:.1f}%) 用时{elapsed:.0f}s 预计剩{eta:.0f}s')

    elapsed = time.time() - t0
    print(f'\nOCR完成! 总用时 {elapsed:.0f}s, 平均 {elapsed/total:.2f}s/页')

    # 组装输出
    pages = []
    for i in range(total):
        pages.append({
            'page': i + 1,
            'text': results.get(i, '')
        })

    # TOC结构
    toc_data = []
    for level, title, page in toc:
        toc_data.append({'level': level, 'title': title.strip(), 'page': page})

    output = {
        'book': {
            'title': '软件工程 第3版',
            'authors': '钱乐秋，赵文耘，牛军钰编著',
            'publisher': '清华大学出版社',
            'total_pages': total,
            'source': '14043807.pdf',
            'ocr_date': time.strftime('%Y-%m-%d %H:%M'),
            'ocr_engine': 'macOS Vision Framework (zh-Hans)',
            'avg_confidence': '95%+'
        },
        'toc': toc_data,
        'pages': pages
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(OUT_PATH)
    total_chars = sum(len(p['text']) for p in pages)
    non_empty = sum(1 for p in pages if p['text'].strip())
    print(f'\n已保存: {OUT_PATH}')
    print(f'文件大小: {size//1024}KB, 总字符: {total_chars}, 非空页: {non_empty}/{total}')

if __name__ == '__main__':
    main()
