#!/usr/bin/env python3
"""各言語の scripts と docs の mp3 から Podcast RSS とエピソード一覧ページを生成する。

出力:
    docs/feed.xml, docs/index.html               … 日本語
    docs/<lang>/feed.xml, docs/<lang>/index.html … 翻訳版
"""
import json
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LANGS = CONFIG["languages"]
JST = timezone(timedelta(hours=9))

GENRE_LABELS = {
    "ja": {"frontend": "フロントエンド", "ai_tech": "AI・テック", "theme": "テーマ回", "trivia": "雑学"},
    "en": {"frontend": "Frontend", "ai_tech": "AI & Tech", "theme": "Deep Dive", "trivia": "Trivia"},
    "es": {"frontend": "Frontend", "ai_tech": "IA y Tecnología", "theme": "A Fondo", "trivia": "Curiosidades"},
    "pt": {"frontend": "Frontend", "ai_tech": "IA e Tecnologia", "theme": "Aprofundado", "trivia": "Curiosidades"},
}

LANG_NAMES = {"ja": "日本語", "en": "English", "es": "Español", "pt": "Português"}

FOOTER_TEXT = {
    "ja": "エピソード選定・原稿・収録・投稿まで全自動で運用しています。",
    "en": "Episode selection, scripts, recording, and publishing are fully automated.",
    "es": "La selección de episodios, guiones, grabación y publicación están totalmente automatizadas.",
    "pt": "A seleção de episódios, roteiros, gravação e publicação são totalmente automatizadas.",
}


