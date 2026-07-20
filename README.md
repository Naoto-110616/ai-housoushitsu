# AIの放送室 🎙️

エピソード選定 → 原稿執筆 → 収録（音声合成）→ 投稿（RSS配信）まで**全自動**で運用する AI ポッドキャスト。

- 配信ページ / RSS: https://naoto-110616.github.io/ai-housoushitsu/ （`feed.xml`）
- 出演: ずんだもん × 四国めたん の2人掛け合い（VOICEVOX による音声合成）
- 配信: 月・水・金 朝6時（JST）
- ジャンルローテーション: フロントエンド/Next.js → AI・テック → テーマ回 → 雑学

## 仕組み

```
┌────────────────────────┐   台本JSONをcommit   ┌──────────────────────┐
│ Claude スケジュールタスク │ ──────────────────▶ │ GitHub Actions        │
│ (月水金 朝・全自動)       │                     │  1. VOICEVOX で合成   │
│  1. ジャンル決定          │                     │  2. mp3 生成          │
│  2. Webリサーチ          │                     │  3. feed.xml 再生成   │
│  3. 掛け合い原稿を執筆    │                     │  4. docs/ へ commit   │
└────────────────────────┘                     └──────────┬───────────┘
                                                          ▼
                                              GitHub Pages (docs/)
                                              mp3 + RSS + 一覧ページ
                                                          ▼
                                          Spotify / Apple Podcasts 等が
                                          RSS を自動クロールして配信
```

## ディレクトリ構成

| パス | 役割 |
|---|---|
| `config.json` | 番組設定（タイトル・話者・配信URL など） |
| `themes.json` | テーマ回のネタリスト（pending → done に消化） |
| `AGENT.md` | 自動生成セッションが従う運用手順書 |
| `scripts/epNNN.json` | 各エピソードの台本（AIがcommit） |
| `tools/synthesize.py` | VOICEVOX Engine で台本→mp3 |
| `tools/build_feed.py` | RSS (`docs/feed.xml`) と一覧ページを生成 |
| `tools/make_cover.py` | カバーアート生成（初回のみ） |
| `docs/` | GitHub Pages 配信ルート（mp3・RSS・HTML） |

## 台本フォーマット

```json
{
  "id": "001",
  "title": "エピソードタイトル",
  "genre": "frontend | ai_tech | theme | trivia",
  "date": "2026-07-20",
  "description": "エピソードの説明（ショーノート）",
  "sources": ["https://参考にした記事のURL"],
  "lines": [
    { "s": "Z", "t": "ずんだもんのセリフなのだ" },
    { "s": "M", "t": "四国めたんのセリフよ" }
  ]
}
```

`scripts/epNNN.json` を main に push すると GitHub Actions が自動で収録・配信します。
手動で回したい場合は Actions タブから `publish` を workflow_dispatch してください。

## 初回セットアップ（手動作業は2つだけ）

1. **GitHub Pages を有効化**: Settings → Pages → Branch: `main` / フォルダ: `/docs` → Save
2. **Spotify に登録**: [Spotify for Creators](https://creators.spotify.com/) で「既存のRSSフィードから追加」を選び、
   `https://naoto-110616.github.io/ai-housoushitsu/feed.xml` を登録（メール認証あり）。
   Apple Podcasts は [Podcasts Connect](https://podcastsconnect.apple.com/) から同じRSSを登録。

登録後は新エピソードが RSS 経由で自動反映されます。

## クレジット

音声合成に [VOICEVOX](https://voicevox.hiroshiba.jp/) を使用しています。
キャラクター利用規約に基づき表記: **VOICEVOX:ずんだもん / VOICEVOX:四国めたん**
