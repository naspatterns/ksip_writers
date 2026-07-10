#!/usr/bin/env python3
"""data/를 읽어 GitHub Pages용 정적 대시보드(docs/)를 생성한다.

현재 페이지: index.html (랜딩 + 서론 차트 '연도별 논문 발행수')
장별 상세 페이지는 이후 단계에서 추가한다.

사용법:
    python3 scripts/build_dashboard.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# 논문 표지 팔레트
INK = "#1C1B19"
GOLD = "#B8911F"
MUTED = "#6E675C"
GRID = "#E4E2DA"
BARBG = "#EFE9DA"
PAPER = "#FAF9F5"

YEAR0, YEAR1, BINW = 1989, 2026, 4


def yearly_chart() -> str:
    papers = pd.read_parquet(ROOT / "data" / "processed" / "papers.parquet")
    counts = papers["발행연도"].dropna().astype(int).value_counts()
    years = list(range(YEAR0, YEAR1 + 1))
    n = [int(counts.get(y, 0)) for y in years]
    assert sum(n) == 641, sum(n)

    # 4년 구간 연평균 (마지막 구간은 2년)
    bins = []
    for b0 in range(YEAR0, YEAR1 + 1, BINW):
        b1 = min(b0 + BINW - 1, YEAR1)
        span = [c for y, c in zip(years, n) if b0 <= y <= b1]
        bins.append((b0, b1, round(sum(span) / len(span), 1)))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[(b0 + b1) / 2 for b0, b1, _ in bins],
        y=[avg for *_, avg in bins],
        width=[b1 - b0 + 0.8 for b0, b1, _ in bins],
        marker_color=BARBG, marker_line_width=0,
        text=[f"{avg}" for *_, avg in bins],
        textposition="inside", insidetextanchor="start", textangle=0,
        constraintext="none",
        textfont=dict(color=MUTED, size=11),
        customdata=[[f"{b0}–{b1}"] for b0, b1, _ in bins],
        hovertemplate="%{customdata[0]} 연평균 %{y}편<extra></extra>",
        name="4년 구간 연평균",
    ))
    fig.add_trace(go.Scatter(
        x=years, y=n, mode="lines",
        line=dict(color=INK, width=2),
        hovertemplate="%{x}년 · %{y}편<extra></extra>",
        name="연도별 발행 편수",
    ))
    fig.add_annotation(x=1990.2, y=16.5, text="휴간 1990–91", showarrow=False,
                       font=dict(color=MUTED, size=12), xanchor="left", yanchor="bottom")
    fig.add_annotation(x=2014, y=36, text="2014년 36편", showarrow=False,
                       font=dict(color=MUTED, size=12), yshift=12)
    fig.update_layout(
        template="none", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Noto Sans KR', sans-serif", color=INK, size=14),
        margin=dict(l=40, r=16, t=8, b=36), height=420,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID, font=dict(color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=13, color=MUTED)),
        bargap=0,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color=MUTED),
                     dtick=5, range=[YEAR0 - 0.8, YEAR1 + 0.8])
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED),
                     rangemode="tozero")
    return fig.to_html(full_html=False, include_plotlyjs="cdn",
                       config={"displayModeBar": False, "responsive": True})


SECTIONS = [
    ("서론", "쇠퇴의 첫인상", "연도별 발행 편수가 그려내는 최근 10년의 하강 곡선."),
    ("핵심 필진", "첫 번째 압박", "학술지를 지탱해 온 핵심 필진층이 얇아지고 있다."),
    ("인도철학과", "두 번째 압박", "핵심 필진을 길러내던 제도적 기반이 사라졌다."),
    ("헌신성", "세 번째 압박", "남은 필진의 <인도철학>에 대한 헌신도가 떨어지고 있다."),
]


def build_index() -> None:
    chart = yearly_chart()
    cards = "\n".join(
        f'''      <div class="card">
        <div class="card-kicker">{kicker}</div>
        <h3>{name}</h3>
        <p>{desc}</p>
        <span class="badge">준비 중</span>
      </div>'''
        for name, kicker, desc in SECTIONS)

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>&lt;인도철학&gt;은 왜 점점 얇아지고 있는가?</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
<style>
  :root {{ --ink:{INK}; --gold:{GOLD}; --muted:{MUTED}; --grid:{GRID}; --paper:{PAPER}; }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ background:var(--paper); color:var(--ink); font-family:'Noto Sans KR',sans-serif;
         line-height:1.7; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:960px; margin:0 auto; padding:0 24px; }}
  header {{ padding:72px 0 40px; border-bottom:1px solid var(--grid); }}
  .kicker {{ color:var(--gold); font-weight:700; letter-spacing:.14em; font-size:.82rem; }}
  h1 {{ font-family:'Noto Serif KR',serif; font-size:clamp(1.6rem,4vw,2.4rem); line-height:1.35; margin:.5em 0 .3em; }}
  .subtitle {{ color:var(--muted); font-size:1.02rem; max-width:44em; }}
  section {{ padding:48px 0; }}
  h2 {{ font-family:'Noto Serif KR',serif; font-size:1.3rem; margin-bottom:.4em; }}
  .note {{ color:var(--muted); font-size:.9rem; }}
  .chart {{ margin-top:20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-top:24px; }}
  .card {{ border:1px solid var(--grid); border-radius:10px; padding:20px; background:#fff; }}
  .card-kicker {{ color:var(--gold); font-size:.78rem; font-weight:700; letter-spacing:.1em; }}
  .card h3 {{ font-family:'Noto Serif KR',serif; margin:.3em 0; font-size:1.05rem; }}
  .card p {{ color:var(--muted); font-size:.88rem; }}
  .badge {{ display:inline-block; margin-top:12px; padding:2px 10px; border-radius:99px;
           border:1px solid var(--grid); color:var(--muted); font-size:.75rem; }}
  footer {{ border-top:1px solid var(--grid); padding:32px 0 56px; color:var(--muted); font-size:.85rem; }}
  a {{ color:var(--ink); }}
</style>
</head>
<body>
  <header><div class="wrap">
    <div class="kicker">데이터로 읽는 학술지</div>
    <h1>&lt;인도철학&gt;은 왜 점점 얇아지고 있는가?</h1>
    <p class="subtitle">핵심 필진, 인도철학과, 그리고 헌신성으로 본 &lt;인도철학&gt; 필진 구성의 추이.
    논문과 함께 공개하는 인터랙티브 대시보드입니다.</p>
  </div></header>

  <section><div class="wrap">
    <h2>『인도철학』 연도별 논문 발행수</h2>
    <p class="note">전수 641편 · 제1–76집 (1989–2026) · 배경 막대 = 4년 구간 연평균 (막대 안 숫자).
    원자료는 <a href="https://github.com/">저장소의 data/</a>에서 표로 열람할 수 있습니다.</p>
    <div class="chart">{chart}</div>
  </section></div>

  <section><div class="wrap">
    <h2>세 가지 압박</h2>
    <div class="grid">
{cards}
    </div>
  </div></section>

  <footer><div class="wrap">
    자료: KCI(한국학술지인용색인) · 동국대학교 dCollection —
    수집·가공 과정과 원본 데이터는 저장소의 <code>data/README.md</code> 참조.
  </div></footer>
</body>
</html>
'''
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"docs/index.html 생성 ({len(html):,}자)")


if __name__ == "__main__":
    build_index()
