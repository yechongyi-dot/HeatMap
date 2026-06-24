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

# Time windows: label -> max age in hours
TIME_WINDOWS = {
    "24h": 24,
    "3d": 72,
    "7d": 168,
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
