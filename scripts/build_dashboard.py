#!/usr/bin/env python3
"""data/를 읽어 GitHub Pages용 정적 대시보드(docs/)를 생성한다.

구성: 상단 제목 배너 + 왼쪽 섹션 탭 + 콘텐츠.
페이지: index.html(개관) · core-authors.html(핵심 필진) ·
        department.html(인도철학과) · commitment.html(헌신성)

차트 공통 규격:
  - 조절 변수 1–2개 (버튼 그룹)
  - 캡처 버튼: PNG(4배율, 흰 배경) + SVG — 사용자가 조절한 현재 상태 그대로 저장
  - 그래프 아래 원본 데이터 링크(GitHub 파일 페이지)
  - 해석적 설명 없음. 범례·각주는 의미 왜곡을 막는 최소한만.

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


def page(slug: str, title: str, content: str, *, plotly: bool = False) -> str:
    nav = "\n".join(
        f'      <a href="{s}"{" class=\"on\"" if s == slug else ""}>{t}</a>'
        for s, t in PAGES)
    plotly_tag = ('<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" '
                  'charset="utf-8"></script>' if plotly else "")
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
    원본 데이터와 수집·가공 과정은 <a href="{REPO}/blob/main/data/README.md">data/README.md</a> 참조</footer>
</body>
</html>
"""


def overview_chart() -> str:
    """개관: 연도별 논문 발행수. 변수 = 구간 폭(4년/5년/없음), 기간(전체/2000~/최근 10년)."""
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
  <div class="panel-foot">자료:
    <a href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a></div>
</div>

