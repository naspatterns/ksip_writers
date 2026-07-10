#!/usr/bin/env python3
"""저자별 KCI 출판 CSV들을 필진 그룹별 단일 CSV로 병합한다.

원본 (ksip_transition, 저자 1인당 1파일, 파일명 = 저자 식별자):
  - data/kci/collect/*.csv        → 핵심 필진 79명
  - data/kci/collect_비인철/*.csv → 비인철 학자 41명

출력 (data/raw/):
  - core_authors_kci_publications.csv
  - non_core_authors_kci_publications.csv

원본 CSV 컬럼: artiId, pub_year, journal, categories, title, n_authors, authors, affil
출력 CSV 컬럼: author + 위 8개 컬럼
(*.prebak 등 백업 파일은 제외한다)

사용법:
    python3 scripts/merge_author_publications.py [ksip_transition_경로]
"""
import csv
import sys
from pathlib import Path

DEFAULT_TRANSITION = Path(
    "/Users/jibak/Documents/@CLASSES/2026-1/DigitalHumanities/ksip_transition"
)
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

JOBS = [
    ("data/kci/collect", "core_authors_kci_publications.csv"),
    ("data/kci/collect_비인철", "non_core_authors_kci_publications.csv"),
]


def merge(src: Path, out: Path) -> None:
    files = sorted(p for p in src.glob("*.csv") if p.suffix == ".csv")
    if not files:
        sys.exit(f"원본 CSV를 찾을 수 없음: {src}")

    header_out = None
    n_rows = 0
    with out.open("w", newline="", encoding="utf-8-sig") as f_out:
        writer = csv.writer(f_out)
        for path in files:
            author = path.stem
            with path.open(newline="", encoding="utf-8-sig") as f_in:
                reader = csv.reader(f_in)
                header = next(reader)
                if header_out is None:
                    header_out = ["author"] + header
                    writer.writerow(header_out)
                elif ["author"] + header != header_out:
                    sys.exit(f"컬럼 불일치: {path.name} → {header}")
                for row in reader:
                    writer.writerow([author] + row)
                    n_rows += 1

    print(f"저자 {len(files)}명, 논문 {n_rows}행 → {out.name}")


def main() -> None:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TRANSITION
    for subdir, out_name in JOBS:
        merge(base / subdir, RAW / out_name)


if __name__ == "__main__":
    main()
