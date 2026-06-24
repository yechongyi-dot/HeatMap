"""Shared utility functions for scrapers.

Consolidates duplicate parsing and filtering logic that was previously
copy-pasted across youtube.py and channels.py.
"""

import math
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))

# ── Investment title keywords (used by both YouTube keyword search and channel scrape) ──
#
# Two-tier matching to avoid false positives:
#   • JP_TITLE_KEYWORDS — Japanese (kana/kanji) terms. Japanese has no word
#     boundaries, so plain substring matching is both necessary and safe.
#   • LATIN_KEYWORDS_*  — Latin-script acronyms/proper nouns. These are matched
#     as *whole tokens* (bounded by non-alphanumerics) so that e.g. "PER" does
#     not match the Italian preposition "per" inside "per favore", and "FX"
#     does not match inside "VFX"/"SFX". The collision-prone ratios (PER/ROE/PBR)
#     are additionally matched case-SENSITIVELY (uppercase only).

JP_TITLE_KEYWORDS = [
    "株", "投資", "経済", "金融", "資金", "証券", "財",
    "トレード", "取引", "相場", "為替", "円", "ドル",
    "配当", "優待", "決算", "銘柄", "ビットコイン", "暗号", "仮想通貨",
    "マーケット", "株価", "指数", "日経", "マザーズ",
    "利上げ", "利下げ", "金利", "インフレ", "デフレ", "政策",
    "バフェット", "ウォーレン", "ソロス", "ダリオ",
    "騰落", "買い", "売り", "暴落", "暴騰", "急騰", "高騰", "急落",
    "金融庁", "減税", "増税", "年金", "賃上げ",
    "景気", "不況", "好況", "リセッション",
    "為替介入", "財務省", "財務相", "日銀", "黒田", "植田",
    "米国株", "中国株", "半導体", "エヌビディア", "テスラ", "アップル",
    "NYダウ", "ダウ平均",
]

# Case-INsensitive whole-token acronyms + high-confidence English finance words
# (no common-word collisions). A trailing plural "s" is tolerated (see regex).
LATIN_KEYWORDS_CI = [
    "FX", "ETF", "IPO", "GDP", "CPI", "FOMC", "FRB", "ECB",
    "NISA", "iDeCo", "REIT", "NASDAQ", "JASDAQ", "TOPIX",
    "TSMC", "NVIDIA", "nikkei", "dow", "bitcoin", "S&P500", "S&P",
    "dividend", "shareholder", "earnings", "investor", "investing",
    "investment", "portfolio", "equity",
]

# Case-SENSITIVE (uppercase) whole-token tickers/ratios that collide with
# common lowercase words: PER↔"per", ROE↔"roe", PBR↔"pbr".
LATIN_KEYWORDS_CS = ["PER", "ROE", "PBR"]


def _token_regex(words: list[str], flags=0) -> "re.Pattern":
    """Compile an alternation that matches any *word* as a whole token.

    A token is bounded on both sides by a non-alphanumeric character (or the
    string edge), so the keyword cannot match inside a larger Latin word.
    Longer alternatives are tried first.
    """
    alts = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    # Optional trailing plural "s" so "REITs"/"Dividends" still match "REIT"/"dividend".
    return re.compile(rf"(?<![A-Za-z0-9])(?:{alts})s?(?![A-Za-z0-9])", flags)


_LATIN_CI_RE = _token_regex(LATIN_KEYWORDS_CI, re.IGNORECASE)
_LATIN_CS_RE = _token_regex(LATIN_KEYWORDS_CS)

