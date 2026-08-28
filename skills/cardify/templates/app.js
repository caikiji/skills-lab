// 读内嵌卡片数据并渲染三种视图：卡片流 / 关系图 / 大纲
const DATA = JSON.parse(document.getElementById("cards-data").textContent);
const TYPE_COLORS = {
  "总卡": "#8b95a3",
  "概念卡": "#3b82f6",
  "流程卡": "#10b981",
  "决策卡": "#f59e0b",
  "陷阱卡": "#ef4444",
  "接口卡": "#8b5cf6",
};
const cards = DATA.cards.slice().sort((a, b) => a.num - b.num);
const root = cards.find((c) => c.type === "总卡");
const cardByTitle = new Map(cards.map((c) => [c.title, c.num]));

document.getElementById("topic").textContent = DATA.topic;
document.getElementById("page-title").textContent = DATA.topic + " · 卡片视图";

// 脚本错误可见化：顶部红条显示错误，避免静默空白
window.addEventListener("error", (e) => {
  const bar = document.createElement("div");
  bar.style.cssText = "position:fixed;top:0;left:0;right:0;background:#ef4444;color:#fff;" +
    "padding:6px 12px;z-index:99;font-size:13px;";
  bar.textContent = "脚本错误: " + (e.message || e.type);
  document.body.prepend(bar);
});

function esc(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
  return String(text).replace(/[&<>"]/g, (ch) => map[ch]);
}

// ---- 代码高亮（逐行：截断片段状态不跨行泄漏，不会串色）----
const LANG_BY_EXT = {
  go: "go", py: "python", js: "javascript", mjs: "javascript", cjs: "javascript",
  ts: "typescript", c: "c", h: "c", cpp: "cpp", cc: "cpp", hpp: "cpp",
  java: "java", rs: "rust", sh: "bash", bash: "bash", json: "json",
  xml: "xml", yaml: "yaml", yml: "yaml", sql: "sql", lua: "lua", md: "markdown",
};

function langOf(file) {
  const ext = String(file || "").split(".").pop().toLowerCase();
  return LANG_BY_EXT[ext] || "";
}

function highlightLine(line, lang) {
  if (lang && hljs.getLanguage(lang)) {
    try { return hljs.highlight(line, { language: lang }).value; } catch (e) { /* 降级原文 */ }
  }
  return esc(line);
}

function highlightCode(block, lang) {
  return block.text.split("\n").map((line, i) =>
    '<span class="cl" data-ln="' + (block.start + i) + '">' +
    highlightLine(line, lang) + "</span>").join("\n");
}

function codeRefLabel(block) {
  return block.start === block.end
    ? block.file + ":" + block.start
    : block.file + ":" + block.start + "~" + block.end;
}

function matchBlock(card, anchorText) {
  const m = anchorText.match(/([\w./\\-]+):(\d+)(?:~(\d+))?/);
  if (!m) return null;
  const start = parseInt(m[2], 10);
  const end = m[3] ? parseInt(m[3], 10) : start;
  return (card.codeBlocks || []).findIndex((b) =>
    b.file === m[1] && b.start === start && b.end === end);
}

function renderText(card, text) {
  // 锚点渲染为弱化小字；命中代码块时加联动引用
  let html = "";
  let last = 0;
  const re = /（[^（）]*）/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    html += esc(text.slice(last, m.index));
    const idx = matchBlock(card, m[0].slice(1, -1));
    const ref = idx !== null ? ' data-ref="' + card.num + "-" + idx + '"' : "";
    html += '<span class="anchor"' + ref + ">" + esc(m[0]) + "</span>";
    last = m.index + m[0].length;
  }
  return html + esc(text.slice(last));
}

function cardHtml(card) {
  const color = TYPE_COLORS[card.type] || "#888";
  const points = card.points.map((p) => {
    if (card.type === "总卡" && cardByTitle.has(p)) {
      return '<li><a class="goto" data-goto="' + cardByTitle.get(p) + '">' + esc(p) + "</a></li>";
    }
    return "<li>" + renderText(card, p) + "</li>";
  }).join("");
  const links = []
    .concat(card.linksIn.map((n) => "← 卡" + n), card.linksOut.map((n) => "→ 卡" + n))
    .map((t) => '<a data-link="' + t.match(/\d+/)[0] + '">' + t + "</a>")
    .join("");
  return [
    '<article class="card" style="--type-color:' + color + '" data-num="' + card.num + '">',
    '<div class="head"><span class="num">卡 ' + card.num + "/" + DATA.total + "</span>",
    '<span class="badge">' + esc(card.type) + "</span><h2>" + esc(card.title) + "</h2></div>",
    '<p class="one">' + renderText(card, card.one) + "</p>",
    "<ul>" + points + "</ul>",
    card.code
      ? '<details class="handcode"><summary>代码</summary><pre><code>' + esc(card.code) + "</code></pre></details>"
      : "",
    links ? '<div class="links">' + links + "</div>" : "",
    "</article>",
  ].join("\n");
}

// ---- 卡片流 ----
document.getElementById("view-flow").innerHTML = cards.map(cardHtml).join("");

// ---- 大纲（纯目录：总卡概要 + 子卡标题列表，点击跳卡片流）----
document.getElementById("view-outline").innerHTML =
  '<div class="outline-root" style="--type-color:' + TYPE_COLORS["总卡"] + '">' +
  '<div class="head"><span class="badge">总卡</span><h2>' + esc(root.title) + "</h2></div>" +
  '<p class="one">' + esc(root.one) + "</p></div>" +
  cards.filter((c) => c.type !== "总卡").map((c) =>
    '<div class="outline-item" data-goto="' + c.num + '" style="--type-color:' +
    (TYPE_COLORS[c.type] || "#888") + '"><span class="badge">' + esc(c.type) +
    '</span><strong>' + esc(c.title) + '</strong><span class="oi-one">' +
    esc(c.one) + "</span></div>").join("");

// ---- 关系图 ----
let network = null;
let hierarchical = false;

function showDetail(card) {
  const box = document.getElementById("graph-detail");
  box.innerHTML = cardHtml(card);
  box.classList.remove("hidden");
}

function buildGraph() {
  // 同步创建：switchView 已把容器切为可见，同步读尺寸会强制布局，不会拿到 0。
  // 不用 requestAnimationFrame：后台/隐藏 tab 中 rAF 完全暂停，图会永远空白。
  const container = document.getElementById("graph");
  const nodes = new vis.DataSet(cards.map((c) => ({
    id: c.num,
    label: "卡" + c.num + " " + c.title,
    shape: "box",
    margin: 10,
    color: {
      background: TYPE_COLORS[c.type] || "#888",
      border: TYPE_COLORS[c.type] || "#888",
      highlight: { background: TYPE_COLORS[c.type] || "#888", border: "#ffffff" },
    },
    font: { color: "#ffffff", size: 14 },
    card: c,
  })));
  const edges = new vis.DataSet();
  cards.forEach((c) => {
    c.linksOut.forEach((t) => {
      const viaRoot = c.num === root.num || t === root.num;
      edges.add({
        from: c.num, to: t, arrows: "to",
        dashes: viaRoot,
        color: viaRoot ? { color: "#9aa1a9", opacity: 0.45 } : { color: TYPE_COLORS[c.type] },
      });
    });
  });
  const options = {
    layout: { improvedLayout: true },
    physics: { enabled: true, solver: "forceAtlas2Based" },
    interaction: { hover: true },
  };
  network = new vis.Network(container, { nodes, edges }, options);
  network.on("click", (params) => {
    if (params.nodes.length === 0) return;
    showDetail(nodes.get(params.nodes[0]).card);
  });
  network.once("afterDrawing", () => network.redraw());
}

document.getElementById("btn-layout").addEventListener("click", () => {
  if (!network) return;
  hierarchical = !hierarchical;
  network.setOptions(hierarchical
    ? { layout: { hierarchical: { enabled: true, direction: "UD", sortMethod: "hubsize",
        levelSeparation: 150, nodeSpacing: 110, treeSpacing: 180 } }, physics: { enabled: false } }
    : { layout: { hierarchical: { enabled: false }, improvedLayout: true },
        physics: { enabled: true, solver: "forceAtlas2Based" } });
  document.getElementById("btn-layout").textContent =
    "布局：" + (hierarchical ? "分层" : "力导向");
});

// ---- 代码浮层 ----
const pop = document.getElementById("code-pop");
const backdrop = document.getElementById("code-backdrop");
const popFile = document.getElementById("pop-file");
const popCode = document.getElementById("pop-code");

function openPop(cardNum, idx) {
  const card = cards.find((c) => c.num === cardNum);
  const block = card && card.codeBlocks && card.codeBlocks[idx];
  if (!block) return;
  popFile.textContent = codeRefLabel(block);
  popCode.innerHTML = highlightCode(block, langOf(block.file));
  backdrop.classList.remove("hidden");
  pop.classList.remove("hidden");
}

function closePop() {
  pop.classList.add("hidden");
  backdrop.classList.add("hidden");
}

backdrop.addEventListener("click", closePop);
document.getElementById("pop-close").addEventListener("click", closePop);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closePop();
});

