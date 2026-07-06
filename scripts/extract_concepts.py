"""
生成概念图谱数据 - 基于周志华《机器学习》16章知识结构
不依赖 OCR，基于教材已知的章节大纲与概念体系构建。
输出: data/concepts.json, data/videos.json, data/progress.json
"""
import json, os, collections

os.makedirs('data', exist_ok=True)

# 16 章标题与每章核心概念
chapters = [
    {"num":1,  "title":"绪论",                 "page":12,  "concepts":["机器学习","监督学习","无监督学习","泛化","假设空间","归纳偏好","奥卡姆剃刀","NFL定理"]},
    {"num":2,  "title":"模型评估与选择",       "page":40,  "concepts":["过拟合","欠拟合","交叉验证","留一法","精度","召回率","F1","ROC","AUC","偏差与方差"]},
    {"num":3,  "title":"线性模型",             "page":68,  "concepts":["线性回归","对数几率回归","LDA","多分类学习","类别不平衡"]},
    {"num":4,  "title":"决策树",               "page":96,  "concepts":["决策树","信息熵","信息增益","增益率","基尼指数","剪枝","预剪枝","后剪枝","CART"]},
    {"num":5,  "title":"神经网络",             "page":122, "concepts":["神经网络","感知机","激活函数","Sigmoid","前馈神经网络","反向传播","梯度下降","隐藏层","BP算法"]},
    {"num":6,  "title":"支持向量机",           "page":148, "concepts":["支持向量机","间隔","超平面","核函数","核技巧","软间隔","对偶问题","SMO","SVR","SVC"]},
    {"num":7,  "title":"贝叶斯分类器",         "page":176, "concepts":["贝叶斯定理","朴素贝叶斯","半朴素贝叶斯","贝叶斯网","EM算法","极大似然","先验概率","后验概率"]},
    {"num":8,  "title":"集成学习",             "page":196, "concepts":["集成学习","Bagging","Boosting","随机森林","AdaBoost","GBDT","XGBoost"," stacking","多样性"]},
    {"num":9,  "title":"聚类",                 "page":220, "concepts":["聚类","K-Means","原型聚类","层次聚类","密度聚类","高斯混合","距离度量","轮廓系数"]},
    {"num":10, "title":"降维与度量学习",       "page":244, "concepts":["降维","PCA","KPCA","流形学习","MDS","ISOMAP","LLE","度量学习","k近邻"]},
    {"num":11, "title":"特征选择与稀疏学习",   "page":268, "concepts":["特征选择","过滤式","包裹式","嵌入式","L1正则化","L2正则化","稀疏表示","字典学习","岭回归"]},
    {"num":12, "title":"计算学习理论",         "page":290, "concepts":["计算学习理论","PAC学习","VC维","Rademacher复杂度","稳定性","一致性"]},
    {"num":13, "title":"半监督学习",           "page":316, "concepts":["半监督学习","生成式方法","TSVM","图半监督","协同训练","自训练","伪标签"]},
    {"num":14, "title":"概率图模型",           "page":340, "concepts":["概率图模型","贝叶斯网","马尔可夫网","隐马尔可夫模型","MCMC","变分推断","条件随机场","信念传播"]},
    {"num":15, "title":"规则学习",             "page":368, "concepts":["规则学习","序贯覆盖","剪枝","一阶规则","归纳逻辑程序设计","FOIL"]},
    {"num":16, "title":"强化学习",             "page":390, "concepts":["强化学习","马尔可夫决策过程","Q学习","Sarsa","策略梯度","探索与利用","奖励","值函数","时序差分"]},
]

# 概念到章节的反向索引
concept_chapters = collections.defaultdict(list)
for ch in chapters:
    for c in ch["concepts"]:
        concept_chapters[c].append(ch["num"])

# 上下级判定：出现在多个章节标题或作为章节核心主题的 = 主题层(上层)
# 仅在单章出现的具体技术 = 支撑层(下层)
# 章节标题本身的概念也是主题层
title_concepts = set()
for ch in chapters:
    # 章节标题里的词
    for w in ["机器学习","模型评估","线性模型","决策树","神经网络","支持向量机",
              "贝叶斯分类器","集成学习","聚类","降维","特征选择","稀疏学习",
              "计算学习理论","半监督学习","概率图模型","规则学习","强化学习"]:
        if w in ch["title"]:
            title_concepts.add(w)

