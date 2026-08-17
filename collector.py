# -*- coding: utf-8 -*-
"""
やさしいニュース収集スクリプト
RSSフィードを巡回し、Gemini APIで「心が痛まない話か」を判定して
data/news.json に追記する。GitHub Actionsから定期実行される想定。
"""
import os
import json
import time
from pathlib import Path

import feedparser
import google.generativeai as genai

ROOT = Path(__file__).parent
SOURCES_FILE = ROOT / "sources.json"
SEEN_FILE = ROOT / "seen.json"
DATA_FILE = ROOT / "data" / "news.json"

MAX_ENTRIES_PER_FEED = 20   # 1フィードにつき新しい順に何件まで見るか
MAX_NEWS_KEEP = 300         # news.json に保持する最大件数
MAX_SEEN_KEEP = 3000        # 重複チェック用リストの最大件数
SLEEP_BETWEEN_CALLS = 2     # Gemini APIのレート制限対策(秒)

JUDGE_PROMPT = """あなたは「心が痛まない、やさしいニュース」だけを選ぶ編集者です。
以下のニュース見出しと概要を読み、次の形式のJSONのみを出力してください。
説明文やコードブロック記号は一切つけないでください。

{{"gentle": true か false, "reason": "15文字程度の短い理由"}}

判定基準:
- 事件・事故・死亡・災害・戦争・政治的対立・強い批判/炎上を含むものは false
- 心温まる話、動物、地域や個人の心温まる取り組み、科学の明るい発見、
  文化・エンタメの前向きな話題などは true
- 内容が薄い広告・PRだけの記事は false
- 判断に迷う場合は false（安全側に倒す）

見出し: {title}
概要: {summary}
"""


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"警告: {path} の読み込みに失敗したため初期値を使います")
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def judge(model, title: str, summary: str):
    """Gemini APIに1記事を判定させる。失敗時は安全側(false)を返す"""
    prompt = JUDGE_PROMPT.format(title=title, summary=(summary or "")[:200])
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        # ```json ... ``` のようなコードブロックで返ってきた場合の後処理
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
        result = json.loads(text)
        gentle = bool(result.get("gentle", False))
        reason = str(result.get("reason", ""))[:60]
        return gentle, reason
    except Exception as e:
        print(f"  判定エラー（この記事はスキップ扱い）: {e}")
        return False, ""


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("環境変数 GEMINI_API_KEY が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    sources = load_json(SOURCES_FILE, [])
    seen = set(load_json(SEEN_FILE, []))
    news = load_json(DATA_FILE, [])

    added = 0

    for src in sources:
        name = src.get("name", src.get("url", "unknown"))
        print(f"取得中: {name}")
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"  フィード取得エラー: {e}")
            continue

        if getattr(feed, "bozo", False) and not feed.entries:
            print(f"  警告: {src['url']} は正しいRSSとして読めませんでした")
            continue

        for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
            link = entry.get("link", "")
            title = entry.get("title", "")
            if not link or not title or link in seen:
                continue

            seen.add(link)
            summary = entry.get("summary", "") or entry.get("description", "")

            gentle, reason = judge(model, title, summary)
            time.sleep(SLEEP_BETWEEN_CALLS)

            if gentle:
                news.append({
                    "title": title,
                    "url": link,
                    "reason": reason,
                    "source": name,
                    "addedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                added += 1
                print(f"  灯した: {title}")

    # 保持件数を制限（古いものから切り捨て）
    news = news[-MAX_NEWS_KEEP:]
    seen_list = list(seen)[-MAX_SEEN_KEEP:]

    save_json(DATA_FILE, news)
    save_json(SEEN_FILE, seen_list)

    print(f"完了: {added}件のやさしいニュースを新たに追加しました")


if __name__ == "__main__":
    main()
