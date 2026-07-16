const DATA_URL = "data/chapter1_workspace.json";
const RESOURCE_URL = "data/chapter1_resources.json";
const BASKET_KEY = "digital-textbook:prep-basket:v1";

const state = {
  data: null,
  resources: [],
  page: 14,
  zoom: 0.28,
  fitZoom: 0.28,
  tab: "evidence",
  selectedConceptId: null,
  selectedFigureId: null,
  basket: loadBasket(),
};

const elements = {
  toc: document.querySelector("#toc-tree"),
  search: document.querySelector("#chapter-search"),
  stage: document.querySelector("#stage-canvas"),
  pageFrame: document.querySelector("#page-frame"),
  pageImage: document.querySelector("#page-image"),
  skeleton: document.querySelector("#page-skeleton"),
  layer: document.querySelector("#annotation-layer"),
  pageInput: document.querySelector("#page-input"),
  pageLabel: document.querySelector("#page-label"),
  sectionLabel: document.querySelector("#section-label"),
  zoomLabel: document.querySelector("#zoom-label"),
  panelBody: document.querySelector("#panel-body"),
  panelTabs: [...document.querySelectorAll("[data-tab]")],
  basketCount: document.querySelector("#basket-count"),
  basketItems: document.querySelector("#basket-items"),
  basketDescription: document.querySelector("#basket-description"),
  qualitySummary: document.querySelector("#quality-summary"),
  toast: document.querySelector("#toast"),
  scrim: document.querySelector("#drawer-scrim"),
};

init();

async function init() {
  renderLoadingPanel();
  bindEvents();
  try {
    const [dataResponse, resourceResponse] = await Promise.all([fetch(DATA_URL), fetch(RESOURCE_URL)]);
    if (!dataResponse.ok || !resourceResponse.ok) throw new Error("数据文件读取失败");
    state.data = await dataResponse.json();
    state.resources = (await resourceResponse.json()).resources;
    renderToc();
    renderQuality();
    renderBasket();
    await setPage(state.page, { fit: true });
    selectFirstConceptOnPage();
  } catch (error) {
    elements.panelBody.innerHTML = emptyState("数据暂时无法读取", "请使用本地 HTTP 服务打开此页面。", "error");
    showToast(error.message, "error");
  }
}

function bindEvents() {
  document.querySelector("#prev-page").addEventListener("click", () => setPage(state.page - 1));
  document.querySelector("#next-page").addEventListener("click", () => setPage(state.page + 1));
  document.querySelector("#edge-prev").addEventListener("click", () => setPage(state.page - 1));
  document.querySelector("#edge-next").addEventListener("click", () => setPage(state.page + 1));
  elements.pageInput.addEventListener("change", (event) => setPage(Number(event.target.value)));
  document.querySelector("#zoom-in").addEventListener("click", () => setZoom(state.zoom + 0.04));
  document.querySelector("#zoom-out").addEventListener("click", () => setZoom(state.zoom - 0.04));
  document.querySelector("#fit-page").addEventListener("click", fitPage);
  elements.search.addEventListener("input", renderSearchResults);
  document.querySelector("#basket-summary").addEventListener("click", toggleBasket);

  for (const tab of elements.panelTabs) {
    if (tab.dataset.comingSoon) continue;
    tab.addEventListener("click", () => setTab(tab.dataset.tab));
    tab.addEventListener("keydown", (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const index = elements.panelTabs.indexOf(tab);
      const direction = event.key === 'ArrowRight' ? 1 : -1;
      const next = elements.panelTabs[(index + direction + elements.panelTabs.length) % elements.panelTabs.length];
      setTab(next.dataset.tab);
      next.focus();
    });
  }

  for (const button of document.querySelectorAll("[data-coming-soon]")) {
    button.addEventListener("click", () => showToast(`${button.dataset.comingSoon}将在阅读样板验收后接入`));
  }

  for (const button of document.querySelectorAll("[data-drawer]")) {
    button.addEventListener("click", () => toggleDrawer(button.dataset.drawer, true));
  }
  for (const button of document.querySelectorAll("[data-drawer-close]")) {
    button.addEventListener("click", () => toggleDrawer(button.dataset.drawerClose, false));
  }
  elements.scrim.addEventListener("click", closeDrawers);

  window.addEventListener("resize", debounce(() => {
    if (Math.abs(state.zoom - state.fitZoom) < 0.015) fitPage();
  }, 120));

  window.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      elements.search.focus();
      return;
    }
    if (event.target.matches("input, textarea")) return;
    if (event.key === "ArrowLeft") setPage(state.page - 1);
    if (event.key === "ArrowRight") setPage(state.page + 1);
    if (event.key === "+" || event.key === "=") setZoom(state.zoom + 0.04);
    if (event.key === "-") setZoom(state.zoom - 0.04);
    if (event.key === "Escape") closeDrawers();
  });
}

