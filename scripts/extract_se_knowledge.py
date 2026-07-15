#!/usr/bin/env python3
"""
从OCR全文抽取知识点、定义、关键词，构建知识图谱
依赖: data/se_fulltext.json (OCR结果)
输出:
  - data/se_knowledge.json  知识点（含定义、页码溯源、所属章节）
  - data/se_graph.json      概念知识图谱（节点+边）
"""
import json, re, os
from collections import defaultdict

BASE = '/Users/a1111/Desktop/数值平台/data'
FULLTEXT = f'{BASE}/se_fulltext.json'

def load():
    with open(FULLTEXT, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_chapters(toc):
    """从TOC构建章节结构，计算每章/节的页码范围"""
    chapters = []
    # 只取正文部分（第1章到第16章）
    ch1_idx = next(i for i, t in enumerate(toc) if '第1章' in t['title'])
    last_idx = next((i for i, t in enumerate(toc) if '词汇索引' in t['title']), len(toc))
    body_toc = toc[ch1_idx:last_idx]

    # 按1级分章
    ch_starts = [i for i, t in enumerate(body_toc) if t['level'] == 1]
    ch_starts.append(len(body_toc))

    for ci in range(len(ch_starts) - 1):
        s, e = ch_starts[ci], ch_starts[ci+1]
        ch_toc = body_toc[s:e]
        ch = ch_toc[0]
        ch_end_page = body_toc[ch_starts[ci+1]]['page'] - 1 if ci + 1 < len(ch_starts) - 1 else 373

        # 2级节
        sections = []
        sec_starts = [i for i, t in enumerate(ch_toc) if t['level'] == 2]
        sec_starts.append(len(ch_toc))
        for si in range(len(sec_starts) - 1):
            ss, se = sec_starts[si], sec_starts[si+1]
            sec_toc = ch_toc[ss:se]
            sec = sec_toc[0]
            sec_end_page = ch_toc[sec_starts[si+1]]['page'] - 1 if si + 1 < len(sec_starts) - 1 else ch_end_page

            # 3级小节
            subsections = []
            for t in sec_toc[1:]:
                if t['level'] == 3:
                    subsections.append({'title': t['title'], 'page': t['page']})

            sections.append({
                'title': sec['title'],
                'page_start': sec['page'],
                'page_end': sec_end_page,
                'subsections': subsections
            })

        # 解析章号
        m = re.match(r'第(\d+)章\s*(.*)', ch['title'])
        ch_num = int(m.group(1)) if m else ci + 1
        ch_title = m.group(2) if m else ch['title']

        chapters.append({
            'num': ch_num,
            'title': ch_title,
            'full_title': ch['title'],
            'page_start': ch['page'],
            'page_end': ch_end_page,
            'sections': sections
        })
    return chapters

def get_page_text(data, page_num):
    for p in data['pages']:
        if p['page'] == page_num:
            return p['text']
    return ''

def get_section_text(data, page_start, page_end):
    """合并一个节范围内的页面文本"""
    texts = []
    for p in data['pages']:
        if page_start <= p['page'] <= page_end:
            texts.append(p['text'])
    return '\n'.join(texts)

# 定义抽取模式
DEF_PATTERNS = [
    r'(?:称为|定义为|是[指什么]*[：:])\s*[，。]',
    r'(?:定义[为是]|指的?是|是指)\s*[^。\n]{5,80}[。]',
    r'在[《<]([^》>]+)[》>]中[，,]?\s*(?:对[^，,]+作出)?(?:如下)?定义[：:]\s*([^。\n]+[。])',
    r'所谓([^，,。]+)[，,]\s*是指\s*([^。\n]+[。])',
]

def extract_definitions(text):
    """从文本中抽取定义句"""
    defs = []
    # 模式1: "在《XXX》中，...定义：..."
    for m in re.finditer(r'在[《<]([^》>]+)[》>]中[，,]?\s*[^。]*?定义[：:]\s*([^。\n]{10,150}[。])', text):
        defs.append({'source': m.group(1), 'text': m.group(2).strip()})
    # 模式2: "XXX是指/定义为/称为..."
    for m in re.finditer(r'([A-Za-z\u4e00-\u9fa5]{2,15})\s*(?:是指|定义为|称为|指的是|是指的?是)\s*([^。\n]{10,120}[。])', text):
        term = m.group(1).strip()
        definition = m.group(2).strip()
        if len(term) >= 2 and not term.startswith('这') and not term.startswith('那'):
            defs.append({'term': term, 'text': definition})
    # 模式3: "所谓XXX，是指..."
    for m in re.finditer(r'所谓([A-Za-z\u4e00-\u9fa5]{2,15})[，,]\s*是指\s*([^。\n]{10,120}[。])', text):
        defs.append({'term': m.group(1), 'text': m.group(2).strip()})
    return defs

def extract_keywords(text, max_n=15):
    """简易关键词抽取：高频术语"""
    # 候选：中文2-6字词、英文术语
    words = re.findall(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)*|[A-Z]{2,}|[\u4e00-\u9fa5]{2,6}', text)
    # 停用词
    stop = set(['软件','系统','方法','过程','可以','一个','这种','这种','进行','需要','通过','以及','或者','例如',
                '如下','以下','上述','该章','本章','如图','所示','表示','进行','这一','这些','这种','从而','因此',
                '以及','对于','关于','为了','使得','使得','得到','成为','称为','作为','基于','根据','按照',
                '其中','其他','另外','此外','一般','通常','主要','基本','或者','如果','虽然','但是','然后',
                '已经','可能','应该','必须','可以','能够','这样','那样','什么','怎么','为什么','哪些',
                '开发','设计','分析','管理','模型','类型','阶段','活动','目标','结果','要求','功能','数据',
                '信息','结构','关系','方面','方式','形式','机制','原理','概念','特点','特征','性质','分类'])
    freq = defaultdict(int)
    for w in words:
        if w not in stop and len(w) >= 2:
            freq[w] += 1
    return sorted(freq.items(), key=lambda x: -x[1])[:max_n]

def find_term_pages(data, term):
    """查找术语出现的页码"""
    pages = []
    for p in data['pages']:
        if term in p['text']:
            pages.append(p['page'])
    return pages

def main():
    print('=== 抽取知识点/定义/关键词 ===')
    data = load()
    chapters = build_chapters(data['toc'])
    print(f'章节结构: {len(chapters)}章')

    knowledge = []
    graph_nodes = {}
    graph_edges = []

    for ch in chapters:
        print(f'\n处理 {ch["full_title"]} (p{ch["page_start"]}-{ch["page_end"]})...')
        for sec in ch['sections']:
            sec_text = get_section_text(data, sec['page_start'], sec['page_end'])
            if not sec_text.strip():
                continue

            # 解析节号
            m = re.match(r'(\d+\.\d+)\s*(.*)', sec['title'])
            sec_num = m.group(1) if m else ''
            sec_title = m.group(2) if m else sec['title']

            # 抽取定义
            defs = extract_definitions(sec_text)
            # 抽取关键词
            keywords = extract_keywords(sec_text, max_n=10)

            kp = {
                'chapter': ch['num'],
                'chapter_title': ch['title'],
                'section': sec_num,
                'section_title': sec_title,
                'full_title': f'{ch["num"]}.{sec_num} {sec_title}' if sec_num else sec_title,
                'page_start': sec['page_start'],
                'page_end': sec['page_end'],
                'definitions': defs[:5],
                'keywords': [{'term': t, 'freq': f} for t, f in keywords],
                'text_preview': sec_text[:200].replace('\n', ' '),
                'text_length': len(sec_text)
            }
            knowledge.append(kp)

            # 图谱节点：节
            node_id = f'{ch["num"]}.{sec_num}' if sec_num else f'ch{ch["num"]}'
            graph_nodes[node_id] = {
                'id': node_id,
                'label': sec_title,
                'type': 'section',
                'chapter': ch['num'],
                'page': sec['page_start'],
                'full': f'第{ch["num"]}章 {ch["title"]} → {sec_num} {sec_title}'
            }
            # 边：章→节
            ch_id = f'ch{ch["num"]}'
            if ch_id not in graph_nodes:
                graph_nodes[ch_id] = {
                    'id': ch_id,
                    'label': ch['title'],
                    'type': 'chapter',
                    'chapter': ch['num'],
                    'page': ch['page_start'],
                    'full': f'第{ch["num"]}章 {ch["title"]}'
                }
            graph_edges.append({'source': ch_id, 'target': node_id, 'type': 'contains'})

            # 关键词作为概念节点
            for kw, freq in keywords[:5]:
                kw_id = f'kw_{kw}'
                if kw_id not in graph_nodes:
                    # 查找术语出现的所有页码
                    term_pages = find_term_pages(data, kw)
                    graph_nodes[kw_id] = {
                        'id': kw_id,
                        'label': kw,
                        'type': 'concept',
                        'freq': freq,
                        'pages': term_pages[:10],
                        'page_count': len(term_pages)
                    }
                graph_edges.append({'source': node_id, 'target': kw_id, 'type': 'mentions', 'weight': freq})

    # 保存知识点
    out_kp = {
        'book': data['book'],
        'chapters': [{'num': c['num'], 'title': c['title'], 'full_title': c['full_title'],
                      'page_start': c['page_start'], 'page_end': c['page_end'],
                      'section_count': len(c['sections'])} for c in chapters],
        'sections': knowledge,
        'total_sections': len(knowledge),
        'total_definitions': sum(len(k['definitions']) for k in knowledge)
    }
    with open(f'{BASE}/se_knowledge.json', 'w', encoding='utf-8') as f:
        json.dump(out_kp, f, ensure_ascii=False, indent=2)
    print(f'\n知识点已保存: {BASE}/se_knowledge.json')
    print(f'  节数: {len(knowledge)}, 定义数: {out_kp["total_definitions"]}')

    # 保存图谱
    out_graph = {
        'book': data['book'],
        'nodes': list(graph_nodes.values()),
        'links': graph_edges,
        'node_count': len(graph_nodes),
        'edge_count': len(graph_edges)
    }
    with open(f'{BASE}/se_graph.json', 'w', encoding='utf-8') as f:
        json.dump(out_graph, f, ensure_ascii=False, indent=2)
    print(f'知识图谱已保存: {BASE}/se_graph.json')
    print(f'  节点: {len(graph_nodes)}, 边: {len(graph_edges)}')

if __name__ == '__main__':
    main()
