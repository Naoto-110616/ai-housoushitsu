#!/usr/bin/env python3
"""各言語のカバーアート (cover.png, 1400x1400) を生成する。既に存在する言語はスキップ。"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LANGS = CONFIG["languages"]

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]


def find_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    raise RuntimeError("フォントが見つかりません (fonts-noto-cjk をインストールしてください)")


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
    size = start_size
    while size > 40:
        font = find_font(size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 10
    return find_font(size)


def make_cover(out: Path, title: str, subtitle: str) -> None:
    if out.exists():
        print(f"skip (exists): {out}")
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

    title_font = fit_font(d, title, 1240, 190)
    sub_font = fit_font(d, subtitle, 1100, 56)
    tw = d.textlength(title, font=title_font)
    d.text(((size - tw) / 2, 780), title, font=title_font, fill=(231, 233, 238))
    sw = d.textlength(subtitle, font=sub_font)
    d.text(((size - sw) / 2, 1020), subtitle, font=sub_font, fill=(255, 176, 120))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print(f"wrote {out}")


def main() -> None:
    for code, lc in LANGS.items():
        out = (DOCS / lc["dir"] / "cover.png") if lc["dir"] else (DOCS / "cover.png")
        make_cover(out, lc["title"], lc.get("subtitle", ""))


if __name__ == "__main__":
    main()