function renderToc() {
  elements.toc.innerHTML = state.data.sections.map((section, index) => `
    <button class="toc-item ${pageInSection(state.page, section) ? "active" : ""}" type="button" data-page="${section.page_start}">
      <span class="toc-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="toc-copy"><strong>${escapeHtml(section.label === section.title ? section.title : `${section.label} ${section.title}`)}</strong><small>扫描 ${section.page_start}–${section.page_end}页</small></span>
      <svg class="icon"><use href="#i-chevron"/></svg>
    </button>
  `).join("");
  for (const item of elements.toc.querySelectorAll("[data-page]")) {
    item.addEventListener("click", () => {
      setPage(Number(item.dataset.page));
      toggleDrawer("left", false);
    });
  }
}

function renderQuality() {
  const quality = state.data.quality;
  elements.qualitySummary.textContent = `${quality.concept_occurrences}个概念位置 · ${quality.figure_candidates}个图表候选`;
}

async function setPage(page, options = {}) {
  if (!state.data) return;
  const nextPage = Math.max(state.data.book.page_start, Math.min(state.data.book.page_end, page));
  const pageData = getPage(nextPage);
  if (!pageData) return;
  state.page = nextPage;
  state.selectedConceptId = null;
  state.selectedFigureId = null;
  elements.pageInput.value = nextPage;
  elements.pageLabel.textContent = `扫描第${nextPage}页 · 书页${pageData.printed_label}`;
  const section = getSection(pageData.section_id);
  elements.sectionLabel.textContent = section.label === section.title ? section.title : `${section.label} ${section.title}`;
  elements.pageFrame.setAttribute("aria-label", `教材扫描第${nextPage}页，书页${pageData.printed_label}`);
  elements.skeleton.hidden = false;
  elements.pageImage.classList.remove("loaded");
  elements.layer.replaceChildren();

  await loadImage(pageData.image);
  if (options.fit || !state.fitZoom) fitPage();
  else applyPageSize(pageData);
  renderAnnotations(pageData);
  renderToc();
  updatePageButtons();
  updatePanel();
  preloadPage(nextPage + 1);
  preloadPage(nextPage - 1);
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    elements.pageImage.onload = () => {
      elements.skeleton.hidden = true;
      elements.pageImage.classList.add("loaded");
      resolve();
    };
    elements.pageImage.onerror = reject;
    elements.pageImage.src = src;
  });
}

function preloadPage(page) {
  const pageData = getPage(page);
  if (!pageData) return;
  const image = new Image();
  image.src = pageData.image;
}

function fitPage() {
  const pageData = getPage(state.page);
  if (!pageData) return;
  const availableWidth = Math.max(360, elements.stage.clientWidth - 136);
  const availableHeight = Math.max(480, elements.stage.clientHeight - 84);
  state.fitZoom = Math.min(availableWidth / pageData.width, availableHeight / pageData.height, 0.48);
  setZoom(state.fitZoom);
}

function setZoom(value) {
  state.zoom = Math.max(0.18, Math.min(0.62, value));
  const pageData = getPage(state.page);
  if (pageData) applyPageSize(pageData);
  elements.zoomLabel.textContent = `${Math.round((state.zoom / state.fitZoom) * 100)}%`;
}

