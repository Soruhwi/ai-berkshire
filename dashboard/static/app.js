"use strict";

const DEFAULT_WATCHLIST = [
  { code: "005930", name: "삼성전자" },
  { code: "000660", name: "SK하이닉스" },
  { code: "373220", name: "LG에너지솔루션" },
  { code: "005380", name: "현대차" },
  { code: "035420", name: "NAVER" },
  { code: "035720", name: "카카오" },
  { code: "000270", name: "기아" },
  { code: "068270", name: "셀트리온" },
];

const main = document.getElementById("main");
let treeData = [];
let reportCfg = { available: false, kinds: [] };

// ---- 유틸 ----
async function getJSON(url) {
  const r = await fetch(url);
  return r.json();
}
function loadWatchlist() {
  try {
    const s = JSON.parse(localStorage.getItem("aib_watchlist"));
    if (Array.isArray(s) && s.length) return s;
  } catch (e) {}
  return DEFAULT_WATCHLIST.slice();
}
function saveWatchlist(w) { localStorage.setItem("aib_watchlist", JSON.stringify(w)); }
function chgClass(rate) {
  const v = parseFloat(rate);
  if (isNaN(v) || v === 0) return "flat";
  return v > 0 ? "up" : "down";
}
function chgSign(rate) {
  const v = parseFloat(rate);
  return (v > 0 ? "▲ +" : v < 0 ? "▼ " : "") + rate + "%";
}

// ---- 관심종목 ----
function renderChips() {
  const wl = loadWatchlist();
  const box = document.getElementById("chips");
  box.innerHTML = "";
  wl.forEach((s) => {
    const c = document.createElement("div");
    c.className = "chip";
    c.textContent = s.name || s.code;
    c.title = s.code;
    c.onclick = () => showStock(s.code);
    box.appendChild(c);
  });
}
function inWatchlist(code) { return loadWatchlist().some((s) => s.code === code); }
function addWatch(s) {
  const wl = loadWatchlist();
  if (!wl.some((x) => x.code === s.code)) { wl.push(s); saveWatchlist(wl); renderChips(); }
}
function removeWatch(code) {
  saveWatchlist(loadWatchlist().filter((s) => s.code !== code));
  renderChips();
}

// ---- 기본 화면: 관심종목 실시간 ----
async function showWatchlist() {
  setActiveFile(null);
  const wl = loadWatchlist();
  main.innerHTML = `<h2 class="section-title">📈 관심종목 실시간</h2>
    <p class="hint">카드를 클릭하면 상세(밸류에이션·재무)로 이동합니다. 종목은 상단 검색에서 추가할 수 있어요.</p>
    <div class="grid" id="wlgrid"><div class="loading">시세 불러오는 중…</div></div>`;
  const grid = document.getElementById("wlgrid");
  const cards = await Promise.all(wl.map((s) => getJSON(`/api/krx/quote?code=${s.code}`).catch(() => null)));
  grid.innerHTML = "";
  cards.forEach((q, i) => {
    if (!q || q.error) {
      grid.insertAdjacentHTML("beforeend",
        `<div class="card"><div class="name">${wl[i].name}</div><div class="code">${wl[i].code}</div><div class="err">데이터 오류</div></div>`);
      return;
    }
    const el = document.createElement("div");
    el.className = "card";
    el.onclick = () => showStock(q.code);
    el.innerHTML = `
      <span class="x" title="관심종목 제거">✕</span>
      <div class="name">${q.name}</div>
      <div class="code">${q.code} · ${q.exchange}</div>
      <div class="price">${q.price} <span style="font-size:12px;color:var(--muted)">${q.currency}</span></div>
      <div class="chg ${chgClass(q.changeRate)}">${chgSign(q.changeRate)} (${q.change})</div>
      <div class="meta"><span>시총 ${q.marketCap}</span><span>거래량 ${q.volume}</span></div>`;
    el.querySelector(".x").onclick = (ev) => { ev.stopPropagation(); removeWatch(q.code); showWatchlist(); };
    grid.appendChild(el);
  });
}

