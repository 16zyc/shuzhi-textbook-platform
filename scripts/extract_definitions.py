#!/usr/bin/env python3
"""
从OCR全文自动提取概念定义，扩充引经据典库
模式：XXX是指/XXX是/XXX（XXX）/所谓XXX/XXX定义为
输出: data/se_definitions.json
"""
import json, re, os
from collections import defaultdict

BASE = '/Users/a1111/Desktop/数值平台/data'

def main():
    print('=== 提取概念定义 ===')
    with open(f'{BASE}/se_fulltext.json','r',encoding='utf-8') as f:
        fulltext = json.load(f)
    with open(f'{BASE}/se_knowledge.json','r',encoding='utf-8') as f:
        knowledge = json.load(f)

    # 专业术语列表（作为定义提取的目标）
    TERMS = [
        '软件工程','软件危机','软件过程','软件生命周期','软件生存周期',
        '需求工程','需求获取','需求分析','需求规约','需求验证','需求管理','需求规格说明书',
        '软件设计','体系结构','详细设计','概要设计','设计模式','模块化','内聚','耦合',
        '结构化分析','结构化设计','结构化程序设计','数据流图','数据字典',
        '面向对象','封装','继承','多态','类','对象','消息','方法',
        '统一建模语言','UML','类图','用例图','时序图','状态图','活动图',
        '软件构件','构件复用','软件复用','面向服务架构','微服务',
        '敏捷开发','Scrum','极限编程','看板','持续集成',
        '人机界面','用户界面','交互设计','可用性','用户体验',
        '程序设计语言','编码规范','代码审查','重构',
        '软件测试','单元测试','集成测试','系统测试','验收测试','白盒测试','黑盒测试','回归测试','测试用例',
        'Web工程','前端开发','后端开发',
        '软件维护','再工程','逆向工程','技术债务','遗留系统',
        '软件项目管理','项目计划','风险管理','质量保证','配置管理','基线',
        '瀑布模型','增量模型','螺旋模型','原型模型','喷泉模型',
        '软件质量','软件可靠性','软件可维护性','软件可移植性',
        '版本控制','软件度量','软件文档',
        '数据结构','算法','数据库',
        '客户端','服务器',
        '验证','确认','评审','审计',
    ]

    # 定义提取模式
    PATTERNS = [
        # "所谓XXX，是指/是..."
        re.compile(r'所谓(.{2,15}?)[，,。]?是指(.{15,120}?)[。；]'),
        re.compile(r'所谓(.{2,15}?)[，,。]?是(.{15,120}?)[。；]'),
        # "XXX是指..."
        re.compile(r'(软件工程|需求工程|软件设计|结构化分析|面向对象|软件测试|软件维护|软件项目管理|软件构件|软件复用|软件过程|软件危机|软件生命周期|需求分析|需求获取|需求规约|需求验证|需求管理|体系结构|详细设计|概要设计|设计模式|模块化|内聚|耦合|结构化设计|结构化程序设计|数据流图|数据字典|封装|继承|多态|统一建模语言|UML|类图|用例图|时序图|状态图|活动图|面向服务架构|微服务|敏捷开发|Scrum|极限编程|看板|持续集成|人机界面|用户界面|交互设计|可用性|用户体验|程序设计语言|编码规范|代码审查|重构|单元测试|集成测试|系统测试|验收测试|白盒测试|黑盒测试|回归测试|测试用例|Web工程|软件维护|再工程|逆向工程|技术债务|遗留系统|软件项目管理|项目计划|风险管理|质量保证|配置管理|基线|瀑布模型|增量模型|螺旋模型|原型模型|喷泉模型|软件质量|软件可靠性|软件可维护性|软件可移植性|版本控制|软件度量|软件文档|验证|确认|评审|审计)[，,]?\s*是指(.{15,120}?)[。；]'),
        # "XXX是..."
        re.compile(r'(软件工程|需求工程|软件设计|结构化分析|面向对象|软件测试|软件维护|软件项目管理|软件构件|软件复用|软件过程|软件危机|软件生命周期|需求分析|体系结构|设计模式|模块化|内聚|耦合|封装|继承|多态|统一建模语言|UML|敏捷开发|极限编程|人机界面|可用性|用户体验|重构|单元测试|集成测试|白盒测试|黑盒测试|回归测试|再工程|逆向工程|技术债务|遗留系统|软件项目管理|风险管理|质量保证|配置管理|基线|瀑布模型|螺旋模型|软件质量|软件可靠性|软件可维护性|版本控制|软件度量)[，,]?\s*是(?:指)?(.{20,120}?)[。；]'),
        # "XXX：..."（定义列表形式）
        re.compile(r'(软件工程|需求工程|软件设计|结构化分析|面向对象|软件测试|软件维护|软件项目管理|软件构件|软件复用|软件过程|需求分析|体系结构|设计模式|模块化|内聚|耦合|封装|继承|多态|UML|敏捷开发|极限编程|人机界面|可用性|单元测试|集成测试|白盒测试|黑盒测试|再工程|逆向工程|风险管理|质量保证|配置管理|基线|瀑布模型|螺旋模型|软件质量|软件可靠性|版本控制|软件度量)[：:]\s*(.{20,120}?)[。；\n]'),
    ]

    definitions = []
    seen_terms = set()

    for page_data in fulltext['pages']:
        page = page_data['page']
        text = page_data['text']
        if not text or len(text) < 20:
            continue

        # 找到所属章节
        ch = None
        for c in knowledge['chapters']:
            if c['page_start'] <= page <= c['page_end']:
                ch = c['num']
                break

        for pattern in PATTERNS:
            for match in pattern.finditer(text):
                term = match.group(1).strip()
                definition = match.group(2).strip() if match.lastindex >= 2 else ''

                # 清理
                term = re.sub(r'[，,。；：:、\s]+$', '', term)
                definition = re.sub(r'^[，,。；：:、\s]+', '', definition)

                # 过滤
                if len(term) < 2 or len(definition) < 15:
                    continue
                # 只要专业术语
                if term not in TERMS and not any(t in term for t in TERMS):
                    continue
                # 去重：同一术语只保留第一个定义
                if term in seen_terms:
                    continue

                # 提取上下文
                pos = match.start()
                ctx_start = max(0, pos - 10)
                ctx_end = min(len(text), pos + len(match.group(0)) + 10)
                context = text[ctx_start:ctx_end].replace('\n', ' ')

                definitions.append({
                    'term': term,
                    'definition': definition,
                    'page': page,
                    'chapter': ch or 0,
                    'context': context,
                    'source': '《软件工程第3版》'
                })
                seen_terms.add(term)

    # 按章节排序
    definitions.sort(key=lambda d: (d['chapter'], d['page']))

    output = {
        'total': len(definitions),
        'definitions': definitions,
        'by_chapter': {}
    }
    for d in definitions:
        output['by_chapter'].setdefault(str(d['chapter']), []).append(d['term'])

    out_path = f'{BASE}/se_definitions.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'定义提取完成: {out_path}')
    print(f'  总定义数: {len(definitions)}')
    print(f'  覆盖术语: {len(seen_terms)}')
    print(f'\n各章定义数:')
    for ch in sorted(output['by_chapter'].keys()):
        if ch != '0':
            c = next(c for c in knowledge['chapters'] if c['num'] == int(ch))
            terms = output['by_chapter'][ch]
            print(f'  第{ch}章 {c["title"]}: {len(terms)}个定义')
            print(f'    术语: {", ".join(terms[:8])}{"..." if len(terms)>8 else ""}')

if __name__ == '__main__':
    main()
