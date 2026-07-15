# 数智教材平台第二期：本地检索、备课与课件生成设计

## 1. 目标

第二期将第一章阅读样板扩展为教师可在本机真实使用的备课系统。系统不依赖在线模型账号，基于现有《软件工程》第3版398页 OCR、章节结构、术语索引、概念图谱和扫描页，完成全文检索问答、可溯源教案生成以及真实 DOCX/PPTX 导出。

核心闭环：打开本地平台 -> 阅读或搜索全书 -> 提问并核验原文 -> 收集素材 -> 配置课时 -> 生成并编辑教案 -> 导出 Word 与 PowerPoint。

## 2. 范围

### 2.1 本期交付

- 一条命令启动稳定的本地 HTTP 服务，浏览器不再通过 `file://` 读取数据。
- 398页全文和16章目录可检索、可定位；阅读页按需加载，不把全书坐标一次性送到前端。
- 本地检索增强问答，回答必须附教材页码、章节和原文摘录。
- 可编辑、排序和持久化的备课素材篮。
- 生成中心：课时配置、教学目标、重点难点、教学过程、课堂活动、作业和引用清单。
- 导出可正常打开的 `.docx` 教案和 `.pptx` 课件。
- 生成状态、错误提示、重试和下载记录。
- 桌面端优先，并保持1024px窄屏可用。

### 2.2 明确不做

- 在线大模型、联网搜索生成、账号体系、多用户协作和云端存储。
- 无依据的开放式创作。系统只允许基于教材、人工输入和已核验资源生成事实性内容。
- 对398页全部生成精细字符框。第一章保留高精度坐标层，其余章节先支持全文、章节和页码级定位。
- 将本地模板生成描述成模型推理；界面应明确标注“本地检索与模板生成”。

## 3. 运行与性能架构

### 3.1 本地服务

新增 Python 服务作为唯一入口，监听 `127.0.0.1`，提供静态文件、检索 API、生成 API 和产物下载。启动脚本检查端口、数据文件和导出依赖，启动成功后输出并打开 HTTP 地址。直接打开 HTML 时，页面显示明确的“请启动本地服务”说明，不进入无限加载。

服务不需要数据库。只读教材数据在进程启动时建立紧凑内存索引；教师状态和生成记录写入项目内 `runtime/`，该目录不提交版本控制。写文件采用临时文件加原子替换，避免中断造成损坏。

`runtime/manifest.json` 记录 `schema_version: 1`、源数据 SHA-256、索引状态和最后成功启动时间。篮子与教案分别存为 `basket.json` 和 `lesson-plans/<id>.json`，均包含单调递增的整数 `revision`。更新请求必须携带当前 revision；不匹配返回 `409 REVISION_CONFLICT` 和服务端最新对象。单进程内写入使用互斥锁，同一文件不并发写。素材篮不存在时 `GET` 返回内存中的 `{schema_version:1,revision:0,items:[]}`，第一次 `PUT` 只接受 revision 0并原子创建 revision 1；并发首次写入只有先取得锁的一次成功，后续请求收到409。

### 3.2 性能策略

- 首屏只请求应用壳、当前章摘要和当前页图片。
- 全书 OCR 不进入首屏响应；检索索引由服务端常驻。
- 页面图片只预取前后各一页；重复页面使用浏览器缓存。
- 概念查询使用启动时构建的字典，禁止前端对数组反复线性扫描。
- JSON API 开启 gzip、ETag 和 `Cache-Control`；扫描图使用长期缓存。
- 首次启动允许构建索引，进度需可见；后续启动优先读取带源文件摘要的缓存索引。

性能验收环境为本机回环网络、冷启动后第一次访问：应用壳可交互时间不超过2秒，首张教材页显示不超过3秒，章节搜索响应不超过300毫秒，全文问答检索不超过1秒。指标由自动化脚本记录中位数和最慢值，不以主观感受验收。

测量环境固定为当前交付机器、未开启 CPU 限速、Python服务已完成索引、浏览器磁盘缓存清空。使用浏览器 Performance API 从导航开始计时，连续测量5次，报告中位数和最大值；搜索与问答使用固定测试集各执行12次并排除第一次解释器预热值。若交付机器变化，报告必须同时记录 CPU 型号、内存、Python版本和数据摘要。

## 4. 模块边界

### 4.1 `LocalServer`

