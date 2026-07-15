# Phase Two Local Teaching System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fast local textbook service with grounded full-book Q&A, persistent preparation materials, editable lesson plans, and real DOCX/PPTX exports.

**Architecture:** A Python standard-library HTTP server owns book data, retrieval, persistence, generation, and downloads. Focused Python modules expose typed dictionary contracts and are tested with `unittest`; the existing reader becomes an API client, while a new generation page consumes the same lesson-plan schema. Exporters use the bundled `python-docx` and `python-pptx` runtime but degrade independently when those packages are unavailable.

**Tech Stack:** Python 3.11+ standard library, `python-docx 1.2.0`, `python-pptx 1.0.2`, vanilla HTML/CSS/JavaScript, `unittest`, Codex in-app browser.

---

## File Map

- `server/app.py`: HTTP entry point, routing, cache headers, safe downloads.
- `server/config.py`: project paths, limits, runtime discovery.
- `server/errors.py`: stable API errors and JSON response envelope.
- `server/repository.py`: source JSON validation and normalized entities.
- `server/retrieval.py`: passage splitting, BM25 ranking, grounded answers.
- `server/storage.py`: revisions, atomic JSON writes, basket and artifact manifests.
- `server/lesson_plans.py`: deterministic lesson-plan construction and validation.
- `server/export_docx.py`: Word generation and reopen validation.
- `server/export_pptx.py`: slide pagination, PowerPoint generation and validation.
- `server/service.py`: application facade used by routes and tests.
- `scripts/start_platform.py`: dependency-aware local launcher.
- `start.command`: double-clickable macOS startup wrapper.
- `workspace.js`: API bootstrap, full-book search, Q&A, basket migration.
- `workspace.html`, `workspace.css`: reader states and enabled Q&A UI.
- `generate.html`, `generate.css`, `generate.js`: four-step generation center.
- `tests/`: repository, API, retrieval, storage, lesson-plan and export tests.
- `tests/fixtures/retrieval-gold.json`: deterministic retrieval and refusal cases.
- `runtime/`: ignored user state, search cache and generated artifacts.

### Task 1: Preserve the Phase-One Reader Baseline

**Files:**
- Modify: `.gitignore`
- Verify: `workspace.html`, `workspace.css`, `workspace.js`
- Verify: `data/chapter1_workspace.json`, `data/chapter1_resources.json`

- [ ] **Step 1: Add runtime outputs to ignore rules**

```gitignore
runtime/
*.tmp
```

- [ ] **Step 2: Run baseline validation**

Run:

```bash
node --check workspace.js
python3 -m py_compile scripts/build_chapter1_workspace.py
python3 - <<'PY'
import json
d=json.load(open('data/chapter1_workspace.json'))
assert len(d['pages']) == 26
assert len(d['occurrences']) == 237
assert len(d['figures']) == 14
PY
```

Expected: exit 0 with no output.

- [ ] **Step 3: Commit the working reader baseline**

```bash
git add .gitignore index.html workspace.html workspace.css workspace.js scripts/build_chapter1_workspace.py data/chapter1_workspace.json data/chapter1_resources.json
git commit -m "feat: establish traceable textbook reader"
```

### Task 2: Local Server and Book Repository

**Files:**
- Create: `server/__init__.py`
- Create: `server/config.py`
- Create: `server/errors.py`
- Create: `server/repository.py`
- Create: `server/service.py`
- Create: `server/app.py`
- Create: `tests/test_repository.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write repository and health-route tests**

```python
# tests/test_repository.py
import unittest
from pathlib import Path
from server.repository import BookRepository

ROOT = Path(__file__).parents[1]

class RepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = BookRepository(ROOT / "data", ROOT)

    def test_normalizes_complete_book(self):
        self.assertEqual(398, len(self.repo.pages))
        self.assertEqual(list(range(1, 17)), [c["number"] for c in self.repo.chapters])
        self.assertEqual("软件工程 第3版", self.repo.book["title"])

    def test_first_chapter_keeps_coordinate_annotations(self):
        page = self.repo.get_page(18)
        self.assertTrue(page["annotations"])
        self.assertEqual(18, page["scan_page"])
```

```python
# tests/test_app.py
import json, threading, unittest
from http.client import HTTPConnection
from server.app import create_server

class AppTest(unittest.TestCase):
    def test_health_envelope(self):
        server = create_server(port=0)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        conn = HTTPConnection("127.0.0.1", server.server_port)
        conn.request("GET", "/api/health")
        response = conn.getresponse()
        payload = json.loads(response.read())
        thread.join()
        server.server_close()
        self.assertEqual(200, response.status)
        self.assertTrue(payload["ok"])
        self.assertIn(payload["data"]["status"], {"ready", "degraded"})
```

- [ ] **Step 2: Verify tests fail before implementation**

Run: `python3 -m unittest tests.test_repository tests.test_app -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'server'`.

- [ ] **Step 3: Implement normalized repository and HTTP shell**

```python
# server/errors.py
class ApiError(Exception):
    def __init__(self, status, code, message, fields=None):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.fields = fields or {}

def envelope(data=None, error=None, request_id="local"):
    return {"ok": error is None, "data": data, "error": error, "request_id": request_id}
```

Implement `BookRepository` to validate the exact contracts in spec §4.2, normalize 398 pages, retain chapter-one annotations, and expose `get_page()`, `get_chapter()`, `find_concept()`, and `get_reference()`. Implement `ThreadingHTTPServer` routes for `/api/health`, `/api/book`, `/api/chapters/{id}`, `/api/pages/{id}`, and static files. Every response uses `envelope`, API JSON uses gzip when accepted, JSON receives ETag, and images receive `Cache-Control: public, max-age=31536000, immutable`.

- [ ] **Step 4: Run repository and API tests**

Run: `python3 -m unittest tests.test_repository tests.test_app -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit server foundation**

```bash
git add server tests/test_repository.py tests/test_app.py
git commit -m "feat: serve normalized textbook data locally"
```

### Task 3: Full-Book Retrieval and Grounded Answers

**Files:**
- Create: `server/retrieval.py`
- Create: `tests/test_retrieval.py`
- Create: `tests/fixtures/retrieval-gold.json`
- Modify: `server/service.py`
- Modify: `server/app.py`

- [ ] **Step 1: Add retrieval gold fixtures**

```json
[
  {"question":"什么是软件危机？","chapter":1,"allowed_pages":[15],"required_terms":["软件危机"],"refuse":false},
  {"question":"软件工程的定义是什么？","chapter":1,"allowed_pages":[18],"required_terms":["软件工程"],"refuse":false},
  {"question":"软件过程是什么？","chapter":1,"allowed_pages":[20],"required_terms":["软件过程"],"refuse":false},
  {"question":"瀑布模型有哪些阶段？","chapter":1,"allowed_pages":[29,30],"required_terms":["瀑布"],"refuse":false},
  {"question":"原型模型适合什么情况？","chapter":1,"allowed_pages":[31,32],"required_terms":["原型"],"refuse":false},
  {"question":"增量模型如何交付？","chapter":1,"allowed_pages":[31,32],"required_terms":["增量"],"refuse":false},
  {"question":"螺旋模型强调什么？","chapter":1,"allowed_pages":[33,34],"required_terms":["螺旋"],"refuse":false},
  {"question":"RUP包含哪些阶段？","chapter":1,"allowed_pages":[35],"required_terms":["RUP"],"refuse":false},
  {"question":"CMM和CMMI有什么关系？","chapter":1,"allowed_pages":[24,25,26,27],"required_terms":["CMM"],"refuse":false},
  {"question":"需求工程的主要任务是什么？","chapter":3,"allowed_pages":[46,47,48,49,50,51,52,53,54,55,56,57,58],"required_terms":["需求"],"refuse":false},
  {"question":"软件测试的目的是什么？","chapter":12,"allowed_pages":[276,277,278,279,280,281,282,283,284,285,286,287,288,289,290],"required_terms":["测试"],"refuse":false},
  {"question":"项目管理为什么需要估算？","chapter":15,"allowed_pages":[324,325,326,327,328,329,330,331,332,333,334,335,336],"required_terms":["估算"],"refuse":false},
  {"question":"本书如何评价量子纠错？","chapter":null,"allowed_pages":[],"required_terms":[],"refuse":true},
  {"question":"作者明天会发布什么软件？","chapter":null,"allowed_pages":[],"required_terms":[],"refuse":true}
]
```

