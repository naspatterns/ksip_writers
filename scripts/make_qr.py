#!/usr/bin/env python3
"""대시보드 QR 코드 생성 — 단축 서비스 경유 없이 주소를 직접 인코딩.

(기존 graph/3_dashboard_qrcode.png 는 qrto.org 단축 링크 경유 — 서비스 만료·추적
위험이 있어 직접 인코딩 버전을 별도 생성한다. 기존 파일은 건드리지 않음.)

산출: docs/qr.png (사이트 우측 dock용, 잉크색 모듈)
     graph/3_dashboard_qrcode_direct.png (논문 인쇄용 1024px, 흑백)

사용법: python3 scripts/make_qr.py
"""
from pathlib import Path

import qrcode

ROOT = Path(__file__).resolve().parent.parent
URL = "https://naspatterns.github.io/ksip_writers/"
INK_DEEP = "#131211"


def make(box: int, fill: str, out: Path) -> None:
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=box, border=2)
    q.add_data(URL)
    q.make(fit=True)
    img = q.make_image(fill_color=fill, back_color="white")
    img.save(out)
    print(f"{out.relative_to(ROOT)} ({img.size[0]}px, {out.stat().st_size:,}B)")


def main() -> None:
    make(12, INK_DEEP, ROOT / "docs" / "qr.png")                       # 사이트 dock용
    make(32, "black", ROOT / "graph" / "3_dashboard_qrcode_direct.png")  # 논문 인쇄용


if __name__ == "__main__":
    main()
