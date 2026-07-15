# 数智教材平台：可溯源教材阅读工作台设计

## 1. 目标

第一阶段以《软件工程第3版》第1章为真实纵向样板，交付一个面向高校教师的教材阅读与备课工作台。教师应能在原版教材页面上点击核心概念或插图，查看可信证据与精选外部资源，并把素材加入备课篮。

核心闭环：选教材 -> 读原文 -> 点概念或图 -> 核验证据与资源 -> 加入备课篮 -> 为后续教案与 PPT 生成提供结构化输入。

## 2. 产品边界

### 第一阶段包含

- 原版页面、章节树、翻页、缩放、章节内搜索和页码跳转。
- 与页面缩放同步的文字和插图坐标层。
- 概念、插图和图注的点击关联。
- 三级证据链及原文回跳定位。
- 经校验的 B站、GitHub、arXiv 等精选资源。
- 可持久化的个人备课篮。
- 第1章数据质量报告。

### 第一阶段不包含

- 多角色、学校后台、权限和多人协作。
- 全书级开放问答和复杂模型服务。
- 最终教案/PPT生成质量优化。
- 教材上传、任务队列和资源审核后台的完整产品化。

## 3. 信息架构

全站保留五个一级模块：

1. 工作台：最近教材、备课进度、待完善引用和最近成果。
2. 教材阅读：左侧章节树、中间原版页面、右侧证据与资源。
3. 备课篮：概念、原句、插图、论文、视频和代码素材。
4. 生成中心：后续根据备课篮生成并编辑教案和 PPT。
5. 资源库：已审核资源及其校验状态和关联理由。

第一阶段实现教材阅读和备课篮主闭环，其余模块保留清晰入口但不伪装成完整能力。

## 4. 阅读工作区

### 4.1 布局

- 左栏约 264px：章节树、阅读进度、章节搜索、定义和插图数量。
- 中栏为主区域：深灰蓝工作台承载原版教材页和透明坐标层。
- 右栏约 380px：第一阶段仅启用证据和资源；关系、问答入口标记为后续能力且不纳入验收。
- 底部为备课篮状态条：已选素材数和进入备课篮操作。

在窄屏下，目录和右侧面板改为抽屉，不压缩教材页到不可读宽度。

### 4.2 交互

- 关键词默认显示轻量虚线，不大面积涂色破坏阅读。
- 悬停显示概念类型，点击形成选中态并打开对应证据卡。
- 插图区域悬停显示边框和“查看图解”，图片与图注绑定到同一实体。
- 右侧资源点击后新窗口打开；原文出处点击后定位到对应页和坐标。
- “加入备课篮”是证据卡的稳定主操作，加入后提供明确反馈。

## 5. 数据模型

### 5.1 页面身份与标注

`page_id` 是不可变主键，格式为 `<source_sha256>:<scan_index>`。`scan_index` 是从 1 开始的 PDF/扫描页序号，`printed_label` 是书页上印刷的页码字符串，两者不得混用。章节范围使用 `page_id` 或 `scan_index`，用户引用同时显示书名、印刷页码和扫描页序号。

```json
{
  "schema_version": 1,
  "page_id": "abc123:15",
  "source_sha256": "abc123",
  "scan_index": 15,
  "printed_label": "2",
  "image": "images/se/p015_0.jpeg",
  "width": 2000,
  "height": 2984,
  "text_blocks": [
    {
      "block_id": "p15-b42",
      "text": "软件工程是...",
      "bbox": [0.18, 0.31, 0.60, 0.025],
      "char_boxes": [[0, [0.18, 0.31, 0.03, 0.025]]],
      "confidence": 0.97
    }
  ],
  "occurrences": [
    {
      "occurrence_id": "occ:software-engineering:p15:1",
      "concept_id": "concept:software-engineering",
      "text": "软件工程",
      "spans": [{"block_id": "p15-b42", "start": 0, "end": 4}],
      "boxes": [[0.18, 0.31, 0.12, 0.025]],
      "confidence": 0.97,
      "review_status": "reviewed"
    }
  ]
}
```