- [ ] **Step 2: Write failing retrieval tests**

```python
class RetrievalTest(unittest.TestCase):
    def test_gold_questions(self):
        for case in self.gold:
            result = self.answerer.answer(case["question"], case["chapter"])
            if case["refuse"]:
                self.assertFalse(result["grounded"])
            else:
                self.assertTrue(result["grounded"])
                self.assertTrue(set(case["allowed_pages"]) & {p["page"] for p in result["passages"]})
                self.assertTrue(all(term in result["answer"] for term in case["required_terms"]))
```

Run: `python3 -m unittest tests.test_retrieval -v`

Expected: FAIL because `server.retrieval` is missing.

- [ ] **Step 3: Implement passage index, BM25 and answer templates**

Implement spec §4.3, §4.4 and §6 exactly: 150-450 character passages, 60-character overlap, longest known-concept matching, Chinese bigrams, `k1=1.5`, `b=0.75`, fixed boosts, `score/(score+8)` normalization, and 0.22 refusal threshold. `GroundedAnswerer.answer()` must return claims whose evidence IDs resolve to returned passages and must never use external resources as the only factual source.

- [ ] **Step 4: Expose `/api/search` and `/api/answer` and pass tests**

Run:

```bash
python3 -m unittest tests.test_retrieval tests.test_app -v
```

Expected: all tests PASS; the two refusal fixtures return `grounded: false`.

- [ ] **Step 5: Commit retrieval**

```bash
git add server/retrieval.py server/service.py server/app.py tests/test_retrieval.py tests/fixtures/retrieval-gold.json
git commit -m "feat: add grounded full-book retrieval"
```

### Task 4: Revisioned Basket and Artifact Storage

**Files:**
- Create: `server/storage.py`
- Create: `tests/test_storage.py`
- Modify: `server/app.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write storage failure and revision tests**

```python
def test_first_basket_write_and_conflict(self):
    self.assertEqual(0, self.store.get_basket()["revision"])
    saved = self.store.put_basket({"revision": 0, "items": []})
    self.assertEqual(1, saved["revision"])
    with self.assertRaises(RevisionConflict):
        self.store.put_basket({"revision": 0, "items": []})