function applyPageSize(pageData) {
  elements.pageFrame.style.width = `${Math.round(pageData.width * state.zoom)}px`;
  elements.pageFrame.style.height = `${Math.round(pageData.height * state.zoom)}px`;
}

function renderAnnotations(pageData) {
  const fragment = document.createDocumentFragment();
  for (const occurrenceId of pageData.occurrence_ids) {
    const occurrence = state.data.occurrences.find((item) => item.occurrence_id === occurrenceId);
    const concept = getConcept(occurrence.concept_id);
    for (const box of occurrence.boxes) {
      const button = annotationButton(box, "annotation", concept.canonical_name);
      button.dataset.conceptId = concept.concept_id;
      button.dataset.occurrenceId = occurrence.occurrence_id;
      button.classList.toggle("selected", concept.concept_id === state.selectedConceptId);
      button.innerHTML = `<span>${escapeHtml(concept.canonical_name)}</span>`;
      button.addEventListener("click", () => selectConcept(concept.concept_id));
      fragment.append(button);
    }
  }
  for (const figureId of pageData.figure_ids) {
    const figure = state.data.figures.find((item) => item.figure_id === figureId);
    for (const box of figure.image_boxes) {
      const button = annotationButton(box, "figure-hotspot", figure.figure_number);
      button.dataset.figureId = figure.figure_id;
      button.innerHTML = `<span><svg class="icon"><use href="#i-image"/></svg>${escapeHtml(figure.figure_number)} · 图表候选</span>`;
      button.addEventListener("click", () => selectFigure(figure.figure_id));
      fragment.append(button);
    }
  }
  elements.layer.append(fragment);
}

function annotationButton(box, className, label) {
  const [x, y, width, height] = box;
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.setAttribute("aria-label", `查看${label}的关联信息`);
  Object.assign(button.style, {
    left: `${x * 100}%`,
    top: `${y * 100}%`,
    width: `${Math.max(width * 100, 1.2)}%`,
    height: `${Math.max(height * 100, 0.8)}%`,
  });
  return button;
}

function selectFirstConceptOnPage() {
  const pageData = getPage(state.page);
  const occurrence = state.data.occurrences.find((item) => pageData.occurrence_ids.includes(item.occurrence_id));
  if (occurrence) selectConcept(occurrence.concept_id, { announce: false });
  else renderPageOverview();
}

function selectConcept(conceptId, options = {}) {
  state.selectedConceptId = conceptId;
  state.selectedFigureId = null;
  state.tab = "evidence";
  updateTabs();
  document.querySelectorAll(".annotation").forEach((node) => node.classList.toggle("selected", node.dataset.conceptId === conceptId));
  renderEvidence(getConcept(conceptId));
  if (options.announce !== false) showToast(`已定位“${getConcept(conceptId).canonical_name}”的证据链`, "success");
}

function selectFigure(figureId) {
  state.selectedFigureId = figureId;
  state.selectedConceptId = null;
  state.tab = "evidence";
  updateTabs();
  renderFigure(state.data.figures.find((item) => item.figure_id === figureId));
  showToast("已打开图表候选，当前标注仍需人工复核");
}

function setTab(tab) {
  state.tab = tab;
  updateTabs();
  updatePanel();
}

function updateTabs() {
  for (const tab of elements.panelTabs) {
    const active = tab.dataset.tab === state.tab;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  }
  const selectedTab = elements.panelTabs.find((tab) => tab.dataset.tab === state.tab);
  elements.panelBody.setAttribute("aria-labelledby", selectedTab?.id || "tab-evidence");
  selectedTab?.setAttribute("tabindex", "0");
  for (const tab of elements.panelTabs) {
    if (tab !== selectedTab) tab.setAttribute("tabindex", "-1");
  }
}