`bbox` 和 `boxes` 使用相对页面宽高的 `[x, y, width, height]`。`char_boxes` 为 `[原始 Unicode code point index, box]`。一个概念出现项可包含多个 `span` 和多个框，以支持同行多概念与跨行概念。每个 `span` 显式引用一个 `block_id`；`start` 为包含、`end` 为不包含的 Unicode code point 索引。索引基于 OCR 原始 NFC 文本。匹配器生成 `normalized_text` 时必须同时生成 `normalized_to_original[]`，将每个规范化字符索引映射回原始 code point 索引；只允许 Unicode NFC、连续 ASCII 空白折叠和全半角标点统一。`spans` 与 `boxes` 按阅读顺序一一对应。渲染坐标为 `render_x = content_left + x * rendered_width`、`render_y = content_top + y * rendered_height`，宽高同理；旋转页面必须先按页面旋转矩阵转换，再应用缩放。

### 5.2 核心接口 schema

所有文件包含整数 `schema_version`。ID 在同一教材版本内唯一，内容更新不改变实体 ID；来源发生变化时创建新版本。相同规范化 URL 或相同书目 DOI/ISBN 视为重复资源。

- `figure`：`figure_id`、`page_id`、`image_boxes[]`、`caption_boxes[]`、`caption_text`、`concept_ids[]`、`confidence`、`review_status`。
- `concept`：`concept_id`、`canonical_name`、`aliases[]`、`english_names[]`、`description`、`ambiguity_group`、`review_status`。
- `evidence`：`evidence_id`、`concept_id`、`tier`、`source_kind`、`quote`、`target_occurrence_id`、`target_boxes[]`、`external_locator`、`url`、`relation_reason`、`review_status`、`reviewed_at`。一级证据必须设置 `target_occurrence_id`；外部证据使用结构化 `external_locator`（页码、章节、DOI、ISBN 中适用的字段）。
- `resource`：`resource_id`、`concept_ids[]`、`platform`、`title`、`authors[]`、`url`、`relation_reason`、`verification_status`、`verified_at`、`http_status`、`verification_method`、`verified_by`、`verification_note`、`manual_confirmation`。`manual_confirmation` 为 `{confirmed: boolean, reviewer_id: string, confirmed_at: ISO-8601, target_title: string, final_url: string}` 或 `null`。
- `relationship`：`relationship_id`、`source_concept_id`、`target_concept_id`、`relation_type`、`evidence_ids[]`、`review_status`。
- `basket_item`：`basket_item_id`、`book_version_id`、`item_type`、`entity_id`、`note`、`created_at`、`sort_order`。

审核枚举统一为 `unreviewed | needs_review | reviewed | rejected`；资源校验枚举为 `unchecked | reachable | redirected | auth_required | unavailable`。第一阶段只有 `reviewed` 证据和 `reachable`/已人工确认可用的 `auth_required` 资源可显示“已核验”。

插图无法可靠绑定图注时进入 `needs_review`，不展示强关联结论。备课篮第一阶段以 `book_version_id` 分区存入浏览器 `localStorage`，单浏览器单用户持久化；schema 升级必须迁移或安全忽略旧数据。

### 5.3 概念

概念使用稳定 `concept_id`。页面命中、图谱节点、外部资源和备课素材均引用该 ID，不以显示文本作为主键。

### 5.4 证据

- 一级证据：当前教材原文、页码、原句、坐标和 OCR 置信度。
- 二级证据：权威百科、行业标准、经典教材等权威定义。
- 三级证据：论文、视频、代码和优质开放资料。

一级证据是概念在当前教材中的原文依据，二级证据是外部权威定义，三级证据是支持教学拓展的学术或工程内容。资源是三级证据的展示载体；同一记录可同时拥有 `evidence_id` 和 `resource_id`，但引用关系必须明确。

每个纳入第一章金标清单的核心概念必须至少有一条一级证据。二级和三级证据按适用性配置，不强制每个概念凑齐三级；缺失层级明确显示“暂无已核验来源”。只有维护者人工核对标题、目标页面和关联理由后，记录才能标记为 `reviewed`。

## 6. 数据处理流水线

