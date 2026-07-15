#!/usr/bin/env python3
"""
重新构建关键词索引：jieba分词+专业词典+停用词+全文真实频次
解决：碎片化、无意义词、频次不准
输出: data/se_keyword_index.json (覆盖)
"""
import json, re, os
from collections import defaultdict, Counter

BASE = '/Users/a1111/Desktop/数值平台/data'

# 软件工程专业词典（保持完整，不被切分）
SE_DICT = [
    # 核心概念
    '软件工程','软件危机','软件过程','软件生命周期','软件生存周期','软件度量',
    '需求工程','需求获取','需求分析','需求规约','需求验证','需求管理','需求规格说明',
    '软件设计','体系结构设计','详细设计','概要设计','设计模式','模块化','内聚','耦合',
    '结构化分析','结构化设计','结构化程序设计','数据流图','数据字典','DFD',
    '面向对象','面向对象分析','面向对象设计','面向对象编程','封装','继承','多态',
    'UML','统一建模语言','类图','用例图','时序图','状态图','活动图','对象图',
    '软件构件','构件复用','CBSD','软件复用','SOA','微服务','面向服务架构',
    '敏捷开发','Scrum','极限编程','XP','看板','DevOps','持续集成','持续交付',
    '人机界面','用户界面','交互设计','可用性','用户体验',
    '程序设计语言','编码规范','代码质量','代码审查','重构',
    '软件测试','单元测试','集成测试','系统测试','验收测试','白盒测试','黑盒测试',
    '回归测试','自动化测试','测试用例','测试覆盖','JMeter','JUnit','Selenium',
    'Web工程','前端开发','后端开发','RESTful','API设计',
    '软件维护','再工程','逆向工程','技术债务','遗留系统',
    '软件项目管理','项目计划','风险管理','质量保证','配置管理','CMM','CMMI',
    # 方法与模型
    '瀑布模型','增量模型','螺旋模型','原型模型','喷泉模型','V模型','敏捷模型',
    '软件质量','软件可靠性','软件可维护性','软件可移植性',
    '基线','里程碑','版本控制','Git',
    # 工具与标准
    'ISO','IEC','IEEE','GB','国家标准',
    '软件工具','CASE工具','集成开发环境','IDE',
    '软件文档','需求文档','设计文档','测试文档','用户手册',
    # 经典概念
    '数据结构','算法','数据库','关系数据库','SQL',
    '客户端','服务器','浏览器','HTTP','TCP','IP',
    '面向数据流','面向数据结构','Jackson方法','Warnier图',
    '类','对象','消息','方法','属性','接口','组件','框架',
    '抽象','封装','继承','多态','重用','复用',
    '验证','确认','评审','审计','走查','检视',
]

# 停用词（无意义词，不作为关键词）
STOP_WORDS = {
    # 常用动词
    '进行','可以','应该','需要','可能','使用','通过','基于','根据','按照','为了','使得',
    '包括','包含','组成','形成','产生','建立','实现','完成','提供','支持','保证',
    '描述','说明','表示','定义','确定','设定','设置','选择','采用','利用','运用',
    '做什么','的问题','简述','如下','例如','比如','其中','其他','以及','并且','或者',
    '用于','属于','关于','对于','由于','鉴于','考虑','涉及','相关','对应','适用',
    '开始','结束','结果','过程','方式','方法','方面','方向','目的','目标','原因',
    # 常用名词（太泛）
    '人员','工具','东西','内容','部分','方面','类型','种类','形式','状态','情况',
    '问题','要求','需求','功能','性能','质量','效果','结果','能力','水平',
    '原则','限制','描述','分解','限制','成本','效益','获取','验证','维护',
    '世纪','年代','时间','时期','阶段','步骤','过程','周期',
    # 单字
    '的','了','是','在','和','与','或','及','以','为','对','从','到','向','按','把','被','让','使',
    '中','上','下','内','外','前','后','间','里','旁',
    '这','那','其','此','该','某','各','每','任','所',
    '一','二','三','四','五','六','七','八','九','十',
    '个','只','种','类','些','多','少','大','小','长','短','高','低',
    '做','说','看','想','给','拿','放','用','来','去','到','成','变','得','地',
    # 抽取出的错误片段
    '据流','基于计算机的','计算机的系统','报名单','考生通知单','主程序',
    '结构化程序设','结构化分析与','增量','代码','测试','需求','模块',
    '语言','风险','体系结构','加工','数据流',
}