职责：静态资源、API路由、输入校验、错误编码、运行文件与下载目录。它不理解教学内容，仅调用检索器和生成器。

### 4.2 `BookRepository`

职责：读取 `se_fulltext.json`、`se_knowledge.json`、`se_keyword_index.json`、`se_graph.json` 与章节坐标数据；暴露教材、章节、页面、概念和资源查询。启动时校验页数、章节页界和引用关系。

输入契约固定如下，超出字段允许忽略，必需字段缺失则健康检查返回 `DATA_SCHEMA_INVALID`：

- `se_fulltext.json`：`{book:{title,total_pages,source}, toc:[{level,title,page}], pages:[{page,text}]}`；`page` 为从1开始的扫描页，必须恰好覆盖1至398且不重复。
- `se_knowledge.json`：`{chapters:[{num,title,page_start,page_end}], sections:[{chapter,section,section_title,page_start,page_end,definitions:[{term,definition,page?}],keywords:[{term,freq}]}]}`；章节号为1至16，范围闭合且不得越出1至398。缺少可选 `page` 的定义通过该节文本首次完整短语命中确定引用页，无法命中则不进入自动生成。
- `se_keyword_index.json`：`{keywords:[{term,freq,occurrences:[{page,pos,context}]}], page_terms:{"<page>":[{term,count?}]|[string]}}`；`pos` 是对应页面 OCR 字符串的 Unicode code point 索引，两种 `page_terms` 项形态在仓库层规范化为 `{term,count}`。
- `se_graph.json`：`{nodes:[{id,label,type,page?,chapter?}], links:[{source,target,type,weight?}]}`；边端点必须存在。
- `se_images.json`：`{images:[{page,file,width,height,size_kb,chapter}]}`；`file` 必须是项目根目录内的相对路径，页面1至388有图；缺失的389至398按“无扫描图”降级为纯文本页，不阻止检索。
- `chapter1_workspace.json`：第一章高精度页面、出现项和插图采用第一期规格中的 schema；插图规范化为 `{figure_id,page,caption_text,image_boxes[],caption_boxes[],concept_ids[],review_status}`，只在扫描14至39页启用坐标回跳。
- `chapter1_resources.json` 与 `se_external_resources.json`：资源规范化为 `{resource_id,title,platform:"bilibili"|"github"|"arxiv"|"standard"|"web",url,concept_ids[],chapter_ids[],relation_reason,verification_status,verified_at}`；缺失稳定ID时使用规范化 URL 的 SHA-256 前12位生成，重复 URL 只保留校验时间最新项。
- 习题不依赖独立源文件。仓库在每章最后一个标题含“习题、思考题或练习”的小节范围内，按 OCR 行中 `^\s*[一二三四五六七八九十0-9]+[、.．)]` 切分，规范化为 `{exercise_id,page,text,chapter,section}`；不足10字或超过1000字的候选标记待复核，不进入自动生成。

内部统一页面实体为 `{scan_page:int, printed_page:string|null, chapter:int|null, section:string|null, text:string, image_url:string|null, annotations:array}`。扫描页是所有API和引用的主定位；印刷页仅用于显示，不参与查找。

### 4.3 `LocalRetriever`

职责：中文查询规范化、关键词提取、BM25风格评分、章节/页码过滤、片段切分、去重和排序。输出证据片段，不生成结论。

检索片段结构：

```json
{
  "passage_id": "se3:p18:3",
  "page": 18,
  "printed_page": "5",
  "chapter": 1,
  "section": "1.2 软件工程",
  "quote": "软件工程是建立和使用一套合理的工程原则……",
  "score": 12.48,
  "matched_terms": ["软件工程"]
}
```

### 4.4 `GroundedAnswerer`

职责：根据前若干证据片段组织简洁回答。回答句只能来自以下三类操作：抽取原句、对多个原句做有标记的概括、列出章节位置。每个事实段必须关联至少一个 `passage_id`。没有足够证据时返回“教材中未找到足够依据”，并给出可改写的查询建议。

本地回答不是大模型推理；界面和导出物均标注“由本地教材检索生成，请教师复核”。

确定性组织规则：取评分最高且归一化分数不低于0.22的最多5个片段；按页面顺序合并同义重复句。若问题包含“什么是/定义”，优先抽取含“是、指、称为、定义”且命中查询词的完整句；包含“区别/比较”时按命中实体分组列出各组原句；包含“步骤/过程/阶段”时按原文序号或句序列出；其他问题给出不超过3条摘录式要点。不得补充片段中未出现的因果、数字、作者或结论。最高结果低于阈值或有效片段少于1条时拒答。

