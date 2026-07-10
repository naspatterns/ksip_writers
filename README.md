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
