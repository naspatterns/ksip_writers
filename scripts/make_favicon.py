#!/usr/bin/env python3
"""표지 모티프 파비콘 생성 — 잉크 바탕 + 세로 골드 밴드(괘선 무늬) + 헤어라인.

대시보드 배너("표지의 잔상")와 동일한 문법을 탭 아이콘 크기로 축소.
산출(docs/): favicon.svg · favicon-32.png · favicon-16.png · favicon.ico(16/32/48)
            · apple-touch-icon.png(180, iOS 홈 화면용)

사용법: python3 scripts/make_favicon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# build_dashboard.py 팔레트와 동일
INK_DEEP = (19, 18, 17)        # #131211
GOLD_SOFT = (200, 155, 36)     # #C89B24 (밴드 상단)
GOLD = (184, 145, 31)          # #B8911F (밴드 하단)
PAPER = (250, 249, 245)        # #FAF9F5 (괘선)
HAIR = (228, 226, 218)         # #E4E2DA (헤어라인)

X0, X1 = 0.25, 0.57            # 골드 밴드 좌우 위치 (표지 세로 밴드 비율 인용)


def draw(size: int, scale: int = 16) -> Image.Image:
    """scale배 슈퍼샘플링으로 그린 뒤 LANCZOS 축소 — 작은 크기에서도 경계가 선명."""
    s = size * scale
    img = Image.new("RGB", (s, s), INK_DEEP)
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1 = round(s * X0), round(s * X1)

    # 밴드: 세로 그라디언트 gold_soft → gold
    for y in range(s):
        t = y / s
        c = tuple(round(GOLD_SOFT[i] * (1 - t) + GOLD[i] * t) for i in range(3))
        d.line([(x0, y), (x1 - 1, y)], fill=c)

    # 괘선(界線): 밴드 안 가로 밝은 골드 선 8개 (배너 무늬와 동일 알파 ~0.13)
    step = s // 8
    lw = max(1, s // 56)
    for y in range(step // 2, s, step):
        d.rectangle([x0, y, x1 - 1, y + lw - 1], fill=PAPER + (33,))

    # 헤어라인: 밴드 양측 (표지의 검정|헤어라인|골드 경계, 알파 0.4)
    hw = max(1, s // 72)
    d.rectangle([x0 - hw, 0, x0 - 1, s], fill=HAIR + (102,))
    d.rectangle([x1, 0, x1 + hw - 1, s], fill=HAIR + (102,))

    return img.resize((size, size), Image.LANCZOS)


SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#C89B24"/><stop offset="1" stop-color="#B8911F"/>
</linearGradient>
<pattern id="r" width="64" height="8" patternUnits="userSpaceOnUse">
<rect width="64" height="8" fill="url(#g)"/>
<rect y="3.5" width="64" height="1" fill="#FAF9F5" fill-opacity="0.13"/>
</pattern>
</defs>
<rect width="64" height="64" fill="#131211"/>
<rect x="{X0 * 64:g}" width="{(X1 - X0) * 64:g}" height="64" fill="url(#r)"/>
<rect x="{X0 * 64 - 0.9:g}" width="0.9" height="64" fill="#E4E2DA" fill-opacity="0.4"/>
<rect x="{X1 * 64:g}" width="0.9" height="64" fill="#E4E2DA" fill-opacity="0.4"/>
</svg>
"""


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / "favicon.svg").write_text(SVG, encoding="utf-8")
    draw(32).save(DOCS / "favicon-32.png")
    draw(16).save(DOCS / "favicon-16.png")
    draw(180).save(DOCS / "apple-touch-icon.png")
    draw(48).save(DOCS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    for f in ["favicon.svg", "favicon-32.png", "favicon-16.png",
              "apple-touch-icon.png", "favicon.ico"]:
        print(f"docs/{f} ({(DOCS / f).stat().st_size:,}B)")


if __name__ == "__main__":
    main()