def main():
    print('=== 重新构建关键词索引 ===')
    import jieba

    # 加载专业词典
    for w in SE_DICT:
        jieba.add_word(w, freq=10000, tag='se')
    print(f'已加载 {len(SE_DICT)} 个专业词典')

    # 加载数据
    with open(f'{BASE}/se_fulltext.json','r',encoding='utf-8') as f:
        fulltext = json.load(f)
    with open(f'{BASE}/se_knowledge.json','r',encoding='utf-8') as f:
        knowledge = json.load(f)
    with open(f'{BASE}/se_videos.json','r',encoding='utf-8') as f:
        videos = json.load(f)
    with open(f'{BASE}/se_external_resources.json','r',encoding='utf-8') as f:
        ext = json.load(f)

    # 收集定义术语
    def_terms = {}
    for sec in knowledge['sections']:
        for d in sec['definitions']:
            if 'term' in d and len(d['term']) >= 2:
                def_terms[d['term']] = {
                    'definition': d['text'],
                    'def_source': d.get('source',''),
                    'def_page': sec['page_start'],
                    'chapter': sec['chapter'],
                    'section': sec['section']
                }
    print(f'定义术语: {len(def_terms)}')

    # 构建视频关联
    video_map = {}
    for ch in videos['chapters']:
        for res in ch['resources']:
            video_map.setdefault(ch['chapter'], []).append({
                'title': res['title'], 'url': res['url']
            })

    # 在全文上分词并统计
    print('开始全文分词...')
    term_freq = Counter()  # 全局频次
    term_pages = defaultdict(list)  # term -> [(page, pos, context)]

    pages_dict = {p['page']: p['text'] for p in fulltext['pages']}

    for page_num, text in pages_dict.items():
        if not text or len(text) < 10:
            continue
        words = jieba.cut(text)
        pos = 0
        for w in words:
            wl = len(w)
            if wl >= 2 and w not in STOP_WORDS and not w.isdigit() and not re.match(r'^[A-Z]+$', w) and not re.match(r'^[\d\.\-]+$', w):
                # 进一步过滤：纯标点、纯英文单字母
                if re.match(r'^[\W_]+$', w):
                    pos += wl
                    continue
                # 只保留专业词典中的词，或频次>=5的词，或有定义的词
                if w in SE_DICT or w in def_terms:
                    term_freq[w] += 1
                    if len(term_pages[w]) < 15:
                        ctx_start = max(0, pos-20)
                        ctx_end = min(len(text), pos+wl+20)
                        ctx = text[ctx_start:ctx_end].replace('\n',' ')
                        term_pages[w].append({
                            'page': page_num, 'pos': pos, 'context': ctx
                        })
            pos += wl

    print(f'分词完成，候选术语: {len(term_freq)}')

    # 过滤：频次>=3 或 有定义
    valid_terms = Counter({k:v for k,v in term_freq.items() if v >= 3 or k in def_terms})
    print(f'有效术语: {len(valid_terms)}')

    # 构建关键词索引
    keywords = []
    for term, freq in valid_terms.most_common():
        occs = term_pages[term]
        def_info = def_terms.get(term, {})
        # 找视频关联：按章节
        chapter = def_info.get('chapter', 0)
        vids = []
        if chapter and chapter in video_map:
            # 关联该章节的视频
            vids = video_map[chapter][:3]
        # 外部资源关联
        ch_ext = next((c for c in ext['chapters'] if c['chapter'] == chapter), None) if chapter else None
        ext_vids = ch_ext['videos'][:2] if ch_ext else []
        ext_gh = ch_ext['github'][:2] if ch_ext else []
        ext_arxiv = ch_ext['arxiv'][:1] if ch_ext else []

        entry = {
            'term': term,
            'freq': freq,
            'occurrences': [{'page':o['page'],'pos':o['pos'],'context':o['context']} for o in occs[:10]],
            'definition': def_info.get('definition',''),
            'def_source': def_info.get('def_source',''),
            'def_page': def_info.get('def_page',0),
            'chapter': chapter,
            'section': def_info.get('section',''),
            'videos': ext_vids,
            'github': ext_gh,
            'arxiv': ext_arxiv
        }
        keywords.append(entry)

    # 构建页码→术语反向索引
    page_terms = defaultdict(list)
    for entry in keywords:
        for occ in entry['occurrences']:
            page_terms[occ['page']].append({
                'term': entry['term'],
                'pos': occ['pos'],
                'length': len(entry['term']),
                'has_def': bool(entry['definition']),
                'has_video': len(entry['videos']) > 0
            })

    # 每页按位置排序去重
    for page in page_terms:
        seen = set()
        unique = []
        for t in sorted(page_terms[page], key=lambda x: x['pos']):
            key = (t['pos'], t['term'])
            if key not in seen and t['pos'] >= 0:
                seen.add(key)
                unique.append(t)
        page_terms[page] = unique

    output = {
        'book': fulltext['book'],
        'total_terms': len(keywords),
        'total_page_annotations': sum(len(v) for v in page_terms.values()),
        'keywords': keywords,
        'page_terms': {str(k): v for k, v in page_terms.items()}
    }

    out_path = f'{BASE}/se_keyword_index.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n关键词索引已保存: {out_path}')
    print(f'  术语数: {len(keywords)}')
    print(f'  页面标注: {sum(len(v) for v in page_terms.values())} 处')
    print(f'  有定义: {sum(1 for k in keywords if k["definition"])}')
    print(f'  有视频: {sum(1 for k in keywords if k["videos"])}')

    print('\n=== Top 30 术语 ===')
    for k in keywords[:30]:
        def_info = '📖' if k['definition'] else '  '
        vid_info = '🎬' if k['videos'] else '  '
        print(f'  {def_info}{vid_info} {k["term"]:12s} 频次:{k["freq"]:3d} 章:{k["chapter"]}')

if __name__ == '__main__':
    main()
