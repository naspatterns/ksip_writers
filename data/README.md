# 데이터 사전 (Data Dictionary)

논문 「<인도철학>은 왜 점점 얇아지고 있는가?」의 분석에 사용된 데이터.

- `raw/` — 수집한 원본 데이터. **직접 수정하지 않는다.**
- `processed/` — `scripts/`의 스크립트가 `raw/`를 가공해 생성한 데이터. 각 파일의 생성 스크립트를 아래에 명시한다.

모든 파일은 UTF-8(BOM) 인코딩 CSV이다. 파일명은 영문, 데이터 내용(저자명·논문명 등)은 한국어 원문 그대로다.

## 수록 범위 (제외한 것)

이 데이터는 서지 **사실**(제목·저자·연도·학술지명·소속 등)만 수록한다. Zenodo 공개본
([10.5281/zenodo.21319529](https://doi.org/10.5281/zenodo.21319529))과 동일한 기준이며, 다음은 수집 원본에 있었으나 제외했다.

- **저작물성 콘텐츠**: 논문 초록·영어초록(KCI), 학위논문 초록(dCollection), `title_en`에 혼입되어 있던 초록.
  제호(제목)는 저작권법상 저작물로 보호되지 않으므로 수록하고, 자유서술형 텍스트는 제외한다.
  전 파일에서 최장 텍스트 필드 = 논문 제목(248자).
- **개인정보**: 저자 개인 이메일이 포함된 `주저자_소속_원문` 컬럼. 수록된 인명·소속은 공개 출판된 서지 기록의 일부다.

분석에는 어느 것도 사용하지 않으므로, 제외해도 논문·대시보드의 모든 수치가 동일하게 재현된다.

---

## raw/

### 1. `kci_journal_articles_export.csv` — 학술지 <인도철학> 발행 논문 전체 (KCI 웹 반출)

- **행수**: 636편 (제1집 1989 ~ 제75집)
- **출처**: KCI(한국학술지인용색인, kci.go.kr) 웹사이트의 논문 반출 기능. 1회 최대 300편 제한으로 3회에 나누어 반출 후 병합.
- **원본 위치**: `ksip_transition/data/raw/인도철학_통합.csv` (원반출본: `인도철학_1_300.xls`, `인도철학_301_600.xls`, `인도철학_601_636.xls`)
- **컬럼** (24개): 유형, 논문 ID, 저자명, 주저자 소속기관, 논문명, 논문영어명, 학술지명, 저자키워드, 참고문헌 수, 인용된 총 횟수, 발행기관명, 발행연도, 발행일, 권, 호, 특별호, 시작 페이지, 끝 페이지, 논문번호, DOI, 주제분야, URL, KCI 등재 구분, 반출일

### 2. `kci_journal_articles_api.csv` — 학술지 <인도철학> 발행 논문 전체 (KCI OpenAPI)

- **행수**: 641편 (제1집 1989 ~ 제76집 2026; 웹 반출본에 없는 제76집 포함)
- **출처**: KCI OpenAPI `articleSearch` (학술지=인도철학). 수집 스크립트: `ksip_transition/src/transition/kci_journal_fetch.py`
- **원본 위치**: `ksip_transition/data/kci/journal_articles.csv`
- **컬럼** (9개): `artiId`(KCI 논문 ID), `pub_year`, `pub_mon`, `통권`, `volume`, `categories`(주제분야), `title_ko`, `title_en`, `authors`(세미콜론 구분 저자 목록)

### 3. `dongguk_indophil_theses.csv` — 동국대 인도철학과 석·박사 학위논문

- **행수**: 246건 (석사 및 박사)
- **출처**: 동국대학교 dCollection (dcollection.dongguk.edu) 메타데이터 수집. 지도교수는 일부 학위논문 인준서(PDF)에서 수동 보완 (`지도교수_수동입력여부` 컬럼으로 구분).
- **원본 위치**: `ksip_transition/data/indo_phil_degrees.csv`
- **컬럼** (23개): `detail_id`(dCollection ID), `student_ko`/`student_kr`/`student_kr_src`/`student_en`(학생 이름 표기), `person_id`(인물 식별자), `student_affil`, `degree`(석사/박사), `pub_year`, `degree_ym`(수여 연월), `dept_major`, `advisor`(지도교수), `지도교수_수동입력여부`, `title_ko`, `title_en`, `keywords`, `ddc`(듀이십진분류), `institution`, `pages`, `language`, `copyright`, `handle_uri`(dCollection 링크), `include_reason`(수록 판단 근거)

### 4. `core_authors_kci_publications.csv` — 핵심 필진의 KCI 등재(후보)지 출판 논문 전체

- **행수**: 1,230편 / 저자 79명
- **출처**: KCI OpenAPI로 핵심 필진 각각의 KCI 등재(후보)지 게재 논문을 수집. 동명이인은 저자명에 접미사로 구분 (예: `김성철_유식`, `김성철_중관`, `김미숙_자이나`). 수집 스크립트: `ksip_transition/src/transition/kci_collect_sadan.py`
- **원본 위치**: `ksip_transition/data/kci/collect/*.csv` (저자별 79개 파일) → `scripts/merge_core_authors.py`로 병합
- **컬럼** (9개): `author`(핵심 필진 이름, 병합 시 파일명에서 추가), `artiId`, `pub_year`, `journal`(게재 학술지), `categories`, `title`, `n_authors`(공저자 수), `authors`, `affil`(소속)

### 5. `core_authors_summary.csv` — 핵심 필진 요약표

- **행수**: 79명
- **출처**: 4번 데이터의 저자별 집계. 생성 스크립트: `ksip_transition/src/transition/kci_collect_sadan.py`
- **원본 위치**: `ksip_transition/data/kci/collection_summary.csv`
- **컬럼** (8개): `person_id`, `base_name`, `사단`(소속 학맥 그룹), `n_total`(KCI 전체 논문 수), `n_indo`(<인도철학> 게재 수), `n_anchors`(동정 확정 근거 논문 수), `인도철학_집중도`(n_indo/n_total), `top_journals`(주요 게재지)

### 6. `non_core_authors_kci_publications.csv` — 비인철 학자의 KCI 등재(후보)지 출판 논문 전체

- **행수**: 774편 / 저자 41명
- **출처**: 인도철학과 출신이 아닌(비인철) 현역 인도철학 연구자들의 KCI 출판 수집. 4번과 동일한 방식·컬럼.
- **원본 위치**: `ksip_transition/data/kci/collect_비인철/*.csv` (저자별 41개 파일) → `scripts/merge_author_publications.py`로 병합
- **컬럼** (9개): 4번과 동일

### 7. `non_core_authors_summary.csv` — 비인철 학자 요약표

- **행수**: 41명
- **원본 위치**: `ksip_transition/data/kci/collection_summary_비인철.csv`
- **컬럼**: 5번과 동일

---

## processed/

### `papers.parquet` / `papers.csv` — <인도철학> 발행 논문 정본 테이블

- **행수**: 641편 (제1~76집), 32열
- **출처**: raw의 KCI 반출본+API본을 클리닝·병합한 정본. 원 생성 파이프라인은 `ksip_transition/src/transition/` (원본: `ksip_transition/data/journal/papers.parquet`)
- 그래프·대시보드가 읽는 실질적 입력. parquet이 정본이고 CSV는 열람용 사본 (`scripts/export_processed_csv.py`로 변환).

### `authors.parquet` / `authors.csv` — 논문-저자 연결 테이블

- **행수**: 659행 (논문ID × 저자), 4열 (`논문ID`, `저자_원본` 등)
- **출처**: 위와 동일 파이프라인 (원본: `ksip_transition/data/journal/authors.parquet`)
- 주저자 판별(논문별 첫 저자)에 사용. 동명이인 분리(김성철#유식/#중관, 김미숙#자이나)는 각 그래프 스크립트 안에서 적용.
