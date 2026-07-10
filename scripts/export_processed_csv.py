#!/usr/bin/env python3
"""data/processed/의 parquet 파일들을 사람이 읽을 수 있는 CSV로 변환한다.

parquet이 분석용 정본이고, CSV는 깃허브에서 바로 열람하기 위한 사본이다.
parquet이 갱신되면 이 스크립트를 다시 실행한다.

사용법:
    python3 scripts/export_processed_csv.py
"""
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


def main() -> None:
    for pq in sorted(PROCESSED.glob("*.parquet")):
        out = pq.with_suffix(".csv")
        df = pd.read_parquet(pq)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"{pq.name}: {len(df)}행 {len(df.columns)}열 → {out.name}")


if __name__ == "__main__":
    main()