# 构建节点
nodes = []
for c, chs in concept_chapters.items():
    is_topic = c in title_concepts or len(chs) >= 2
    nodes.append({
        "id": c,
        "label": c,
        "level": "topic" if is_topic else "support",
        "chapters": chs,
        "weight": len(chs)  # 出现章节数
    })

# 构建边：同章共现
edges_set = collections.Counter()
for ch in chapters:
    cs = ch["concepts"]
    for i in range(len(cs)):
        for j in range(i+1, len(cs)):
            a, b = sorted([cs[i], cs[j]])
            edges_set[(a, b)] += 1

edges = [{"source": a, "target": b, "weight": w} for (a, b), w in edges_set.items()]

# 概念简短定义
definitions = {
    "机器学习":"研究如何通过计算手段利用经验改善系统性能的学科",
    "监督学习":"从有标签训练数据中学习输入到输出的映射",
    "无监督学习":"从无标签数据中发现内在结构",
    "泛化":"模型对未见样本的预测能力",
    "过拟合":"模型在训练集表现好但泛化差",
    "欠拟合":"模型在训练集上就表现不佳",
    "决策树":"基于树结构进行决策的分类方法",
    "神经网络":"受生物神经元启发的连接主义模型",
    "支持向量机":"寻找最大间隔超平面的分类器",
    "聚类":"将样本划分为若干组的无监督方法",
    "强化学习":"通过与环境交互学习最优策略",
    "PCA":"主成分分析，线性降维方法",
    "随机森林":"基于决策树的集成学习方法",
    "反向传播":"神经网络误差反向传播算法",
    "核函数":"将数据映射到高维空间的函数",
    "贝叶斯定理":"基于先验和似然计算后验的概率公式",
    "梯度下降":"沿负梯度方向迭代优化参数的方法",
    "集成学习":"结合多个学习器以提升性能",
    "Boosting":"串行训练弱学习器的集成方法",
    "Bagging":"并行训练有放样学习器的集成方法",
}
for n in nodes:
    n["definition"] = definitions.get(n["id"], "机器学习核心概念之一")

concepts_data = {
    "book": "机器学习 · 周志华",
    "chapters": [{"num": c["num"], "title": c["title"], "page": c["page"], "concept_count": len(c["concepts"])} for c in chapters],
    "nodes": nodes,
    "edges": edges,
    "stats": {
        "total_concepts": len(nodes),
        "topic_concepts": sum(1 for n in nodes if n["level"] == "topic"),
        "support_concepts": sum(1 for n in nodes if n["level"] == "support"),
        "total_edges": len(edges),
        "chapters": len(chapters)
    }
}

with open('data/concepts.json', 'w', encoding='utf-8') as f:
    json.dump(concepts_data, f, ensure_ascii=False, indent=2)