### 4.5 `LessonPlanGenerator`

职责：把课程配置、备课篮和检索证据转换为结构化 `lesson_plan`。每个内容块有稳定 ID，可在前端编辑和排序；引用以独立对象保存，不把页码硬编码在富文本中。

输入包括课程名称、授课对象、课时数、单课时分钟数、选定章节、教学风格和教师补充说明。生成规则优先采用备课篮，其次补充章节中的定义、模型、插图和习题。目标使用可观察动词，过程按“导入、讲授、活动、检查、总结、作业”组织。

确定性生成规则：从备课篮按 `sort_order` 取素材，再从选定章节补齐最多8个高频概念、3条定义、2个插图和3道习题。目标按“解释定义、比较模型、应用方法”三个模板生成，缺少对应证据时省略而不凑数。重点取频次前2至4个且有一级证据的概念；难点取包含模型、过程、度量或图表的前1至3项。每课时独立生成阶段，分钟按导入10%、讲授45%、活动25%、检查10%、总结5%、作业5%分配，使用最大余数法取整，最小非零阶段1分钟，确保每课时分钟严格守恒。证据不足以填充讲授阶段时生成“教师补充”占位并标记 `needs_teacher_input: true`，此状态允许保存但禁止导出。

### 4.6 `ArtifactExporter`

职责：只接受通过 schema 校验的 `lesson_plan`，生成 DOCX 和 PPTX。导出器不重新检索、不修改教学含义，确保预览和文件内容一致。

## 5. API

所有 API 返回 `{ok:boolean, data:object|null, error:{code,message,fields?}|null, request_id:string}`；输入错误使用400，资源不存在使用404，版本冲突使用409，生成失败使用500。字段错误通过 `error.fields` 返回 `{field: reason}`。列表统一返回 `{items,total,limit,offset}`，`limit` 默认为20、最大100，`offset` 默认为0。

- `GET /api/health` -> `{status:"ready"|"indexing"|"degraded", degraded_reasons:("data"|"index"|"storage"|"docx"|"pptx")[], index:{processed,total,percent}, data_version, capabilities:{docx,pptx}}`。
- `GET /api/book` -> 教材元信息、`chapters[]` 与 `{pages,indexed_passages,images,annotations}` 质量统计。
- `GET /api/chapters/{chapter}` -> `{chapter,sections[],page_start,page_end,concepts[]}`。
- `GET /api/pages/{page}` -> 内部统一页面实体；非法页返回 `PAGE_OUT_OF_RANGE`。
- `GET /api/search?q=&chapter=&limit=&offset=` -> 检索片段列表；`q` 为1至500字符，`chapter` 省略或1至16。
- `POST /api/answer` 输入 `{question:string, chapter:int|null, selected_passage_ids:string[]}`，输出 `{answer_id,answer,claims:[{text,evidence_ids[]}],passages[],grounded:boolean,notice}`；证据ID最多20个且必须存在。
- `GET /api/basket` -> `{schema_version:1,revision,items[]}`；`PUT /api/basket` 输入同结构。素材项 schema 为 `{basket_item_id,item_type:"concept"|"passage"|"figure"|"resource",entity_id,title,note,sort_order,created_at}`，ID唯一，最多200项，备注最多1000字。
- `POST /api/lesson-plans` 输入 `{title,audience,sessions,minutes_per_session,chapter_ids,style,teacher_notes,basket_item_ids}`，输出完整教案。课时1至8，每课时20至180分钟，章节1至16，标题和对象各最多200字，说明最多5000字。
- `GET /api/lesson-plans/{id}` -> 完整教案；`PUT` 输入完整教案和当前 `revision`，成功后 revision 加1。
- `POST /api/lesson-plans/{id}/exports` 输入 `{format:"docx"|"pptx",revision:int}`，同步输出 `{artifact_id,format,filename,size_bytes,created_at,download_url}`。单机导出目标低于10秒，不引入通用任务队列；超时或失败返回 `EXPORT_FAILED`，可重复提交且不覆盖成功文件。
- `GET /api/artifacts?lesson_plan_id=&limit=&offset=` -> 已成功产物历史，项为 `{artifact_id,lesson_plan_id,lesson_plan_revision,format,filename,size_bytes,sha256,created_at,download_url,status:"available"|"missing"}`。
- `GET /downloads/{artifact_id}`：只接受服务生成的ID并从 manifest 解析真实文件名。

