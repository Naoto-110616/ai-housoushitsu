#!/usr/bin/env python3
"""scripts/*.json と docs/audio/*.mp3 から Podcast RSS (docs/feed.xml) と
エピソード一覧ページ (docs/index.html) を生成する。"""
import json
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
JST = timezone(timedelta(hours=9))

GENRE_LABELS = {
    "frontend": "フロントエンド",
    "ai_tech": "AI・テック",
    "theme": "テーマ回",
    "trivia": "雑学",
}


def fmt_duration(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def load_episodes() -> list[dict]:
    eps = []
    for p in sorted((ROOT / "scripts").glob("ep*.json")):
        ep = json.loads(p.read_text(encoding="utf-8"))
        mp3 = DOCS / "audio" / f"ep{ep['id']}.mp3"
        if not mp3.exists():
            print(f"skip (no audio yet): ep{ep['id']}")
            continue
        info = MP3(mp3)
        ep["_size"] = mp3.stat().st_size
        ep["_duration"] = info.info.length
        ep["_url"] = f"{CONFIG['baseUrl']}/audio/ep{ep['id']}.mp3"
        y, m, d = map(int, ep["date"].split("-"))
        ep["_pub"] = datetime(y, m, d, 6, 0, 0, tzinfo=JST)
        eps.append(ep)
    eps.sort(key=lambda e: e["id"])
    return eps


def build_feed(eps: list[dict]) -> None:
    c = CONFIG
    cover = f"{c['baseUrl']}/cover.png"
    items = []
    for ep in reversed(eps):  # 新しい順
        genre = GENRE_LABELS.get(ep.get("genre", ""), "")
        desc = ep.get("description", "")
        if genre:
            desc = f"【{genre}】{desc}"
        desc += "\n\n音声: VOICEVOX:ずんだもん / VOICEVOX:四国めたん"
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
    <title>{escape(c['title'])}</title>
    <link>{escape(c['link'])}</link>
    <language>{c['language']}</language>
    <description>{escape(c['description'])}</description>
    <atom:link href="{c['baseUrl']}/feed.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{escape(c['author'])}</itunes:author>
    <itunes:summary>{escape(c['description'])}</itunes:summary>
    <itunes:owner>
      <itunes:name>{escape(c['author'])}</itunes:name>
      <itunes:email>{c['email']}</itunes:email>
    </itunes:owner>
    <itunes:image href="{cover}"/>
    <image>
      <url>{cover}</url>
      <title>{escape(c['title'])}</title>
      <link>{escape(c['link'])}</link>
    </image>
    <itunes:category text="{c['category']}"/>
    <itunes:explicit>{c['explicit']}</itunes:explicit>
    <itunes:type>episodic</itunes:type>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (DOCS / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"wrote docs/feed.xml ({len(eps)} episodes)")


def build_index(eps: list[dict]) -> None:
    c = CONFIG
    rows = []
    for ep in reversed(eps):
        genre = GENRE_LABELS.get(ep.get("genre", ""), "")
        rows.append(f"""      <article class="ep">
        <div class="meta"><span class="num">#{int(ep['id'])}</span><span class="genre">{escape(genre)}</span><span class="date">{ep['date']}</span><span class="dur">{fmt_duration(ep['_duration'])}</span></div>
        <h2>{escape(ep['title'])}</h2>
        <p>{escape(ep.get('description', ''))}</p>
        <audio controls preload="none" src="audio/ep{ep['id']}.mp3"></audio>
      </article>""")

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(c['title'])}</title>
<link rel="alternate" type="application/rss+xml" title="{escape(c['title'])}" href="feed.xml">
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif; background: #0f1115; color: #e7e9ee; margin: 0; }}
.wrap {{ max-width: 720px; margin: 0 auto; padding: 32px 20px 80px; }}
header {{ display: flex; gap: 20px; align-items: center; margin-bottom: 8px; }}
header img {{ width: 96px; height: 96px; border-radius: 20px; }}
h1 {{ font-size: 26px; margin: 0; }}
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
    <header><img src="cover.png" alt=""><h1>{escape(c['title'])}</h1></header>
    <p class="desc">{escape(c['description'])}</p>
    <a class="rss" href="feed.xml">📡 RSS フィード</a>
{chr(10).join(rows)}
    <footer>音声合成: VOICEVOX:ずんだもん / VOICEVOX:四国めたん<br>エピソード選定・原稿・収録・投稿まで全自動で運用しています。</footer>
  </div>
</body>
</html>
"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print("wrote docs/index.html")


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    eps = load_episodes()
    build_feed(eps)
    build_index(eps)


if __name__ == "__main__":
    main()