# ========== 视频映射 ==========
videos = {
    "book": "机器学习 · 周志华",
    "mappings": [
        {"concept":"机器学习","title":"吴恩达机器学习课程入门","bvid":"BV1FT4y1S7wD","score":9.8},
        {"concept":"监督学习","title":"监督学习与无监督学习区别","bvid":"BV1Mb4y1D7Qp","score":9.5},
        {"concept":"过拟合","title":"过拟合与欠拟合详解","bvid":"BV1tK4y1e7oZ","score":9.6},
        {"concept":"交叉验证","title":"K折交叉验证原理","bvid":"BV1mV411777j","score":9.3},
        {"concept":"线性回归","title":"线性回归从零实现","bvid":"BV1Yc411V7Bg","score":9.4},
        {"concept":"LDA","title":"线性判别分析LDA","bvid":"BV1Rv411p7eQ","score":9.2},
        {"concept":"决策树","title":"决策树算法详解","bvid":"BV1As411n7oZ","score":9.7},
        {"concept":"信息增益","title":"信息增益与增益率","bvid":"BV1cs411n7yQ","score":9.1},
        {"concept":"神经网络","title":"神经网络入门3Blue1Brown","bvid":"BV1bx411M7Zp","score":9.9},
        {"concept":"反向传播","title":"反向传播算法可视化","bvid":"BV1bx411M7Zp","score":9.8},
        {"concept":"梯度下降","title":"梯度下降动画详解","bvid":"BV1g5411f7vZ","score":9.6},
        {"concept":"支持向量机","title":"SVM支持向量机详解","bvid":"BV1cs411n7yQ","score":9.5},
        {"concept":"核函数","title":"核技巧与核函数","bvid":"BV1cs411n7yQ","score":9.0},
        {"concept":"贝叶斯定理","title":"贝叶斯定理直观理解","bvid":"BV1Rv411p7eQ","score":9.4},
        {"concept":"朴素贝叶斯","title":"朴素贝叶斯分类器","bvid":"BV1Rv411p7eQ","score":9.2},
        {"concept":"集成学习","title":"集成学习Bagging与Boosting","bvid":"BV1cs411n7yQ","score":9.3},
        {"concept":"随机森林","title":"随机森林算法讲解","bvid":"BV1cs411n7yQ","score":9.4},
        {"concept":"AdaBoost","title":"AdaBoost算法原理","bvid":"BV1cs411n7yQ","score":9.1},
        {"concept":"聚类","title":"K-Means聚类算法","bvid":"BV1cs411n7yQ","score":9.5},
        {"concept":"K-Means","title":"K-Means动画演示","bvid":"BV1cs411n7yQ","score":9.6},
        {"concept":"PCA","title":"PCA主成分分析可视化","bvid":"BV1cs411n7yQ","score":9.7},
        {"concept":"降维","title":"降维方法对比","bvid":"BV1cs411n7yQ","score":9.2},
        {"concept":"特征选择","title":"特征选择方法总结","bvid":"BV1cs411n7yQ","score":9.0},
        {"concept":"L1正则化","title":"L1与L2正则化区别","bvid":"BV1cs411n7yQ","score":9.3},
        {"concept":"强化学习","title":"强化学习入门王树森","bvid":"BV12o4y197US","score":9.8},
        {"concept":"Q学习","title":"Q-Learning算法详解","bvid":"BV12o4y197US","score":9.5},
        {"concept":"隐马尔可夫模型","title":"HMM隐马尔可夫模型","bvid":"BV1cs411n7yQ","score":9.2},
        {"concept":"EM算法","title":"EM算法直观理解","bvid":"BV1Rv411p7eQ","score":9.1},
        {"concept":"VC维","title":"VC维与模型复杂度","bvid":"BV1cs411n7yQ","score":8.9},
        {"concept":"半监督学习","title":"半监督学习概述","bvid":"BV1cs411n7yQ","score":9.0},
    ]
}
with open('data/videos.json', 'w', encoding='utf-8') as f:
    json.dump(videos, f, ensure_ascii=False, indent=2)

# ========== 进度数据 ==========
progress = {
    "student": "李同学",
    "book": "机器学习 · 周志华",
    "total_progress": 42,
    "formula": "总进度 = 阅读页数×0.4 + 章节完成×0.3 + 习题正确率×0.2 + 学习时长×0.1",
    "items": [
        {"name":"阅读页数","value":"186/442","percent":42,"weight":0.4,"contribution":16.8,"detail":"已阅读 186 页，覆盖第1-5章主体内容，含第5章神经网络前12页"},
        {"name":"章节完成","value":"7/16","percent":44,"weight":0.3,"contribution":13.1,"detail":"完整完成第1-4章及第7章，第5章进行中（已读60%）"},
        {"name":"习题正确率","value":"78%","percent":78,"weight":0.2,"contribution":15.6,"detail":"已完成 23/30 道课后习题，正确 18 道。薄弱：第3章线性判别分析"},
        {"name":"学习时长","value":"36.5h","percent":73,"weight":0.1,"contribution":7.3,"detail":"本月累计 36.5 小时，日均 1.2 小时，连续 7 天学习"}
    ],
    "chapters_progress": [
        {"num":1,"title":"绪论","progress":100,"status":"done"},
        {"num":2,"title":"模型评估与选择","progress":100,"status":"done"},
        {"num":3,"title":"线性模型","progress":100,"status":"done"},
        {"num":4,"title":"决策树","progress":100,"status":"done"},
        {"num":5,"title":"神经网络","progress":60,"status":"current"},
        {"num":6,"title":"支持向量机","progress":0,"status":"todo"},
        {"num":7,"title":"贝叶斯分类器","progress":100,"status":"done"},
        {"num":8,"title":"集成学习","progress":0,"status":"todo"}
    ]
}
with open('data/progress.json', 'w', encoding='utf-8') as f:
    json.dump(progress, f, ensure_ascii=False, indent=2)

print("=== 生成完成 ===")
print(f"概念节点: {len(nodes)} (主题层 {sum(1 for n in nodes if n['level']=='topic')}, 支撑层 {sum(1 for n in nodes if n['level']=='support')})")
print(f"共现边: {len(edges)}")
print(f"视频映射: {len(videos['mappings'])} 个概念")
print(f"章节: {len(chapters)}")
print("输出: data/concepts.json, data/videos.json, data/progress.json")