稳定错误码至少包括 `SERVICE_INDEXING`、`DATA_SCHEMA_INVALID`、`INDEX_BUILD_FAILED`、`VALIDATION_ERROR`、`PAGE_OUT_OF_RANGE`、`EVIDENCE_NOT_FOUND`、`REVISION_CONFLICT`、`LESSON_INCOMPLETE`、`EXPORT_DEPENDENCY_MISSING`、`EXPORT_FAILED`、`ARTIFACT_MISSING`、`STORAGE_UNAVAILABLE` 和 `NOT_FOUND`。请求体最大1 MB；所有路径和文件名由服务端生成，客户端不得传入文件系统路径。

索引构建期间前端每500毫秒轮询健康检查；搜索、问答和生成接口返回 `503 SERVICE_INDEXING`，阅读静态页仍可用。索引缓存写入 `runtime/search-index-v1.json`，只有 schema 和全部输入摘要匹配时复用；构建失败时健康状态为 `degraded` 并保留最后错误。服务重启后若发现 `indexing` 状态但无匹配缓存，必须重新构建，不把中断状态视为成功。

`runtime/artifacts/manifest.json` 为 `{schema_version:1,artifacts:[artifact...]}`，每次成功导出后原子更新。产物默认保留最近100个且至少保留30天；超限时先删除最旧文件再移除记录。记录存在但文件缺失时状态为 `missing`，下载返回404 `ARTIFACT_MISSING`，历史仍保留以便诊断。健康检查 `degraded_reasons[]` 使用 `data | index | storage | docx | pptx` 枚举，使前端能给出对应恢复操作。

## 6. 检索与引用规则

OCR文本按标题和段落切成150至450字片段，相邻片段保留最多60字重叠。规范化仅执行 Unicode NFC、大小写统一、连续空白折叠和常见全半角标点统一，原始摘录必须保持不变。

基础分使用 BM25，固定 `k1=1.5`、`b=0.75`；中文查询按已知概念最长匹配后回退到连续二元字切分，停用单字不计分。完整查询短语命中正文加2.0，章节或小节标题命中加3.0，概念规范名命中加2.0，显式指定章节内结果乘1.25；页眉、页脚、版权页和目录页乘0.2。对候选原始分执行 `score / (score + 8)` 得到0至1归一化分数并应用0.22拒答阈值。结果按 `passage_id` 去重；同页相邻命中可合并展示，但引用仍保留原始片段 ID。

每条引用展示书名、章节、扫描页、印刷页和不超过220字的原文。点击引用定位到对应扫描页；第一章存在坐标时进一步高亮目标区域。OCR置信度不足或文本明显乱码时标记“识别待复核”，不用于自动概括的唯一依据。

## 7. 生成中心

### 7.1 工作流

生成中心采用四步流程：课程设置 -> 素材与依据 -> 教案编辑 -> 导出。教师可在任何一步返回修改，未导出的草稿自动保存。

### 7.2 教案 schema

```json
{
  "lesson_plan_id": "lp_20260715_ab12",
  "schema_version": 1,
  "title": "软件工程概论",
  "audience": "计算机专业本科二年级",
  "sessions": 2,
  "minutes_per_session": 45,
  "chapter_ids": [1],
  "revision": 1,
  "style": "讲授与案例结合",
  "created_at": "2026-07-15T12:00:00+08:00",
  "updated_at": "2026-07-15T12:00:00+08:00",
  "teacher_notes": "",
  "objectives": [{"id": "obj_1", "text": "解释软件危机产生的背景", "evidence_ids": ["se3:p15:2"], "sort_order": 0}],
  "key_points": [{"id": "kp_1", "text": "软件危机", "evidence_ids": ["se3:p15:2"], "sort_order": 0}],
  "difficult_points": [{"id": "dp_1", "text": "过程模型比较", "evidence_ids": [], "sort_order": 0}],
  "sessions_data": [{"id": "session_1", "title": "第一课时", "sort_order": 0, "stages": [{"id": "stage_1", "type": "intro", "minutes": 5, "title": "问题导入", "content": "…", "evidence_ids": [], "needs_teacher_input": false, "sort_order": 0}]}],
  "activities": [{"id": "act_1", "title": "模型辨析", "instructions": "…", "minutes": 10, "evidence_ids": [], "sort_order": 0}],
  "assignments": [{"id": "hw_1", "text": "完成章后习题1", "evidence_ids": ["se3:p39:1"], "sort_order": 0}],
  "references": [{"evidence_id": "se3:p15:2", "evidence_type":"passage", "title":"软件危机", "book":"软件工程 第3版", "chapter":"第1章 概论", "scan_page":15, "printed_page":"2", "quote":"…", "url":null}]
}
```