1. 将 PDF 渲染为稳定尺寸的页面图片。
2. 识别带坐标的文本行、阅读顺序和置信度。
3. 分类标题、正文、页眉页脚、公式、图片和图注。
4. 将术语、同义词和缩写对齐到 `concept_id`。
5. 检测插图区域并绑定最近且编号匹配的图注。
6. 组装三级证据链和外部资源。
7. 输出覆盖率、准确率、歧义项、低置信项和失效链接报告。

所有处理结果记录输入文件摘要、引擎版本、执行时间和人工修订状态，支持重复执行和问题追踪。

## 7. 外部资源质量

第一阶段资源以“少而可信”为原则。每条展示资源必须满足：

- 链接直接指向目标内容，而不是泛搜索结果或 `#` 占位。
- 标题、作者/仓库、平台数据与目标页面一致。
- 明确记录与章节或概念的匹配理由。
- 记录最后校验时间和校验结果。
- 失效或相关性不足时从用户界面下线并进入待审核列表。

自动校验使用 HTTP HEAD，服务不支持时回退 GET；允许最多 5 次重定向，连接与读取总超时 10 秒。B站等需要登录或反爬的平台允许标记 `auth_required`，但必须由维护者在登录浏览器中人工打开确认，并完整写入 `manual_confirmation`。机器判定人工确认有效的谓词为：`confirmed == true`、`reviewer_id` 非空、`confirmed_at` 距校验时不超过 30 天、`target_title` 非空，且 `final_url` 与资源 URL 规范化后的站点和内容路径一致。`verified_at` 超过 30 天的资源不显示“近期已核验”。

## 7.1 第一章完整性清单

第一章范围固定为当前源文件 `scan_index` 14-39，共 26 页；目录单元为 1.1、1.2、1.3、1.4、1.5 和习题。实现前生成并提交 `data/chapter-1-gold.json`，由维护者确认以下清单后冻结版本：

- 26 页页面身份、印刷页码和章节归属。
- 每页正文区域与排除的页眉页脚区域。
- 全部编号插图/表格及图注；无编号但具有教学意义的插图单独标记。
- 核心概念清单，至少覆盖现有定义“软件危机、软件工程、软件过程、软件生命周期”，并覆盖各目录单元的主概念。
- 每个核心概念至少一条一级证据；全章至少 2 条二级权威证据，以及 B站、GitHub、arXiv 各至少 1 条经核验且确实相关的三级资源。

未进入冻结清单的自动识别结果可作为候选项展示为“待核验”，但不得计入完成指标。

金标文件 schema 固定为：

```json
{
  "schema_version": 1,
  "gold_version": "chapter-1-v1",
  "source_sha256": "abc123",
  "pages": [{
    "page_id": "abc123:14",
    "scan_index": 14,
    "printed_label": "1",
    "section_ids": ["section:1.1"],
    "body_regions": [[0.1, 0.08, 0.8, 0.84]],
    "excluded_regions": [],
    "gold_text_nfc": "...",
    "gold_char_boxes": [[0, [0.1, 0.1, 0.01, 0.02]]]
  }],
  "concepts": [{"concept_id": "concept:software-crisis", "required": true, "canonical_occurrence_id": "gold:occ:1"}],
  "occurrences": [{
    "occurrence_id": "gold:occ:1",
    "concept_id": "concept:software-crisis",
    "page_id": "abc123:14",
    "text_nfc": "软件危机",
    "boxes": [[0.2, 0.3, 0.1, 0.02]],
    "expected_evidence_id": "evidence:software-crisis:primary"
  }],
  "figures": [{"figure_id": "figure:1-1", "page_id": "abc123:20", "classification": "numbered", "figure_number": "图1-1", "boxes": [], "caption_text_nfc": "...", "concept_ids": []}],
  "resources": [{"resource_id": "resource:example", "required_platform": "arxiv"}]
}
```

`classification` 只能是 `numbered | unnumbered_teaching`。`gold_char_boxes` 中每项为 `[Unicode code point index, box]`，只记录正文金标字符。证据回跳的期望目标由每个概念的 `canonical_occurrence_id` 指向的金标出现项和 `expected_evidence_id` 唯一确定。

## 8. 状态与降级

