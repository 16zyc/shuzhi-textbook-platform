#!/usr/bin/env python3
"""
从PDF提取真实图片，生成图片索引
输出:
  - data/se_images.json (图片元数据)
  - images/se/ (图片文件，按页码命名)
"""
import json, os
import fitz  # PyMuPDF

PDF_PATH = '/Users/a1111/Desktop/数值平台/14043807.pdf'
OUT_DIR = '/Users/a1111/Desktop/数值平台/images/se'
DATA_DIR = '/Users/a1111/Desktop/数值平台/data'

os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print('=== 从PDF提取图片 ===')
    doc = fitz.open(PDF_PATH)
    print(f'总页数: {doc.page_count}')

    images = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        if not image_list:
            continue

        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image['image']
                ext = base_image['ext']
                # 只保留有意义的图片（>2KB，排除小图标）
                if len(image_bytes) < 2000:
                    continue

                img_filename = f'p{page_num+1:03d}_{img_index}.{ext}'
                img_path = os.path.join(OUT_DIR, img_filename)
                with open(img_path, 'wb') as f:
                    f.write(image_bytes)

                # 获取图片在页面中的位置
                page_rect = page.rect
                blocks = page.get_text('dict')['blocks']
                img_bbox = None
                for b in blocks:
                    if b['type'] == 1:  # image block
                        img_bbox = b['bbox']
                        break

                images.append({
                    'page': page_num + 1,
                    'index': img_index,
                    'file': f'images/se/{img_filename}',
                    'width': base_image.get('width', 0),
                    'height': base_image.get('height', 0),
                    'size_kb': round(len(image_bytes) / 1024, 1)
                })
            except Exception as e:
                print(f'  页{page_num+1} 图片{img_index} 提取失败: {e}')
                continue

        if (page_num + 1) % 50 == 0:
            print(f'  已处理 {page_num+1}/{doc.page_count} 页，提取 {len(images)} 张图片')

    # 按章节分组
    chapters = {}
    # 加载章节信息
    with open(f'{DATA_DIR}/se_knowledge.json','r',encoding='utf-8') as f:
        knowledge = json.load(f)

    for img in images:
        # 找到所属章节
        ch = None
        for c in knowledge['chapters']:
            if c['page_start'] <= img['page'] <= c['page_end']:
                ch = c['num']
                break
        if ch is None:
            ch = 0
        img['chapter'] = ch
        chapters.setdefault(ch, []).append(img)

    output = {
        'total_images': len(images),
        'total_pages': doc.page_count,
        'images': images,
        'by_chapter': {str(k): len(v) for k, v in chapters.items()}
    }

    out_path = f'{DATA_DIR}/se_images.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n图片提取完成:')
    print(f'  总图片数: {len(images)}')
    print(f'  数据保存: {out_path}')
    print(f'  图片目录: {OUT_DIR}')
    print(f'\n各章图片数:')
    for ch in sorted(chapters.keys()):
        if ch > 0:
            c = next(c for c in knowledge['chapters'] if c['num'] == ch)
            print(f'  第{ch}章 {c["title"]}: {len(chapters[ch])}张')

    doc.close()

if __name__ == '__main__':
    main()
