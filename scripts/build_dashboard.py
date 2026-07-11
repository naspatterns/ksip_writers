#!/usr/bin/env python3
"""data/를 읽어 GitHub Pages용 정적 대시보드(docs/)를 생성한다.

구성: 상단 제목 배너 + 왼쪽 섹션 탭 + 콘텐츠.
페이지·차트 (11개, 논문 그림과 동일 구성):
  index.html(개관)             — overview_chart(연도별 발행수)
  core-authors.html(핵심 필진) — asymmetry_chart(필자·논문 비대칭) · top_authors_chart(상위 필자)
                               · activity_chart(활동 필자) · stockflow_chart(유입·이탈)
  department.html(인도철학과)  — dept_composition_chart(출신 3막대·조각 호버 연동)
                               · dept_share_chart(비중 추이 3선) · dept_flow_chart(발산 막대)
  commitment.html(헌신성)      — debut_chart(데뷔 코호트) · kci_activity_chart(KCI 활동·게재)
                               · devotion_chart(평균 헌신도)

차트 공통 규격:
  - 조절 변수 1–2개 (버튼 그룹) — 데이터를 페이지에 임베드해 JS 실시간 재계산
    · 공용 임베드: KSIP_AY(주저자별 연도) · KSIP_AS(+출신 여부) · KSIP_KCI(핵심 70명 KCI 출판)
  - 캡처 버튼: PNG(4배율, 흰 배경) + SVG — 사용자가 조절한 현재 상태 그대로 저장
  - 그래프 아래 원본 데이터 링크(GitHub 파일 페이지, 새 탭) — 설명과 줄바꿈 분리
  - 해석적 설명 없음. 범례·각주는 의미 왜곡을 막는 최소한만.
  - 웹폰트 로드 후 재렌더링(document.fonts.ready) — 한글 범례 겹침 방지
  - 잠정 구간(마지막 bin)은 빗금·점선·빈 마커, 구간 눈금은 "1989–92" 형식

검증: 각 차트의 기본값(4년·3편) 수치는 graph/ 폴더의 논문 그림 스크립트가
가진 assert 검증값과 대조를 마쳤다 (커밋 이력 참조).

사용법:
    python3 scripts/build_dashboard.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = "https://github.com/naspatterns/ksip_writers"

# 논문 표지 팔레트
INK = "#1C1B19"
GOLD = "#B8911F"
MUTED = "#6E675C"
GRID = "#E4E2DA"
BARBG = "#EFE9DA"
PAPER = "#FAF9F5"

PAGES = [
    ("index.html", "개관"),
    ("core-authors.html", "핵심 필진"),
    ("department.html", "인도철학과"),
    ("commitment.html", "헌신성"),
]

CSS = f"""
  :root {{ --ink:{INK}; --gold:{GOLD}; --muted:{MUTED}; --grid:{GRID}; --paper:{PAPER}; --barbg:{BARBG}; }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ background:var(--paper); color:var(--ink); font-family:'Noto Sans KR',sans-serif;
         line-height:1.7; -webkit-font-smoothing:antialiased; }}
  a {{ color:var(--ink); }}

  /* 상단 배너 */
  .banner {{ border-bottom:1px solid var(--grid); padding:28px 32px 22px; }}
  .banner .kicker {{ color:var(--gold); font-weight:700; letter-spacing:.14em; font-size:.75rem; }}
  .banner h1 {{ font-family:'Noto Serif KR',serif; font-size:clamp(1.15rem,2.6vw,1.6rem); line-height:1.4; margin:.2em 0 .1em; }}
  .banner .subtitle {{ color:var(--muted); font-size:.88rem; }}

  /* 좌측 탭 + 콘텐츠 */
  .frame {{ display:flex; min-height:calc(100vh - 110px); }}
  nav {{ width:172px; flex:none; padding:28px 0 28px 20px; }}
  nav a {{ display:block; padding:9px 14px; margin-bottom:2px; text-decoration:none; color:var(--muted);
          border-left:2px solid transparent; font-size:.95rem; }}
  nav a:hover {{ color:var(--ink); }}
  nav a.on {{ color:var(--ink); font-weight:700; border-left-color:var(--gold); }}
  main {{ flex:1; min-width:0; padding:28px 32px 64px; max-width:1000px; }}

  /* 차트 패널 */
  .panel {{ background:#fff; border:1px solid var(--grid); border-radius:12px; padding:22px 24px; margin-bottom:28px; }}
  .panel h2 {{ font-family:'Noto Serif KR',serif; font-size:1.12rem; margin-bottom:2px; }}
  .panel-bar {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px 18px; margin:10px 0 4px; }}
  .ctl {{ display:flex; align-items:center; gap:6px; }}
  .ctl-label {{ color:var(--muted); font-size:.8rem; }}
  .seg {{ display:inline-flex; border:1px solid var(--grid); border-radius:8px; overflow:hidden; }}
  .seg button {{ border:0; background:#fff; padding:4px 12px; font:inherit; font-size:.82rem;
                color:var(--muted); cursor:pointer; }}
  .seg button + button {{ border-left:1px solid var(--grid); }}
  .seg button.on {{ background:var(--barbg); color:var(--ink); font-weight:500; }}
  .dl {{ margin-left:auto; display:flex; gap:6px; }}
  .dl button {{ border:1px solid var(--grid); border-radius:8px; background:#fff; padding:4px 12px;
               font:inherit; font-size:.82rem; color:var(--muted); cursor:pointer; }}
  .dl button:hover {{ color:var(--ink); border-color:var(--muted); }}
  .panel-foot {{ margin-top:8px; color:var(--muted); font-size:.8rem; }}
  .panel-foot a {{ color:var(--muted); }}
  .names-box {{ margin-top:12px; padding:11px 14px; border:1px solid var(--grid);
               border-radius:8px; background:var(--barbg); min-height:3.1em; font-size:.86rem; }}
  .names-box .nb-head {{ font-size:.8rem; margin-bottom:5px; }}
  .names-box .nb-names {{ color:var(--ink); line-height:1.75; }}
  .names-box .nb-hint {{ color:var(--muted); }}
  .pending {{ color:var(--muted); padding:48px 0; text-align:center; }}

  footer {{ border-top:1px solid var(--grid); padding:20px 32px 40px; color:var(--muted); font-size:.82rem; }}

  @media (max-width: 760px) {{
    .frame {{ flex-direction:column; }}
    nav {{ width:auto; display:flex; padding:10px 16px 0; border-bottom:1px solid var(--grid); }}
    nav a {{ border-left:0; border-bottom:2px solid transparent; padding:8px 12px; }}
    nav a.on {{ border-bottom-color:var(--gold); }}
    main {{ padding:20px 16px 48px; }}
  }}
"""


# 가로 범례가 좁은 폭에서 줄바꿈 대신 오버플로우해 글자가 잘리는 문제를 막는 공용 헬퍼.
# 각 차트의 한 줄 범례 폭을 실측해 필요한 줄 수를 구하고, 상단 여백을 늘려 Plotly가
# 줄바꿈할 공간을 준다. plotly_afterplot마다 실행하되 (폭, 줄 수) 키로 중복을 막아 무한 루프 방지.
LEGEND_FIT_JS = """
<script>
window.addEventListener("load", function () {
  function rowsNeeded(gd) {
    var leg = gd.querySelector(".legend");
    if (!leg) return 1;
    var items = leg.querySelectorAll(".traces");
    if (items.length < 2) return 1;
    var sum = 0;
    for (var i = 0; i < items.length; i++) sum += items[i].getBoundingClientRect().width + 30;  // Plotly 실제 간격·패딩 여유(폰트 편차 대비)
    var fl = gd._fullLayout;
    var plotW = fl ? (fl.width - fl.margin.l - fl.margin.r) : gd.clientWidth;
    return Math.min(3, Math.max(1, Math.ceil(sum / Math.max(plotW, 60))));
  }
  function fit(gd) {
    if (gd.__baseTop == null) gd.__baseTop = (gd.layout && gd.layout.margin && gd.layout.margin.t) || 30;
    var rows = rowsNeeded(gd);
    var key = Math.round(gd.clientWidth) + ":" + rows;
    if (gd.__fitKey === key) return;
    gd.__fitKey = key;
    var want = gd.__baseTop + (rows - 1) * 30;
    var cur = gd._fullLayout && gd._fullLayout.margin.t;
    if (cur != null && Math.abs(cur - want) > 1) Plotly.relayout(gd, { "margin.t": want });
  }
  function attach(gd) {
    if (gd.__fitWired) return;
    gd.__fitWired = true;
    if (gd.on) gd.on("plotly_afterplot", function () { fit(gd); });
    fit(gd);
  }
  function scan() {
    document.querySelectorAll(".js-plotly-plot").forEach(attach);
  }
  scan();
  new MutationObserver(scan).observe(document.body, { subtree: true, childList: true });
});
</script>
"""


def page(slug: str, title: str, content: str, *, plotly: bool = False) -> str:
    nav = "\n".join(
        f'      <a href="{s}"{" class=\"on\"" if s == slug else ""}>{t}</a>'
        for s, t in PAGES)
    plotly_tag = ('<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" '
                  'charset="utf-8"></script>' if plotly else "")
    legend_fit = LEGEND_FIT_JS if plotly else ""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — &lt;인도철학&gt;은 왜 점점 얇아지고 있는가?</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
{plotly_tag}
<style>{CSS}</style>
</head>
<body>
  <div class="banner">
    <div class="kicker">데이터로 읽는 학술지</div>
    <h1>&lt;인도철학&gt;은 왜 점점 얇아지고 있는가?</h1>
    <div class="subtitle">핵심 필진, 인도철학과, 그리고 헌신성으로 본 &lt;인도철학&gt; 필진 구성의 추이</div>
  </div>
  <div class="frame">
    <nav>
{nav}
    </nav>
    <main>
{content}
    </main>
  </div>
  <footer>자료: KCI(한국학술지인용색인) · 동국대학교 dCollection —
    원본 데이터와 수집·가공 과정은 <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/README.md">data/README.md</a> 참조</footer>
{legend_fit}
</body>
</html>
"""


def overview_chart() -> str:
    """개관: 연도별 논문 발행수. 변수 = 구간 폭(4년/5년/없음), 기간(전체/2000~/최근 10년).
    휴간(1990–91) 음영, 기간별 연평균선(휴간·미완 2026 제외 평균), 구간/연도 눈금."""
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    counts = papers["발행연도"].dropna().astype(int).value_counts()
    years = list(range(1989, 2027))
    n = [int(counts.get(y, 0)) for y in years]
    assert sum(n) == 641, sum(n)

    data_js = json.dumps({"years": years, "n": n}, ensure_ascii=False)
    return f"""
<div class="panel">
  <h2>『인도철학』 연도별 논문 발행수</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-binw">
        <button data-v="4" class="on">4년</button><button data-v="5">5년</button><button data-v="0">없음</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">기간</span>
      <span class="seg" id="seg-range">
        <button data-v="all" class="on">전체</button><button data-v="2000">2000년~</button><button data-v="recent">최근 10년</button>
      </span></div>
    <div class="dl">
      <button id="dl-png">PNG 저장</button><button id="dl-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-overview"></div>
  <div class="panel-foot">발행 주기: 연 1회(1989–2003, 2002만 2회) · 연 2회(2004–09) · 연 3회(2010~) ·
    연평균(선·막대) = 휴간 1990–91 제외 평균, 평균선은 미완 2026도 제외 <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a></div>
</div>

<script>
(function () {{
  const D = {data_js};
  const INK = "{INK}", MUTED = "{MUTED}", GRID = "{GRID}", BARBG = "{BARBG}";
  const HIATUS = [1990, 1991];
  const YMAX = 44;                              // 논문 원본 y축 상한
  const gd = document.getElementById("chart-overview");
  let binw = 4, range = "all";

  function bins(w) {{
    const out = [];
    for (let b0 = 1989; b0 <= 2026; b0 += w) {{
      const b1 = Math.min(b0 + w - 1, 2026);
      let s = 0, c = 0;
      for (let y = b0; y <= b1; y++) {{      // 휴간 연도는 분모에서 제외
        if (HIATUS.includes(y)) continue;
        s += D.n[y - 1989]; c++;
      }}
      const avg = c ? Math.round(s / c * 10) / 10 : 0;
      out.push({{ b0, b1, avg }});
    }}
    return out;
  }}

  function xrange() {{
    if (range === "2000") return [1999.2, 2026.8];
    if (range === "recent") return [2016.2, 2026.8];
    return [1988.2, 2026.8];
  }}

  function render() {{
    const traces = [];
    const xr = xrange();
    const y0 = Math.ceil(xr[0]), y1 = Math.floor(xr[1]);
    const B = binw > 0 ? bins(binw) : [];

    if (binw > 0) {{
      traces.push({{
        type: "bar",
        x: B.map(b => (b.b0 + b.b1) / 2),
        y: B.map(b => b.avg),
        width: B.map(b => b.b1 - b.b0 + 0.8),
        marker: {{ color: BARBG, line: {{ width: 0 }} }},
        text: B.map(b => {{
          const c = (b.b0 + b.b1) / 2;
          return (c >= xr[0] && c <= xr[1]) ? String(b.avg) : "";
        }}),
        textposition: "inside", insidetextanchor: "start", textangle: 0,
        constraintext: "none",
        textfont: {{ color: MUTED, size: 11 }},
        customdata: B.map(b => b.b0 + "–" + b.b1),
        hovertemplate: "%{{customdata}} 연평균 %{{y}}편<extra></extra>",
        name: binw + "년 구간 연평균",
      }});
    }}
    // ── 기간 연평균 (휴간·미완 2026 제외) ──
    let sum = 0, cnt = 0;
    for (let y = Math.max(1989, y0); y <= Math.min(2026, y1); y++) {{
      if (HIATUS.includes(y) || y === 2026) continue;
      sum += D.n[y - 1989]; cnt++;
    }}
    const avg = cnt ? sum / cnt : 0;

    // 휴간 밴드: 막대 위·평균선 아래 (트레이스 순서로 z 제어)
    traces.push({{
      type: "scatter", mode: "lines",
      x: [1989.5, 1991.5], y: [YMAX, YMAX],
      fill: "tozeroy", fillcolor: "rgba(205,199,184,0.45)",
      line: {{ width: 0 }},
      hoverinfo: "skip", showlegend: false,
    }});
    // 평균선: 막대 위·연도선 아래 (트레이스 순서로 z 제어)
    traces.push({{
      type: "scatter", mode: "lines",
      x: [xr[0], xr[1]], y: [avg, avg],
      line: {{ color: INK, width: 1, dash: "dot" }}, opacity: 0.55,
      hoverinfo: "skip", showlegend: false,
    }});
    traces.push({{
      type: "scatter", mode: "lines",
      x: D.years, y: D.n,
      line: {{ color: INK, width: 2 }},
      hovertemplate: "%{{x}}년 · %{{y}}편<extra></extra>",
      name: "연도별 발행 편수",
    }});

    // ── x축 눈금: 구간 선택 시 구간 연도, 없음 시 매년 ──
    let tickvals, ticktext, tickangle = 0;
    if (binw > 0) {{
      tickvals = B.map(b => (b.b0 + b.b1) / 2);
      ticktext = B.map(b => b.b0 + "–" + String(b.b1 % 100).padStart(2, "0"));
    }} else {{
      tickvals = D.years.filter(y => y >= y0 && y <= y1);
      ticktext = tickvals.map(String);
      if (tickvals.length > 16) tickangle = -90;
    }}

    const shapes = [];
    const annos = [
      {{ x: xr[1] - 0.3, y: avg, xref: "x", yref: "y",
        xanchor: "right", yshift: 10, showarrow: false,
        text: (range === "all" ? "전체 " : "") + "연평균 " + Math.round(avg) + "편",
        bgcolor: "rgba(255,255,255,0.8)", borderpad: 1,
        font: {{ color: INK, size: 11.5 }} }},
    ];
    if (xr[0] < 1991.5) {{
      annos.push({{ x: 1990.5, y: YMAX - 1.5, xref: "x", yref: "y",
        yanchor: "top", showarrow: false, text: "휴간<br>1990–91",
        font: {{ color: MUTED, size: 10.5 }} }});
    }}

    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 40, r: 16, t: 8, b: binw > 0 ? 36 : 52 }}, height: 420,
      hovermode: "x unified",
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
      showlegend: binw > 0,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.02, x: 0,
               font: {{ size: 13, color: MUTED }} }},
      bargap: 0,
      xaxis: {{ showgrid: false, zeroline: false, range: xr,
              tickvals: tickvals, ticktext: ticktext, tickangle: tickangle,
              tickfont: {{ color: MUTED, size: binw > 0 ? 12 : 11 }} }},
      yaxis: {{ gridcolor: GRID, zeroline: false, tickfont: {{ color: MUTED }},
              range: [0, YMAX], tickvals: [0, 10, 20, 30, 40] }},
      shapes: shapes,
      annotations: annos,
    }};
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
  }}

  function segWire(id, fn) {{
    const seg = document.getElementById(id);
    seg.addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      seg.querySelectorAll("button").forEach(b => b.classList.toggle("on", b === btn));
      fn(btn.dataset.v);
      render();
    }});
  }}
  segWire("seg-binw", v => {{ binw = parseInt(v, 10); }});
  segWire("seg-range", v => {{ range = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 420,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_연도별_발행수",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-svg").addEventListener("click", () => capture("svg"));

  render();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def asymmetry_chart() -> str:
    """핵심 필진 ①: 필자·논문 비대칭. 변수 = 핵심 기준(누적 N편, 2/3/4/5)."""
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    authors = pd.read_parquet(ROOT / "data" / "processed" / "authors.parquet")
    papers["주저자"] = papers["논문 ID"].map(
        authors.sort_index().groupby("논문ID")["저자_원본"].first())
    ks = papers["주저자"] == "김성철"
    papers.loc[ks, "주저자"] = ["김성철#유식" if "금강" in str(a) else "김성철#중관"
                                for a in papers.loc[ks, "주저자 소속기관"].fillna("")]
    papers.loc[papers["주저자"] == "김미숙", "주저자"] = "김미숙#자이나"
    life = papers.groupby("주저자").size()
    hist = {int(k): int(v) for k, v in life.value_counts().sort_index().items()}
    n_authors, n_papers = int(life.size), int(life.sum())
    assert (n_authors, n_papers) == (207, 641), (n_authors, n_papers)

    hist_js = json.dumps(hist)
    return f"""
<div class="panel">
  <h2>필자 구성 개관</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-asym-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-asym-png">PNG 저장</button><button id="dl-asym-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-asym"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
</div>

<script>
(function () {{
  const HIST = {hist_js};
  const TOT_P = {n_authors}, TOT_W = {n_papers};
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}";
  const MID = "#A8A294", LITE = "#D8D5CC";
  const gd = document.getElementById("chart-asym");
  let N = 3;

  function sum(from, to, fn) {{
    let s = 0;
    for (const k in HIST) {{
      const kk = parseInt(k, 10);
      if (kk >= from && kk <= to) s += fn(kk, HIST[k]);
    }}
    return s;
  }}

  function render() {{
    // 세그먼트: 핵심(N편 이상) / 2–(N-1)편 / 1편
    const segs = [
      {{ name: "핵심 필진 · " + N + "편 이상", color: GOLD, tcol: "#FFFFFF",
        p: sum(N, 99, (k, c) => c), w: sum(N, 99, (k, c) => k * c) }},
    ];
    if (N > 2) segs.push(
      {{ name: N === 3 ? "2편" : "2–" + (N - 1) + "편", color: MID, tcol: INK,
        p: sum(2, N - 1, (k, c) => c), w: sum(2, N - 1, (k, c) => k * c) }});
    segs.push(
      {{ name: "일회성 · 1편", color: LITE, tcol: INK,
        p: HIST[1] || 0, w: HIST[1] || 0 }});

    const ROWS = [
      {{ y: "필자 " + TOT_P + "명", tot: TOT_P, key: "p", unit: "명", pos: 1 }},
      {{ y: "논문 " + TOT_W + "편", tot: TOT_W, key: "w", unit: "편", pos: 0 }},
    ];
    const traces = [], annos = [];
    segs.forEach(seg => {{
      const xs = [], texts = [];
      ROWS.forEach(r => {{
        const cnt = seg[r.key];
        const pct = cnt / r.tot * 100;
        xs.push(Math.round(pct * 10) / 10);
        const label = Math.round(pct) + "% · " + cnt + r.unit;
        texts.push(pct >= 15 ? label : "");
        if (pct < 15 && pct > 0) {{
          // 좁은 칸 → 막대 밖 리더선 (필자 행은 위, 논문 행은 아래)
          let left = 0;
          for (const s2 of segs) {{ if (s2 === seg) break; left += s2[r.key] / r.tot * 100; }}
          const up = r.pos === 1;
          annos.push({{
            x: left + pct / 2, y: r.pos + (up ? 0.26 : -0.26),
            ax: 0, ay: up ? -22 : 22,
            text: label, showarrow: true, arrowhead: 0, arrowwidth: 0.8,
            arrowcolor: MUTED, font: {{ color: MUTED, size: 11 }},
          }});
        }}
      }});
      traces.push({{
        type: "bar", orientation: "h",
        y: ROWS.map(r => r.y), x: xs,
        width: 0.52,
        name: seg.name,
        marker: {{ color: seg.color, line: {{ color: "#FFFFFF", width: 1.4 }} }},
        text: texts, textposition: "inside", insidetextanchor: "middle",
        textangle: 0,
        textfont: {{ color: seg.tcol, size: 13 }},
        hoverinfo: "none",
      }});
    }});

    // 핵심 확장 리본 (필자 막대 아래변 → 논문 막대 위변)
    const cA = segs[0].p / TOT_P * 100, cW = segs[0].w / TOT_W * 100;
    const ribbon = {{
      type: "path",
      path: "M 0,0.74 L " + cA + ",0.74 L " + cW + ",0.26 L 0,0.26 Z",
      fillcolor: "rgba(184,145,31,0.12)", line: {{ width: 0 }}, layer: "below",
    }};

    const layout = {{
      barmode: "stack",
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 96, r: 16, t: 34, b: 12 }}, height: 300,
      showlegend: true,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.06, x: 0, traceorder: "normal",
               font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ range: [0, 100.5], visible: false, fixedrange: true }},
      yaxis: {{ tickfont: {{ color: INK, size: 14 }}, categoryorder: "array",
              categoryarray: [ROWS[1].y, ROWS[0].y], fixedrange: true }},
      shapes: [ribbon],
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: "{GRID}", font: {{ color: INK }} }},
    }};
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    nTraces = traces.length;
  }}

  // ── 호버 연동: 같은 빈도 그룹(핵심/2편대/일회성)의 필자·논문 조각을 함께 강조 ──
  let nTraces = 0, hl;
  function setHighlight(idx) {{
    if (hl === idx) return;
    hl = idx;
    const ops = [];
    for (let i = 0; i < nTraces; i++) ops.push(idx == null || i === idx ? 1 : 0.25);
    Plotly.restyle(gd, {{ opacity: ops }});
    Plotly.relayout(gd, {{ "shapes[0].fillcolor":                 // 리본 = 핵심 그룹 연동
      (idx == null || idx === 0) ? "rgba(184,145,31,0.12)" : "rgba(184,145,31,0.03)" }});
  }}

  document.getElementById("seg-asym-n").addEventListener("click", e => {{
    const btn = e.target.closest("button");
    if (!btn) return;
    document.querySelectorAll("#seg-asym-n button").forEach(b => b.classList.toggle("on", b === btn));
    N = parseInt(btn.dataset.v, 10);
    render();
  }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 300,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_필자_구성_개관",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-asym-png").addEventListener("click", () => {{ setHighlight(null); capture("png"); }});
  document.getElementById("dl-asym-svg").addEventListener("click", () => {{ setHighlight(null); capture("svg"); }});

  render();
  if (document.fonts) document.fonts.ready.then(render);
  gd.on("plotly_hover", ev => setHighlight(ev.points[0].curveNumber));
  gd.on("plotly_unhover", () => setHighlight(null));
}})();
</script>
"""


def top_authors_chart() -> str:
    """핵심 필진 ②: 누적 게재 상위 필자 가로 막대. 변수 = 상위 N명(10/20/30)."""
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    authors = pd.read_parquet(ROOT / "data" / "processed" / "authors.parquet")
    papers["주저자"] = papers["논문 ID"].map(
        authors.sort_index().groupby("논문ID")["저자_원본"].first())
    ks = papers["주저자"] == "김성철"
    papers.loc[ks, "주저자"] = ["김성철#유식" if "금강" in str(a) else "김성철#중관"
                                for a in papers.loc[ks, "주저자 소속기관"].fillna("")]
    papers.loc[papers["주저자"] == "김미숙", "주저자"] = "김미숙#자이나"
    jp = papers[papers["발행연도"].notna()].copy()
    jp["발행연도"] = jp["발행연도"].astype(int)
    st = jp.groupby("주저자")["발행연도"].agg(n="size", last="max", first="min")
    # 동률이면 최종 편수에 먼저 도달한(마지막 게재가 이른) 순, 그다음 데뷔 이른 순
    st = st.sort_values(["n", "last", "first"], ascending=[False, True, True])
    top = []
    for nm, r in st.head(30).iterrows():
        disp = nm.replace("#", "(") + ")" if "#" in nm else nm
        top.append({"name": disp, "n": int(r["n"]),
                    "first": int(r["first"]), "last": int(r["last"])})
    assert top[0]["name"] == "정승석" and top[0]["n"] == 31, top[0]

    top_js = json.dumps(top, ensure_ascii=False)
    return f"""