function updatePanel() {
  if (!state.data) return;
  if (state.tab === "resources") {
    renderResources(state.selectedConceptId);
    return;
  }
  if (state.selectedFigureId) {
    renderFigure(state.data.figures.find((item) => item.figure_id === state.selectedFigureId));
  } else if (state.selectedConceptId) {
    renderEvidence(getConcept(state.selectedConceptId));
  } else {
    renderPageOverview();
  }
}

function renderLoadingPanel() {
  elements.panelBody.innerHTML = `<div class="panel-loading"><span></span><span></span><span></span></div>`;
}

function renderPageOverview() {
  const pageData = getPage(state.page);
  const concepts = pageData.occurrence_ids
    .map((id) => state.data.occurrences.find((item) => item.occurrence_id === id))
    .map((item) => getConcept(item.concept_id))
    .filter((item, index, all) => all.findIndex((candidate) => candidate.concept_id === item.concept_id) === index);
  elements.panelBody.innerHTML = `
    <div class="panel-intro">
      <span class="panel-kicker">本页关联</span>
      <h2>扫描第${state.page}页</h2>
      <p>点击原文中的虚线概念，查看可回跳的教材证据与权威拓展资料。</p>
    </div>
    <div class="page-facts"><div><strong>${concepts.length}</strong><span>个概念</span></div><div><strong>${pageData.figure_ids.length}</strong><span>个图表</span></div><div><strong>${pageData.text_blocks.length}</strong><span>个文本块</span></div></div>
    <div class="concept-list">${concepts.map((concept) => `<button type="button" data-concept="${concept.concept_id}"><span>${escapeHtml(concept.canonical_name)}</span><small>${concept.occurrence_count}处</small></button>`).join("") || emptyState("本页暂无核心概念", "可继续翻页查看。")}</div>
  `;
  elements.panelBody.querySelectorAll("[data-concept]").forEach((button) => button.addEventListener("click", () => selectConcept(button.dataset.concept)));
}

function renderEvidence(concept) {
  const evidence = concept.primary_evidence;
  const occurrences = state.data.occurrences.filter((item) => item.concept_id === concept.concept_id);
  const related = state.resources.filter((item) => item.concept_ids.includes(concept.concept_id));
  const reviewed = evidence.review_status === "reviewed";
  elements.panelBody.innerHTML = `
    <div class="concept-heading">
      <div><span class="panel-kicker">概念证据链</span><h2>${escapeHtml(concept.canonical_name)}</h2></div>
      <span class="status-pill ${reviewed ? "verified" : "pending"}"><svg class="icon"><use href="#i-${reviewed ? "check" : "focus"}"/></svg>${reviewed ? "教材已核验" : "待复核"}</span>
    </div>
    <div class="concept-meta"><span>本章出现 ${occurrences.length} 次</span><span>${escapeHtml(concept.aliases.join(" / "))}</span></div>
    <section class="evidence-card tier-one">
      <header><span class="tier-number">01</span><div><strong>教材原文 · 一级证据</strong><small>直接支撑本知识点</small></div></header>
      <blockquote>${escapeHtml(evidence.quote)}</blockquote>
      <div class="citation-line"><svg class="icon"><use href="#i-book"/></svg><span>${escapeHtml(evidence.source_title)} · 扫描第${evidence.page || "?"}页</span></div>
      ${evidence.target_occurrence_id ? `<button class="text-button" type="button" data-jump-evidence="${evidence.target_occurrence_id}">回到原文位置<svg class="icon"><use href="#i-chevron"/></svg></button>` : ""}
    </section>
    <section class="evidence-card tier-two">
      <header><span class="tier-number">02</span><div><strong>权威定义 · 二级证据</strong><small>标准与知识体系</small></div></header>
      <p>${escapeHtml(concept.description)}</p>
      <div class="mini-resource-list">${related.filter((item) => item.type === "authority").map(miniResource).join("") || `<span class="muted">暂无已核验权威来源</span>`}</div>
    </section>
    <section class="evidence-card tier-three">
      <header><span class="tier-number">03</span><div><strong>教学拓展 · 三级证据</strong><small>视频、代码与论文</small></div></header>
      <div class="resource-preview">${related.filter((item) => item.type !== "authority").slice(0, 3).map(resourcePreview).join("") || `<span class="muted">暂无已核验拓展资源</span>`}</div>
      <button class="text-button" type="button" data-open-resources>查看全部 ${related.filter((item) => item.type !== "authority").length} 项资源<svg class="icon"><use href="#i-chevron"/></svg></button>
    </section>
    <button class="add-material" type="button" data-add-concept="${concept.concept_id}"><svg class="icon"><use href="#i-basket"/></svg><span>加入备课素材篮</span></button>
  `;
  elements.panelBody.querySelector("[data-jump-evidence]")?.addEventListener("click", (event) => jumpToOccurrence(event.currentTarget.dataset.jumpEvidence));
  elements.panelBody.querySelector("[data-open-resources]")?.addEventListener("click", () => setTab("resources"));
  elements.panelBody.querySelector("[data-add-concept]")?.addEventListener("click", () => addConceptToBasket(concept));
}

