#!/usr/bin/env python3
"""
构建概念图谱数据：上下级关系（章→节→概念）+ 共现关系（同章节共同出现的概念）
输出: data/se_concept_graph.json
"""
import json
from collections import defaultdict
from itertools import combinations

BASE = '/Users/a1111/Desktop/数值平台/data'

def main():
    print('=== 构建概念图谱 ===')
    with open(f'{BASE}/se_knowledge.json','r',encoding='utf-8') as f:
        knowledge = json.load(f)
    with open(f'{BASE}/se_definitions.json','r',encoding='utf-8') as f:
        defs_data = json.load(f)
    with open(f'{BASE}/se_keyword_index.json','r',encoding='utf-8') as f:
        kw_index = json.load(f)

    nodes = []
    edges = []

    # 1. 章节节点
    for ch in knowledge['chapters']:
        nodes.append({
            'id': f'ch-{ch["num"]}',
            'label': f'第{ch["num"]}章 {ch["title"]}',
            'type': 'chapter',
            'chapter': ch['num']
        })

    # 2. 节节点
    for sec in knowledge['sections']:
        nodes.append({
            'id': f'sec-{sec["chapter"]}-{sec["section"]}',
            'label': f'{sec["section"]} {sec["section_title"]}',
            'type': 'section',
            'chapter': sec['chapter']
        })
        # 章→节 上下级边
        edges.append({
            'source': f'ch-{sec["chapter"]}',
            'target': f'sec-{sec["chapter"]}-{sec["section"]}',
            'type': 'hierarchy'
        })

    # 3. 概念节点
    for kw in kw_index['keywords']:
        if kw['chapter'] > 0 or kw['definition']:
            ch = kw['chapter'] if kw['chapter'] > 0 else 0
            nodes.append({
                'id': f'kw-{kw["term"]}',
                'label': kw['term'],
                'type': 'concept',
                'chapter': ch,
                'has_def': bool(kw['definition']),
                'has_video': len(kw.get('videos',[])) > 0,
                'freq': kw['freq']
            })

    # 4. 概念的上下级关系（章→概念）
    for kw in kw_index['keywords']:
        if kw['chapter'] > 0:
            edges.append({
                'source': f'ch-{kw["chapter"]}',
                'target': f'kw-{kw["term"]}',
                'type': 'hierarchy'
            })

    # 5. 共现关系（同一页出现的概念之间）
    page_concepts = defaultdict(set)
    for page_str, terms in kw_index['page_terms'].items():
        for t in terms:
            page_concepts[int(page_str)].add(t['term'])

    cooccur_count = defaultdict(int)
    for page, terms in page_concepts.items():
        if len(terms) < 2:
            continue
        for pair in combinations(sorted(terms), 2):
            cooccur_count[pair] += 1

    # 只保留共现>=2次的
    for (t1, t2), count in cooccur_count.items():
        if count >= 2:
            edges.append({
                'source': f'kw-{t1}',
                'target': f'kw-{t2}',
                'type': 'cooccurrence',
                'weight': count
            })

    # 按章节分组（方便前端按章加载）
    by_chapter = {}
    for ch in knowledge['chapters']:
        ch_num = ch['num']
        ch_nodes = [n for n in nodes if n.get('chapter') == ch_num]
        ch_node_ids = {n['id'] for n in ch_nodes}
        ch_edges = [e for e in edges if e['source'] in ch_node_ids or e['target'] in ch_node_ids]
        by_chapter[str(ch_num)] = {
            'chapter': ch_num,
            'title': ch['title'],
            'nodes': ch_nodes,
            'edges': ch_edges
        }

    output = {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'nodes': nodes,
        'edges': edges,
        'by_chapter': by_chapter
    }

    out_path = f'{BASE}/se_concept_graph.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'概念图谱已保存: {out_path}')
    print(f'  节点: {len(nodes)} (章{len(knowledge["chapters"])} + 节{len(knowledge["sections"])} + 概念{len([n for n in nodes if n["type"]=="concept"])})')
    print(f'  边: {len(edges)} (上下级{len([e for e in edges if e["type"]=="hierarchy"])} + 共现{len([e for e in edges if e["type"]=="cooccurrence"])})')
    print(f'\n各章图谱规模:')
    for ch in knowledge['chapters']:
        g = by_chapter[str(ch['num'])]
        print(f'  第{ch["num"]}章 {ch["title"]}: {len(g["nodes"])}节点, {len(g["edges"])}边')

if __name__ == '__main__':
    main()
