"""Journal impact factor service with EasyScholar + OpenAlex fallback.

EasyScholar API docs:
- Endpoint: GET https://www.easyscholar.cc/open/getPublicationRank
- Params: secretKey (string), publicationName (string, journal name)
- Response: data.officialRank.all contains fields like sciif, sci, sciUp, etc.
- Rate limit: max 2 requests per second
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.paper import JournalMetric
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

CACHE_DAYS = 30

# EasyScholar rate limit: 2 req/s
_es_rate_limiter = RateLimiter(max_per_second=2)


@dataclass
class MetricResult:
    impact_factor: float | None = None
    sci_partition: str | None = None
    source: str | None = None
    raw_data: str | None = None


async def get_impact_factor(
    db: AsyncSession, issn: str, journal_name: str = ""
) -> MetricResult:
    """Get impact factor for a journal. Checks cache first, then EasyScholar, then OpenAlex."""
    if not issn and not journal_name:
        return MetricResult()

    cache_key = issn or journal_name

    # Check cache
    cached = await _get_cached(db, cache_key)
    if cached:
        return MetricResult(
            impact_factor=cached.impact_factor,
            sci_partition=cached.sci_partition,
            source=cached.source,
        )

    # Try EasyScholar (uses journal name, not ISSN)
    if journal_name:
        result = await _try_easyscholar(journal_name)
        if result.impact_factor is not None:
            await _save_cache(db, cache_key, journal_name, result)
            return result

    # Fallback: OpenAlex (uses ISSN)
    if issn:
        result = await _try_openalex(issn)
        if result.impact_factor is not None:
            await _save_cache(db, cache_key, journal_name, result)
            return result

    # Save empty result to avoid repeated lookups
    await _save_cache(db, cache_key, journal_name, MetricResult(source="none"))
    return MetricResult()


async def _get_cached(db: AsyncSession, cache_key: str) -> JournalMetric | None:
    stmt = select(JournalMetric).where(JournalMetric.issn == cache_key)
    result = await db.execute(stmt)
    metric = result.scalar_one_or_none()
    if metric and metric.fetched_at:
        cutoff = datetime.now(timezone.utc) - timedelta(days=CACHE_DAYS)
        fetched = metric.fetched_at
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        if fetched > cutoff:
            return metric
    return None


async def _save_cache(
    db: AsyncSession, cache_key: str, journal_name: str, result: MetricResult
):
    stmt = select(JournalMetric).where(JournalMetric.issn == cache_key)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.impact_factor = result.impact_factor
        existing.sci_partition = result.sci_partition
        existing.source = result.source
        existing.raw_data = result.raw_data
        existing.fetched_at = datetime.now(timezone.utc)
    else:
        db.add(JournalMetric(
            issn=cache_key,
            journal_name=journal_name,
            impact_factor=result.impact_factor,
            sci_partition=result.sci_partition,
            source=result.source,
            raw_data=result.raw_data,
            fetched_at=datetime.now(timezone.utc),
        ))
    await db.commit()


async def _try_easyscholar(journal_name: str) -> MetricResult:
    """Query EasyScholar API for journal metrics.

    API: GET /open/getPublicationRank?secretKey=xxx&publicationName=xxx
    Response structure:
        data.officialRank.all: {
            sciif: "33.9",      # SCI影响因子-JCR
            sciif5: "30.2",     # SCI五年影响因子-JCR
            sci: "1",           # SCI分区-JCR (1=Q1, 2=Q2, ...)
            sciUp: "1",         # SCI升级版分区-中科院
            sciBase: "1",       # SCI基础版分区-中科院
            ...
        }
    """
    if not settings.easyscholar_secret_key:
        return MetricResult()

    try:
        await _es_rate_limiter.acquire()

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                settings.easyscholar_base_url,
                params={
                    "secretKey": settings.easyscholar_secret_key,
                    "publicationName": journal_name,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 200 or not data.get("data"):
            logger.info(f"EasyScholar: no data for '{journal_name}', code={data.get('code')}, msg={data.get('msg')}")
            return MetricResult()

        official_rank = data["data"].get("officialRank", {})
        all_ranks = official_rank.get("all", {})

        if not all_ranks:
            return MetricResult()

        # Extract impact factor from sciif field
        impact_factor = None
        sciif_val = all_ranks.get("sciif")
        if sciif_val:
            try:
                impact_factor = float(sciif_val)
            except (ValueError, TypeError):
                pass

        # If no JCR IF, try 5-year IF
        if impact_factor is None:
            sciif5_val = all_ranks.get("sciif5")
            if sciif5_val:
                try:
                    impact_factor = float(sciif5_val)
                except (ValueError, TypeError):
                    pass

        # Extract SCI partition
        # sciUp values are like "生物学1区", "医学1区" (CAS upgraded)
        # sciBase values are like "生物1区", "医学2区" (CAS base)
        # sci values are like "Q1", "Q2" (JCR)
        sci_partition = None
        for partition_key in ["sciUp", "sciBase", "sci"]:
            part_val = all_ranks.get(partition_key)
            if part_val:
                sci_partition = str(part_val)
                break

        # Check for CAS top journal flag
        # sciUpTop values are like "生物学TOP", "医学TOP"
        sci_up_top = all_ranks.get("sciUpTop")
        if sci_up_top:
            if sci_partition:
                sci_partition = f"{sci_partition} Top"
            else:
                sci_partition = str(sci_up_top)

        # Check for warning status (预警期刊)
        sci_warn = all_ranks.get("sciwarn")
        if sci_warn:
            warn_text = f"预警({sci_warn})" if sci_warn != "1" else "预警"
            sci_partition = f"{sci_partition} {warn_text}" if sci_partition else warn_text

        # Store raw response for debugging
        raw_data = json.dumps(all_ranks, ensure_ascii=False)

        logger.info(
            f"EasyScholar: '{journal_name}' -> IF={impact_factor}, partition={sci_partition}"
        )

        return MetricResult(
            impact_factor=impact_factor,
            sci_partition=sci_partition,
            source="easyscholar",
            raw_data=raw_data,
        )
    except Exception as e:
        logger.warning(f"EasyScholar query failed for '{journal_name}': {e}")
        return MetricResult()


async def _try_openalex(issn: str) -> MetricResult:
    """Fallback: query OpenAlex for citation-based metrics."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openalex.org/sources",
                params={"filter": f"issn:{issn}"},
                headers={"User-Agent": "pubmed-bot/1.0 (mailto:pubmed-bot@example.com)"},
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        if not results:
            return MetricResult()

        source = results[0]
        # OpenAlex doesn't have JCR IF but has summary_stats
        stats = source.get("summary_stats", {})
        # 2yr mean citedness is closest proxy to IF
        two_yr = stats.get("2yr_mean_citedness")
        if two_yr is not None:
            return MetricResult(
                impact_factor=round(float(two_yr), 3),
                sci_partition=None,
                source="openalex",
            )
        return MetricResult()
    except Exception as e:
        logger.warning(f"OpenAlex query failed for {issn}: {e}")
        return MetricResult()