<script>
(function () {{
  const D = {data_js};
  const INK = "{INK}", MUTED = "{MUTED}", GRID = "{GRID}", BARBG = "{BARBG}";
  const gd = document.getElementById("chart-overview");
  let binw = 4, range = "all";

  function bins(w) {{
    const out = [];
    for (let b0 = 1989; b0 <= 2026; b0 += w) {{
      const b1 = Math.min(b0 + w - 1, 2026);
      const span = D.n.slice(b0 - 1989, b1 - 1989 + 1);
      const avg = Math.round(span.reduce((a, c) => a + c, 0) / span.length * 10) / 10;
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
    if (binw > 0) {{
      const B = bins(binw);
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
    traces.push({{
      type: "scatter", mode: "lines",
      x: D.years, y: D.n,
      line: {{ color: INK, width: 2 }},
      hovertemplate: "%{{x}}년 · %{{y}}편<extra></extra>",
      name: "연도별 발행 편수",
    }});
    const layout = {{
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 40, r: 16, t: 8, b: 36 }}, height: 420,
      hovermode: "x unified",
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
      showlegend: binw > 0,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.02, x: 0,
               font: {{ size: 13, color: MUTED }} }},
      bargap: 0,
      xaxis: {{ showgrid: false, zeroline: false, dtick: 5, range: xr,
              tickfont: {{ color: MUTED }} }},
      yaxis: {{ gridcolor: GRID, zeroline: false, rangemode: "tozero",
              tickfont: {{ color: MUTED }} }},
      annotations: [{{ x: 1990.2, y: 16.5, text: "휴간 1990–91", showarrow: false,
                     xanchor: "left", yanchor: "bottom",
                     font: {{ color: MUTED, size: 12 }} }}],
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
  <div class="panel-foot">주저자 기준 · 동명이인 분리 — 자료:
    <a href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
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
        customdata: ROWS.map(r => seg[r.key] + r.unit),
        hovertemplate: seg.name + " · %{{customdata}} (%{{x}}%)<extra></extra>",
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
  document.getElementById("dl-asym-png").addEventListener("click", () => capture("png"));
  document.getElementById("dl-asym-svg").addEventListener("click", () => capture("svg"));

  render();
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
    life = papers.groupby("주저자").size().sort_values(ascending=False)
    top = [{"name": nm.replace("#", "("), "n": int(c)} for nm, c in life.head(30).items()]
    top = [{"name": t["name"] + ")" if "(" in t["name"] else t["name"], "n": t["n"]}
           for t in top]
    assert top[0] == {"name": "정승석", "n": 31}, top[0]

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
  <div class="panel-foot">주저자 기준 · 동명이인 분리 — 자료:
    <a href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
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
      hovertemplate: "%{{y}} · %{{x}}편<extra></extra>",
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
}})();
</script>
"""


def _author_years() -> list[list[int]]:
    """주저자(동명이인 분리)별 발행연도 목록 — 시계열 차트들의 공통 입력."""
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    authors = pd.read_parquet(ROOT / "data" / "processed" / "authors.parquet")
    papers["주저자"] = papers["논문 ID"].map(
        authors.sort_index().groupby("논문ID")["저자_원본"].first())
    ks = papers["주저자"] == "김성철"
    papers.loc[ks, "주저자"] = ["김성철#유식" if "금강" in str(a) else "김성철#중관"
                                for a in papers.loc[ks, "주저자 소속기관"].fillna("")]
    papers.loc[papers["주저자"] == "김미숙", "주저자"] = "김미숙#자이나"
    jp = papers[papers["발행연도"].notna() & papers["주저자"].notna()]
    return [sorted(int(y) for y in g) for _, g in jp.groupby("주저자")["발행연도"]]


def ay_script() -> str:
    """주저자별 발행연도 목록을 페이지 전역(KSIP_AY)으로 1회 임베드."""
    ay = _author_years()
    assert len(ay) == 207 and sum(len(a) for a in ay) == 641
    return f"<script>const KSIP_AY = {json.dumps(ay)};</script>"


def activity_chart() -> str:
    """핵심 필진 ③: 시기별 활동 필자 수 + 핵심 논문 점유율.
    변수 = 구간 폭(4/5년), 핵심 기준(누적 2/3/4/5편)."""
    return f"""
<div class="panel">
  <h2>시기별 활동 필자 수</h2>
  <div class="panel-bar">
    <div class="ctl"><span class="ctl-label">구간</span>
      <span class="seg" id="seg-act-w">
        <button data-v="4" class="on">4년</button><button data-v="5">5년</button>
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
  <div class="panel-foot">주저자 기준 · 동명이인 분리 · 마지막 구간은 진행 중(잠정) — 자료:
    <a href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
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
      labels.push(String(b0 % 100).padStart(2, "0") + "–" + String(b1 % 100).padStart(2, "0"));
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
        hovertemplate: "%{{x}} · 점유율 %{{y}}%<extra></extra>" }},
      // 잠정 구간 점선 + 빈 마커
      {{ type: "scatter", mode: "lines+markers", x: xs.slice(prov - 1), y: C.share.slice(prov - 1),
        yaxis: "y2", showlegend: false,
        line: {{ color: INK, width: 2, dash: "dot" }},
        marker: {{ size: 7, color: ["rgba(0,0,0,0)", "#FFFFFF"],
                 line: {{ color: INK, width: 1.2 }} }},
        hovertemplate: "%{{x}} · 점유율 %{{y}}%<extra></extra>" }},
    ];

    const annos = [];
    C.core.forEach((c, i) => {{               // 핵심 수 라벨
      if (c === 0) return;
      const inside = c >= 15;
      annos.push({{ x: xs[i], y: inside ? c / 2 : c + 1.4, yref: "y",
        text: "<b>" + c + "</b>", showarrow: false,
        yanchor: inside ? "middle" : "bottom",
        font: {{ color: inside ? (i === prov ? INK : "#FFFFFF") : GOLD, size: 12 }} }});
    }});
    C.total.forEach((t, i) => {{              // 활동 총계 라벨 (막대 위)
      annos.push({{ x: xs[i], y: t + 1.6, yref: "y", text: String(t), showarrow: false,
        yanchor: "bottom", font: {{ color: MUTED, size: 10.5 }} }});
    }});
    C.share.forEach((s, i) => {{              // 점유율 값 라벨 (마커 위)
      annos.push({{ x: xs[i], y: s, yref: "y2", yshift: 11, text: "<b>" + s + "</b>",
        showarrow: false, font: {{ color: INK, size: 10.5 }} }});
    }});

    const layout = {{
      barmode: "stack", bargap: 0.3,
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 56, t: 30, b: 40 }}, height: 460,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ tickfont: {{ color: INK, size: 12 }}, fixedrange: true }},
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
        <button data-v="4" class="on">4년</button><button data-v="5">5년</button>
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
  <div class="panel-foot">주저자 기준 · 동명이인 분리 ·
    <span id="sf-def">유입 = 3편째 게재</span> · 이탈 = 마지막 게재 후 미게재 ·
    마지막 구간은 진행 중(잠정) — 자료:
    <a href="{REPO}/blob/main/data/processed/papers.csv">papers.csv</a> ·
    <a href="{REPO}/blob/main/data/processed/authors.csv">authors.csv</a></div>
