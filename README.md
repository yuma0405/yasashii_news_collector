# やさしいニュース収集システム

心が痛まないニュースだけを、RSS＋Gemini APIで自動的に集めて表示するシステムです。

## 構成

```
yasashii_news_collector/
├── .github/workflows/collect.yml  ← 1日2回自動実行するActions設定
├── collector.py                    ← RSS取得→Geminiで判定→保存
├── sources.json                    ← 巡回するRSSフィードの一覧
├── seen.json                       ← 処理済み記事URL（重複防止・自動更新）
├── data/news.json                  ← 公開される「やさしいニュース」データ（自動更新）
├── requirements.txt
└── index.html                      ← 表示用アプリ（GitHub Pagesで公開）
```

## セットアップ手順

1. **このフォルダの中身をリポジトリにそのままコミット＆プッシュ**
   ```
   git add .
   git commit -m "init"
   git push
   ```

2. **APIキーをSecretsに登録**（まだなら）
   `Settings → Secrets and variables → Actions → New repository secret`
   名前: `GEMINI_API_KEY` / 値: 取得したGemini APIキー

3. **GitHub Pagesを有効化**
   `Settings → Pages → Source` を `Deploy from a branch` にし、
   ブランチは `main`、フォルダは `/ (root)` を選択
   → 数分で `https://yuma0405.github.io/yasashii_news_collector/` が使えるようになります

4. **初回実行を試す**
   `Actions` タブ → `Collect gentle news` → `Run workflow` で手動起動できます。
   成功すると `data/news.json` が更新されてコミットされます。

5. 以降は `.github/workflows/collect.yml` の`cron`設定どおり、
   毎日 朝7時・夜19時（日本時間）に自動実行されます。

## ニュースソースについて

- 初期状態では **楽しいニュース.com** のRSSのみ登録しています（`sources.json`）。
- **Yahoo!ニュースのRSSは使えません。** Yahoo!の利用規約で「RSSを使ったアプリ・サイトの作成や公開」「再配信」が明確に禁止されているためです（個人が自分のRSSリーダーで読む用途のみ許可）。
- 他の候補（ほっこり癒しニュース／いい話まとめ等）はRSS配信の有無を実際に確認できていないため、まずは動作確認が取れた1件から始めています。増やしたい場合は `sources.json` に `{ "name": "サイト名", "url": "フィードURL" }` を追記してください。フィードURLが正しいRSS/Atom形式かどうかは、ブラウザでそのURLを直接開いて確認できます（記事のタイトルがXMLタグに並んでいればOK）。

## 判定方式の調整

`collector.py` 内の `JUDGE_PROMPT` を書き換えると、「やさしい」の判定基準を細かく調整できます。
判定に使うモデルは `gemini-2.5-flash`（無料枠あり）です。

## 表示アプリについて

`index.html` は GitHub Pages で公開すると、`data/news.json`（自動収集分）と、
あなたが直接アプリ上で追加した話（ブラウザごとの個人データ）を両方まとめて表示します。
ローカルで直接ファイルを開いた場合は自動収集分は読み込めません（ブラウザのセキュリティ制限のため）。GitHub Pages経由でアクセスしてください。
