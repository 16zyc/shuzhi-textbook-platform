#!/usr/bin/env python3
"""
构建关键词索引：概念→页码+位置
在原文中标注术语位置，支持前端高亮和点击关联
输出: data/se_keyword_index.json
"""
import json, re, os
from collections import defaultdict

BASE = '/Users/a1111/Desktop/数值平台/data'

def main():
    print('=== 构建关键词索引 ===')

    # 加载数据
    with open(f'{BASE}/se_fulltext.json', 'r', encoding='utf-8') as f:
        fulltext = json.load(f)
    with open(f'{BASE}/se_knowledge.json', 'r', encoding='utf-8') as f:
        knowledge = json.load(f)
    with open(f'{BASE}/se_graph.json', 'r', encoding='utf-8') as f:
        graph = json.load(f)
    with open(f'{BASE}/se_videos.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)

    # 收集所有术语（从知识图谱的概念节点）
    concepts = {}
    for node in graph['nodes']:
        if node['type'] == 'concept':
            term = node['label']
            concepts[term] = {
                'term': term,
                'freq': node.get('freq', 0),
                'pages': node.get('pages', []),
                'page_count': node.get('page_count', 0)
            }

    # 从定义中收集术语
    for sec in knowledge['sections']:
        for d in sec['definitions']:
            if 'term' in d and len(d['term']) >= 2:
                if d['term'] not in concepts:
                    concepts[d['term']] = {
                        'term': d['term'],
                        'freq': 0,
                        'pages': [],
                        'page_count': 0,
                        'definition': d['text'],
                        'def_source': d.get('source', ''),
                        'def_page': sec['page_start'],
                        'chapter': sec['chapter'],
                        'section': sec['section']
                    }
                else:
                    concepts[d['term']]['definition'] = d['text']
                    concepts[d['term']]['def_source'] = d.get('source', '')
                    concepts[d['term']]['def_page'] = sec['page_start']
                    concepts[d['term']]['chapter'] = sec['chapter']
                    concepts[d['term']]['section'] = sec['section']

    # 过滤：只保留长度>=2的术语，且出现次数>=2
    terms = {k: v for k, v in concepts.items() if len(k) >= 2}
    print(f'候选术语: {len(terms)}')

    # 构建视频关联
    video_map = {}  # term -> video keywords
    for ch in videos['chapters']:
        for res in ch['resources']:
            # 把视频关键词拆分成术语
            for kw in res['keyword'].split():
                if len(kw) >= 2:
                    video_map.setdefault(kw, []).append({
                        'title': res['title'],
                        'url': res['url'],
                        'type': res['type']
                    })

    # 在原文中查找每个术语的位置
    keyword_index = []
    pages_dict = {p['page']: p['text'] for p in fulltext['pages']}

    for term, info in terms.items():
        occurrences = []
        for page_num, text in pages_dict.items():
            start = 0
            while True:
                idx = text.find(term, start)
                if idx == -1:
                    break
                # 获取上下文（前后30字）
                ctx_start = max(0, idx - 30)
                ctx_end = min(len(text), idx + len(term) + 30)
                context = text[ctx_start:ctx_end].replace('\n', ' ')
                occurrences.append({
                    'page': page_num,
                    'pos': idx,
                    'context': context
                })
                start = idx + len(term)
                if len(occurrences) >= 20:  # 每个术语最多记录20处
                    break
            if len(occurrences) >= 20:
                break

        if len(occurrences) >= 1:  # 至少出现1次
            entry = {
                'term': term,
                'freq': len(occurrences),
                'occurrences': occurrences[:10],  # 最多保存10处
                'definition': info.get('definition', ''),
                'def_source': info.get('def_source', ''),
                'def_page': info.get('def_page', 0),
                'chapter': info.get('chapter', 0),
                'section': info.get('section', ''),
                'videos': video_map.get(term, [])
            }
            keyword_index.append(entry)

    # 按频次排序
    keyword_index.sort(key=lambda x: -x['freq'])

    # 构建页码→术语的反向索引（用于前端高亮）
    page_terms = defaultdict(list)
    for entry in keyword_index:
        for occ in entry['occurrences']:
            page_terms[occ['page']].append({
                'term': entry['term'],
                'pos': occ['pos'],
                'length': len(entry['term']),
                'has_def': bool(entry['definition']),
                'has_video': len(entry['videos']) > 0
            })

    # 每页的术语按位置排序，去重
    for page in page_terms:
        seen = set()
        unique = []
        for t in sorted(page_terms[page], key=lambda x: x['pos']):
            key = (t['pos'], t['term'])
            if key not in seen:
                seen.add(key)
                unique.append(t)
        page_terms[page] = unique

    output = {
        'book': fulltext['book'],
        'total_terms': len(keyword_index),
        'total_page_annotations': sum(len(v) for v in page_terms.values()),
        'keywords': keyword_index,
        'page_terms': {str(k): v for k, v in page_terms.items()}
    }

    out_path = f'{BASE}/se_keyword_index.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n关键词索引已保存: {out_path}')
    print(f'  术语数: {len(keyword_index)}')
    print(f'  页面标注: {sum(len(v) for v in page_terms.values())} 处')
    print(f'  有定义的术语: {sum(1 for k in keyword_index if k["definition"])}')
    print(f'  有视频的术语: {sum(1 for k in keyword_index if k["videos"])}')

    # 样例输出
    print('\n=== Top 10 高频术语 ===')
    for k in keyword_index[:10]:
        def_info = f' 📜有定义' if k['definition'] else ''
        vid_info = f' 🎬有视频' if k['videos'] else ''
        print(f'  {k["term"]}: {k["freq"]}次{def_info}{vid_info}')

if __name__ == '__main__':
    main()