def test_corrupt_json_is_preserved(self):
    self.basket_path.write_text("{")
    with self.assertRaises(StorageUnavailable):
        self.store.get_basket()
    self.assertTrue(list(self.root.glob("basket.json.corrupt-*")))
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_storage -v`

Expected: FAIL because `server.storage` is missing.

- [ ] **Step 3: Implement locked atomic storage**

Implement `JsonStore.atomic_write()` with a sibling `.tmp`, `flush()`, `os.fsync()`, and `os.replace()`. Implement revision-0 basket creation, 200-item validation, `item_type + entity_id` de-duplication, corrupt-file preservation, schema rejection, free-space checks, artifact manifest, available/missing states, and 100-item/30-day retention.

- [ ] **Step 4: Add basket and artifact APIs and pass tests**

Run: `python3 -m unittest tests.test_storage tests.test_app -v`

Expected: all tests PASS, including conflict and path-traversal cases.

- [ ] **Step 5: Commit persistence**

```bash
git add .gitignore server/storage.py server/app.py tests/test_storage.py
git commit -m "feat: persist preparation state safely"
```

### Task 5: Deterministic Lesson-Plan Generation

**Files:**
- Create: `server/lesson_plans.py`
- Create: `tests/test_lesson_plans.py`
- Modify: `server/service.py`
- Modify: `server/app.py`

- [ ] **Step 1: Write minute-conservation and citation tests**

```python
def test_two_session_plan_is_complete_and_grounded(self):
    plan = self.generator.create({
        "title":"软件工程概论", "audience":"本科二年级", "sessions":2,
        "minutes_per_session":45, "chapter_ids":[1],
        "style":"讲授与案例结合", "teacher_notes":"", "basket_item_ids":[]
    })
    self.assertEqual(2, len(plan["sessions_data"]))
    self.assertTrue(all(sum(s["minutes"] for s in session["stages"]) == 45 for session in plan["sessions_data"]))
    reference_ids = {item["evidence_id"] for item in plan["references"]}
    for block in plan["objectives"] + plan["key_points"]:
        self.assertTrue(set(block["evidence_ids"]) <= reference_ids)
```

- [ ] **Step 2: Verify tests fail**

Run: `python3 -m unittest tests.test_lesson_plans -v`

Expected: FAIL because `LessonPlanGenerator` is missing.

- [ ] **Step 3: Implement generation and validation**

Implement the exact selection order, objective templates, difficulty rules, maximum-rank additions and largest-remainder minute allocation from spec §4.5. Implement `validate_plan()` for IDs, text lengths, enum values, session count, per-session minute conservation, reference resolution, external-resource restrictions and `needs_teacher_input` export blocking.

- [ ] **Step 4: Add create/get/update lesson-plan APIs**

Run: `python3 -m unittest tests.test_lesson_plans tests.test_app -v`

Expected: all tests PASS; stale revisions return 409 and invalid minute totals return 400.

- [ ] **Step 5: Commit lesson plans**

```bash
git add server/lesson_plans.py server/service.py server/app.py tests/test_lesson_plans.py
git commit -m "feat: generate grounded lesson plans"
```

### Task 6: DOCX and PPTX Exporters

**Files:**
- Create: `server/export_docx.py`
- Create: `server/export_pptx.py`
- Create: `tests/test_exports.py`
- Modify: `server/service.py`
- Modify: `server/app.py`

- [ ] **Step 1: Write reopen and layout-bound tests**

```python
@unittest.skipUnless(DOCX_AVAILABLE and PPTX_AVAILABLE, "document runtime unavailable")
def test_exports_reopen_with_required_structure(self):
    docx_path = export_docx(self.plan, self.output)
    pptx_path = export_pptx(self.plan, self.output)
    document = Document(docx_path)
    presentation = Presentation(pptx_path)
    all_text = "\n".join(p.text for p in document.paragraphs)
    for title in ["课程概况","教学目标","重点难点","教学过程","课堂活动","作业","引经据典"]:
        self.assertIn(title, all_text)
    self.assertGreaterEqual(len(presentation.slides), 10)
    self.assertLessEqual(len(presentation.slides), 18)
    for slide in presentation.slides:
        for shape in slide.shapes:
            self.assertLessEqual(shape.left + shape.width, presentation.slide_width)
            self.assertLessEqual(shape.top + shape.height, presentation.slide_height)
