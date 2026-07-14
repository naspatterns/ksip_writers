# ksip_writers

논문 **「<인도철학>은 왜 점점 얇아지고 있는가? — 핵심 필진, 인도철학과, 그리고 헌신성으로 본 <인도철학> 필진 구성의 추이」**의 공개 데이터·대시보드 저장소.

한국인도철학회 학술지 **<인도철학>**(1989~, KCI 등재)의 필진 구성 변화를 데이터로 분석한 연구의 재현용 원본 데이터와, 논문과 함께 공개하는 인터랙티브 대시보드(GitHub Pages)를 담고 있다.

**대시보드: https://naspatterns.github.io/ksip_writers/**

## 구성

```
data/
├── raw/          # 수집 원본 데이터 (수정 금지) — 상세는 data/README.md
├── processed/    # 가공 데이터 (scripts/로 생성)
└── README.md     # 데이터 사전: 파일별 출처·컬럼·행수
scripts/          # 데이터 가공 및 대시보드 차트 생성 스크립트
docs/             # GitHub Pages 정적 대시보드 (Plotly HTML)
```

## 대시보드

논문의 장 구조를 따르는 4개 탭, 인터랙티브 차트 11개. 상단 배너 + 좌측 탭 레이아웃.

| 탭 (페이지) | 차트 | 조절 변수 |
|---|---|---|
| 개관 (`index.html`) | 연도별 논문 발행수 | 구간 폭(4/5년/없음) · 기간(전체/2000~/최근 10년) |
| 핵심 필진 (`core-authors.html`) | 필자·논문 비대칭 / 누적 게재 상위 필자 / 시기별 활동 필자 / 핵심 유입·이탈(스톡플로우) | 핵심 기준(2~5편) · 상위 N명 · 구간 폭 |
| 인도철학과 (`department.html`) | 출신 구성 3막대(조각 호버 연동) / 출신별 핵심 논문 비중 추이 / 유입·이탈 발산 막대 | 구간 폭 · 핵심 기준 |
| 헌신성 (`commitment.html`) | 데뷔 코호트 일회성 비율 / KCI 활동 핵심·게재 / 평균 개인 헌신도 | 구간 폭 · 핵심 기준(②③은 3~5편만 — KCI 수집 로스터가 3편 기준) |

**공통 기능** — 모든 차트에 적용:
- 조절 변수는 버튼 그룹으로 단순하게, 데이터는 페이지에 임베드되어 브라우저에서 실시간 재계산
- **PNG 저장**(4배율·흰 배경, 논문 삽입 품질)·**SVG 저장** — 사용자가 조절한 현재 상태 그대로 캡처
- 그래프 아래 원본 데이터 링크(GitHub 파일 페이지, 새 탭)
- 해석적 설명 없음 — 범례·각주는 의미 왜곡을 막는 최소한만 (예: 휴간·잠정 구간·KCI 미커버 표시)
- 기본값(4년 구간·3편 기준)의 모든 수치는 논문 그림 생성 스크립트의 검증값과 일치 확인됨

**방문 통계** — 대시보드는 [GoatCounter](https://www.goatcounter.com)로 페이지뷰를 집계한다
(쿠키·localStorage 미사용, IP 미저장, 개인 식별 정보 미수집 — 페이지 풋터에도 고지).

### 대시보드 재생성

```bash
pip install -r requirements.txt
python3 scripts/build_dashboard.py   # data/ → docs/*.html 생성
```

배포는 GitHub Pages (main 브랜치 `/docs` 폴더). push하면 1~2분 내 자동 반영.

## 데이터 출처

| 데이터 | 출처 | 파일 |
|---|---|---|
| <인도철학> 발행 논문 전체 (636/641편) | KCI 웹 반출 / KCI OpenAPI | `data/raw/kci_journal_articles_{export,api}.csv` |
| 동국대 인도철학과 석·박사 학위논문 (246건) | 동국대 dCollection | `data/raw/dongguk_indophil_theses.csv` |
| 핵심 필진 79명의 KCI 전체 출판 (1,230편) | KCI OpenAPI | `data/raw/core_authors_kci_publications.csv` |
| 비인철 학자 41명의 KCI 전체 출판 (774편) | KCI OpenAPI | `data/raw/non_core_authors_kci_publications.csv` |

## 재현

KCI OpenAPI로 데이터를 재수집하려면 API 키가 필요하다. 키는 저장소에 포함하지 않으며, 환경변수 `KSIP_KCI_API_KEY`로 전달한다.

```bash
export KSIP_KCI_API_KEY="발급받은 키"
```

> 이 저장소의 사본은 GitHub이 원본이다. 로컬 작업 사본이 손상되면 GitHub에서 다시 클론한다.