NEGATIVE_TITLE_KEYWORDS = [
    # Food / cooking
    "grilled", "recipe", "rice paper", "cooking", "food", "street food",
    "料理", "レシピ", "グルメ", "食べ", "おいしい",
    # Entertainment / non-financial
    "vlog", "prank", "reaction", "unboxing", "haul",
    "gaming", "gameplay", "minecraft", "fortnite", "roblox",
    "asmr", "sleep", "meditation",
    "makeup", "beauty", "fashion", "outfit",
    "travel", "tour", "sightseeing",
    "music", "song", "cover", "dance", "mv",
    "sports", "football", "soccer", "basketball", "baseball",
    # Idol / variety / story-time / fortune (caught short tokens like ドル/円)
    "アイドル", "スカッと", "修羅場", "占い", "燃え尽き", "バーンアウト",
    # Pets / animals
    "cat ", "dog ", "kitten", "puppy", "ペット", "猫", "犬",
]


def parse_relative_time(text: Optional[str]) -> Optional[datetime]:
    """Parse YouTube relative time strings ("3 days ago", "Streamed 2 hours ago")
    into an approximate timezone-aware JST datetime.

    Returns None if the text cannot be parsed.
    """
    if not text:
        return None
    text_s = text.strip()
    # Strip leading prefixes like "Streamed ", "Premiered ", "Scheduled for "
    for prefix in ("Streamed ", "Premiered ", "Scheduled for "):
        if text_s.startswith(prefix):
            text_s = text_s[len(prefix):]
            break
    text_s = text_s.lower().replace("ago", "").strip()
    match = re.match(
        r"(\d+)\s*(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)",
        text_s,
    )
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    now = datetime.now(JST)
    if unit.startswith("minute"):
        return now - timedelta(minutes=amount)
    elif unit.startswith("hour"):
        return now - timedelta(hours=amount)
    elif unit.startswith("day"):
        return now - timedelta(days=amount)
    elif unit.startswith("week"):
        return now - timedelta(weeks=amount)
    elif unit.startswith("month"):
        return now - timedelta(days=amount * 30)
    elif unit.startswith("year"):
        return now - timedelta(days=amount * 365)
    return None


def parse_view_count(text: str) -> int:
    """Parse YouTube view count strings like "1.2M views", "500K views", "123 views"
    into an integer.  Returns 0 for unparseable input.
    """
    if not text:
        return 0
    text = text.replace("views", "").replace("view", "").strip().replace(",", "")
    if not text or text.lower() == "no":
        return 0
    multiplier = 1
    t = text.lower()
    if "k" in t:
        multiplier = 1_000
        t = t.replace("k", "")
    elif "m" in t:
        multiplier = 1_000_000
        t = t.replace("m", "")
    elif "b" in t:
        multiplier = 1_000_000_000
        t = t.replace("b", "")
    try:
        return int(float(t) * multiplier)
    except (ValueError, TypeError):
        return 0


def is_investment_related(title: str) -> bool:
    """Check if a video title is genuinely investment / finance related.

    Strategy:
      1. Reject if any NEGATIVE keyword is present (substring, case-insensitive).
      2. Accept if any Japanese finance term appears (substring — safe in JP).
      3. Accept if any Latin acronym appears as a *whole token* (boundary match),
         so "PER" matches 予想PER but not "per favore", and "FX" matches 【FX】
         but not "VFX".

    Shared by the YouTube keyword scraper, the Niconico scraper, and the channel
    deep-scraper so filtering stays consistent everywhere.
    """
    if not title:
        return False
    title_lower = title.lower()
    for kw in NEGATIVE_TITLE_KEYWORDS:
        if kw.lower() in title_lower:
            return False
    for kw in JP_TITLE_KEYWORDS:
        if kw in title:
            return True
    if _LATIN_CI_RE.search(title):
        return True
    if _LATIN_CS_RE.search(title):
        return True
    return False


# Backwards-compatible alias (flattened keyword list) for any external importer.
INVESTMENT_TITLE_KEYWORDS = JP_TITLE_KEYWORDS + LATIN_KEYWORDS_CI + LATIN_KEYWORDS_CS


def is_japanese(text: str) -> bool:
    """Check if *text* contains Japanese characters (kana or kanji)."""
    return bool(re.search(r"[぀-ヿ一-鿿㐀-䶿]", text))



