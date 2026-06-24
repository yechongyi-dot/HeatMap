"""
Search keywords and time-window configuration.

Keywords are searched independently, then results are deduplicated.
"""

KEYWORDS = [
    # 核心词
    "日本株",
    "株式投資",
    "日経平均",
    "投資戦略",
    # 市场行情
    "日経225",
    "TOPIX",
    "東証",
    "マザーズ",
    "相場展望",
    "テクニカル分析",
    # 交易实战
    "デイトレード",
    "スイングトレード",
    "FX",
    "信用取引",
    "チャート分析",
    # 制度/税务
    "NISA",
    "新NISA",
    "iDeCo",
    "配当金",
    "株主優待",
    "確定申告",
    # 宏观经济
    "日銀",
    "金融政策",
    "金利",
    "為替",
    "円安",
    "円高",
    # 个股/不动产/暗号
    "決算",
    "PER",
    "成長株",
    "配当利回り",
    "不動産投資",
    "REIT",
    "暗号資産",
    "ビットコイン",
]

# Time windows: label -> max age in hours.
# 30d mainly serves the sparse sources (official gov channels, niconico) whose
# content is too infrequent to show up in the shorter windows.
TIME_WINDOWS = {
    "24h": 24,
    "3d": 72,
    "7d": 168,
    "30d": 720,
}

# Max results per keyword per platform
RESULTS_PER_KEYWORD = 50

# Final top-N per platform per window
TOP_N = 300

# Delay between keyword searches (seconds), used within batches.
# YouTube uses the unofficial InnerTube API → keep polite to avoid soft-bans.
REQUEST_DELAY = 1.0
REQUEST_JITTER = 1.5

# Niconico uses the official Snapshot Search API → much higher tolerance,
# so it can run with a shorter delay and more workers.
NICONICO_DELAY = 0.3
NICONICO_JITTER = 0.4

# Concurrent workers per platform (keyword-level parallelism)
YOUTUBE_WORKERS = 5
NICONICO_WORKERS = 5

# ── Official / authoritative sources (the "official" platform) ──
#
# Curated YouTube channels: Japanese government / public bodies + established
# finance-news media. Channel IDs validated to return videos via search_channel
# (tubescrape's get_channel_videos is unreliable in the pinned version).
# "filter": True marks broad-news channels whose uploads must pass the finance
# keyword check (e.g. Reuters posts war/general news too). Government bodies and
# finance-specialist media are trusted wholesale so their vaguely-titled flagship
# videos (e.g. a BOJ press conference) are never dropped.
OFFICIAL_CHANNELS = [
    # 政府・公共機関（财经导向，全面信任，不过滤）
    {"name": "日本銀行",                 "channel_id": "UC32Yu7NyStgmKYsXvYofPvQ"},
    {"name": "財務省",                   "channel_id": "UCBBBgFnML-9hLHa8tk3506g"},
    {"name": "金融庁",                   "channel_id": "UCpIgZIDc-ptkZZTvzqlwGQg"},
    {"name": "日本取引所グループ JPX",    "channel_id": "UCnZA74T8a8dEbavWRq8F2nA"},
    {"name": "経済産業省",               "channel_id": "UCAMvYSb3oO7oQpcaHZQYv7A"},
    # 権威ある経済・金融メディア／証券会社（专注财经，不过滤）
    {"name": "日経CNBC",                 "channel_id": "UClVsQnfs-jKkjKmUKUHnT2g"},
    {"name": "トウシル（楽天証券）",      "channel_id": "UC5BiTvy2Ni2MyigJPspjhOA"},
    {"name": "ストックボイス",           "channel_id": "UCgYt_yLa5ZVq7e_4Dzes8DQ"},
    {"name": "東洋経済オンライン",        "channel_id": "UCN36kFB7Lh4tptI4rsy5vFw"},
    {"name": "SBI証券",                  "channel_id": "UCQHZXj_ZXCHuwWLiHHahetQ"},
    # 综合新闻 / 政治为主（含非财经内容，需按关键词过滤）
    {"name": "ロイター日本",             "channel_id": "UCpC6ZVYT8-SxVb9zIcPDOTA", "filter": True},
    {"name": "首相官邸",                 "channel_id": "UCogK43-0HpBQXPahOswXJ0g", "filter": True},
]

# Parallel channel-feed fetchers for the official scraper.
OFFICIAL_WORKERS = 5