function renderFigure(figure) {
  elements.panelBody.innerHTML = `
    <div class="concept-heading"><div><span class="panel-kicker">书中插图</span><h2>${escapeHtml(figure.figure_number)}</h2></div><span class="status-pill pending">待复核</span></div>
    <section class="figure-detail">
      <div class="figure-crop"><img src="${getPage(state.page).image}" alt="${escapeHtml(figure.caption_text)}"></div>
      <h3>${escapeHtml(figure.caption_text)}</h3>
      <p>该区域由教材图注自动定位。当前可作为备课候选素材，正式引用前仍需教师确认裁切范围。</p>
      <dl><div><dt>教材位置</dt><dd>扫描第${state.page}页 · 书页${getPage(state.page).printed_label}</dd></div><div><dt>识别置信度</dt><dd>${Math.round(figure.confidence * 100)}%</dd></div></dl>
    </section>
    <button class="add-material" type="button" data-add-figure="${figure.figure_id}"><svg class="icon"><use href="#i-basket"/></svg><span>作为插图素材加入</span></button>
  `;
  const crop = elements.panelBody.querySelector(".figure-crop img");
  const [x, y, width, height] = figure.image_boxes[0];
  crop.style.objectPosition = `${(x + width / 2) * 100}% ${(y + height / 2) * 100}%`;
  elements.panelBody.querySelector("[data-add-figure]").addEventListener("click", () => addFigureToBasket(figure));
}

function renderResources(conceptId) {
  const resources = conceptId ? state.resources.filter((item) => item.concept_ids.includes(conceptId)) : state.resources;
  const concept = conceptId ? getConcept(conceptId) : null;
  const groups = [
    ["authority", "权威来源"], ["video", "相关视频"], ["code", "开源课程与代码"], ["paper", "研究文献"],
  ];
  elements.panelBody.innerHTML = `
    <div class="panel-intro"><span class="panel-kicker">精选且真实可访问</span><h2>${concept ? `“${escapeHtml(concept.canonical_name)}”的拓展资源` : "第一章资源"}</h2><p>所有条目均为直达链接，并记录关联理由与校验日期。</p></div>
    <div class="verified-banner"><svg class="icon"><use href="#i-check"/></svg><span>最近校验：2026-07-15</span></div>
    ${groups.map(([type, label]) => {
      const items = resources.filter((item) => item.type === type);
      if (!items.length) return "";
      return `<section class="resource-group"><h3>${label}<span>${items.length}</span></h3>${items.map(resourceCard).join("")}</section>`;
    }).join("") || emptyState("暂无关联资源", "该概念还没有通过校验的外部资料。")}
  `;
  elements.panelBody.querySelectorAll("[data-add-resource]").forEach((button) => {
    button.addEventListener("click", () => addResourceToBasket(state.resources.find((item) => item.resource_id === button.dataset.addResource)));
  });
}