```

- [ ] **Step 2: Verify tests fail**

Run with the bundled runtime:

```bash
/Users/a1111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_exports -v
```

Expected: FAIL because exporter modules are missing.

- [ ] **Step 3: Implement DOCX export**

Generate A4 portrait output with cover metadata, seven required sections, repeated table headers, page footer, numbered textbook citations, font fallback, sanitized unique filenames, `.tmp` write, reopen validation and atomic final rename.

- [ ] **Step 4: Implement PPTX export**

Generate 16:9 slides through a pure `paginate_plan(plan)` function shared with preview metadata. Enforce at most six 60-character bullets, split overflow into continuation slides, use at least 20pt body type, render native process diagrams, add source labels to every fact slide, and create a final de-duplicated reference slide.

- [ ] **Step 5: Pass exporter and API tests**

Run:

```bash
/Users/a1111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_exports tests.test_app -v
```

Expected: all tests PASS and generated files reopen successfully.

- [ ] **Step 6: Commit exporters**

```bash
git add server/export_docx.py server/export_pptx.py server/service.py server/app.py tests/test_exports.py
git commit -m "feat: export lesson plans to docx and pptx"
```

### Task 7: Fast Reader API Client and Full-Book Q&A

**Files:**
- Create: `api-client.js`
- Modify: `workspace.html`
- Modify: `workspace.css`
- Modify: `workspace.js`
- Create: `tests/test_frontend_contract.py`

- [ ] **Step 1: Write static frontend contract tests**

```python
def test_reader_has_service_failure_and_qa_states(self):
    html = Path("workspace.html").read_text()
    js = Path("workspace.js").read_text()
    self.assertIn('id="service-status"', html)
    self.assertIn('data-tab="qa"', html)
    self.assertIn("/api/answer", js)
    self.assertNotIn('DATA_URL = "data/chapter1_workspace.json"', js)
```

- [ ] **Step 2: Verify frontend test fails**

Run: `python3 -m unittest tests.test_frontend_contract -v`

Expected: FAIL because the reader still starts from static JSON.

- [ ] **Step 3: Implement API bootstrap and indexed lookups**

Create `api-client.js` with `request(path, options)`, timeout, JSON-envelope parsing and typed Chinese errors. Change reader startup to health -> book -> page, request first-chapter annotations only for pages14-39, and replace `Array.find()` hot paths with `Map` indexes. Keep only adjacent-page image prefetch.

- [ ] **Step 4: Enable full-book navigation, search and Q&A**

Add 16-chapter tree, paginated search results, indexing progress, service-not-started panel with `python3 scripts/start_platform.py`, answer history, citation cards and page jump. Migrate `digital-textbook:prep-basket:v1` once using revision 0 and preserve unmapped items visibly.

- [ ] **Step 5: Pass syntax and contract tests**

Run:

```bash
node --check api-client.js
node --check workspace.js
python3 -m unittest tests.test_frontend_contract -v
```

Expected: all checks PASS.

- [ ] **Step 6: Commit reader upgrade**

```bash
git add api-client.js workspace.html workspace.css workspace.js tests/test_frontend_contract.py
git commit -m "feat: connect reader to full-book teaching service"
```

### Task 8: Generation Center UI

**Files:**
- Create: `generate.html`
- Create: `generate.css`
- Create: `generate.js`
- Modify: `workspace.html`
- Modify: `index.html`
- Modify: `tests/test_frontend_contract.py`

- [ ] **Step 1: Extend contract tests for the four-step workflow**

```python
def test_generation_center_exposes_complete_flow(self):
    html = Path("generate.html").read_text()
    js = Path("generate.js").read_text()
    for step in ["课程设置", "素材与依据", "教案编辑", "导出"]:
        self.assertIn(step, html)
    self.assertIn("/api/lesson-plans", js)
    self.assertIn("/exports", js)
    self.assertIn("/api/artifacts", js)