</div>

<script>
(function () {{
  const AY = KSIP_AY;
  const INK = "{INK}", MUTED = "{MUTED}", GOLD = "{GOLD}", GRID = "{GRID}";
  const GRAY = "#CDC7B8", RUST = "#9E4A2E";
  const Y0 = 1989, Y1 = 2026;
  const gd = document.getElementById("chart-sf");
  let W = 4, N = 3;

  function compute() {{
    const nbin = Math.floor((Y1 - Y0) / W) + 1;
    const bin = y => Math.min(Math.floor((y - Y0) / W), nbin - 1);
    const labels = [];
    for (let i = 0; i < nbin; i++) {{
      const b0 = Y0 + i * W, b1 = Math.min(b0 + W - 1, Y1);
      labels.push(String(b0 % 100).padStart(2, "0") + "–" + String(b1 % 100).padStart(2, "0"));
    }}
    const core = Array(nbin).fill(0), total = Array(nbin).fill(0);
    const ent = Array(nbin).fill(0), exi = Array(nbin).fill(0);
    AY.forEach(years => {{
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
        ent[bin(years[N - 1])]++;                     // 유입 = N편째 게재 구간
        exi[bin(years[years.length - 1])]++;          // 마지막 게재 구간
      }}
    }});
    const exiShift = [0].concat(exi.slice(0, -1));    // 이탈 = 그다음 구간
    return {{ nbin, labels, core, noncore: total.map((t, b) => t - core[b]),
             total, ent, exi: exiShift }};
  }}

  function render() {{
    const C = compute();
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
        x: xs.slice(prov - 1), y: vals.slice(prov - 1), yaxis: "y2", showlegend: false,
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
        font: {{ color: INK, size: 10.5 }} }});
      annos.push({{ x: xs[i], y: x2, yref: "y2",
        yshift: (close || x2 < 2) ? 12 : -13, xshift: close ? 11 : 0,
        text: "<b>" + x2 + "</b>", showarrow: false,
        bgcolor: "rgba(255,255,255,0.92)", borderpad: 1,
        font: {{ color: RUST, size: 10.5 }} }});
    }});

    const yMax = Math.max.apply(null, C.total) * 1.15;
    const y2Max = Math.max.apply(null, C.ent.concat(C.exi)) * 1.3 + 2;
    const layout = {{
      barmode: "stack", bargap: 0.3,
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {{ family: "'Noto Sans KR', sans-serif", color: INK, size: 14 }},
      margin: {{ l: 56, r: 56, t: 30, b: 40 }}, height: 460,
      legend: {{ orientation: "h", yanchor: "bottom", y: 1.04, x: 0,
               traceorder: "normal", font: {{ size: 13, color: MUTED }} }},
      xaxis: {{ tickfont: {{ color: INK, size: 12 }}, fixedrange: true }},
      yaxis: {{ range: [0, yMax],
              title: {{ text: "활동 필자 수 (명)", font: {{ color: MUTED, size: 12 }} }},
              gridcolor: GRID, tickfont: {{ color: MUTED }}, fixedrange: true }},
      yaxis2: {{ range: [0, y2Max], overlaying: "y", side: "right",
               title: {{ text: "핵심 유입·이탈 (명)", font: {{ color: MUTED, size: 12 }} }},
               showgrid: false, tickfont: {{ color: MUTED }}, fixedrange: true }},
      annotations: annos,
      hoverlabel: {{ bgcolor: "#FFFFFF", bordercolor: GRID, font: {{ color: INK }} }},
    }};
    document.getElementById("sf-def").textContent = "유입 = " + N + "편째 게재";
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
        "department.html": (PENDING, False),
        "commitment.html": (PENDING, False),
    }
    for slug, title in PAGES:
        body, needs_plotly = contents[slug]
        html = page(slug, title, body, plotly=needs_plotly)
        (DOCS / slug).write_text(html, encoding="utf-8")
        print(f"docs/{slug} 생성 ({len(html):,}자)")


if __name__ == "__main__":
    main()