function resourceCard(resource) {
  const url = safeUrl(resource.url);
  return `<article class="resource-card">
    <div class="resource-top"><span class="platform ${safeToken(resource.type)}">${escapeHtml(resource.platform)}</span><span class="resource-status"><svg class="icon"><use href="#i-check"/></svg>可访问</span></div>
    <h4><a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(resource.title)}<svg class="icon"><use href="#i-external"/></svg></a></h4>
    ${resource.meta ? `<p class="resource-meta">${escapeHtml(resource.meta)}</p>` : ""}
    <p>${escapeHtml(resource.relation_reason)}</p>
    <button type="button" data-add-resource="${escapeHtml(resource.resource_id)}"><svg class="icon"><use href="#i-basket"/></svg>加入素材</button>
  </article>`;
}

function miniResource(resource) {
  return `<a href="${escapeHtml(safeUrl(resource.url))}" target="_blank" rel="noreferrer"><span>${escapeHtml(resource.platform)}</span><strong>${escapeHtml(resource.title)}</strong><svg class="icon"><use href="#i-external"/></svg></a>`;
}

function resourcePreview(resource) {
  return `<a href="${escapeHtml(safeUrl(resource.url))}" target="_blank" rel="noreferrer"><span class="platform ${safeToken(resource.type)}">${escapeHtml(resource.platform)}</span><strong>${escapeHtml(resource.title)}</strong></a>`;
}

function jumpToOccurrence(occurrenceId) {
  const occurrence = state.data.occurrences.find((item) => item.occurrence_id === occurrenceId);
  if (!occurrence) return;
  const page = Number(occurrence.page_id.split(":").at(-1));
  setPage(page).then(() => {
    selectConcept(occurrence.concept_id, { announce: false });
    const target = document.querySelector(`[data-occurrence-id="${CSS.escape(occurrence.occurrence_id)}"]`);
    target?.focus({ preventScroll: true });
    target?.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
    target?.classList.add("pulse");
    setTimeout(() => target?.classList.remove("pulse"), 800);
  });
}

function addConceptToBasket(concept) {
  addBasketItem({ id: concept.concept_id, type: "concept", title: concept.canonical_name, subtitle: `教材证据 · 本章${concept.occurrence_count}处` });
}

function addFigureToBasket(figure) {
  addBasketItem({ id: figure.figure_id, type: "figure", title: figure.figure_number, subtitle: `扫描第${state.page}页 · 待复核裁切` });
}

function addResourceToBasket(resource) {
  addBasketItem({ id: resource.resource_id, type: "resource", title: resource.title, subtitle: `${resource.platform} · 已校验` });
}

function addBasketItem(item) {
  if (state.basket.some((candidate) => candidate.id === item.id)) {
    showToast("该素材已在备课篮中");
    return;
  }
  state.basket.push({ ...item, createdAt: new Date().toISOString() });
  saveBasket();
  renderBasket();
  showToast(`“${item.title}”已加入备课篮`, "success");
}

function removeBasketItem(id) {
  state.basket = state.basket.filter((item) => item.id !== id);
  saveBasket();
  renderBasket();
}

function renderBasket() {
  elements.basketCount.textContent = state.basket.length;
  elements.basketDescription.textContent = state.basket.length ? `已收集 ${state.basket.length} 项可溯源素材` : "从原文证据和拓展资源中收集素材";
  elements.basketItems.innerHTML = state.basket.map((item) => `
    <div class="basket-chip"><span class="chip-type">${item.type === "concept" ? "概念" : item.type === "figure" ? "插图" : "资源"}</span><span>${escapeHtml(item.title)}</span><button type="button" data-remove-basket="${escapeHtml(item.id)}" aria-label="移除${escapeHtml(item.title)}"><svg class="icon"><use href="#i-close"/></svg></button></div>
  `).join("");
  elements.basketItems.querySelectorAll("[data-remove-basket]").forEach((button) => button.addEventListener("click", () => removeBasketItem(button.dataset.removeBasket)));
}

function toggleBasket() {
  const bar = document.querySelector("#basket-bar");
  const expanded = bar.classList.toggle("expanded");
  document.querySelector("#basket-summary").setAttribute("aria-expanded", String(expanded));
}

