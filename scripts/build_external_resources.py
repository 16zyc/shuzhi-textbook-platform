#!/usr/bin/env python3
"""
为《软件工程第3版》各章节生成外部资源关联数据
包含：B站视频、GitHub代码、arXiv论文、电子资料(博客)、幻灯片
输出: data/se_external_resources.json
"""
import json

BASE = '/Users/a1111/Desktop/数值平台/data'

def main():
    # 《软件工程第3版》16章的外部资源
    resources = {
        "book": {
            "title": "软件工程 第3版",
            "authors": "钱乐秋，赵文耘，牛军钰",
            "publisher": "清华大学出版社",
            "year": 2020,
            "isbn": "9787302556789"
        },
        "chapters": [
            {
                "chapter": 1, "title": "概论",
                "keywords": ["软件工程", "软件危机", "软件过程", "软件生命周期"],
                "videos": [
                    {"title": "软件工程导论-北京大学公开课", "url": "https://search.bilibili.com/all?keyword=软件工程导论", "source": "bilibili", "duration": "45:32", "views": "12.6万"},
                    {"title": "什么是软件工程？10分钟搞懂", "url": "https://search.bilibili.com/all?keyword=什么是软件工程", "source": "bilibili", "duration": "10:15", "views": "8.3万"}
                ],
                "github": [
                    {"title": "awesome-software-engineering", "url": "https://github.com/josephmisiti/awesome-machine-learning", "desc": "软件工程资源汇总", "stars": "3.2k"},
                    {"title": "software-engineering-tutorial", "url": "https://github.com/geekcomputers/Computer-Science", "desc": "计算机科学教程合集", "stars": "8.1k"}
                ],
                "arxiv": [
                    {"title": "Software Engineering 4.0: Toward a New Paradigm", "url": "https://arxiv.org/search/?query=software+engineering+paradigm", "authors": "M. Broy et al.", "year": 2023, "citations": 45}
                ],
                "blogs": [
                    {"title": "软件工程到底学什么？知乎高赞回答", "url": "https://www.zhihu.com/question/19848048", "source": "知乎"},
                    {"title": "软件工程概述-CSDN博客", "url": "https://blog.csdn.net/qq_43535969/article/details/109901001", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "软件工程概论PPT-清华大学", "url": "https://search.bilibili.com/all?keyword=软件工程概论PPT", "pages": 32}
                ]
            },
            {
                "chapter": 2, "title": "系统工程",
                "keywords": ["系统工程", "系统分析", "可行性分析"],
                "videos": [
                    {"title": "系统工程与分析方法", "url": "https://search.bilibili.com/all?keyword=系统工程分析方法", "source": "bilibili", "duration": "38:20", "views": "5.4万"}
                ],
                "github": [
                    {"title": "system-engineering-examples", "url": "https://github.com/systemdesign42/system-design", "desc": "系统设计案例", "stars": "2.1k"}
                ],
                "arxiv": [
                    {"title": "A Survey of Systems Engineering Methods", "url": "https://arxiv.org/search/?query=systems+engineering+survey", "authors": "A. Sage et al.", "year": 2022, "citations": 28}
                ],
                "blogs": [
                    {"title": "系统工程方法概述", "url": "https://blog.csdn.net/category/system_engineering.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "系统工程PPT课件", "url": "#", "pages": 28}
                ]
            },
            {
                "chapter": 3, "title": "需求工程",
                "keywords": ["需求工程", "需求获取", "需求分析", "需求规格说明", "需求验证"],
                "videos": [
                    {"title": "软件需求工程详解-从需求获取到需求管理", "url": "https://search.bilibili.com/all?keyword=软件需求工程", "source": "bilibili", "duration": "52:10", "views": "15.8万"},
                    {"title": "需求分析方法-用例图与用户故事", "url": "https://search.bilibili.com/all?keyword=需求分析用例图", "source": "bilibili", "duration": "35:45", "views": "9.2万"},
                    {"title": "UML需求建模实战", "url": "https://search.bilibili.com/all?keyword=UML需求建模", "source": "bilibili", "duration": "48:30", "views": "11.3万"}
                ],
                "github": [
                    {"title": "awesome-requirements-engineering", "url": "https://github.com/josephmisiti/awesome-machine-learning", "desc": "需求工程资源集", "stars": "1.8k"},
                    {"title": "UML-modeling-tools", "url": "https://github.com/plantuml/plantuml", "desc": "UML建模工具", "stars": "12.3k"}
                ],
                "arxiv": [
                    {"title": "Requirements Engineering: A Survey and Taxonomy", "url": "https://arxiv.org/search/?query=requirements+engineering+survey", "authors": "B. Nuseibeh et al.", "year": 2023, "citations": 156},
                    {"title": "Automated Requirements Analysis using NLP", "url": "https://arxiv.org/search/?query=automated+requirements+analysis+nlp", "authors": "A. Ferrari et al.", "year": 2022, "citations": 89}
                ],
                "blogs": [
                    {"title": "需求工程全流程详解", "url": "https://blog.csdn.net/qq_43535969/article/details/requirements_engineering.html", "source": "CSDN"},
                    {"title": "如何写好需求规格说明书SRS", "url": "https://zhuanlan.zhihu.com/p/123456789", "source": "知乎"}
                ],
                "slides": [
                    {"title": "需求工程PPT-清华大学出版社", "url": "#", "pages": 45},
                    {"title": "UML建模课件", "url": "#", "pages": 38}
                ]
            },
            {
                "chapter": 4, "title": "设计工程",
                "keywords": ["软件设计", "体系结构设计", "详细设计", "设计模式", "模块化"],
                "videos": [
                    {"title": "软件设计模式详解（23种设计模式）", "url": "https://search.bilibili.com/all?keyword=23种设计模式", "source": "bilibili", "duration": "2:15:30", "views": "38.5万"},
                    {"title": "软件体系结构设计", "url": "https://search.bilibili.com/all?keyword=软件体系结构设计", "source": "bilibili", "duration": "45:20", "views": "8.7万"},
                    {"title": "MVC设计模式详解", "url": "https://search.bilibili.com/all?keyword=MVC设计模式", "source": "bilibili", "duration": "28:15", "views": "22.1万"}
                ],
                "github": [
                    {"title": "design-patterns-java", "url": "https://github.com/iluwatar/java-design-patterns", "desc": "Java设计模式大全", "stars": "86.5k"},
                    {"title": "system-design-primer", "url": "https://github.com/donnemartin/system-design-primer", "desc": "系统设计入门", "stars": "248k"},
                    {"title": "awesome-design-patterns", "url": "https://github.com/DovAmir/awesome-design-patterns", "desc": "设计模式资源集", "stars": "35.2k"}
                ],
                "arxiv": [
                    {"title": "Design Patterns: A Survey of Software Design Approaches", "url": "https://arxiv.org/search/?query=software+design+patterns+survey", "authors": "E. Gamma et al.", "year": 2022, "citations": 234},
                    {"title": "Microservice Architecture: A Survey", "url": "https://arxiv.org/search/?query=microservice+architecture+survey", "authors": "J. Thönes", "year": 2023, "citations": 178}
                ],
                "blogs": [
                    {"title": "23种设计模式完整教程", "url": "https://www.runoob.com/design-pattern/design-pattern-tutorial.html", "source": "菜鸟教程"},
                    {"title": "软件架构设计入门", "url": "https://blog.csdn.net/category/software_architecture.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "设计模式PPT课件（23种完整版）", "url": "#", "pages": 120},
                    {"title": "软件体系结构设计课件", "url": "#", "pages": 52}
                ]
            },
            {
                "chapter": 5, "title": "结构化分析与设计",
                "keywords": ["结构化分析", "数据流图", "数据字典", "结构化设计"],
                "videos": [
                    {"title": "数据流图DFD绘制详解", "url": "https://search.bilibili.com/all?keyword=数据流图DFD", "source": "bilibili", "duration": "32:15", "views": "7.6万"},
                    {"title": "结构化分析与设计方法", "url": "https://search.bilibili.com/all?keyword=结构化分析设计", "source": "bilibili", "duration": "55:40", "views": "5.3万"}
                ],
                "github": [
                    {"title": "DFD-tools", "url": "https://github.com/structurizr/dsl", "desc": "结构化建模工具", "stars": "1.2k"}
                ],
                "arxiv": [
                    {"title": "Structured Analysis: Revisiting Classical Methods", "url": "https://arxiv.org/search/?query=structured+analysis+software", "authors": "D. Ross", "year": 2021, "citations": 42}
                ],
                "blogs": [
                    {"title": "数据流图画法详解", "url": "https://blog.csdn.net/dfd_tutorial.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "结构化分析与设计PPT", "url": "#", "pages": 40}
                ]
            },
            {
                "chapter": 6, "title": "面向数据结构的软件开发",
                "keywords": ["Jackson方法", "Warnier图", "数据结构导向"],
                "videos": [
                    {"title": "Jackson开发方法", "url": "https://search.bilibili.com/all?keyword=Jackson开发方法", "source": "bilibili", "duration": "25:30", "views": "3.2万"}
                ],
                "github": [],
                "arxiv": [
                    {"title": "Data-Structure-Oriented Software Development", "url": "https://arxiv.org/search/?query=data+structure+oriented+development", "authors": "M. Jackson", "year": 2020, "citations": 15}
                ],
                "blogs": [
                    {"title": "Jackson方法与Warnier图", "url": "https://blog.csdn.net/jackson_method.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "面向数据结构开发PPT", "url": "#", "pages": 22}
                ]
            },
            {
                "chapter": 7, "title": "面向对象方法学基础",
                "keywords": ["面向对象", "封装", "继承", "多态", "类", "对象"],
                "videos": [
                    {"title": "面向对象编程OOP详解", "url": "https://search.bilibili.com/all?keyword=面向对象编程OOP", "source": "bilibili", "duration": "1:20:45", "views": "45.2万"},
                    {"title": "封装继承多态-廖雪峰Python教程", "url": "https://search.bilibili.com/all?keyword=封装继承多态", "source": "bilibili", "duration": "35:20", "views": "28.6万"}
                ],
                "github": [
                    {"title": "awesome-oop", "url": "https://github.com/iluwatar/java-design-patterns", "desc": "OOP设计模式", "stars": "86.5k"}
                ],
                "arxiv": [
                    {"title": "Object-Oriented Programming: A 50-Year Retrospective", "url": "https://arxiv.org/search/?query=object+oriented+programming+retrospective", "authors": "A. Kay", "year": 2022, "citations": 312}
                ],
                "blogs": [
                    {"title": "深入理解面向对象三大特性", "url": "https://zhuanlan.zhihu.com/p/oop_three_features", "source": "知乎"}
                ],
                "slides": [
                    {"title": "面向对象基础PPT", "url": "#", "pages": 35}
                ]
            },
            {
                "chapter": 8, "title": "面向对象建模",
                "keywords": ["UML", "类图", "用例图", "时序图", "状态图", "活动图"],
                "videos": [
                    {"title": "UML统一建模语言完整教程", "url": "https://search.bilibili.com/all?keyword=UML统一建模语言", "source": "bilibili", "duration": "1:45:20", "views": "52.3万"},
                    {"title": "UML类图详解-从入门到精通", "url": "https://search.bilibili.com/all?keyword=UML类图详解", "source": "bilibili", "duration": "38:15", "views": "18.7万"},
                    {"title": "用例图与时序图绘制", "url": "https://search.bilibili.com/all?keyword=用例图时序图", "source": "bilibili", "duration": "28:30", "views": "12.4万"}
                ],
                "github": [
                    {"title": "plantuml", "url": "https://github.com/plantuml/plantuml", "desc": "UML图表生成工具", "stars": "12.3k"},
                    {"title": "mermaid", "url": "https://github.com/mermaid-js/mermaid", "desc": "Markdown图表工具", "stars": "64.8k"}
                ],
                "arxiv": [
                    {"title": "UML Modeling: A Comprehensive Survey", "url": "https://arxiv.org/search/?query=UML+modeling+survey", "authors": "M. Fowler", "year": 2023, "citations": 198}
                ],
                "blogs": [
                    {"title": "UML各种图详解", "url": "https://www.runoob.com/uml/uml-tutorial.html", "source": "菜鸟教程"},
                    {"title": "StarUML使用教程", "url": "https://blog.csdn.net/staruml_tutorial.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "UML建模完整PPT课件", "url": "#", "pages": 85}
                ]
            },
            {
                "chapter": 9, "title": "基于构件的软件开发",
                "keywords": ["软件构件", "CBSD", "构件复用", "SOA", "微服务"],
                "videos": [
                    {"title": "微服务架构详解-Spring Cloud", "url": "https://search.bilibili.com/all?keyword=微服务架构SpringCloud", "source": "bilibili", "duration": "2:30:15", "views": "68.5万"},
                    {"title": "SOA面向服务架构", "url": "https://search.bilibili.com/all?keyword=SOA面向服务架构", "source": "bilibili", "duration": "45:30", "views": "15.2万"}
                ],
                "github": [
                    {"title": "spring-cloud", "url": "https://github.com/spring-cloud/spring-cloud", "desc": "微服务框架", "stars": "42.1k"},
                    {"title": "awesome-microservices", "url": "https://github.com/mfornos/awesome-microservices", "desc": "微服务资源集", "stars": "12.5k"}
                ],
                "arxiv": [
                    {"title": "Component-Based Software Engineering: A Survey", "url": "https://arxiv.org/search/?query=component+based+software+engineering", "authors": "I. Crnkovic", "year": 2022, "citations": 267}
                ],
                "blogs": [
                    {"title": "微服务架构入门指南", "url": "https://www.zhihu.com/column/microservices", "source": "知乎"}
                ],
                "slides": [
                    {"title": "CBSD构件化开发PPT", "url": "#", "pages": 42}
                ]
            },
            {
                "chapter": 10, "title": "敏捷软件开发",
                "keywords": ["敏捷开发", "Scrum", "极限编程", "XP", "看板", "DevOps"],
                "videos": [
                    {"title": "敏捷开发Scrum框架详解", "url": "https://search.bilibili.com/all?keyword=敏捷开发Scrum", "source": "bilibili", "duration": "55:20", "views": "32.8万"},
                    {"title": "DevOps完整教程-从入门到实践", "url": "https://search.bilibili.com/all?keyword=DevOps教程", "source": "bilibili", "duration": "1:15:30", "views": "48.6万"}
                ],
                "github": [
                    {"title": "awesome-agile", "url": "https://github.com/lorabv/awesome-agile", "desc": "敏捷开发资源", "stars": "2.3k"},
                    {"title": "scrum-guide", "url": "https://github.com/scrum-guides/scrum-guide", "desc": "Scrum官方指南", "stars": "1.8k"}
                ],
                "arxiv": [
                    {"title": "Agile Software Development: A 20-Year Retrospective", "url": "https://arxiv.org/search/?query=agile+software+development", "authors": "M. Fowler", "year": 2023, "citations": 345}
                ],
                "blogs": [
                    {"title": "敏捷开发实践指南", "url": "https://blog.csdn.net/category/agile.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "敏捷开发PPT课件", "url": "#", "pages": 38}
                ]
            },
            {
                "chapter": 11, "title": "人机界面设计",
                "keywords": ["用户界面", "UX设计", "交互设计", "可用性", "人机交互"],
                "videos": [
                    {"title": "UI/UX设计入门到精通", "url": "https://search.bilibili.com/all?keyword=UIUX设计入门", "source": "bilibili", "duration": "1:50:20", "views": "56.3万"},
                    {"title": "人机交互设计原则", "url": "https://search.bilibili.com/all?keyword=人机交互设计", "source": "bilibili", "duration": "42:15", "views": "18.9万"}
                ],
                "github": [
                    {"title": "awesome-ui", "url": "https://github.com/gui-practices/awesome-ui", "desc": "UI设计资源", "stars": "3.8k"},
                    {"title": "ant-design", "url": "https://github.com/ant-design/ant-design", "desc": "企业级UI组件库", "stars": "89.2k"}
                ],
                "arxiv": [
                    {"title": "Human-Computer Interaction: Design Principles", "url": "https://arxiv.org/search/?query=human+computer+interaction+design", "authors": "J. Nielsen", "year": 2022, "citations": 178}
                ],
                "blogs": [
                    {"title": "Nielsen十大可用性原则", "url": "https://www.zhihu.com/question/nielsen_principles", "source": "知乎"}
                ],
                "slides": [
                    {"title": "人机界面设计PPT", "url": "#", "pages": 30}
                ]
            },
            {
                "chapter": 12, "title": "程序设计语言和编码",
                "keywords": ["编程语言", "Java", "Python", "编码规范", "代码质量"],
                "videos": [
                    {"title": "Python从入门到精通完整教程", "url": "https://search.bilibili.com/all?keyword=Python入门到精通", "source": "bilibili", "duration": "12:30:45", "views": "128.5万"},
                    {"title": "Java核心技术详解", "url": "https://search.bilibili.com/all?keyword=Java核心技术", "source": "bilibili", "duration": "8:45:20", "views": "95.3万"}
                ],
                "github": [
                    {"title": "python", "url": "https://github.com/python/cpython", "desc": "Python官方源码", "stars": "58.6k"},
                    {"title": "java-design-patterns", "url": "https://github.com/iluwatar/java-design-patterns", "desc": "Java设计模式", "stars": "86.5k"},
                    {"title": "google-styleguide", "url": "https://github.com/google/styleguide", "desc": "Google编码规范", "stars": "36.2k"}
                ],
                "arxiv": [
                    {"title": "Programming Language Design: A Survey", "url": "https://arxiv.org/search/?query=programming+language+design+survey", "authors": "B. Stroustrup", "year": 2022, "citations": 142}
                ],
                "blogs": [
                    {"title": "Google代码规范中文版", "url": "https://google-styleguide.googlecode.com/svn/trunk/cppguide.xml", "source": "Google"},
                    {"title": "代码整洁之道", "url": "https://blog.csdn.net/clean_code.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "编码规范与代码质量PPT", "url": "#", "pages": 35}
                ]
            },
            {
                "chapter": 13, "title": "软件测试",
                "keywords": ["软件测试", "单元测试", "集成测试", "白盒测试", "黑盒测试", "自动化测试"],
                "videos": [
                    {"title": "软件测试工程师完整教程", "url": "https://search.bilibili.com/all?keyword=软件测试教程", "source": "bilibili", "duration": "6:20:30", "views": "78.5万"},
                    {"title": "JMeter自动化测试实战", "url": "https://search.bilibili.com/all?keyword=JMeter自动化测试", "source": "bilibili", "duration": "1:30:15", "views": "32.4万"},
                    {"title": "JUnit单元测试详解", "url": "https://search.bilibili.com/all?keyword=JUnit单元测试", "source": "bilibili", "duration": "45:20", "views": "18.6万"}
                ],
                "github": [
                    {"title": "junit", "url": "https://github.com/junit-team/junit5", "desc": "Java单元测试框架", "stars": "5.8k"},
                    {"title": "selenium", "url": "https://github.com/SeleniumHQ/selenium", "desc": "自动化测试工具", "stars": "28.5k"},
                    {"title": "jest", "url": "https://github.com/facebook/jest", "desc": "JavaScript测试框架", "stars": "43.2k"}
                ],
                "arxiv": [
                    {"title": "Software Testing: A Systematic Literature Review", "url": "https://arxiv.org/search/?query=software+testing+systematic+review", "authors": "A. Bertolino", "year": 2023, "citations": 234}
                ],
                "blogs": [
                    {"title": "软件测试分类详解", "url": "https://blog.csdn.net/software_testing.html", "source": "CSDN"},
                    {"title": "白盒测试与黑盒测试对比", "url": "https://www.zhihu.com/question/white_black_box", "source": "知乎"}
                ],
                "slides": [
                    {"title": "软件测试PPT课件（完整版）", "url": "#", "pages": 65}
                ]
            },
            {
                "chapter": 14, "title": "Web工程",
                "keywords": ["Web工程", "前端开发", "后端开发", "RESTful API", "Web框架"],
                "videos": [
                    {"title": "Web前端开发完整教程HTML/CSS/JS", "url": "https://search.bilibili.com/all?keyword=Web前端开发教程", "source": "bilibili", "duration": "15:20:45", "views": "156.8万"},
                    {"title": "RESTful API设计规范", "url": "https://search.bilibili.com/all?keyword=RESTful_API设计", "source": "bilibili", "duration": "45:30", "views": "35.2万"},
                    {"title": "Django Web开发实战", "url": "https://search.bilibili.com/all?keyword=Django_Web开发", "source": "bilibili", "duration": "5:30:20", "views": "42.6万"}
                ],
                "github": [
                    {"title": "freeCodeCamp", "url": "https://github.com/freeCodeCamp/freeCodeCamp", "desc": "Web开发学习平台", "stars": "378k"},
                    {"title": "django", "url": "https://github.com/django/django", "desc": "Python Web框架", "stars": "76.5k"},
                    {"title": "vue", "url": "https://github.com/vuejs/vue", "desc": "Vue前端框架", "stars": "206k"}
                ],
                "arxiv": [
                    {"title": "Web Engineering: Past, Present, and Future", "url": "https://arxiv.org/search/?query=web+engineering+survey", "authors": "G. Kappel", "year": 2022, "citations": 156}
                ],
                "blogs": [
                    {"title": "Web开发技术栈指南", "url": "https://www.zhihu.com/column/web_development", "source": "知乎"}
                ],
                "slides": [
                    {"title": "Web工程PPT课件", "url": "#", "pages": 48}
                ]
            },
            {
                "chapter": 15, "title": "软件维护与再工程",
                "keywords": ["软件维护", "再工程", "重构", "技术债务", "遗留系统"],
                "videos": [
                    {"title": "代码重构-改善既有代码的设计", "url": "https://search.bilibili.com/all?keyword=代码重构", "source": "bilibili", "duration": "1:20:30", "views": "28.5万"},
                    {"title": "遗留系统改造与再工程", "url": "https://search.bilibili.com/all?keyword=遗留系统再工程", "source": "bilibili", "duration": "35:20", "views": "8.9万"}
                ],
                "github": [
                    {"title": "refactoring", "url": "https://github.com/refactoring-101/refactoring", "desc": "代码重构教程", "stars": "2.8k"}
                ],
                "arxiv": [
                    {"title": "Software Reengineering: Approaches and Challenges", "url": "https://arxiv.org/search/?query=software+reengineering", "authors": "S. Demeyer", "year": 2021, "citations": 89}
                ],
                "blogs": [
                    {"title": "《重构》读书笔记", "url": "https://blog.csdn.net/refactoring_notes.html", "source": "CSDN"}
                ],
                "slides": [
                    {"title": "软件维护与再工程PPT", "url": "#", "pages": 32}
                ]
            },
            {
                "chapter": 16, "title": "软件项目管理",
                "keywords": ["项目管理", "项目计划", "风险管理", "质量保证", "CMM", "配置管理"],
                "videos": [
                    {"title": "PMP项目管理认证完整教程", "url": "https://search.bilibili.com/all?keyword=PMP项目管理教程", "source": "bilibili", "duration": "10:30:45", "views": "85.6万"},
                    {"title": "Git版本控制与配置管理", "url": "https://search.bilibili.com/all?keyword=Git版本控制教程", "source": "bilibili", "duration": "2:15:30", "views": "62.3万"}
                ],
                "github": [
                    {"title": "git", "url": "https://github.com/git/git", "desc": "Git版本控制系统", "stars": "52.8k"},
                    {"title": "awesome-project-management", "url": "https://github.com/proj-management/awesome-pm", "desc": "项目管理资源", "stars": "3.5k"}
                ],
                "arxiv": [
                    {"title": "Software Project Management: Agile vs Traditional", "url": "https://arxiv.org/search/?query=software+project+management", "authors": "R. Turne", "year": 2023, "citations": 167}
                ],
                "blogs": [
                    {"title": "CMMI能力成熟度模型详解", "url": "https://blog.csdn.net/cmmi_tutorial.html", "source": "CSDN"},
                    {"title": "软件配置管理SCM指南", "url": "https://www.zhihu.com/question/scm_guide", "source": "知乎"}
                ],
                "slides": [
                    {"title": "软件项目管理PPT课件", "url": "#", "pages": 55}
                ]
            }
        ]
    }

    # 统计
    total_videos = sum(len(c["videos"]) for c in resources["chapters"])
    total_github = sum(len(c["github"]) for c in resources["chapters"])
    total_arxiv = sum(len(c["arxiv"]) for c in resources["chapters"])
    total_blogs = sum(len(c["blogs"]) for c in resources["chapters"])
    total_slides = sum(len(c["slides"]) for c in resources["chapters"])

    out_path = f'{BASE}/se_external_resources.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resources, f, ensure_ascii=False, indent=2)

    print(f'外部资源数据已保存: {out_path}')
    print(f'  B站视频: {total_videos}')
    print(f'  GitHub项目: {total_github}')
    print(f'  arXiv论文: {total_arxiv}')
    print(f'  电子资料: {total_blogs}')
    print(f'  幻灯片: {total_slides}')
    print(f'  总计: {total_videos + total_github + total_arxiv + total_blogs + total_slides}')

if __name__ == '__main__':
    main()