- 坐标缺失：仍展示原版页面，并提示本页关联待完善。
- OCR 低置信：标记为待核验，不作为已核验定义自动引用。
- 概念歧义：要求教师选择概念含义，不自动绑定。
- 外链失效：不展示虚假数据，保留内部审核记录。
- 一级证据缺失：该概念不得标记为“已核验”。
- 问答和生成入口第一阶段显示为“后续开放”，不提供伪交互。

## 9. 视觉系统

定位为“学术工作台 + 精密工具感”。使用墨蓝、纸白和青绿色作为基础色，琥珀色仅表示引文与证据。背景可使用克制的纸张纹理或细网格。标题字体强调书卷感，正文使用高可读现代黑体，页码和引用编号使用等宽数字。

不使用 Emoji 作为结构性图标，统一采用同一套线性 SVG 图标。交互动效只表达状态变化，时长 150-280ms，并支持 `prefers-reduced-motion`。

## 10. 前端边界

核心组件：

- `AppShell`：全局导航和布局。
- `BookNavigator`：章节、搜索和页码状态。
- `PageCanvas`：页面图片、缩放和预取。
- `AnnotationLayer`：概念和插图坐标层。
- `EvidencePanel`：三级证据、资源和回跳操作。
- `PrepBasket`：素材收集、持久化和状态条。

组件通过明确数据接口通信，不直接读取彼此 DOM。现有 JSON 先作为只读数据源，后续替换 API 时保持 schema 稳定。

## 11. 验收标准

第1章必须满足。所有指标使用冻结的 `chapter-1-gold.json` 作为分母，并由 `scripts/validate_chapter.py` 输出机器可读报告：

- 正文坐标覆盖率不低于 98%：对预测文本和 `gold_text_nfc` 执行 Unicode NFC、连续 ASCII 空白折叠和全半角标点统一后进行最小编辑距离对齐；字符相等且预测框与金标字符框相交的金标字符数 / `gold_char_boxes` 总数。页眉页脚不计入分母。
- 核心概念点击准确率不低于 95%：金标概念出现项中，预测框与金标框的聚合 IoU >= 0.5 且打开正确 `concept_id` 的数量 / 金标概念出现项总数。聚合 IoU 将每组框先求几何并集，再计算两个并集区域的 `intersection_area / union_area`；另报告误报率，自动框不得通过隐藏来规避统计。
- 教材一级证据回跳率为 100%：金标核心概念中，点击一级证据后到达该概念 `canonical_occurrence_id` 对应的正确 `page_id`，且目标框并集中心与金标框并集中心距离不超过页面短边 1% 的概念数 / 金标核心概念总数。每个概念只计一次。
- 用户界面展示的外部链接可访问率为 100%：展示记录中，在最近 30 天内按第7节协议得到 `reachable`，或得到 `auth_required` 且有人工确认记录的数量 / 展示记录总数。
- 概念误报率 = 未匹配任何金标出现项的可见预测出现项数 / 全部可见预测出现项数，必须不高于 5%。
- 金标文件 `figures` 中全部插图可点击，并能显示相同 NFC 图注和清单中的相关概念。
- 备课篮在刷新后保留素材。
- 支持 1440px、1920px 和 1024px 宽度；核心操作可通过键盘完成。
- 流水线可重复执行并输出质量报告。

核心操作枚举为：目录跳转、上一页/下一页、页码跳转、放大/缩小、章节内搜索、概念选择、插图选择、证据回跳、资源打开、加入/移除备课篮。每项必须有键盘路径和自动化测试。

校验报告包含 `schema_version`、`gold_version`、输入文件摘要、各指标的分子/分母/比率、失败实体 ID 和总体 `passed`。任一硬指标失败时脚本退出码为 1，通过时为 0，schema 或输入错误时为 2。

## 12. 实施顺序

1. 建立页面、概念、插图、证据和资源 schema。
2. 生成并冻结第一章金标清单。
3. 为第1章生成带坐标的页面标注和质量报告，重建阅读器三栏框架和页面坐标层。
4. 接入证据卡、资源卡、回跳和备课篮。
5. 完成响应式、键盘、性能和视觉验收。
6. 第1章通过后再批量处理全书，并进入生成中心阶段。
