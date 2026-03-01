#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

import feedparser
import requests

# ===== 1) AMS RSS 源 =====
AMS_RSS_FEEDS = {
    "JAS": "https://journals.ametsoc.org/journalissuetocrss/journals/atsc/atsc-overview.xml",
    "MWR": "https://journals.ametsoc.org/journalissuetocrss/journals/mwre/mwre-overview.xml",
    "WAF": "https://journals.ametsoc.org/journalissuetocrss/journals/wefo/wefo-overview.xml",
}

# ===== 2) 关键词 =====
PHRASE_KEYWORDS = [
    "tropical cyclone",
    "extratropical cyclone",
    "binary typhoon",
    "fujiwhara",
    "fujiwhara effect",
    "twin typhoon",
    "binary interaction",
    "cyclone-cyclone interaction",
    "cyclone cyclone interaction",
]
ABBREV_KEYWORDS = ["TC", "ETC"]
CO_OCCUR_TERMS = ["cyclone", "typhoon", "hurricane", "storm"]

SEEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen.json")


# ===== 3) 工具函数 =====
def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def stable_id(entry: Dict[str, Any]) -> str:
    link = (entry.get("link", "") or "").strip()
    title = (entry.get("title", "") or "").strip()
    return hashlib.sha256((link + "|" + title).encode()).hexdigest()


def load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def fetch_rss(feed_url: str) -> List[Dict[str, Any]]:
    d = feedparser.parse(feed_url)
    out = []
    for e in d.entries:
        out.append({
            "title": getattr(e, "title", "") or "",
            "link": getattr(e, "link", "") or "",
            "summary": getattr(e, "summary", "")
                       or getattr(e, "description", "") or "",
        })
    return out


def keyword_hits(title: str, summary: str) -> List[str]:
    text = norm_text(title) + " " + norm_text(summary)
    hits: List[str] = []
    for kw in PHRASE_KEYWORDS:
        k = norm_text(kw)
        if k and k in text:
            hits.append(kw)
    for kw in ABBREV_KEYWORDS:
        k = kw.lower()
        if re.search(rf"\b{k}\b", text) and any(
            term in text for term in CO_OCCUR_TERMS
        ):
            hits.append(kw)
    return hits


# ===== 4) DeepSeek AI 摘��� =====
def deepseek_summarize(title: str, abstract: str) -> Optional[str]:
    """
    调用 DeepSeek API，对英文摘要生成中文 AI 总结（3-4句话）。
    失败时返回 None（不影响主流程）。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return None

    # 如果摘要太短（RSS里有时只有期刊信息，没有真实摘要），跳过
    if not abstract or len(abstract.strip()) < 50:
        return None

    prompt = (
        "请用中文对以下气象学论文摘要进行简洁总结（3-4句话），"
        "突出研究对象、方法和主要结论，不要逐句翻译：\n\n"
        f"标题：{title}\n\n"
        f"摘要：{abstract}"
    )

    try:
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[DeepSeek] 调用失败（跳过）: {e}")
        return None


# ===== 5) 消息拼装 =====
def build_message(items: List[Dict[str, Any]]) -> tuple:
    today = datetime.now().strftime("%Y-%m-%d")

    if not items:
        title = f"[论文推送] {today}：无关键词命中"
        desp = "今日 JAS / MWR / WAF 无关键词命中文章。"
        return title, desp

    title = f"[论文推送] {today}：命中 {len(items)} 篇"
    lines = []

    for it in items[:20]:
        lines.append(f"### ({it['journal']}) {it['title']}")
        lines.append(f"- **命中关键词**：{', '.join(it['hits'])}")
        lines.append(f"- **链接**：{it['link']}")

        ai_summary = it.get("ai_summary")
        if ai_summary:
            lines.append(f"- **AI 总结**：{ai_summary}")

        lines.append("")

    if len(items) > 20:
        lines.append(f"> 仅显示前 20 篇，共命中 {len(items)} 篇")

    return title, "\n".join(lines)


# ===== 6) Server酱发送 =====
def serverchan_send(title: str, desp: str) -> None:
    sendkey = os.environ.get("SERVERCHAN_SENDKEY", "")
    if not sendkey:
        raise SystemExit("请设置环境变量 SERVERCHAN_SENDKEY")

    r = requests.post(
        f"https://sctapi.ftqq.com/{sendkey}.send",
        data={"title": title, "desp": desp},
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 0:
        raise RuntimeError(f"Server酱发送失败: {j}")
    print(f"推送成功：{j}")


# ===== 7) 主流程 =====
def main():
    seen_db = load_json(SEEN_PATH, default={"seen": {}})
    seen = seen_db.setdefault("seen", {})

    matched: List[Dict[str, Any]] = []

    for journal, url in AMS_RSS_FEEDS.items():
        for e in fetch_rss(url):
            sid = stable_id(e)
            if sid in seen:
                continue

            hits = keyword_hits(e["title"], e["summary"])
            if hits:
                print(f"[命中] {e['title']}")

                # 调用 DeepSeek 生成 AI 总结
                ai_summary = deepseek_summarize(e["title"], e["summary"])

                matched.append({
                    "journal": journal,
                    "title": e["title"],
                    "link": e["link"],
                    "hits": hits,
                    "ai_summary": ai_summary,
                })

            seen[sid] = {"ts": int(time.time()), "journal": journal}

    save_json(SEEN_PATH, seen_db)

    title, desp = build_message(matched)
    serverchan_send(title, desp)


if __name__ == "__main__":
    main()