<div class="panel">
  <h2>누적 게재 상위 필자</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">인원</span>
      <span class="seg" id="seg-top-n">
        <button data-v="10">10명</button><button data-v="20" class="on">20명</button><button data-v="30">30명</button>
      </span></div>
    <div class="dl">
      <button id="dl-top-png">PNG 저장</button><button id="dl-top-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-top"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
</div>

<script>
(function () {{
  const TOP = {top_js};
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const gd = document.getElementById("chart-top");
  let N = 20;

  function chartHeight() {{ return 30 + N * 26 + 20; }}

  function render() {{
    const rows = TOP.slice(0, N);
    const traces = [{{
      type: "bar", orientation: "h",
      y: rows.map(r => r.name), x: rows.map(r => r.n),
      marker: {{ color: GOLD, line: {{ width: 0 }} }},
      width: 0.62,
      text: rows.map(r => String(r.n)),
      textposition: "outside", textangle: 0,
      textfont: {{ color: MUTED, size: 12 }},
      cliponaxis: false,
      customdata: rows.map(r => [r.first, r.last]),
      hovertemplate: "%{{y}} · %{{x}}편 · 활동 기간 %{{customdata[0]}}–%{{customdata[1]}}<extra></extra>",
      name: "",
    }}];
    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 110, r: 34, t: 8, b: 8 }}, height: chartHeight(),
      showlegend: false,
      xaxis: {{ visible: false, fixedrange: true,
              range: [0, Math.max(...rows.map(r => r.n)) * 1.08] }},
      yaxis: {{ autorange: "reversed", tickfont: {{ color: INK, size: 13 }},
              fixedrange: true }},
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
  }}

  document.getElementById("seg-top-n").addEventListener("click", e => {{
    const btn = e.target.closest("button");
    if (!btn) return;
    document.querySelectorAll("#seg-top-n button").forEach(b => b.classList.toggle("on", b === btn));
    N = parseInt(btn.dataset.v, 10);
    render();
  }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 720, height: chartHeight(),
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_누적게재_상위" + N + "인",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-top-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-top-svg").addEventListener("click", () => capture("svg"));

  render();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def _author_years(with_names: bool = False):
    """주저자(동명이인 분리)별 발행연도 목록 — 시계열 차트들의 공통 입력.
    with_names=True면 (표시용 이름 목록, 연도 목록) 쌍을 같은 순서로 반환."""
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    authors = pd.read_parquet(ROOT / "data" / "processed" / "authors.parquet")
    papers["주저자"] = papers["논문 ID"].map(
        authors.sort_index().groupby("논문ID")["저자_원본"].first())
    ks = papers["주저자"] == "김성철"
    papers.loc[ks, "주저자"] = ["김성철#유식" if "금강" in str(a) else "김성철#중관"
                                for a in papers.loc[ks, "주저자 소속기관"].fillna("")]
    papers.loc[papers["주저자"] == "김미숙", "주저자"] = "김미숙#자이나"
    jp = papers[papers["발행연도"].notna() & papers["주저자"].notna()]
    groups = jp.groupby("주저자")["발행연도"]
    years = [sorted(int(y) for y in g) for _, g in groups]
    if not with_names:
        return years
    names = [f"{p.split('#')[0]}({p.split('#')[1]})" if "#" in p else p
             for p, _ in groups]
    return names, years


def ay_script() -> str:
    """주저자별 발행연도 목록(KSIP_AY) + 표시용 이름(KSIP_AN)을 페이지 전역으로 1회 임베드."""
    names, ay = _author_years(with_names=True)
    assert len(ay) == 207 and sum(len(a) for a in ay) == 641
    return (f"<script>const KSIP_AY = {json.dumps(ay)};"
            f"const KSIP_AN = {json.dumps(names, ensure_ascii=False)};</script>")


def activity_chart() -> str:
    """핵심 필진 ③: 시기별 활동 필자 수 + 핵심 논문 점유율.
    변수 = 구간 폭(4/5년), 핵심 기준(누적 2/3/4/5편)."""
    return f"""
<div class="panel">
  <h2>시기별 활동 필자 수</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-act-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-act-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-act-png">PNG 저장</button><button id="dl-act-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-act"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 · 마지막 구간은 진행 중(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
</div>

<script>
(function () {{
  const AY = KSIP_AY;                      // 주저자별 발행연도 목록 (공용 임베드)
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const GRAY = "#CDC7B8";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-act");
  let W = 4, N = 3;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const core = Array(nbin).fill(0), total = Array(nbin).fill(0);
    const shN = Array(nbin).fill(0), shD = Array(nbin).fill(0);
    AY.forEach(years => {{
      const cnt = Array(nbin).fill(0);
      years.forEach(y => cnt[bin(y)]++);
      let cum = 0;
      for (let b = 0; b < nbin; b++) {{
        cum += cnt[b];
        if (cnt[b] > 0) {{
          total[b]++;
          if (cum >= N) core[b]++;
          shD[b] += cnt[b];
          if (cum >= N) shN[b] += cnt[b];
        }}
      }}
    }});
    const share = shD.map((d, b) => d > 0 ? Math.round(100 * shN[b] / d) : 0);
    return {{ nbin, labels, core, total, noncore: total.map((t, b) => t - core[b]), share }};
  }}

  function render() {{
    const C = compute();
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 1;               // 마지막 구간 = 잠정
    const xs = C.labels;
    const provOp = i => i === prov ? 0.5 : 1;

    const traces = [
      {{ type: "bar", x: xs, y: C.core, name: "핵심 · " + N + "편 이상",
        width: 0.7,
        marker: {{ color: GOLD, opacity: xs.map((_, i) => provOp(i)),
                 pattern: {{ shape: xs.map((_, i) => i === prov ? "/" : ""),
                           fillmode: "overlay", fgcolor: "#FFFFFF", size: 5, solidity: 0.4 }} }},
        hovertemplate: "%{{x}} · 핵심 %{{y}}명<extra></extra>" }},
      {{ type: "bar", x: xs, y: C.noncore, name: "일회성 필진",
        width: 0.7,
        marker: {{ color: GRAY, opacity: xs.map((_, i) => provOp(i)),
                 pattern: {{ shape: xs.map((_, i) => i === prov ? "/" : ""),
                           fillmode: "overlay", fgcolor: "#FFFFFF", size: 5, solidity: 0.4 }} }},
        hovertemplate: "%{{x}} · 일회성 %{{y}}명<extra></extra>" }},
      // 점유율 선: 확정 구간 실선
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(0, prov), y: C.share.slice(0, prov),
        yaxis: "y2", showlegend: false,
        line: {{ color: INK, width: 2 }},
        marker: {{ size: 7, color: INK, line: {{ color: "#FFFFFF", width: 1.2 }} }},
        hovertemplate: "%{{x}} · 핵심 필자가 쓴 논문의 점유율 %{{y}}%<extra></extra>" }},
      // 잠정 구간 점선 + 빈 마커
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.share.slice(prov - 1),
        yaxis: "y2", showlegend: false,
        line: {{ color: INK, width: 2, dash: "dot" }},
        marker: {{ size: 7, color: ["rgba(0,0,0,0)", "#FFFFFF"],
                 line: {{ color: INK, width: 1.2 }} }},
        hovertemplate: "%{{x}} · 핵심 필자가 쓴 논문의 점유율 %{{y}}%<extra></extra>" }},
    ];

    const annos = [];
    C.core.forEach((c, i) => {{               // 핵심 수 라벨
      if (c === 0) return;
      const inside = c >= 15;
      annos.push({{ x: xs[i], y: inside ? c / 2 : c + 1.4, yref: "y",
        text: "<b>" + c + "</b>", showarrow: false,
        yanchor: inside ? "middle" : "bottom",
        font: {{ color: inside ? (i === prov ? INK : "#FFFFFF") : GOLD, size: SM ? 9.5 : 12 }} }});
    }});
    C.total.forEach((t, i) => {{              // 활동 총계 라벨 (막대 위)
      annos.push({{ x: xs[i], y: t + 1.6, yref: "y", text: String(t), showarrow: false,
        yanchor: "bottom", font: {{ color: MUTED, size: SM ? 9 : 10.5 }} }});
    }});
    C.share.forEach((s, i) => {{              // 점유율 값 라벨 (마커 위)
      annos.push({{ x: xs[i], y: s, yref: "y2", yshift: 11, text: "<b>" + s + "</b>",
        showarrow: false, font: {{ color: INK, size: SM ? 9 : 10.5 }} }});
    }});

    const layout = {{
      barmode: "stack", bargap: 0.3,
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 56, t: 56, b: 40 }}, height: 460,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [0, 150], tickvals: [0, 30, 60, 90],
              title: {{ text: "활동 필자 수 (명)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      yaxis2: {{ range: [0, 100], tickvals: [0, 20, 40, 60, 80, 100],
               overlaying: "y", side: "right",
               title: {{ text: "핵심 논문 점유율 (%)", font: {{ color: INK, size: 12 }} }},
               showgrid: false, tickfont: {{ color: MUTED }}, fixedrange: true }},
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-act-w", v => {{ W = v; }});
  segWire("seg-act-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 460,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_시기별_활동필자수",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-act-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-act-svg").addEventListener("click", () => capture("svg"));

  render();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def stockflow_chart() -> str:
    """핵심 필진 ④: 시기별 핵심 필진 수와 유입·이탈.
    변수 = 구간 폭(4/5년), 핵심 기준(누적 2/3/4/5편)."""
    return f"""
<div class="panel">
  <h2>시기별 핵심 필진 수와 유입·이탈</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-sf-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-sf-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-sf-png">PNG 저장</button><button id="dl-sf-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-sf"></div>
  <div id="sf-names" class="names-box"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 ·
    <span id="sf-def">유입 = 해당 구간 3편째 게재</span> · 이탈 = 이전 구간 마지막 게재 후 미게재 ·
    마지막 구간은 진행 중(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
</div>

<script>
(function () {{
  const AY = KSIP_AY;
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const GRAY = "#CDC7B8", RUST = "#9E4A2E";
  const Y0 = 1989, Y1 = 2026;
  const AN = KSIP_AN;                      // KSIP_AY와 같은 순서의 표시용 이름
  const gd = document.getElementById("chart-sf");
  let W = 4, N = 3, lastC = null;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const core = Array(nbin).fill(0), total = Array(nbin).fill(0);
    const ent = Array(nbin).fill(0), exi = Array(nbin).fill(0);
    const entNm = Array.from({{ length: nbin }}, () => []);
    const exiNm = Array.from({{ length: nbin }}, () => []);
    AY.forEach((years, ai) => {{
      const cnt = Array(nbin).fill(0);
      years.forEach(y => cnt[bin(y)]++);
      let cum = 0;
      for (let b = 0; b < nbin; b++) {{
        cum += cnt[b];
        if (cnt[b] > 0) {{
          total[b]++;
          if (cum >= N) core[b]++;
        }}
      }}
      if (years.length >= N) {{
        const eb = bin(years[N - 1]), xb = bin(years[years.length - 1]);
        ent[eb]++; entNm[eb].push(AN[ai]);            // 유입 = N편째 게재 구간
        exi[xb]++; exiNm[xb].push(AN[ai]);            // 마지막 게재 구간
      }}
    }});
    const exiShift = [0].concat(exi.slice(0, -1));    // 이탈 = 그다음 구간
    const exiNmShift = [[]].concat(exiNm.slice(0, -1));
    return {{ nbin, labels, core, noncore: total.map((t, b) => t - core[b]),
             total, ent, exi: exiShift, entNm, exiNm: exiNmShift }};
  }}

  function render() {{
    const C = compute();
    lastC = C;
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 1;
    const xs = C.labels;
    const provOp = i => i === prov ? 0.5 : 1;
    const pat = {{ shape: xs.map((_, i) => i === prov ? "/" : ""),
                 fillmode: "overlay", fgcolor: "#FFFFFF", size: 5, solidity: 0.4 }};

    const traces = [
      {{ type: "bar", x: xs, y: C.core, name: "핵심 · " + N + "편 이상", width: 0.7,
        marker: {{ color: GOLD, opacity: xs.map((_, i) => provOp(i)), pattern: pat }},
        hovertemplate: "%{{x}} · 핵심 %{{y}}명<extra></extra>" }},
      {{ type: "bar", x: xs, y: C.noncore, name: "일회성 필진", width: 0.7,
        marker: {{ color: GRAY, opacity: xs.map((_, i) => provOp(i)), pattern: pat }},
        hovertemplate: "%{{x}} · 일회성 %{{y}}명<extra></extra>" }},
    ];
    [["유입", C.ent, INK, "circle"], ["이탈", C.exi, RUST, "square"]].forEach(([nm, vals, color, sym]) => {{
      traces.push({{ type: "scatter", mode: "lines+markers",
        x: xs.slice(0, prov), y: vals.slice(0, prov), yaxis: "y2", name: nm,
        line: {{ color: color, width: 2.1 }},
        marker: {{ size: 7, symbol: sym, color: color, line: {{ color: "#FFFFFF", width: 1.2 }} }},
        hovertemplate: "%{{x}} · " + nm + " %{{y}}명<extra></extra>" }});
      traces.push({{ type: "scatter", mode: "lines+markers",
        x: xs.slice(prov - 1), y: vals.slice(prov - 1), yaxis: "y2",
        name: nm, showlegend: false,
        line: {{ color: color, width: 2.1, dash: "dot" }},
        marker: {{ size: 7, symbol: sym, color: ["rgba(0,0,0,0)", "#FFFFFF"],
                 line: {{ color: color, width: 1.3 }} }},
        hovertemplate: "%{{x}} · " + nm + " %{{y}}명<extra></extra>" }});
    }});

    // 값 라벨 (흰 박스) — 유입 위 / 이탈 아래, 근접 시 좌우로 분리
    const annos = [];
    C.ent.forEach((e, i) => {{
      const x2 = C.exi[i], close = Math.abs(e - x2) <= 1;
      annos.push({{ x: xs[i], y: e, yref: "y2", yshift: 12, xshift: close ? -11 : 0,
        text: "<b>" + e + "</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.92)", borderpad: 1,
        font: {{ color: INK, size: SM ? 9 : 10.5 }} }});
      annos.push({{ x: xs[i], y: x2, yref: "y2",
        yshift: (close || x2 < 2) ? 12 : -13, xshift: close ? 11 : 0,
        text: "<b>" + x2 + "</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.92)", borderpad: 1,
        font: {{ color: RUST, size: SM ? 9 : 10.5 }} }});
    }});

    const yMax = Math.max.apply(null, C.total) * 1.15;
    const y2Max = Math.max.apply(null, C.ent.concat(C.exi)) * 1.3 + 2;
    const layout = {{
      barmode: "stack", bargap: 0.3,
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 56, t: 56, b: 40 }}, height: 460,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [0, yMax],
              title: {{ text: "활동 필자 수 (명)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      yaxis2: {{ range: [0, y2Max], overlaying: "y", side: "right",
               title: {{ text: "핵심 유입·이탈 (명)", font: {{ color: MUTED, size: 12 }} }},
               showgrid: false, tickfont: {{ color: MUTED }}, fixedrange: true }},
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    document.getElementById("sf-def").textContent = "유입 = 해당 구간 " + N + "편째 게재";
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    resetNames();
  }}

  const box = document.getElementById("sf-names");
  const HINT = '<span class="nb-hint"><b>유입</b>·<b style="color:' + RUST + '">이탈</b> '
    + '꼭지점에 마우스를 올리면 그 수치에 집계된 필자 이름이 여기에 나열됩니다.</span>';
  function resetNames() {{ box.innerHTML = HINT; }}
  function showNames(kind, bi) {{
    if (!lastC) return;
    const names = (kind === "유입" ? lastC.entNm[bi] : lastC.exiNm[bi]).slice()
      .sort((a, b) => a.localeCompare(b, "ko"));
    const color = kind === "유입" ? INK : RUST;
    box.innerHTML =
      '<div class="nb-head"><b>' + lastC.labels[bi] + '</b> · <span style="color:' + color
      + '">' + kind + '</span> · ' + names.length + '명</div>'
      + '<div class="nb-names">' + (names.join(", ") || "없음") + '</div>';
  }}
  function wireHover() {{
    gd.on("plotly_hover", function (ev) {{
      const pt = ev.points && ev.points[0];
      if (!pt || !lastC) return;
      const nm = (pt.data && pt.data.name) || "";
      if (nm !== "유입" && nm !== "이탈") return;
      const bi = lastC.labels.indexOf(pt.x);
      if (bi >= 0) showNames(nm, bi);
    }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-sf-w", v => {{ W = v; }});
  segWire("seg-sf-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 460,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_핵심필진_유입이탈",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-sf-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-sf-svg").addEventListener("click", () => capture("svg"));

  render();
  wireHover();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def _author_years_sadan() -> list[dict]:
    """주저자별 발행연도 + 인철과 출신 여부(동국대 학위자·그 지도교수) — 인도철학과 탭 공용."""
    import csv
    from collections import defaultdict

    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    authors = pd.read_parquet(ROOT / "data" / "processed" / "authors.parquet")
    papers["주저자"] = papers["논문 ID"].map(
        authors.sort_index().groupby("논문ID")["저자_원본"].first())
    ks = papers["주저자"] == "김성철"
    papers.loc[ks, "주저자"] = ["김성철#유식" if "금강" in str(a) else "김성철#중관"
                                for a in papers.loc[ks, "주저자 소속기관"].fillna("")]
    papers.loc[papers["주저자"] == "김미숙", "주저자"] = "김미숙#자이나"
    jp = papers[papers["발행연도"].notna() & papers["주저자"].notna()]

    rows = list(csv.DictReader(
        open(ROOT / "data" / "raw" / "dongguk_indophil_theses.csv", encoding="utf-8-sig")))
    advisors = {r["advisor"].strip() for r in rows} - {"미상", ""}
    per = defaultdict(list)
    for r in rows:
        per[r["person_id"].strip()].append((r["degree"].strip(), r["advisor"].strip()))

    def sadan(pid: str) -> bool:  # 박사(최종학위) 지도교수 우선 · 지도교수 본인 포함
        if pid in advisors:
            return True
        recs = per.get(pid, [])
        phd = [a for d, a in recs if d == "박사" and a and a != "미상"]
        ma = [a for d, a in recs if d == "석사" and a and a != "미상"]
        return bool(phd or ma)

    def disp(pid: str) -> str:
        if "#" in pid:
            b, s = pid.split("#", 1)
            return f"{b}({s})"
        return pid

    data = [{"nm": disp(nm), "y": sorted(int(v) for v in ys), "s": int(sadan(nm))}
            for nm, ys in jp.groupby("주저자")["발행연도"]]
    n_auth_s = sum(d["s"] for d in data)
    n_pap_s = sum(len(d["y"]) for d in data if d["s"])
    assert (len(data), n_auth_s, n_pap_s) == (207, 79, 390)
    return data


def dept_data_script() -> str:
    return f"<script>const KSIP_AS = {json.dumps(_author_years_sadan())};</script>"


def dept_composition_chart() -> str:
    """인도철학과 ①: 필진과 논문의 출신 구성 (3막대). 변수 = 핵심 기준(2/3/4/5편)."""
    return f"""
<div class="panel">
  <h2>필진의 출신별 구성과 논문의 비중</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-comp-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-comp-png">PNG 저장</button><button id="dl-comp-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-comp"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 ·
    인철과 출신 = 동국대 인도철학과 학위자와 그 지도교수 <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/dongguk_indophil_theses.csv">dongguk_indophil_theses.csv</a></div>
</div>

<script>
(function () {{
  const AS = KSIP_AS;
  const INK = "{INK}", MUTED = "{MUTED}", GRID = "{GRID}";
  const GOLD = "{GOLD}", GOLD_P = "#DBC88F", GREY_D = "#A8A294", GREY = "#D8D5CC";
  const gd = document.getElementById("chart-comp");
  const TOT_A = AS.length;                                    // 207
  const TOT_W = AS.reduce((a, d) => a + d.y.length, 0);       // 641
  const A_S = AS.filter(d => d.s).length;                     // 79
  const W_S = AS.filter(d => d.s).reduce((a, d) => a + d.y.length, 0);  // 390
  let N = 3;

  const YS = [2.15, 1.0, -0.15], H = 0.54;

  function render() {{
    const core = AS.filter(d => d.y.length >= N);
    const nCore = core.length, nCoreS = core.filter(d => d.s).length;
    const gCore = core.filter(d => d.s).reduce((a, d) => a + d.y.length, 0);
    const oCore = core.filter(d => !d.s).reduce((a, d) => a + d.y.length, 0);
    const gOnce = W_S - gCore, oOnce = (TOT_W - W_S) - oCore;
    const pAuth = 100 * A_S / TOT_A, pPap = 100 * W_S / TOT_W, pCore = 100 * nCoreS / nCore;

    const traces = [], annos = [];
    function seg(y, x0, w, color, legendName) {{
      traces.push({{ type: "bar", orientation: "h", y: [y], x: [w], base: [x0],
        width: H, name: legendName || "", showlegend: !!legendName,
        marker: {{ color: color, line: {{ color: "#FFFFFF", width: 1.4 }} }},
        hoverinfo: "none" }});
    }}
    function inLabel(y, cx, text, white, size) {{
      annos.push({{ x: cx, y: y, yref: "y", text: text, showarrow: false,
        font: {{ color: white ? "#FFFFFF" : INK, size: size || 13 }} }});
    }}

    // ── 막대 1: 전체 필진 ──
    seg(YS[0], 0, pAuth, GOLD, "인철과 출신");             // t0
    seg(YS[0], pAuth, 100 - pAuth, GREY, "그 외");          // t1
    inLabel(YS[0], pAuth / 2, "<b>" + Math.round(pAuth) + "% · " + A_S + "명</b>", true);
    inLabel(YS[0], pAuth + (100 - pAuth) / 2, Math.round(100 - pAuth) + "% · " + (TOT_A - A_S) + "명", false);

    // ── 막대 2: 발표 논문 (짙은 칸 = 핵심 필진의 몫) ──
    let left = 0;
    [[gCore, GOLD, "핵심 몫 " + gCore + "편", true],        // t2
     [gOnce, GOLD_P, "일회성 " + gOnce + "편", false],       // t3
     [oCore, GREY_D, "핵심 몫 " + oCore + "편", true],       // t4
     [oOnce, GREY, "일회성 " + oOnce + "편", false]].forEach(([cnt, col, lab, white], i) => {{
      const w = 100 * cnt / TOT_W;
      seg(YS[1], left, w, col);
      if (w >= 9) {{
        inLabel(YS[1], left + w / 2, white ? "<b>" + lab + "</b>" : lab, white, 12);
      }} else if (cnt > 0) {{                       // 좁은 칸 → 바깥 리더
        annos.push({{ x: left + w / 2, y: YS[1] + (i < 2 ? 0.27 : -0.27), yref: "y",
          ax: 0, ay: i < 2 ? -20 : 20,
          text: lab, showarrow: true, arrowhead: 0, arrowwidth: 0.8, arrowcolor: MUTED,
          font: {{ color: MUTED, size: 11 }} }});
      }}
      left += w;
    }});

    // 막대 2 아래 브래킷: 출신 합 / 그 외 합 (핵심 기준과 무관)
    const by = YS[1] - H / 2 - 0.14;
    const shapes = [];
    [[0, pPap, "인철과 출신 " + Math.round(pPap) + "% · " + W_S + "편"],
     [pPap, 100, "그 외 " + Math.round(100 - pPap) + "% · " + (TOT_W - W_S) + "편"]].forEach(([x0, x1, lab]) => {{
      shapes.push({{ type: "path", layer: "above",
        path: "M " + (x0 + 0.4) + "," + (by + 0.09) + " L " + (x0 + 0.4) + "," + by
            + " L " + (x1 - 0.4) + "," + by + " L " + (x1 - 0.4) + "," + (by + 0.09),
        line: {{ color: MUTED, width: 0.9 }} }});
      annos.push({{ x: (x0 + x1) / 2, y: by - 0.10, yref: "y", text: lab, showarrow: false,
        yanchor: "top", font: {{ color: INK, size: 11.5 }} }});
    }});

    // ── 막대 3: 핵심 필진 ──
    seg(YS[2], 0, pCore, GOLD);                             // t6
    seg(YS[2], pCore, 100 - pCore, GREY);                   // t7
    inLabel(YS[2], pCore / 2, "<b>" + Math.round(pCore) + "% · " + nCoreS + "명</b>", true);
    inLabel(YS[2], pCore + (100 - pCore) / 2, Math.round(100 - pCore) + "% · " + (nCore - nCoreS) + "명", false);

    // 리본: 전체 필진 출신 → 논문 출신 (핵심 기준과 무관)
    shapes.push({{ type: "path", layer: "below",
      path: "M 0," + (YS[0] - H / 2) + " L " + pAuth + "," + (YS[0] - H / 2)
          + " L " + pPap + "," + (YS[1] + H / 2) + " L 0," + (YS[1] + H / 2) + " Z",
      fillcolor: "rgba(184,145,31,0.13)", line: {{ width: 0 }} }});

    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 96, r: 16, t: 34, b: 8 }}, height: 360,
      showlegend: true, barmode: "overlay",
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.05, x: 0, traceorder: "normal",
               font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ range: [0, 100.5], visible: false, fixedrange: true }},
      yaxis: {{ range: [-0.85, 2.95], tickvals: YS,
              ticktext: ["전체 필진<br>" + TOT_A + "명", "발표 논문<br>" + TOT_W + "편",
                         "핵심 필진<br>" + nCore + "명"],
              tickfont: {{ color: INK, size: 13 }}, fixedrange: true }},
      shapes: shapes,
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    nTraces = traces.length;
    ribbonIdx = shapes.length - 1;
  }}

  // ── 호버 연동: 조각 단위 — 그 필진이 쓴 논문 칸(역방향: 그 논문을 쓴 필진 조각)을 강조 ──
  // t0 필진·출신  t1 필진·그외 | t2 논문·출신핵심몫 t3 논문·출신일회성 t4 논문·그외핵심몫 t5 논문·그외일회성 | t6 핵심·출신 t7 핵심·그외
  const REL = {{ 0: [0, 2, 3], 1: [1, 4, 5], 2: [2, 0, 6], 3: [3, 0],
               4: [4, 1, 7], 5: [5, 1], 6: [6, 2], 7: [7, 4] }};
  const RIBBON_ON = [0, 2, 3];             // 리본(필진 출신→논문 출신)과 연관된 조각
  let nTraces = 0, ribbonIdx = -1, hl;
  function setHighlight(idx) {{
    if (hl === idx) return;
    hl = idx;
    const rel = idx == null ? null : REL[idx] || [idx];
    const ops = [];
    for (let i = 0; i < nTraces; i++) ops.push(rel === null || rel.includes(i) ? 1 : 0.22);
    Plotly.restyle(gd, {{ opacity: ops }});
    Plotly.relayout(gd, {{ ["shapes[" + ribbonIdx + "].fillcolor"]:
      (idx == null || RIBBON_ON.includes(idx)) ? "rgba(184,145,31,0.13)" : "rgba(184,145,31,0.04)" }});
  }}

  document.getElementById("seg-comp-n").addEventListener("click", e => {{
    const btn = e.target.closest("button");
    if (!btn) return;
    document.querySelectorAll("#seg-comp-n button").forEach(b => b.classList.toggle("on", b === btn));
    N = parseInt(btn.dataset.v, 10);
    render();
  }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 360,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_필진_논문_출신구성",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-comp-png").addEventListener("click", () => {{ setHighlight(null); capture("png"); }});
  document.getElementById("dl-comp-svg").addEventListener("click", () => {{ setHighlight(null); capture("svg"); }});

  render();
  if (document.fonts) document.fonts.ready.then(render);
  gd.on("plotly_hover", ev => setHighlight(ev.points[0].curveNumber));
  gd.on("plotly_unhover", () => setHighlight(null));
}})();
</script>
"""


def dept_share_chart() -> str:
    """인도철학과 ②: 출신별 핵심 논문 비중 추이 (3선).
    변수 = 구간 폭(4/5년), 핵심 기준(2~5편). 동적 핵심(그 구간까지 누적 N편)."""
    return f"""
<div class="panel">
  <h2>핵심 필진의 출신별 논문 비중 추이</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-sh-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-sh-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-sh-png">PNG 저장</button><button id="dl-sh-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-sh"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 ·
    비중 = 그 구간 핵심 논문 ÷ 그 구간 전체 논문 ·
    <span id="sh-def">핵심 = 그 구간까지 누적 3편 이상</span> ·
    마지막 구간은 진행 중(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/dongguk_indophil_theses.csv">dongguk_indophil_theses.csv</a></div>
</div>

<script>
(function () {{
  const AS = KSIP_AS;
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const GREY_TOT = "#B8B4A8";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-sh");
  let W = 4, N = 3;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const tot = Array(nbin).fill(0), gp = Array(nbin).fill(0), rp = Array(nbin).fill(0);
    let nG = 0, nR = 0;
    AS.forEach(d => {{
      if (d.y.length >= N) {{ d.s ? nG++ : nR++; }}
      const cnt = Array(nbin).fill(0);
      d.y.forEach(y => cnt[bin(y)]++);
      let cum = 0;
      for (let b = 0; b < nbin; b++) {{
        cum += cnt[b];
        tot[b] += cnt[b];
        if (cum >= N) (d.s ? gp : rp)[b] += cnt[b];
      }}
    }});
    return {{ nbin, labels,
      gpct: gp.map((v, b) => tot[b] ? Math.round(100 * v / tot[b]) : 0),
      rpct: rp.map((v, b) => tot[b] ? Math.round(100 * v / tot[b]) : 0),
      tpct: gp.map((v, b) => tot[b] ? Math.round(100 * (v + rp[b]) / tot[b]) : 0),
      nG, nR }};
  }}

  function lineTraces(xs, vals, prov, color, sym, name, width, msize) {{
    return [
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(0, prov), y: vals.slice(0, prov),
        name: name, line: {{ color: color, width: width }},
        marker: {{ size: msize, symbol: sym, color: color, line: {{ color: "#FFFFFF", width: 1.1 }} }},
        hovertemplate: "%{{x}} · " + name + " %{{y}}%<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: vals.slice(prov - 1),
        showlegend: false, line: {{ color: color, width: width, dash: "dot" }},
        marker: {{ size: msize, symbol: sym, color: ["rgba(0,0,0,0)", "#FFFFFF"],
                 line: {{ color: color, width: 1.2 }} }},
        hovertemplate: "%{{x}} · " + name + " %{{y}}%<extra></extra>" }},
    ];
  }}

  function render() {{
    const C = compute();
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 1, xs = C.labels;
    const traces = [
      ...lineTraces(xs, C.tpct, prov, GREY_TOT, "circle", "핵심 필진 전체", 1.8, 5),
      ...lineTraces(xs, C.gpct, prov, GOLD, "circle", "인철과 출신 핵심 (" + C.nG + "명)", 2.2, 7),
      ...lineTraces(xs, C.rpct, prov, INK, "square", "비인철과 출신 핵심 (" + C.nR + "명)", 2.2, 7),
    ];
    const annos = [];
    for (let i = 1; i < C.nbin; i++) {{
      annos.push({{ x: xs[i], y: C.gpct[i], yref: "y", yshift: 11, text: "<b>" + C.gpct[i] + "%</b>",
        showarrow: false, bgcolor: "rgba(255,255,255,0.85)", borderpad: 1,
        font: {{ color: GOLD, size: SM ? 9 : 10.5 }} }});
      annos.push({{ x: xs[i], y: C.rpct[i], yref: "y", yshift: C.rpct[i] >= 16 ? -12 : 12,
        text: "<b>" + C.rpct[i] + "%</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.85)", borderpad: 1,
        font: {{ color: INK, size: SM ? 9 : 10.5 }} }});
      if (C.rpct[i] > 2) {{
        annos.push({{ x: xs[i], y: C.tpct[i], yref: "y",
          yshift: (C.tpct[i] - C.gpct[i]) >= 10 ? 10 : 15,
          text: C.tpct[i] + "%", showarrow: false,
          bgcolor: "rgba(255,255,255,0.85)", borderpad: 1,
          font: {{ color: "#8A867B", size: SM ? 8.5 : 10 }} }});
      }}
    }}
    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 20, t: 56, b: 40 }}, height: 440,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 12.5, color: MUTED }} }},
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [0, 100], tickvals: [0, 20, 40, 60, 80, 100],
              title: {{ text: "전체 논문 중 비중 (%)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    document.getElementById("sh-def").textContent = "핵심 = 그 구간까지 누적 " + N + "편 이상";
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-sh-w", v => {{ W = v; }});
  segWire("seg-sh-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 440,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_핵심논문_비중추이",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-sh-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-sh-svg").addEventListener("click", () => capture("svg"));

  render();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def dept_flow_chart() -> str:
    """인도철학과 ③: 핵심 필진의 시기별 유입·이탈 (출신별 발산 막대 + 증감 선).
    변수 = 구간 폭(4/5년), 핵심 기준(2~5편)."""
    return f"""
<div class="panel">
  <h2>핵심 필진의 시기별 유입·이탈</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-fl-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-fl-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-fl-png">PNG 저장</button><button id="dl-fl-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-fl"></div>
  <div id="fl-names" class="names-box"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 ·
    <span id="fl-def">유입 = 해당 구간 3편째 게재</span> · 이탈 = 이전 구간 마지막 게재 후 미게재 ·
    마지막 구간은 진행 중(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/dongguk_indophil_theses.csv">dongguk_indophil_theses.csv</a></div>
</div>

<script>
(function () {{
  const AS = KSIP_AS;
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const GREY_D = "#A8A294";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-fl");
  let W = 4, N = 3, lastC = null;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const z = () => Array(nbin).fill(0);
    const nz = () => Array.from({{ length: nbin }}, () => []);
    const entG = z(), entR = z(), exiG = z(), exiR = z();
    const entGN = nz(), entRN = nz(), exiGN = nz(), exiRN = nz();
    AS.forEach(d => {{
      if (d.y.length < N) return;
      const eb = bin(d.y[N - 1]), xb = bin(d.y[d.y.length - 1]);
      (d.s ? entG : entR)[eb]++; (d.s ? entGN : entRN)[eb].push(d.nm);
      (d.s ? exiG : exiR)[xb]++; (d.s ? exiGN : exiRN)[xb].push(d.nm);
    }});
    const shift = a => [0].concat(a.slice(0, -1));   // 이탈 = 마지막 게재 다음 구간
    const shiftN = a => [[]].concat(a.slice(0, -1));
    const xg = shift(exiG), xr = shift(exiR);
    const net = entG.map((v, b) => v + entR[b] - xg[b] - xr[b]);
    return {{ nbin, labels, entG, entR, exiG: xg, exiR: xr, net,
             nm: {{ entG: entGN, entR: entRN, exiG: shiftN(exiGN), exiR: shiftN(exiRN) }} }};
  }}

  function render() {{
    const C = compute();
    lastC = C;
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 1, xs = C.labels;
    const provOp = i => i === prov ? 0.5 : 1;
    const pat = {{ shape: xs.map((_, i) => i === prov ? "/" : ""),
                 fillmode: "overlay", fgcolor: "#FFFFFF", size: 5, solidity: 0.4 }};
    const bar = (vals, color, name, show, side, key) => ({{
      type: "bar", x: xs, y: vals, name: name, showlegend: !!show, width: 0.7,
      meta: key,
      marker: {{ color: color, opacity: xs.map((_, i) => provOp(i)), pattern: pat,
               line: {{ color: "#FFFFFF", width: 0.8 }} }},
      hovertemplate: "%{{x}} · " + name + " " + side + " %{{customdata}}명<extra></extra>",
      customdata: vals.map(v => Math.abs(v)),
    }});
    const traces = [
      bar(C.entG, GOLD, "인철과 출신", true, "유입", "entG"),
      bar(C.entR, GREY_D, "그 외", true, "유입", "entR"),
      bar(C.exiG.map(v => -v), GOLD, "인철과 출신", false, "이탈", "exiG"),
      bar(C.exiR.map(v => -v), GREY_D, "그 외", false, "이탈", "exiR"),
      // 증감 선
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(0, prov), y: C.net.slice(0, prov),
        name: "증감", line: {{ color: INK, width: 2 }},
        marker: {{ size: 6.5, symbol: "diamond", color: INK, line: {{ color: "#FFFFFF", width: 1.1 }} }},
        hovertemplate: "%{{x}} · 증감 %{{y}}명<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.net.slice(prov - 1),
        showlegend: false, line: {{ color: INK, width: 2, dash: "dot" }},
        marker: {{ size: 6.5, symbol: "diamond", color: ["rgba(0,0,0,0)", "#FFFFFF"],
                 line: {{ color: INK, width: 1.2 }} }},
        hovertemplate: "%{{x}} · 증감 %{{y}}명<extra></extra>" }},
    ];
    const annos = [];
    for (let i = 0; i < C.nbin; i++) {{
      const up = C.entG[i] + C.entR[i], dn = C.exiG[i] + C.exiR[i];
      if (up > 0) annos.push({{ x: xs[i], y: up, yref: "y", yshift: 9, text: String(up),
        showarrow: false, font: {{ color: MUTED, size: SM ? 9 : 10.5 }} }});
      if (dn > 0) annos.push({{ x: xs[i], y: -dn, yref: "y", yshift: -9, text: String(dn),
        showarrow: false, font: {{ color: MUTED, size: SM ? 9 : 10.5 }} }});
      annos.push({{ x: xs[i], y: C.net[i], yref: "y", xshift: 13,
        text: "<b>" + (C.net[i] > 0 ? "+" : "") + C.net[i] + "</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.9)", borderpad: 1,
        font: {{ color: INK, size: SM ? 8.5 : 10 }} }});
    }}
    const hi = Math.max.apply(null, C.entG.map((v, b) => v + C.entR[b]));
    const lo = Math.max.apply(null, C.exiG.map((v, b) => v + C.exiR[b]));
    const layout = {{
      barmode: "relative", bargap: 0.3,
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 20, t: 56, b: 40 }}, height: 440,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [-(lo * 1.25 + 2), hi * 1.25 + 2],
              title: {{ text: "유입(+) · 이탈(−) (명)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, zeroline: true, zerolinecolor: MUTED, zerolinewidth: 1,
              tickfont: {{ color: MUTED }}, fixedrange: true }},
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    document.getElementById("fl-def").textContent = "유입 = 해당 구간 " + N + "편째 게재";
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    resetNames();
  }}

  const box = document.getElementById("fl-names");
  const HINT = '<span class="nb-hint">막대의 각 조각에 마우스를 올리면 '
    + '그 조각에 집계된 필자 이름이 여기에 나열됩니다.</span>';
  function resetNames() {{ box.innerHTML = HINT; }}
  const KEYLAB = {{ entG: ["유입", "인철과 출신", GOLD], entR: ["유입", "그 외", MUTED],
                  exiG: ["이탈", "인철과 출신", GOLD], exiR: ["이탈", "그 외", MUTED] }};
  function showNames(key, bi) {{
    if (!lastC) return;
    const names = lastC.nm[key][bi].slice().sort((a, b) => a.localeCompare(b, "ko"));
    const L = KEYLAB[key];
    box.innerHTML =
      '<div class="nb-head"><b>' + lastC.labels[bi] + '</b> · ' + L[0]
      + ' · <span style="color:' + L[2] + '">' + L[1] + '</span> · ' + names.length + '명</div>'
      + '<div class="nb-names">' + (names.join(", ") || "없음") + '</div>';
  }}
  function wireHover() {{
    gd.on("plotly_hover", function (ev) {{
      const pt = ev.points && ev.points[0];
      if (!pt || !lastC) return;
      const key = pt.data && pt.data.meta;
      if (!key || !lastC.nm[key]) return;
      const bi = lastC.labels.indexOf(pt.x);
      if (bi >= 0) showNames(key, bi);
    }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-fl-w", v => {{ W = v; }});
  segWire("seg-fl-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 440,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_핵심필진_유입이탈_출신별",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-fl-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-fl-svg").addEventListener("click", () => capture("svg"));

  render();
  wireHover();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def _core_kci() -> list[dict]:
    """핵심 필진(평생 3편 이상, 70명)별 인도철학 주저자 연도(j) + KCI 전체 출판(k: [연도, 인도철학 여부]).
    헌신성 06·09의 입력. 핵심 기준 변수는 3~5편만 지원(KCI 수집 로스터가 3편 기준이라 2편은 데이터 없음)."""
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    authors = pd.read_parquet(ROOT / "data" / "processed" / "authors.parquet")
    papers["주저자"] = papers["논문 ID"].map(
        authors.sort_index().groupby("논문ID")["저자_원본"].first())
    ks = papers["주저자"] == "김성철"
    papers.loc[ks, "주저자"] = ["김성철#유식" if "금강" in str(a) else "김성철#중관"
                                for a in papers.loc[ks, "주저자 소속기관"].fillna("")]
    papers.loc[papers["주저자"] == "김미숙", "주저자"] = "김미숙#자이나"
    jp = papers[papers["발행연도"].notna() & papers["주저자"].notna()].copy()
    jp["발행연도"] = jp["발행연도"].astype(int)
    life = jp.groupby("주저자").size()
    core = set(life[life >= 3].index)

    def load(pub, summ):
        s = pd.read_csv(ROOT / "data" / "raw" / summ, dtype=str, keep_default_na=False)
        stem2pid = {p.replace("#", "_"): p for p in s["person_id"]}
        d = pd.read_csv(ROOT / "data" / "raw" / pub, dtype=str, keep_default_na=False)
        d["person_id"] = d["author"].map(stem2pid)
        return d[d["person_id"].notna()]

    K = pd.concat([load("core_authors_kci_publications.csv", "core_authors_summary.csv"),
                   load("non_core_authors_kci_publications.csv", "non_core_authors_summary.csv")],
                  ignore_index=True)
    K = K[K["person_id"].isin(core)].drop_duplicates(["person_id", "artiId"])
    assert not core - set(K["person_id"])

    def disp(pid: str) -> str:
        if "#" in pid:
            b, s = pid.split("#", 1)
            return f"{b}({s})"
        return pid

    jy = jp.groupby("주저자")["발행연도"].apply(lambda s: sorted(int(v) for v in s))
    emb = []
    for pid in sorted(core):
        kk = K[K["person_id"] == pid]
        ky = sorted((int(y), int(j == "인도철학"))
                    for y, j in zip(pd.to_numeric(kk["pub_year"], errors="coerce"), kk["journal"])
                    if pd.notna(y))
        emb.append({"nm": disp(pid), "j": jy[pid], "k": [list(t) for t in ky]})
    assert len(emb) == 70
    return emb


def commit_data_script() -> str:
    names, ay = _author_years(with_names=True)
    return (f"<script>const KSIP_AY = {json.dumps(ay)};"
            f"const KSIP_AN = {json.dumps(names, ensure_ascii=False)};"
            f"const KSIP_KCI = {json.dumps(_core_kci())};</script>")


def debut_chart() -> str:
    """헌신성 ①: 데뷔 시기별 일회성 필자 비율. 변수 = 구간 폭(4/5년), 핵심 기준(2~5편)."""
    return f"""
<div class="panel">
  <h2>데뷔 시기별 일회성 필자 비율</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-db-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-db-n">
        <button data-v="2">2편</button><button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-db-png">PNG 저장</button><button id="dl-db-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-db"></div>
  <div id="db-names" class="names-box"></div>
  <div class="panel-foot">주저자 기준 · 동명이인 분리 · 데뷔 = 첫 게재 ·
    <span id="db-def">일회성 = 평생 3편 미만</span> ·
    마지막 두 코호트는 관찰 기간이 짧음(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
</div>

<script>
(function () {{
  const AY = KSIP_AY;
  const AN = KSIP_AN;                      // KSIP_AY와 같은 순서의 표시용 이름
  const INK = "{INK}", MUTED = "{MUTED}", GRID = "{GRID}";
  const MID = "#A8A294", LITE = "#D8D5CC";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-db");
  let W = 4, N = 3, lastC = null;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const c1 = Array(nbin).fill(0), cm = Array(nbin).fill(0), cn = Array(nbin).fill(0);
    const oneNm = Array.from({{ length: nbin }}, () => []);   // 코호트별 일회성(N편 미만) 필자
    AY.forEach((years, ai) => {{
      const bd = bin(years[0]);
      cn[bd]++;
      if (years.length === 1) c1[bd]++;
      else if (years.length < N) cm[bd]++;
      if (years.length < N) oneNm[bd].push(AN[ai]);
    }});
    const one = c1.map((v, i) => cn[i] ? Math.round(100 * v / cn[i]) : 0);
    const tot = c1.map((v, i) => cn[i] ? Math.round(100 * (v + cm[i]) / cn[i]) : 0);
    return {{ nbin, labels, one, two: tot.map((t, i) => t - one[i]), tot, cn, oneNm }};
  }}

  function render() {{
    const C = compute();
    lastC = C;
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 2, xs = C.labels;            // 마지막 두 코호트 = 잠정
    const pat = i => i >= prov ? "/" : "";
    const traces = [
      {{ type: "bar", x: xs, y: C.one, name: "1편", width: 0.7,
        marker: {{ color: LITE, pattern: {{ shape: xs.map((_, i) => pat(i)),
                 fillmode: "overlay", fgcolor: "#FFFFFF", size: 5, solidity: 0.4 }} }},
        customdata: C.cn, hovertemplate: "%{{x}} 데뷔 %{{customdata}}명 · 1편 %{{y}}%<extra></extra>" }},
    ];
    if (N > 2) traces.push(
      {{ type: "bar", x: xs, y: C.two, name: N === 3 ? "2편" : "2–" + (N - 1) + "편", width: 0.7,
        marker: {{ color: MID, pattern: {{ shape: xs.map((_, i) => pat(i)),
                 fillmode: "overlay", fgcolor: "#FFFFFF", size: 5, solidity: 0.4 }} }},
        hovertemplate: "%{{x}} · " + (N === 3 ? "2편" : "2–" + (N - 1) + "편") + " %{{y}}%p<extra></extra>" }});
    traces.push(
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(0, prov), y: C.tot.slice(0, prov),
        name: "일회성(" + N + "편 미만) 비율", line: {{ color: INK, width: 2 }},
        marker: {{ size: 7, color: INK, line: {{ color: "#FFFFFF", width: 1.3 }} }},
        hovertemplate: "%{{x}} · 일회성 %{{y}}%<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.tot.slice(prov - 1),
        name: "일회성(" + N + "편 미만) 비율", showlegend: false,
        line: {{ color: INK, width: 2, dash: "dot" }},
        marker: {{ size: 7, color: xs.slice(prov - 1).map((_, k) => k === 0 ? INK : "#FFFFFF"),
                 line: {{ color: INK, width: 1.3 }} }},
        hovertemplate: "%{{x}} · 일회성 %{{y}}%<extra></extra>" }});
    const annos = C.tot.map((t, i) => ({{ x: xs[i], y: t, yref: "y", yshift: 10,
      text: "<b>" + t + "</b>", showarrow: false,
      bgcolor: "rgba(255,255,255,0.85)", borderpad: 1,
      font: {{ color: INK, size: SM ? 9 : 10.5 }} }}));
    const layout = {{
      barmode: "stack", bargap: 0.3,
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 20, t: 56, b: 40 }}, height: 420,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [0, 115], tickvals: [0, 20, 40, 60, 80, 100],
              title: {{ text: "데뷔 코호트 중 비율 (%)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      shapes: [{{ type: "rect", x0: prov - 0.5, x1: C.nbin - 0.5, y0: 0, y1: 115,
               xref: "x", yref: "y", fillcolor: GRID, opacity: 0.35, line: {{ width: 0 }},
               layer: "below" }}],
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    document.getElementById("db-def").textContent = "일회성 = 평생 " + N + "편 미만";
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    resetNames();
  }}

  const box = document.getElementById("db-names");
  const HINT = '<span class="nb-hint"><b>꼭지점</b>(일회성 비율)에 마우스를 올리면 '
    + '그 코호트의 일회성 필자 이름이 여기에 나열됩니다.</span>';
  function resetNames() {{ box.innerHTML = HINT; }}
  function showNames(bi) {{
    if (!lastC) return;
    const names = lastC.oneNm[bi].slice().sort((a, b) => a.localeCompare(b, "ko"));
    box.innerHTML =
      '<div class="nb-head"><b>' + lastC.labels[bi] + '</b> · 일회성(' + N + '편 미만) · '
      + names.length + '명 <span class="nb-hint">(데뷔 ' + lastC.cn[bi] + '명 중)</span></div>'
      + '<div class="nb-names">' + (names.join(", ") || "없음") + '</div>';
  }}
  function wireHover() {{
    gd.on("plotly_hover", function (ev) {{
      const pt = ev.points && ev.points[0];
      if (!pt || !lastC) return;
      const nm = (pt.data && pt.data.name) || "";
      if (nm.indexOf("일회성") !== 0) return;
      const bi = lastC.labels.indexOf(pt.x);
      if (bi >= 0) showNames(bi);
    }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-db-w", v => {{ W = v; }});
  segWire("seg-db-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 1080, height: 380,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_데뷔코호트_일회성비율",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-db-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-db-svg").addEventListener("click", () => capture("svg"));

  render();
  wireHover();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def kci_activity_chart() -> str:
    """헌신성 ②: 활동 핵심 필진과 그중 인도철학 게재 수. 변수 = 구간 폭(4/5년), 핵심 기준(3~5편)."""
    return f"""
<div class="panel">
  <h2>KCI 활동 핵심 필진과 『인도철학』 게재 핵심 필진의 수</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-ka-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-ka-n">
        <button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-ka-png">PNG 저장</button><button id="dl-ka-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-ka"></div>
  <div id="ka-names" class="names-box"></div>
  <div class="panel-foot">
    <span id="ka-def">핵심 = 『인도철학』 누적 3편 도달 시점부터</span> ·
    활동 = 그 구간 KCI 등재(후보)지 게재 · 마지막 구간은 진행 중(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/core_authors_kci_publications.csv">core_authors_kci_publications.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/non_core_authors_kci_publications.csv">non_core_authors_kci_publications.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a></div>
</div>

<script>
(function () {{
  const KC = KSIP_KCI;
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-ka");
  let W = 4, N = 3, lastC = null;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const act = Array(nbin).fill(0), indo = Array(nbin).fill(0);
    const indoNm = Array.from({{ length: nbin }}, () => []);
    const outNm = Array.from({{ length: nbin }}, () => []);
    KC.forEach(p => {{
      if (p.j.length < N) return;
      const cnt = Array(nbin).fill(0);
      p.j.forEach(y => cnt[bin(y)]++);
      const cum = []; let c = 0;
      for (let i = 0; i < nbin; i++) {{ c += cnt[i]; cum.push(c); }}
      const kAny = Array(nbin).fill(false), kIndo = Array(nbin).fill(false);
      p.k.forEach(pair => {{ const b = bin(pair[0]); kAny[b] = true; if (pair[1]) kIndo[b] = true; }});
      for (let i = 0; i < nbin; i++) {{
        if (!kAny[i] || cum[i] < N) continue;
        act[i]++;
        if (kIndo[i]) {{ indo[i]++; indoNm[i].push(p.nm); }}
        else outNm[i].push(p.nm);
      }}
    }});
    return {{ nbin, labels, act, indo, indoNm, outNm,
             undercov: bin(2000),
             pctOut: act.map((a, i) => a ? Math.round(100 * (a - indo[i]) / a) : 0) }};
  }}

  function render() {{
    const C = compute();
    lastC = C;
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 1, xs = C.labels;
    const yMax = Math.max.apply(null, C.act) * 1.22;
    const traces = [
      {{ type: "scatter", mode: "lines", x: xs, y: C.indo, showlegend: false,
        line: {{ width: 0 }}, hoverinfo: "skip" }},
      {{ type: "scatter", mode: "lines", x: xs, y: C.act, showlegend: false,
        fill: "tonexty", fillcolor: "rgba(205,199,184,0.6)",
        line: {{ width: 0 }}, hoverinfo: "skip" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(0, prov), y: C.act.slice(0, prov),
        name: "KCI 활동 핵심", line: {{ color: INK, width: 1.9 }},
        marker: {{ size: 6, color: INK, line: {{ color: "#FFFFFF", width: 1 }} }},
        hovertemplate: "%{{x}} · 활동 %{{y}}명<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.act.slice(prov - 1),
        showlegend: false, line: {{ color: INK, width: 1.9, dash: "dot" }},
        marker: {{ size: 6, color: ["rgba(0,0,0,0)", "#FFFFFF"], line: {{ color: INK, width: 1.2 }} }},
        hovertemplate: "%{{x}} · 활동 %{{y}}명<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(0, prov), y: C.indo.slice(0, prov),
        name: "『인도철학』 게재", line: {{ color: GOLD, width: 2.3 }},
        marker: {{ size: 6, color: GOLD, line: {{ color: "#FFFFFF", width: 1 }} }},
        hovertemplate: "%{{x}} · 게재 %{{y}}명<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.indo.slice(prov - 1),
        name: "『인도철학』 게재", showlegend: false, line: {{ color: GOLD, width: 2.3, dash: "dot" }},
        marker: {{ size: 6, color: ["rgba(0,0,0,0)", "#FFFFFF"], line: {{ color: GOLD, width: 1.2 }} }},
        hovertemplate: "%{{x}} · 게재 %{{y}}명<extra></extra>" }},
    ];
    // 음영 밴드(밖에서만 활동) 위 투명 마커 — 호버 감지용. 밴드 내부를 촘촘히 덮어 어디에 올려도 잡히게.
    const bx = [], by = [];
    for (let i = 0; i < C.nbin; i++) {{
      const g = C.act[i] - C.indo[i];
      if (g <= 0) continue;
      const steps = Math.max(2, Math.min(14, Math.round(g)));
      for (let s = 1; s <= steps; s++) {{ bx.push(xs[i]); by.push(C.indo[i] + g * s / (steps + 1)); }}
    }}
    traces.push({{ type: "scatter", mode: "markers", x: bx, y: by, name: "__band__",
      showlegend: false, hoverinfo: "none", marker: {{ size: 18, color: "rgba(0,0,0,0)" }} }});
    const annos = [];
    C.act.forEach((a, i) => {{
      if (a) annos.push({{ x: xs[i], y: a, yref: "y", yshift: 11, text: "<b>" + a + "</b>",
        showarrow: false, bgcolor: "rgba(255,255,255,0.85)", borderpad: 1,
        font: {{ color: INK, size: SM ? 9 : 10.5 }} }});
      if (C.indo[i] && C.indo[i] !== a) annos.push({{ x: xs[i], y: C.indo[i], yref: "y",
        yshift: -11, text: "<b>" + C.indo[i] + "</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.85)", borderpad: 1,
        font: {{ color: GOLD, size: SM ? 9 : 10.5 }} }});
    }});
    for (let i = C.nbin - 2; i < C.nbin; i++) {{
      if (C.act[i] - C.indo[i] >= 3) annos.push({{ x: xs[i], y: (C.act[i] + C.indo[i]) / 2,
        yref: "y", text: "<b>" + C.pctOut[i] + "%</b>", showarrow: false,
        font: {{ color: MUTED, size: SM ? 9.5 : 11 }} }});
    }}
    annos.push({{ x: xs[Math.max(1, Math.floor(C.undercov / 2))], y: yMax * 0.94,
      yref: "y", text: "KCI 초기 미커버(밖=0 인공값)", showarrow: false,
      font: {{ color: MUTED, size: 10.5 }} }});
    // 음영 밴드(『인도철학』 밖에서만 활동) 화살표 라벨 — 정적 그림과 동일, 밴드 가장 넓은 확정 구간을 가리킴
    const gaps = C.act.map((a, i) => a - C.indo[i]);
    let bb = -1, bbG = 3;
    for (let i = C.undercov + 1; i <= C.nbin - 3; i++) {{ if (gaps[i] > bbG) {{ bbG = gaps[i]; bb = i; }} }}
    if (bb >= 0) annos.push({{ x: xs[bb], y: (C.act[bb] + C.indo[bb]) / 2, yref: "y",
      ax: -48, ay: -52, text: "인도철학 밖에서만 활동", showarrow: true,
      arrowhead: 2, arrowsize: 1, arrowwidth: 1, arrowcolor: MUTED,
      bgcolor: "rgba(255,255,255,0.8)", borderpad: 1,
      font: {{ color: MUTED, size: SM ? 9.5 : 11 }} }});
    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 20, t: 56, b: 40 }}, height: 440, hovermode: "closest",
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 12.5, color: MUTED }} }},
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [0, yMax],
              title: {{ text: "핵심 필진 수 (명)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      shapes: [{{ type: "rect", x0: -0.5, x1: C.undercov + 0.5, y0: 0, y1: yMax,
               xref: "x", yref: "y", fillcolor: GRID, opacity: 0.4,
               line: {{ width: 0 }}, layer: "below" }}],
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    document.getElementById("ka-def").textContent =
      "핵심 = 『인도철학』 누적 " + N + "편 도달 시점부터";
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    resetNames();
  }}

  const box = document.getElementById("ka-names");
  const HINT = '<span class="nb-hint"><b style="color:' + GOLD + '">금색 꼭지점</b>'
    + '(그 구간 『인도철학』 게재 필자) 또는 <b>음영 밴드</b>(그 구간 인도철학 밖에서만 활동한 필자)에 '
    + '마우스를 올리면 해당 필자 이름이 여기에 나열됩니다.</span>';
  function resetNames() {{ box.innerHTML = HINT; }}
  function showNames(kind, bi) {{
    if (!lastC) return;
    const names = (kind === "indo" ? lastC.indoNm[bi] : lastC.outNm[bi]).slice()
      .sort((a, b) => a.localeCompare(b, "ko"));
    const label = kind === "indo" ? "『인도철학』 게재" : "인도철학 밖에서만 활동";
    const color = kind === "indo" ? GOLD : MUTED;
    box.innerHTML =
      '<div class="nb-head"><b>' + lastC.labels[bi] + '</b> · <span style="color:' + color
      + '">' + label + '</span> · ' + names.length + '명</div>'
      + '<div class="nb-names">' + (names.join(", ") || "없음") + '</div>';
  }}
  function wireHover() {{
    gd.on("plotly_hover", function (ev) {{
      const pt = ev.points && ev.points[0];
      if (!pt || !lastC) return;
      const nm = (pt.data && pt.data.name) || "";
      let kind = null;
      if (nm === "__band__") kind = "out";
      else if (nm.indexOf("게재") >= 0) kind = "indo";
      if (!kind) return;
      const bi = lastC.labels.indexOf(pt.x);
      if (bi >= 0) showNames(kind, bi);
    }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-ka-w", v => {{ W = v; }});
  segWire("seg-ka-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 440,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_활동핵심_게재수",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-ka-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-ka-svg").addEventListener("click", () => capture("svg"));

  render();
  wireHover();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


def devotion_chart() -> str:
    """헌신성 ③: 게재 핵심의 평균 헌신도. 변수 = 구간 폭(4/5년), 핵심 기준(3~5편)."""
    return f"""
<div class="panel">
  <h2>『인도철학』 게재 핵심 필진의 평균 헌신도</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-dv-w">
        <button data-v="2">2년</button><button data-v="3">3년</button><button data-v="4" class="on">4년</button><button data-v="5">5년</button>
      </span></div>
    <div class="ctl"><span class="ctl-label">핵심 기준</span>
      <span class="seg" id="seg-dv-n">
        <button data-v="3" class="on">3편</button><button data-v="4">4편</button><button data-v="5">5편</button>
      </span></div>
    <div class="dl">
      <button id="dl-dv-png">PNG 저장</button><button id="dl-dv-svg">SVG 저장</button>
    </div>
  </div>
  <div id="chart-dv"></div>
  <div id="dv-names" class="names-box"></div>
  <div class="panel-foot">헌신도 = 그 구간 자기 KCI 논문 중 『인도철학』 비율(게재 핵심만 평균) ·
    N = 게재 핵심 수 · 마지막 구간은 진행 중(잠정) <br>자료:
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/core_authors_kci_publications.csv">core_authors_kci_publications.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/raw/non_core_authors_kci_publications.csv">non_core_authors_kci_publications.csv</a> ·
    <a target="_blank" rel="noopener" href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a></div>
</div>

<script>
(function () {{
  const KC = KSIP_KCI;
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-dv");
  let W = 4, N = 3, lastC = null;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(b0 + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const sums = Array(nbin).fill(0), ncon = Array(nbin).fill(0);
    const dev = Array.from({{ length: nbin }}, () => []);   // 구간별 [이름, 개인 헌신도%]
    KC.forEach(p => {{
      if (p.j.length < N) return;
      const cnt = Array(nbin).fill(0);
      p.j.forEach(y => cnt[bin(y)]++);
      const cum = []; let c = 0;
      for (let i = 0; i < nbin; i++) {{ c += cnt[i]; cum.push(c); }}
      const tot = Array(nbin).fill(0), ind = Array(nbin).fill(0);
      p.k.forEach(pair => {{ const b = bin(pair[0]); tot[b]++; if (pair[1]) ind[b]++; }});
      for (let i = 0; i < nbin; i++) {{
        if (!ind[i] || cum[i] < N) continue;
        ncon[i]++;
        sums[i] += 100 * ind[i] / tot[i];
        dev[i].push([p.nm, Math.round(100 * ind[i] / tot[i])]);
      }}
    }});
    return {{ nbin, labels, ncon, dev,
             avg: sums.map((s, i) => ncon[i] ? Math.round(s / ncon[i]) : 0),
             undercov: bin(2000) }};
  }}

  function render() {{
    const C = compute();
    lastC = C;
    const SM = C.nbin > 10;                // 촘촘한 구간(2·3년) → 라벨 축소
    const prov = C.nbin - 1, xs = C.labels;
    let S = 0;
    while (S < C.nbin && C.ncon[S] === 0) S++;
    const traces = [
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(S, prov), y: C.avg.slice(S, prov),
        showlegend: false, line: {{ color: GOLD, width: 2.3 }},
        marker: {{ size: 7, color: GOLD, line: {{ color: "#FFFFFF", width: 1.1 }} }},
        hovertemplate: "%{{x}} · 평균 헌신도 %{{y}}%<extra></extra>" }},
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.avg.slice(prov - 1),
        showlegend: false, line: {{ color: GOLD, width: 2.3, dash: "dot" }},
        marker: {{ size: 7, color: ["rgba(0,0,0,0)", "#FFFFFF"], line: {{ color: GOLD, width: 1.3 }} }},
        hovertemplate: "%{{x}} · 평균 헌신도 %{{y}}%<extra></extra>" }},
    ];
    const annos = [];
    for (let i = S; i < C.nbin; i++) {{
      const v = C.avg[i], up = v < 95;
      annos.push({{ x: xs[i], y: v, yref: "y", yshift: up ? 10 : -12,
        text: "<b>" + v + "%</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.8)", borderpad: 1,
        font: {{ color: i <= C.undercov ? MUTED : INK, size: SM ? 9 : 10.5 }} }});
    }}
    C.ncon.forEach((n, i) => annos.push({{ x: xs[i], y: -13, yref: "y", text: "N=" + n,
      showarrow: false, font: {{ color: MUTED, size: SM ? 8.5 : 10 }} }}));
    annos.push({{ x: xs[Math.max(1, Math.floor(C.undercov / 2))], y: 14, yref: "y",
      text: "KCI 초기 미커버(헌신도 과대)", showarrow: false,
      font: {{ color: MUTED, size: 10.5 }} }});
    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 20, t: 20, b: 40 }}, height: 440,
      showlegend: false,
      xaxis: {{ tickangle: SM ? -45 : 0, tickfont: {{ color: INK, size: SM ? 10.5 : 12 }}, fixedrange: true }},
      yaxis: {{ range: [-20, 112], tickvals: [0, 25, 50, 75, 100],
              ticktext: ["0", "25", "50", "75", "100%"],
              title: {{ text: "평균 개인 헌신도 (자기 논문 중 %)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      shapes: [
        {{ type: "rect", x0: -0.5, x1: C.undercov + 0.5, y0: -20, y1: 112, xref: "x", yref: "y",
          fillcolor: GRID, opacity: 0.4, line: {{ width: 0 }}, layer: "below" }},
        {{ type: "rect", x0: prov - 0.5, x1: C.nbin - 0.5, y0: -20, y1: 112, xref: "x", yref: "y",
          fillcolor: GRID, opacity: 0.22, line: {{ width: 0 }}, layer: "below" }},
      ],
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    Plotly.react(gd, traces, layout, {{ displayModeBar: false, responsive: true }});
    resetNames();
  }}

  const box = document.getElementById("dv-names");
  const HINT = '<span class="nb-hint"><b style="color:' + GOLD + '">금색 꼭지점</b>에 '
    + '마우스를 올리면 그 구간 『인도철학』 게재 필자와 각자의 헌신도(%)가 여기에 나열됩니다.</span>';
  function resetNames() {{ box.innerHTML = HINT; }}
  function showNames(bi) {{
    if (!lastC) return;
    const list = lastC.dev[bi].slice()
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "ko"));   // 헌신도 내림차순, 동률은 가나다순
    box.innerHTML =
      '<div class="nb-head"><b>' + lastC.labels[bi] + '</b> · <span style="color:' + GOLD
      + '">『인도철학』 게재</span> · ' + list.length + '명 · 평균 ' + lastC.avg[bi] + '%</div>'
      + '<div class="nb-names">' + (list.map(p => p[0] + "(" + p[1] + "%)").join(", ") || "없음") + '</div>';
  }}
  function wireHover() {{
    gd.on("plotly_hover", function (ev) {{
      const pt = ev.points && ev.points[0];
      if (!pt || !lastC) return;
      const bi = lastC.labels.indexOf(pt.x);
      if (bi >= 0 && lastC.ncon[bi] > 0) showNames(bi);
    }});
  }}

  function segWire(id, fn) {{
    document.getElementById(id).addEventListener("click", e => {{
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll("#" + id + " button").forEach(b => b.classList.toggle("on", b === btn));
      fn(parseInt(btn.dataset.v, 10));
      render();
    }});
  }}
  segWire("seg-dv-w", v => {{ W = v; }});
  segWire("seg-dv-n", v => {{ N = v; }});

  async function capture(fmt) {{
    await Plotly.relayout(gd, {{ paper_bgcolor: "#FFFFFF", plot_bgcolor: "#FFFFFF" }});
    try {{
      await Plotly.downloadImage(gd, {{
        format: fmt, width: 960, height: 440,
        scale: fmt === "png" ? 4 : 1,
        filename: "인도철학_게재핵심_평균헌신도",
      }});
    }} finally {{
      await Plotly.relayout(gd, {{ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)" }});
    }}
  }}
  document.getElementById("dl-dv-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-dv-svg").addEventListener("click", () => capture("svg"));

  render();
  wireHover();
  if (document.fonts) document.fonts.ready.then(render);
}})();
</script>
"""


PENDING = '<div class="panel"><div class="pending">그래프 준비 중</div></div>'


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    contents = {
        "index.html": (overview_chart(), True),
        "core-authors.html": (ay_script() + asymmetry_chart() + top_authors_chart()
                              + activity_chart() + stockflow_chart(), True),
        "department.html": (dept_data_script() + dept_composition_chart()
                            + dept_share_chart() + dept_flow_chart(), True),
        "commitment.html": (commit_data_script() + debut_chart()
                            + kci_activity_chart() + devotion_chart(), True),
    }
    for slug, title in PAGES:
        body, needs_plotly = contents[slug]
        html = page(slug, title, body, plotly=needs_plotly)
        (DOCS / slug).write_text(html, encoding="utf-8")
        print(f"docs/{slug} 생성 ({len(html):,}자)")


if __name__ == "__main__":
    main()
