#!/usr/bin/env python3
"""Build page-coordinate annotations for the chapter-one reader workspace."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "14043807.pdf"
OUT = ROOT / "data/chapter1_workspace.json"
OCR_PY = Path.home() / "tools/ocr-env/bin/python3"
OCR_SCRIPT = Path.home() / ".agents/skills/desktop/ocr.py"
PAGE_START = 14
PAGE_END = 39
FIGURE_RE = re.compile(r"图\s*1\s*[.\-—]\s*\d+")

CONCEPTS = [
    ("software", "计算机软件", ["计算机软件"]),
    ("software-crisis", "软件危机", ["软件危机"]),
    ("software-engineering", "软件工程", ["软件工程"]),
    ("software-process", "软件过程", ["软件过程"]),
    ("software-lifecycle", "软件生命周期", ["软件生命周期", "软件生存周期"]),
    ("waterfall-model", "瀑布模型", ["瀑布模型"]),
    ("prototype-model", "原型模型", ["原型模型"]),
    ("incremental-model", "增量模型", ["增量模型"]),
    ("spiral-model", "螺旋模型", ["螺旋模型"]),
    ("rup", "RUP", ["RUP", "统一过程"]),
    ("cmm", "CMM", ["CMM"]),
    ("cmmi", "CMMI", ["CMMI"]),
    ("case", "CASE", ["CASE", "计算机辅助软件工程"]),
    ("software-tool", "软件工具", ["软件工具", "软件开发工具"]),
]

FALLBACK_DEFINITIONS = {
    "software": "计算机软件是计算机系统中的程序及其文档。",
    "software-crisis": "软件危机是指在计算机软件开发和维护过程中所遇到的一系列严重问题。",
    "software-engineering": "软件工程是将系统化、规范化、可度量的方法应用于软件开发、运行和维护。",
    "software-process": "软件过程是软件生命周期中一系列相关活动、方法和实践的集合。",
    "software-lifecycle": "软件生命周期是软件产品从产生、投入使用到最终被淘汰的全过程。",
    "waterfall-model": "瀑布模型按照需求、设计、实现、测试和维护等阶段顺序推进。",
    "prototype-model": "原型模型通过快速构造可运行原型来澄清和验证需求。",
    "incremental-model": "增量模型将系统分批交付，每个增量提供一组可用功能。",
    "spiral-model": "螺旋模型以风险分析为核心，循环推进计划、评估、开发和验证。",
    "rup": "RUP 是一种以用例驱动、架构为中心并采用迭代增量方式的软件过程。",
    "cmm": "CMM 用分级框架描述软件组织过程能力的成熟程度。",
    "cmmi": "CMMI 是用于组织过程改进的集成化能力成熟度模型。",
    "case": "CASE 指使用计算机和相关软件工具辅助软件工程活动。",
    "software-tool": "软件工具是支持软件开发、运行、维护和管理活动的程序系统。",
}

EVIDENCE_PAGES = {
    "software": 14,
    "software-crisis": 15,
    "software-engineering": 18,
    "software-process": 20,
    "software-lifecycle": 20,
    "waterfall-model": 29,
    "prototype-model": 32,
    "incremental-model": 31,
    "spiral-model": 33,
    "rup": 35,
    "cmm": 24,
    "cmmi": 26,
    "case": 36,
    "software-tool": 36,
}


def source_sha256() -> str:
    digest = hashlib.sha256()
    with PDF.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_metadata():
    knowledge = json.loads((ROOT / "data/se_knowledge.json").read_text(encoding="utf-8"))
    definitions = json.loads((ROOT / "data/se_definitions.json").read_text(encoding="utf-8"))
    definition_map = {item["term"]: item for item in definitions["definitions"]}
    sections = []
    for item in knowledge["sections"]:
        if item["chapter"] != 1:
            continue
        sections.append({
            "section_id": f"section:{item['section'] or 'exercise'}",
            "label": item["section"] or "习题",
            "title": item["section_title"],
            "page_start": item["page_start"],
            "page_end": item["page_end"],
        })
    return sections, definition_map


def run_ocr(page: int):
    image = ROOT / f"images/se/p{page:03d}_0.jpeg"
    result = subprocess.run(
        [str(OCR_PY), str(OCR_SCRIPT), str(image), "--bbox"],
        capture_output=True,
        text=True,
        timeout=90,
        check=True,
    )
    return json.loads(result.stdout)


def normalize_box(box, width, height):
    x, y, w, h = box
    return [round(x / width, 6), round(y / height, 6), round(w / width, 6), round(h / height, 6)]


def section_for_page(sections, page):
    return next((item for item in sections if item["page_start"] <= page <= item["page_end"]), sections[0])


def make_occurrence(page, block, block_index, concept_id, alias, offset, width, height, serial):
    x, y, w, h = block["bbox"]
    text = block["text"]
    visual_start = offset / max(len(text), 1)
    visual_width = len(alias) / max(len(text), 1)
    subbox = [x + w * visual_start, y, max(w * visual_width, 22), h]
    return {
        "occurrence_id": f"occ:{concept_id}:p{page}:{serial}",
        "page_id": f"se3:{page}",
        "concept_id": f"concept:{concept_id}",
        "text": alias,
        "line_text": text,
        "block_index": block_index,
        "boxes": [normalize_box(subbox, width, height)],
        "confidence": block.get("confidence", 0),
        "review_status": "reviewed" if block.get("confidence", 0) >= 0.5 else "needs_review",
        "visible": True,
    }


def figure_from_caption(page, block, width, height, serial):
    x, y, w, h = block["bbox"]
    top = max(0, y - min(height * 0.28, 720))
    left = max(width * 0.12, x - width * 0.15)
    right = min(width * 0.88, x + w + width * 0.15)
    return {
        "figure_id": f"figure:p{page}:{serial}",
        "page_id": f"se3:{page}",
        "classification": "numbered",
        "figure_number": FIGURE_RE.search(block["text"]).group(0).replace(" ", ""),
        "image_boxes": [normalize_box([left, top, right - left, y - top], width, height)],
        "caption_boxes": [normalize_box(block["bbox"], width, height)],
        "caption_text": block["text"],
        "concept_ids": [],
        "confidence": block.get("confidence", 0),
        "review_status": "needs_review",
        "visible": True,
    }


def main():
    sections, definition_map = load_metadata()
    pages = []
    occurrences = []
    figures = []
    concept_counts = {concept_id: 0 for concept_id, _, _ in CONCEPTS}

    for page in range(PAGE_START, PAGE_END + 1):
        payload = run_ocr(page)
        width, height = payload["image_size"]
        blocks = []
        page_occurrences = []
        page_figures = []
        for index, item in enumerate(payload.get("items", [])):
            block = {
                "block_id": f"p{page}-b{index}",
                "text": item["text"],
                "bbox": normalize_box(item["bbox"], width, height),
                "confidence": item.get("confidence", 0),
            }
            blocks.append(block)
            for concept_id, _, aliases in CONCEPTS:
                for alias in aliases:
                    start = 0
                    while True:
                        found = item["text"].find(alias, start)
                        if found < 0:
                            break
                        concept_counts[concept_id] += 1
                        occurrence = make_occurrence(
                            page, item, index, concept_id, alias, found, width, height, concept_counts[concept_id]
                        )
                        occurrences.append(occurrence)
                        page_occurrences.append(occurrence["occurrence_id"])
                        start = found + len(alias)
            caption_text = item["text"].strip()
            if FIGURE_RE.match(caption_text) and len(caption_text) <= 40 and "所示" not in caption_text:
                figure = figure_from_caption(page, item, width, height, len(figures) + 1)
                figures.append(figure)
                page_figures.append(figure["figure_id"])

        section = section_for_page(sections, page)
        pages.append({
            "page_id": f"se3:{page}",
            "scan_index": page,
            "printed_label": str(page - 13),
            "section_id": section["section_id"],
            "image": f"images/se/p{page:03d}_0.jpeg",
            "width": width,
            "height": height,
            "text_blocks": blocks,
            "occurrence_ids": page_occurrences,
            "figure_ids": page_figures,
        })
        print(f"page {page}: {len(blocks)} blocks, {len(page_occurrences)} concepts, {len(page_figures)} figures")

    page_map = {page["page_id"]: page for page in pages}
    for occurrence in occurrences:
        blocks = page_map[occurrence["page_id"]]["text_blocks"]
        index = occurrence["block_index"]
        start = max(0, index - 1)
        end = min(len(blocks), index + 2)
        occurrence["context"] = "".join(block["text"] for block in blocks[start:end])

    concepts = []
    for concept_id, name, aliases in CONCEPTS:
        definition_item = definition_map.get(name)
        definition = definition_item["definition"] if definition_item else FALLBACK_DEFINITIONS[concept_id]
        source_page = EVIDENCE_PAGES.get(concept_id)
        concept_occurrences = [item for item in occurrences if item["concept_id"] == f"concept:{concept_id}"]
        if source_page is None and concept_occurrences:
            source_page = int(concept_occurrences[0]["page_id"].split(":")[-1])
        source_candidates = [
            item for item in concept_occurrences if item["page_id"] == f"se3:{source_page}"
        ] or concept_occurrences

        def evidence_score(item):
            line = item["line_text"].strip()
            score = min(len(line), 80)
            if len(line) < 12:
                score -= 120
            if "定义" in line and len(line) > 20:
                score += 100
            for alias in aliases:
                if re.search(rf"{re.escape(alias)}\s*(?:是|指|称为|是指)", line):
                    score += 300
            return score

        source_occurrence = max(source_candidates, key=evidence_score) if source_candidates else None
        concepts.append({
            "concept_id": f"concept:{concept_id}",
            "canonical_name": name,
            "aliases": aliases,
            "description": definition,
            "occurrence_count": len(concept_occurrences),
            "primary_evidence": {
                "evidence_id": f"evidence:{concept_id}:primary",
                "tier": 1,
                "source_kind": "textbook",
                "source_title": "《软件工程》第3版",
                "quote": source_occurrence["context"] if source_occurrence else definition,
                "page": source_page,
                "target_occurrence_id": source_occurrence["occurrence_id"] if source_occurrence else None,
                "review_status": "reviewed" if definition_item else "needs_review",
            },
        })

    output = {
        "schema_version": 1,
        "book": {
            "book_version_id": "se-third-edition",
            "title": "软件工程 第3版",
            "authors": "钱乐秋、赵文耘、牛军钰",
            "publisher": "清华大学出版社",
            "source_sha256": source_sha256(),
            "page_start": PAGE_START,
            "page_end": PAGE_END,
        },
        "sections": sections,
        "pages": pages,
        "concepts": concepts,
        "occurrences": occurrences,
        "figures": figures,
        "quality": {
            "ocr_engine": "macOS Vision Framework",
            "coordinate_pages": len(pages),
            "concept_occurrences": len(occurrences),
            "figure_candidates": len(figures),
            "note": "概念框由行级 OCR 坐标按字符位置换算；插图框为图注驱动候选，仍需人工复核。",
        },
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