function renderSearchResults() {
  const query = elements.search.value.trim().toLowerCase();
  if (!query) {
    renderToc();
    return;
  }
  const concepts = state.data.concepts.filter((concept) => [concept.canonical_name, ...concept.aliases].some((text) => text.toLowerCase().includes(query)));
  elements.toc.innerHTML = concepts.length ? `<div class="search-result-label">找到 ${concepts.length} 个概念</div>${concepts.map((concept) => `
    <button class="search-result" type="button" data-search-concept="${concept.concept_id}"><span><strong>${highlight(concept.canonical_name, query)}</strong><small>本章出现 ${concept.occurrence_count} 次</small></span><svg class="icon"><use href="#i-chevron"/></svg></button>
  `).join("")}` : emptyState("未找到概念", "换一个关键词试试。", "compact");
  elements.toc.querySelectorAll("[data-search-concept]").forEach((button) => button.addEventListener("click", () => {
    const occurrence = state.data.occurrences.find((item) => item.concept_id === button.dataset.searchConcept);
    if (occurrence) jumpToOccurrence(occurrence.occurrence_id);
  }));
}

function updatePageButtons() {
  const atStart = state.page <= state.data.book.page_start;
  const atEnd = state.page >= state.data.book.page_end;
  for (const id of ["prev-page", "edge-prev"]) document.querySelector(`#${id}`).disabled = atStart;
  for (const id of ["next-page", "edge-next"]) document.querySelector(`#${id}`).disabled = atEnd;
}

function toggleDrawer(side, open) {
  document.querySelector(`#${side}-rail, #${side}-panel`)?.classList.toggle("drawer-open", open);
  document.body.classList.toggle("drawer-active", open);
  elements.scrim.classList.toggle("show", open);
}

function closeDrawers() {
  document.querySelector("#left-rail").classList.remove("drawer-open");
  document.querySelector("#right-panel").classList.remove("drawer-open");
  document.body.classList.remove("drawer-active");
  elements.scrim.classList.remove("show");
}

function getPage(page) { return state.data?.pages.find((item) => item.scan_index === page); }
function getSection(id) { return state.data.sections.find((item) => item.section_id === id); }
function getConcept(id) { return state.data.concepts.find((item) => item.concept_id === id); }
function pageInSection(page, section) { return page >= section.page_start && page <= section.page_end; }

function loadBasket() {
  try {
    const value = JSON.parse(localStorage.getItem(BASKET_KEY));
    if (!Array.isArray(value)) return [];
    return value.filter((item) => item && typeof item.id === "string" && typeof item.title === "string" && ["concept", "figure", "resource"].includes(item.type));
  }
  catch { return []; }
}

function saveBasket() { localStorage.setItem(BASKET_KEY, JSON.stringify(state.basket)); }

function emptyState(title, description, variant = "") {
  return `<div class="empty-state ${variant}"><span></span><strong>${escapeHtml(title)}</strong><p>${escapeHtml(description)}</p></div>`;
}

function showToast(message, tone = "") {
  elements.toast.textContent = message;
  elements.toast.className = `toast show ${tone}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { elements.toast.className = "toast"; }, 2800);
}

function highlight(text, query) {
  const safe = escapeHtml(text);
  const index = text.toLowerCase().indexOf(query);
  if (index < 0) return safe;
  return `${escapeHtml(text.slice(0, index))}<mark>${escapeHtml(text.slice(index, index + query.length))}</mark>${escapeHtml(text.slice(index + query.length))}`;
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

function safeUrl(value) {
  try {
    const url = new URL(value, location.href);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : "#";
  } catch { return "#"; }
}

function safeToken(value) {
  return /^[a-z0-9-]+$/i.test(value || "") ? value : "unknown";
}

function debounce(callback, delay) {
  let timeout;
  return (...args) => { clearTimeout(timeout); timeout = setTimeout(() => callback(...args), delay); };
}
