# AGENT.md — エピソード自動生成の手順書

このファイルは、スケジュール実行される Claude セッションが毎回従う手順書です。
番組の方針を変えたいときは、このファイルと `config.json` / `themes.json` を編集してください。

## 番組概要

- 番組名: AIの放送室（日本語版）。英語版 AI Broadcast Room、スペイン語版 La Sala de Radio IA、ポルトガル語版 Sala de Rádio IA を同時配信
- 形式: 2人掛け合い。日本語版はずんだもん（Z）と四国めたん（M）、翻訳版のホスト名は Zen（Z）と Mira（M）
- 長さ: 8〜10分（日本語セリフ合計 3,200〜4,200 文字が目安）
- リスナー像: フロントエンドエンジニアを中心とした、テックに関心のある人

## 実行手順

1. **状態の確認** — GitHub MCP でリポジトリ `Naoto-110616/ai-housoushitsu` を読む
   - `scripts/` 直下（日本語原本）の一覧から最新エピソード番号と直近のジャンルを確認する
   - `config.json` の `genreRotation` に従い、次のジャンルを決める（ローテーション: frontend → ai_tech → theme → trivia → frontend …）
   - 直近5エピソードのタイトル・トピックを確認し、**内容の重複を避ける**

2. **リサーチ** — Web検索で最新かつ正確な情報を集める
   - `frontend`: 直近1週間程度の Next.js / React / TypeScript / CSS / フロントエンド界隈のニュースから2〜3トピック
   - `ai_tech`: 直近1週間程度の AI・テック全般のニュースから2〜3トピック
   - `theme`: `themes.json` の `pending` の先頭テーマを1つ深掘り解説（使ったテーマは `pending` から `done` へ移動。同じコミットに含める）
   - `trivia`: 面白い雑学・科学・歴史・カルチャーの話題を1〜2つ（時事性は不要。過去エピソードと被らないもの）
   - ニュースは必ず検索結果に基づき、事実確認できないことは話さない。参考URLは `sources` に入れる

3. **日本語原稿の執筆** — 台本 JSON を作成する
   - キャラクター:
     - ずんだもん (`"s": "Z"`): 明るく元気。語尾は「〜なのだ」「〜のだ」。素朴な疑問を投げる聞き役・ツッコミ役
     - 四国めたん (`"s": "M"`): 落ち着いたお姉さん口調（「〜よ」「〜ね」「〜かしら」）。解説役
   - 構成:
     1. オープニング: 挨拶と今日のトピック紹介（番組名を必ず言う）
     2. 本編: トピックごとに掛け合いで解説。専門用語はかみ砕く。具体例やたとえ話を入れる
     3. エンディング: まとめと締めの挨拶（「次回もお楽しみに」など）
   - 1セリフは長くても150文字程度。テンポよく交互に話す
   - 読み上げ前提の文章にする: URL・記号・英語スペルの羅列は避け、英語は自然なカタカナに（例: Next.js → ネクストジェイエス）
   - 数字や固有名詞の読み間違いが起きそうな箇所はひらがな・カタカナで書く

4. **翻訳版の作成** — `config.json` の `languages` のうち `ja` 以外の全言語（現在: en / es / pt）について、同じ id の台本 JSON を作る
   - title / description / lines の `t` を自然に翻訳・ローカライズする（直訳調は避ける）。`s`・`genre`・`date`・`sources` はそのまま
   - ホスト名は Zen（Z、明るく好奇心旺盛）と Mira（M、落ち着いた解説役）。「ずんだもん」「四国めたん」という名前や「〜なのだ」の翻訳調は使わない。自己紹介も Zen / Mira に置き換える
   - 番組名は言語ごとのタイトル（en: AI Broadcast Room / es: La Sala de Radio IA / pt: Sala de Rádio IA）を使う
   - 音声読み上げ前提: 略語の羅列を避け、固有名詞は通常表記（例: Next.js）でよい。日本語版のカタカナ読みは元の英語表記に戻す
   - 配置: `scripts/en/epNNN.json`、`scripts/es/epNNN.json`、`scripts/pt/epNNN.json`

5. **コミット** — GitHub MCP の `push_files` を使い、**日本語原本＋全翻訳版（＋theme回なら themes.json）を1回のコミットで** main へ push する
   - ファイルを分けて何度もコミットしないこと（GitHub Actions が多重起動するため）
   - commit すると GitHub Actions が全言語の音声合成→RSS更新を自動で行う（約15〜20分）

6. **検証**
   - commit から20分ほど待ち、以下のフィードに新エピソードが載っていることを確認する
     - https://naoto-110616.github.io/ai-housoushitsu/feed.xml （日本語）
     - https://naoto-110616.github.io/ai-housoushitsu/en/feed.xml
     - https://naoto-110616.github.io/ai-housoushitsu/es/feed.xml
     - https://naoto-110616.github.io/ai-housoushitsu/pt/feed.xml
   - 失敗している場合（フィード未更新）は、台本 JSON の構文を確認し、修正 commit で復旧を試みる
   - 結果（成功/失敗、エピソードタイトル、確認できた言語）を簡潔に報告して終了する

## 禁止事項

- 事実確認できないニュースの捿造
- 特定個人・企業への詹謗中傷、政治・宗教的に偏った主張
- 過去エピソードとの実質的な内容重複
- 翻訳版で VOICEVOX キャラクター名（ずんだもん・四国めたん）を使用すること（翻訳版の音声は VOICEVOX ではないため）
