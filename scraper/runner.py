"""Main runner: parallel scrape YouTube + Niconico, score, deduplicate, store.

Runs both platforms simultaneously via ThreadPoolExecutor.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

from scraper import youtube, niconico
from scraper.scorer import score_and_rank
from scraper.dedup import deduplicate
from db import store

logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))

# Map platform name → scrape-all callable
PLATFORM_SCRAPERS: dict[str, Callable[[], list[dict]]] = {
    "youtube": youtube.scrape_all,
    "niconico": niconico.scrape_all_keywords,
}


def run_platform(platform: str, progress: Callable[[dict], None] | None = None) -> tuple[str, bool]:
    """Scrape, score, dedup, and store one platform's videos.

    Args:
        platform: ``"youtube"`` or ``"niconico"``.
        progress: Optional callback receiving ``{platform, phase, ...}`` dicts
            at each milestone (scraping → dedup → saving → done). Callback
            exceptions are swallowed so they never break the scrape.

    Returns:
        ``(platform, success)`` tuple.
    """
    def _emit(**kw) -> None:
        if progress is None:
            return
        try:
            progress({"platform": platform, **kw})
        except Exception:  # progress must never break scraping
            logger.debug("progress callback raised", exc_info=True)

    logger.info("%s", "=" * 60)
    logger.info("Starting %s scrape", platform)
    logger.info("%s", "=" * 60)

    try:
        _emit(phase="scraping")
        start = datetime.now(JST)
        raw_videos = PLATFORM_SCRAPERS[platform]()
        elapsed = (datetime.now(JST) - start).total_seconds()
        logger.info("%s: %d raw in %.0fs", platform, len(raw_videos), elapsed)
        _emit(phase="dedup", raw=len(raw_videos))

        unique = deduplicate(raw_videos)
        logger.info("%s: %d after dedup", platform, len(unique))

        windows = score_and_rank(unique, platform=platform)

        today = datetime.now(JST).strftime("%Y-%m-%d")
        _emit(phase="saving", raw=len(raw_videos), unique=len(unique))
        store.save_ranked_videos(platform, windows, today)
        _emit(phase="done", raw=len(raw_videos), unique=len(unique))

        for w, vids in windows.items():
            logger.info("  %s/%s: top 3:", platform, w)
            for i, v in enumerate(vids[:3], 1):
                logger.info(
                    "    #%d [%.0f] %s", i, v.get("score", 0), v.get("title", "")[:60],
                )

        return platform, True
    except Exception:
        logger.error("%s failed", platform, exc_info=True)
        _emit(phase="failed")
        return platform, False


def run_all(progress: Callable[[dict], None] | None = None) -> dict[str, bool]:
    """Run all platforms in parallel.

    Args:
        progress: Optional callback forwarded to each :func:`run_platform`,
            receiving per-platform milestone events.

    Returns:
        ``{platform: success}`` mapping.
    """
    store.init()
    results: dict[str, bool] = {}

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(run_platform, platform, progress): platform
            for platform in PLATFORM_SCRAPERS
        }
        for future in as_completed(futures):
            platform, ok = future.result()
            results[platform] = ok

    success = sum(1 for v in results.values() if v)
    logger.info("Done: %d/%d platforms succeeded", success, len(results))
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )
    run_all()