所有 `id` 在教案内唯一，文本为纯文本而非HTML；标题最多200字，普通内容最多5000字。`sort_order` 为从0开始且在同一数组中不重复的整数。`type` 只能是 `intro | lecture | activity | check | summary | assignment`。`evidence_type` 只能是 `passage | concept | figure | exercise | resource`：passage包含页码与quote；concept必须解析到至少一个passage并同时引用该passage；figure包含页码、图注和可选图片路径；exercise包含页码和题目原文；resource包含平台、URL和关联理由。外部resource只能出现在教学拓展、活动或参考资料中，不得作为定义、因果、数字等教材事实的唯一依据。`sessions_data` 数量必须等于 `sessions`；每个课时仅计算其 `stages[].minutes`，且必须严格等于 `minutes_per_session`。`activities[].minutes` 是对应活动阶段的说明值，不额外计入总时长。阶段不得为0分钟。所有 `evidence_ids` 必须出现在 `references` 且能由仓库解析。前端保存前和服务导出前均校验；不一致时显示具体课时差额并禁止导出。删除仍被引用的证据时需要确认，并同步移除引用关系。

### 7.3 DOCX

Word教案包含封面信息、课程概况、教学目标、重点难点、逐阶段教学过程表、课堂活动、作业、引经据典和生成说明。页眉显示课程名，页脚显示页码。引用采用统一编号 `[教材-页码]`，末尾列完整出处。

DOCX模板由导出器代码生成，不依赖外部模板文件。字体优先使用苹方/微软雅黑，缺失时回退思源黑体/Noto Sans CJK；文档自身不嵌入字体。A4纵向，正文10.5pt，标题层级固定。表格跨页允许重复表头；单元格内容过长自动换行，不截断。文件名为服务端清洗后的 `<课程名>-教案-<YYYYMMDD-HHMMSS>-<artifact_id>.docx`，每次导出新建文件。

### 7.4 PPTX

课件采用统一学术工作台视觉，16:9尺寸，默认10至18页：封面、学习目标、知识地图、问题导入、核心概念、模型/流程、案例或活动、课堂检查、总结、作业、参考来源。每页控制信息密度，正文不小于20pt；教材原图或插图必须带页码来源。没有合适图片时使用原生形状和关系图，不生成装饰性假图片。

PPTX由代码模板生成，使用相同字体回退。每页标题最多24字，正文最多6条、每条最多60字；超过时按完整条目拆分为“续”页，不缩小到20pt以下。图片缺失时展示带来源页码的灰色占位框并在导出日志记录，不使整个导出失败。每张包含事实性教材内容的幻灯片右下角必须有至少一个 `[教材-扫描页]`，末页列出全部去重引用。预览与导出共享同一 `lesson_plan` 和分页函数；自动测试比较两者的幻灯片类型序列、标题和引用ID完全相同。文件命名规则与DOCX一致，扩展名为 `.pptx`。

## 8. 前端改造

- 阅读器启动时先请求健康检查，失败时展示启动命令和重试按钮。
- 左栏升级为16章目录与全书搜索；第一章继续使用精细坐标层，其他章节展示页码级结果。
- 右栏启用“智能问答”，显示问题历史、检索状态、引用卡和回到原文操作。
- 底部素材篮升级为抽屉式管理器，支持备注、排序、去重、移除和服务端持久化。
- 新增 `generate.html` 生成中心，与阅读器共享导航、色彩、字体、图标和反馈组件。
- 同步导出显示准备、生成、完成、失败四种状态；完成后显示文件名、大小、时间和下载按钮，进行中禁止重复点击。