// ---- 视图切换与跳转 ----
const tabs = document.querySelectorAll(".tab");
function switchView(name) {
  tabs.forEach((t) => t.classList.toggle("active", t.dataset.view === name));
  document.querySelectorAll(".view").forEach((v) =>
    v.classList.toggle("active", v.id === "view-" + name));
  if (name === "graph") {
    if (!network) buildGraph();
    else network.redraw();
  }
}
tabs.forEach((t) => t.addEventListener("click", () => switchView(t.dataset.view)));

function gotoCard(num) {
  switchView("flow");
  const target = document.querySelector('#view-flow [data-num="' + num + '"]');
  if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.addEventListener("click", (e) => {
  const anchor = e.target.closest(".anchor[data-ref]");
  if (anchor) {
    const ref = anchor.dataset.ref.split("-");
    openPop(parseInt(ref[0], 10), parseInt(ref[1], 10));
    return;
  }
  const link = e.target.closest("a[data-link]");
  if (link) {
    gotoCard(parseInt(link.dataset.link, 10));
    return;
  }
  const item = e.target.closest("[data-goto]");
  if (item) {
    gotoCard(parseInt(item.dataset.goto, 10));
    return;
  }
  if (!e.target.closest(".code-pop") && !e.target.closest(".anchor")) closePop();
});

// ---- 初始视图：URL hash 直达（#flow / #graph / #outline）----
const initial = (location.hash || "#flow").slice(1);
if (["flow", "graph", "outline"].includes(initial)) switchView(initial);
