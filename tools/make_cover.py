#!/usr/bin/env python3
"""カバーアート (docs/cover.png, 1400x1400) を生成する。既に存在する場合は何もしない。"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "cover.png"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]


def find_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    raise RuntimeError("日本語フォントが見つかりません (fonts-noto-cjk をインストールしてください)")


def main() -> None:
    if OUT.exists():
        print("cover.png already exists, skip")
        return

    size = 1400
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)

    top = (15, 17, 21)
    bottom = (120, 45, 20)
    for y in range(size):
        t = y / size
        d.line(
            [(0, y), (size, y)],
            fill=tuple(int(a + (b - a) * t * t) for a, b in zip(top, bottom)),
        )

    cx, cy = size // 2, 470
    for r, alpha in [(150, 90), (240, 60), (330, 35), (420, 20)]:
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 138, 60, alpha), width=10)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    mic_c = (255, 138, 60)
    d.rounded_rectangle([cx - 62, cy - 150, cx + 62, cy + 30], radius=62, fill=mic_c)
    d.arc([cx - 110, cy - 80, cx + 110, cy + 100], start=0, end=180, fill=(231, 233, 238), width=16)
    d.line([(cx, cy + 100), (cx, cy + 170)], fill=(231, 233, 238), width=16)
    d.line([(cx - 70, cy + 175), (cx + 70, cy + 175)], fill=(231, 233, 238), width=16)

    title_font = find_font(190)
    sub_font = find_font(56)
    title = CONFIG["title"]
    tw = d.textlength(title, font=title_font)
    d.text(((size - tw) / 2, 760), title, font=title_font, fill=(231, 233, 238))
    sub = "全自動 AI ポッドキャスト"
    sw = d.textlength(sub, font=sub_font)
    d.text(((size - sw) / 2, 1010), sub, font=sub_font, fill=(255, 176, 120))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