def fmt_duration(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def lang_paths(code: str) -> dict:
    d = LANGS[code]["dir"]
    return {
        "scripts": ROOT / "scripts" / d if d else ROOT / "scripts",
        "docs": DOCS / d if d else DOCS,
        "base": f"{CONFIG['baseUrl']}/{d}" if d else CONFIG["baseUrl"],
    }


def load_episodes(code: str) -> list[dict]:
    p = lang_paths(code)
    eps = []
    if not p["scripts"].exists():
        return eps
    for f in sorted(p["scripts"].glob("ep*.json")):
        ep = json.loads(f.read_text(encoding="utf-8"))
        mp3 = p["docs"] / "audio" / f"ep{ep['id']}.mp3"
        if not mp3.exists():
            print(f"[{code}] skip (no audio yet): ep{ep['id']}")
            continue
        info = MP3(mp3)
        ep["_size"] = mp3.stat().st_size
        ep["_duration"] = info.info.length
        ep["_url"] = f"{p['base']}/audio/ep{ep['id']}.mp3"
        y, m, d = map(int, ep["date"].split("-"))
        ep["_pub"] = datetime(y, m, d, 6, 0, 0, tzinfo=JST)
        eps.append(ep)
    eps.sort(key=lambda e: e["id"])
    return eps


def build_feed(code: str, eps: list[dict]) -> None:
    lc = LANGS[code]
    p = lang_paths(code)
    cover = f"{p['base']}/cover.png"
    site = f"{p['base']}/"
    labels = GENRE_LABELS.get(code, {})
    items = []
    for ep in reversed(eps):
        genre = labels.get(ep.get("genre", ""), "")
        desc = ep.get("description", "")
        if genre:
            desc = f"[{genre}] {desc}"
        desc += "\n\n" + lc["credit"]
        items.append(f"""    <item>
      <title>{escape(f"#{int(ep['id'])} {ep['title']}")}</title>
      <description>{escape(desc)}</description>
      <enclosure url="{escape(ep['_url'])}" length="{ep['_size']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(ep['_url'])}</guid>
      <pubDate>{format_datetime(ep['_pub'])}</pubDate>
      <itunes:duration>{fmt_duration(ep['_duration'])}</itunes:duration>
      <itunes:episode>{int(ep['id'])}</itunes:episode>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    now = format_datetime(datetime.now(timezone.utc))
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(lc['title'])}</title>
    <link>{escape(site)}</link>
    <language>{lc['language']}</language>
    <description>{escape(lc['description'])}</description>
    <atom:link href="{p['base']}/feed.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{escape(CONFIG['author'])}</itunes:author>
    <itunes:summary>{escape(lc['description'])}</itunes:summary>
    <itunes:owner>
      <itunes:name>{escape(CONFIG['author'])}</itunes:name>
      <itunes:email>{CONFIG['email']}</itunes:email>
    </itunes:owner>
    <itunes:image href="{cover}"/>
    <image>
      <url>{cover}</url>
      <title>{escape(lc['title'])}</title>
      <link>{escape(site)}</link>
    </image>
    <itunes:category text="{CONFIG['category']}"/>
    <itunes:explicit>{CONFIG['explicit']}</itunes:explicit>
    <itunes:type>episodic</itunes:type>
{chr(10).join(items)}
  </channel>
</rss>
"""
    p["docs"].mkdir(parents=True, exist_ok=True)
    (p["docs"] / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"[{code}] wrote feed.xml ({len(eps)} episodes)")


def build_index(code: str, eps: list[dict]) -> None:
    lc = LANGS[code]
    p = lang_paths(code)
    labels = GENRE_LABELS.get(code, {})
    rows = []
    for ep in reversed(eps):
        genre = labels.get(ep.get("genre", ""), "")
        rows.append(f"""      <article class="ep">
        <div class="meta"><span class="num">#{int(ep['id'])}</span><span class="genre">{escape(genre)}</span><span class="date">{ep['date']}</span><span class="dur">{fmt_duration(ep['_duration'])}</span></div>
        <h2>{escape(ep['title'])}</h2>
        <p>{escape(ep.get('description', ''))}</p>
        <audio controls preload="none" src="audio/ep{ep['id']}.mp3"></audio>
      </article>""")

    switch_links = []
    for other, ocfg in LANGS.items():
        if other == code:
            switch_links.append(f'<span class="lang active">{LANG_NAMES.get(other, other)}</span>')
        else:
            if LANGS[code]["dir"]:
                href = f"../{ocfg['dir']}/" if ocfg["dir"] else "../"
            else:
                href = f"{ocfg['dir']}/" if ocfg["dir"] else "./"
            switch_links.append(f'<a class="lang" href="{href}">{LANG_NAMES.get(other, other)}</a>')

    html = f"""<!doctype html>
<html lang="{lc['language']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(lc['title'])}</title>
<link rel="alternate" type="application/rss+xml" title="{escape(lc['title'])}" href="feed.xml">
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif; background: #0f1115; color: #e7e9ee; margin: 0; }}
.wrap {{ max-width: 720px; margin: 0 auto; padding: 32px 20px 80px; }}
header {{ display: flex; gap: 20px; align-items: center; margin-bottom: 8px; }}
header img {{ width: 96px; height: 96px; border-radius: 20px; }}
h1 {{ font-size: 26px; margin: 0; }}
.langs {{ display: flex; gap: 8px; margin: 14px 0 4px; flex-wrap: wrap; }}
.lang {{ font-size: 12.5px; color: #9aa3b2; text-decoration: none; border: 1px solid #272c38; border-radius: 999px; padding: 4px 12px; }}
.lang.active {{ color: #0f1115; background: #ff8a3c; border-color: #ff8a3c; font-weight: 600; }}
.desc {{ color: #9aa3b2; font-size: 14px; line-height: 1.8; }}
.rss {{ display: inline-block; margin: 12px 0 28px; color: #ff8a3c; text-decoration: none; font-size: 14px; border: 1px solid #3a2f24; padding: 6px 14px; border-radius: 999px; }}
.ep {{ background: #171a21; border: 1px solid #272c38; border-radius: 14px; padding: 20px; margin-bottom: 16px; }}
.ep h2 {{ font-size: 17px; margin: 8px 0; }}
.ep p {{ color: #9aa3b2; font-size: 13.5px; line-height: 1.8; margin: 0 0 12px; }}
.meta {{ display: flex; gap: 10px; font-size: 12px; color: #6b7280; align-items: center; }}
.num {{ color: #ff8a3c; font-weight: 700; }}
.genre {{ background: #232837; border-radius: 999px; padding: 2px 10px; }}
audio {{ width: 100%; }}
footer {{ margin-top: 40px; color: #6b7280; font-size: 12px; line-height: 1.9; }}
</style>
</head>
<body>
  <div class="wrap">
    <header><img src="cover.png" alt=""><h1>{escape(lc['title'])}</h1></header>
    <div class="langs">{''.join(switch_links)}</div>
    <p class="desc">{escape(lc['description'])}</p>
    <a class="rss" href="feed.xml">📡 RSS</a>
{chr(10).join(rows)}
    <footer>{escape(lc['credit'])}<br>{escape(FOOTER_TEXT.get(code, FOOTER_TEXT['en']))}</footer>
  </div>
</body>
</html>
"""
    (p["docs"] / "index.html").write_text(html, encoding="utf-8")
    print(f"[{code}] wrote index.html")


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    for code in LANGS:
        eps = load_episodes(code)
        build_feed(code, eps)
        build_index(code, eps)


if __name__ == "__main__":
    main()