```

- [ ] **Step 2: Verify test fails**

Run: `python3 -m unittest tests.test_frontend_contract -v`

Expected: FAIL because `generate.html` is missing.

- [ ] **Step 3: Build course setup and evidence review**

Create a responsive four-step workbench matching the reader visual system. Validate title, audience, 1-8 sessions, 20-180 minutes, chapters and teacher notes before calling `POST /api/lesson-plans`. Show selected basket materials grouped by passage, concept, figure, exercise and resource.

- [ ] **Step 4: Build lesson editor and export panel**

Render objectives, key/difficult points, sessions and stages as reorderable editable cards. Recalculate minute differences on every edit, autosave with revision, resolve 409 conflicts, block incomplete exports, show DOCX/PPTX progress, and list available/missing artifact history.

- [ ] **Step 5: Pass frontend checks**

Run:

```bash
node --check generate.js
python3 -m unittest tests.test_frontend_contract -v
```

Expected: all checks PASS.

- [ ] **Step 6: Commit generation center**

```bash
git add generate.html generate.css generate.js workspace.html index.html tests/test_frontend_contract.py
git commit -m "feat: add teacher lesson generation center"
```

### Task 9: Launcher, End-to-End and Performance Verification

**Files:**
- Create: `scripts/start_platform.py`
- Create: `start.command`
- Create: `tests/test_e2e_api.py`
- Create: `tests/test_performance.py`
- Create: `README.md`

- [ ] **Step 1: Write launcher and API-flow tests**

```python
def test_complete_api_flow(self):
    self.assertEqual("ready", self.get("/api/health")["data"]["status"])
    answer = self.post("/api/answer", {"question":"什么是软件工程？","chapter":1})["data"]
    self.assertTrue(answer["grounded"])
    plan = self.post("/api/lesson-plans", self.course_payload)["data"]
    self.assertEqual(45, sum(x["minutes"] for x in plan["sessions_data"][0]["stages"]))
```

- [ ] **Step 2: Implement dependency-aware launcher**

`scripts/start_platform.py` must choose the bundled runtime when it contains `docx` and `pptx`, fall back to the current interpreter, bind only `127.0.0.1`, select an available port starting at8765, wait for `/api/health`, and open `http://127.0.0.1:<port>/workspace.html`. `start.command` changes to the project directory and executes the script.

- [ ] **Step 3: Run the complete automated suite**

Run:

```bash
/Users/a1111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -v
node --check workspace.js
node --check generate.js
git diff --check
```

Expected: all Python tests PASS, JavaScript syntax checks exit 0, and no whitespace errors.

- [ ] **Step 4: Run browser acceptance at 1440px and 1024px**

Verify in the in-app browser: HTTP startup, chapter navigation, search, grounded answer, citation jump, basket persistence, two-session generation, minute editing, DOCX export, PPTX export, download history and reload. At 1024px verify drawers, visible focus, no horizontal overflow and usable export controls. Console errors must be empty.

- [ ] **Step 5: Record performance results**

Run `tests/test_performance.py` against the local service after clearing browser cache. Record CPU, memory, Python version, source digest, five navigation timings and twelve search/answer timings in `runtime/performance-report.json`. Assert median interactive shell <=2s, first page <=3s, search <=300ms and retrieval <=1s.

- [ ] **Step 6: Render and inspect generated artifacts**

Use the document and presentation renderers to inspect every DOCX page and PPTX slide. Confirm no clipped text, at least20pt slide body text, source labels on all fact slides, and the seven required Word sections. Iterate exporters until visual checks pass.

- [ ] **Step 7: Commit launch and verification support**

```bash
git add scripts/start_platform.py start.command README.md tests/test_e2e_api.py tests/test_performance.py
git commit -m "feat: deliver runnable local teaching platform"
```

## Self-Review

- Spec coverage: local HTTP performance,398-page repository, BM25 retrieval, grounded refusal, Q&A, basket migration, revision storage, lesson-plan schema, minute conservation, DOCX/PPTX, artifact history, recovery, responsive UI and acceptance testing are each assigned to a task.
- Placeholder scan: every implementation step names concrete behavior, commands and expected results; no unresolved markers remain.
- Type consistency: API paths, revision fields, evidence IDs, lesson-plan fields and artifact records match the approved specification.