// ---- 종목 상세 ----
async function showStock(code) {
  setActiveFile(null);
  main.innerHTML = `<div class="loading">종목 데이터 불러오는 중… (${code})</div>`;
  const [q, v, f] = await Promise.all([
    getJSON(`/api/krx/quote?code=${code}`).catch(() => null),
    getJSON(`/api/krx/valuation?code=${code}`).catch(() => null),
    getJSON(`/api/krx/financials?code=${code}`).catch(() => null),
  ]);
  if (!q || q.error) { main.innerHTML = `<div class="err">시세를 가져오지 못했습니다: ${code}</div>`; return; }

  const M = (v && v.metrics) || {};
  const valItems = [
    ["시가총액", M.marketValue], ["PER(실적)", M.per], ["PER(추정)", M.cnsPer],
    ["EPS", M.eps], ["PBR", M.pbr], ["BPS", M.bps],
    ["배당수익률", M.dividendYieldRatio], ["외국인소진율", M.foreignRate],
    ["52주 최고", M.highPriceOf52Weeks], ["52주 최저", M.lowPriceOf52Weeks],
  ].filter(([, val]) => val != null);

  let finHtml = "";
  if (f && f.rows && f.rows.length) {
    finHtml = `<h3>핵심 재무 (연간 · ${f.unit})</h3><table class="fin"><thead><tr><th>항목</th>${
      f.periods.map((p) => `<th>${p}</th>`).join("")}</tr></thead><tbody>${
      f.rows.map((r) => `<tr><td>${r.title}</td>${r.values.map((x) => `<td>${x}</td>`).join("")}</tr>`).join("")
    }</tbody></table>`;
  }

  const addBtn = inWatchlist(code) ? "" :
    `<button id="addw" style="margin-left:10px;padding:5px 12px;border-radius:6px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);cursor:pointer">+ 관심종목</button>`;

  main.innerHTML = `<div class="detail">
    <div class="crumb"><a href="#" id="backwl">← 관심종목</a></div>
    <h2>${q.name} <span style="color:var(--muted);font-size:15px">${q.code} · ${q.exchange}</span>${addBtn}</h2>
    <div class="price" style="font-size:30px;font-weight:800">${q.price} <span style="font-size:14px;color:var(--muted)">${q.currency}</span>
      <span class="chg ${chgClass(q.changeRate)}" style="font-size:16px">${chgSign(q.changeRate)} (${q.change})</span></div>
    <div class="kv">
      ${[["시가",q.open],["고가",q.high],["저가",q.low],["거래량",q.volume],["거래대금",q.tradingValue],["시가총액",q.marketCap]]
        .map(([k,val])=>`<div class="item"><div class="k">${k}</div><div class="v">${val}</div></div>`).join("")}
    </div>
    <h3>밸류에이션</h3>
    <div class="kv">${valItems.map(([k,val])=>`<div class="item"><div class="k">${k}</div><div class="v">${val}</div></div>`).join("")}</div>
    ${finHtml}
    <div id="aiReport" class="ai-report"></div>
    <p class="hint" style="margin-top:18px">출처: 네이버금융 · krx_data.py · 체결 ${q.tradedAt || "-"}</p>
  </div>`;
  document.getElementById("backwl").onclick = (e) => { e.preventDefault(); showWatchlist(); };
  const ab = document.getElementById("addw");
  if (ab) ab.onclick = () => { addWatch({ code: q.code, name: q.name }); ab.remove(); };
  renderReportPanel(q.code, q.name);
}

// ---- AI 리포트 생성 패널 ----
function renderReportPanel(code, name) {
  const box = document.getElementById("aiReport");
  if (!box) return;
  if (!reportCfg.available) {
    box.innerHTML = `<h3>🤖 AI 리포트 생성</h3><p class="hint">claude CLI를 찾지 못해 비활성화됨. Claude Code 설치 후 서버를 재시작하세요.</p>`;
    return;
  }
  const opts = reportCfg.kinds.map((k) => `<option value="${k.id}">${k.label}</option>`).join("");
  box.innerHTML = `<h3>🤖 AI 리포트 생성</h3>
    <p class="hint">4대가 워크플로를 실제로 가동해 ${name} 리포트를 생성하고 <code>reports/${name}/</code> 에 저장합니다. 종류에 따라 수 분 소요.</p>
    <div class="ai-controls">
      <select id="aiKind">${opts}</select>
      <button id="aiGo">생성 시작</button>
    </div>
    <div id="aiStatus" class="ai-status"></div>`;
  document.getElementById("aiGo").onclick = () => generateReport(code, name);
}

async function generateReport(code, name) {
  const kind = document.getElementById("aiKind").value;
  const btn = document.getElementById("aiGo");
  const st = document.getElementById("aiStatus");
  btn.disabled = true;
  st.innerHTML = `<span class="spin"></span> 작업 생성 중…`;
  let res;
  try {
    res = await fetch("/api/report/generate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, name, kind }),
    }).then((r) => r.json());
  } catch (e) { st.innerHTML = `<span class="err">요청 실패</span>`; btn.disabled = false; return; }
  if (res.error) { st.innerHTML = `<span class="err">${res.error}</span>`; btn.disabled = false; return; }
  pollReport(res.id, st, btn, Date.now());
}