旧版 `workspace.html` 路由继续有效，数据源从静态 JSON 切换为API。第一章出现项和资源ID保持不变。首次服务启动时若 `runtime/basket.json` 不存在，前端读取 `digital-textbook:prep-basket:v1`，过滤无效字段、按 `item_type + entity_id` 去重后调用 `PUT /api/basket`；成功后写入 `digital-textbook:prep-basket:migrated:v1`，以后不重复迁移。无法映射的旧项保留在 localStorage，并在界面列出“未迁移素材”，不得静默丢失。

## 9. 状态与安全

- 服务未启动：不持续转圈，直接显示诊断和启动方式。
- 索引缺失或过期：后台重建并报告进度；旧索引不可与新源文件混用。
- 搜索无结果：展示建议，不生成无引用答案。
- 导出依赖缺失：健康检查标记具体缺失能力，其他功能仍可使用。
- 导出中断：本次请求返回失败，可用相同输入重试，不产生半成品下载链接。
- 教师输入、OCR文本和资源标题在输出HTML前统一转义。
- 下载路由拒绝路径穿越，只允许产物 manifest 中登记的 `.docx` 和 `.pptx`。
- 本地服务仅绑定回环地址，不提供局域网访问。

运行文件 JSON 损坏时先重命名为 `.corrupt-<timestamp>`，返回 `STORAGE_UNAVAILABLE` 并保留诊断，不自动清空用户数据。schema 版本高于服务支持版本时只读展示并拒绝保存；低于当前版本时执行显式迁移并保留 `.bak`。目录不可写或磁盘空间不足100 MB时禁用保存和导出，但阅读、搜索和问答继续可用。导出先写 `.tmp`，重新打开验证成功后原子改名；服务终止后下次启动清除超过24小时的 `.tmp`，已登记成功产物不删除。同步导出不支持取消，页面离开不会终止服务端正在执行的单次导出。

## 10. 测试与验收

### 10.1 自动测试

- 仓库测试：398页存在、16章页界合法、图片引用存在、索引摘要匹配。
- 检索测试：提交 `tests/fixtures/retrieval-gold.json`，含至少12个问题、每题允许页集合、必含关键词、允许证据ID或原文片段，以及至少2个拒答案例；每题前5条至少一条命中允许页，回答包含必含关键词并引用允许证据，整体通过率100%。
- 回答测试：每个事实段至少一个有效引用；无结果问题不得编造答案。
- API测试：正常、空输入、超长输入、非法章节、未知产物、路径穿越、revision冲突、首次篮子创建、损坏运行文件、存储不可写、陈旧教案导出和产物文件缺失。
- 教案测试：分钟守恒、引用完整、草稿往返保存不丢字段。
- 导出测试：DOCX/PPTX可由标准库重新打开；固定两课时样例DOCX至少5页且包含七个标题“课程概况、教学目标、重点难点、教学过程、课堂活动、作业、引经据典”；PPTX为10至18页。PPTX中全部文本框边界必须位于幻灯片边界内，正文计算字号不低于20pt，事实页引用ID集合非空。
- 浏览器测试：搜索、问答、引用跳转、素材篮、生成、编辑、导出和下载主闭环。

### 10.2 完成标准

- 通过 HTTP 地址打开，不再出现 `file://` 数据读取失败。
- 398页和16章均可搜索并跳转。
- 至少12个固定问题达到金标允许页命中规则并返回教材原文引用。
- 无依据问题明确拒答，引用点击可回到对应页面。
- 素材篮刷新后保留，重复素材不会重复添加。
- 可生成一份两课时教案，并成功下载可打开的 DOCX 和 PPTX。
- Word包含自动测试列出的七个标题和引用清单；PPT为10至18页，除封面、纯活动说明、总结目录和结束页外均定义为事实页并至少保留一个有效来源。
- 首屏、检索和问答达到第3.2节性能门槛。
- 1024px和1440px宽度下主闭环可用，键盘焦点可见。
- 所有自动测试通过，浏览器控制台无未处理错误。

## 11. 实施顺序

1. 建立本地服务、健康检查、运行目录和全书仓库校验。
2. 构建缓存检索索引、全文搜索和有引用回答。
3. 优化阅读器启动、全书目录、按需数据与问答面板。
4. 升级备课篮并实现结构化教案生成和编辑。
5. 实现DOCX/PPTX导出、下载和生成记录。
6. 完成性能、API、产物和浏览器端到端验收。