function pollReport(id, st, btn, t0) {
  const tick = async () => {
    const j = await getJSON(`/api/report/status?id=${id}`).catch(() => null);
    const secs = Math.round((Date.now() - t0) / 1000);
    if (!j) { st.innerHTML = `<span class="err">상태 조회 실패</span>`; btn.disabled = false; return; }
    if (j.status === "running") {
      st.innerHTML = `<span class="spin"></span> 생성 중… (${j.kindLabel}, ${secs}초 경과) — 워크플로가 데이터를 수집/분석 중입니다.`;
      setTimeout(tick, 3000);
    } else if (j.status === "done") {
      st.innerHTML = `✅ 완료 (${secs}초, ${j.chars.toLocaleString()}자) → <a href="#" id="openRep">리포트 열기</a> <span class="hint">${j.path}</span>`;
      document.getElementById("openRep").onclick = (e) => { e.preventDefault(); loadTree().then(() => showReport(j.path)); };
      btn.disabled = false;
    } else {
      st.innerHTML = `<span class="err">실패: ${j.error || "알 수 없음"}</span>`;
      btn.disabled = false;
    }
  };
  tick();
}

// ---- 리포트 트리 ----
function renderTree(nodes, container) {
  nodes.forEach((n) => {
    if (n.type === "dir") {
      const d = document.createElement("details");
      const s = document.createElement("summary");
      s.innerHTML = `<span class="ico">▸</span>${n.name}`;
      d.appendChild(s);
      renderTree(n.children, d);
      container.appendChild(d);
    } else {
      const a = document.createElement("a");
      a.className = "file";
      a.textContent = n.name.replace(/\.md$/, "");
      a.dataset.path = n.path;
      a.title = n.path;
      a.onclick = () => showReport(n.path);
      container.appendChild(a);
    }
  });
}
function setActiveFile(path) {
  document.querySelectorAll(".tree .file").forEach((el) =>
    el.classList.toggle("active", el.dataset.path === path));
}
async function loadTree() {
  treeData = await getJSON("/api/tree");
  const box = document.getElementById("tree");
  box.innerHTML = "";
  renderTree(treeData, box);
}
function filterTree(term) {
  term = term.trim().toLowerCase();
  document.querySelectorAll("#tree .file").forEach((el) => {
    const hit = !term || el.textContent.toLowerCase().includes(term);
    el.style.display = hit ? "" : "none";
  });
  // 매치가 있는 폴더만 펼치기
  document.querySelectorAll("#tree details").forEach((d) => {
    const any = Array.from(d.querySelectorAll(".file")).some((f) => f.style.display !== "none");
    d.open = !!term && any;
    d.style.display = (term && !any) ? "none" : "";
  });
}

async function showReport(path) {
  setActiveFile(path);
  main.innerHTML = `<div class="loading">리포트 불러오는 중…</div>`;
  const data = await getJSON(`/api/file?path=${encodeURIComponent(path)}`).catch(() => null);
  if (!data || data.error) { main.innerHTML = `<div class="err">리포트를 열 수 없습니다.</div>`; return; }
  const html = window.marked ? marked.parse(data.markdown) : `<pre>${data.markdown.replace(/</g, "&lt;")}</pre>`;
  main.innerHTML = `<div class="report"><div class="crumb">📄 ${path}</div>${html}</div>`;
  main.scrollTop = 0;
}

// ---- 검색 ----
let searchTimer = null;
function wireSearch() {
  const input = document.getElementById("q");
  const box = document.getElementById("results");
  input.addEventListener("input", () => {
    clearTimeout(searchTimer);
    const term = input.value.trim();
    if (!term) { box.style.display = "none"; return; }
    searchTimer = setTimeout(async () => {
      const items = await getJSON(`/api/krx/search?q=${encodeURIComponent(term)}`).catch(() => []);
      if (!items.length) { box.style.display = "none"; return; }
      box.innerHTML = items.map((it) =>
        `<div data-code="${it.code}" data-name="${it.name}"><span>${it.name}</span><span class="tag">${it.code} · ${it.type}</span></div>`).join("");
      box.style.display = "block";
      box.querySelectorAll("div[data-code]").forEach((el) => {
        el.onclick = () => {
          box.style.display = "none"; input.value = "";
          showStock(el.dataset.code);
        };
      });
    }, 250);
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search")) box.style.display = "none";
  });
}

// ---- 시작 ----
(async function init() {
  if (window.marked) marked.setOptions({ gfm: true, breaks: false });
  reportCfg = await getJSON("/api/report/available").catch(() => reportCfg);
  renderChips();
  loadTree();
  wireSearch();
  document.getElementById("treeFilter").addEventListener("input", (e) => filterTree(e.target.value));
  showWatchlist();
})();
