"""PubMed E-utilities service: search and fetch papers."""

import asyncio
import logging
from xml.etree import ElementTree

from Bio import Entrez

from ..config import settings
from ..utils.rate_limiter import RateLimiter
from ..utils.xml_parser import parse_pubmed_articles

logger = logging.getLogger(__name__)

_rate_limiter = RateLimiter(
    max_per_second=10 if settings.ncbi_api_key else 3
)


def _configure_entrez():
    Entrez.email = settings.ncbi_email or "pubmed-bot@example.com"
    Entrez.tool = settings.ncbi_tool
    if settings.ncbi_api_key:
        Entrez.api_key = settings.ncbi_api_key


async def search_pmids(
    query: str,
    min_year: int | None = None,
    max_year: int | None = None,
    retmax: int = 100,
) -> list[str]:
    """Search PubMed and return a list of PMIDs."""
    _configure_entrez()

    term = query
    if min_year and max_year:
        term = f"{query} AND {min_year}:{max_year}[pdat]"
    elif min_year:
        term = f"{query} AND {min_year}:3000[pdat]"
    elif max_year:
        term = f"{query} AND 1900:{max_year}[pdat]"

    await _rate_limiter.acquire()

    def _do_search():
        handle = Entrez.esearch(
            db="pubmed",
            term=term,
            retmax=retmax,
            sort="relevance",
            usehistory="n",
        )
        result = Entrez.read(handle)
        handle.close()
        return result.get("IdList", [])

    pmids = await asyncio.to_thread(_do_search)
    logger.info(f"PubMed search '{query}' returned {len(pmids)} PMIDs")
    return pmids


async def fetch_papers(pmids: list[str]) -> list[dict]:
    """Fetch paper details for a batch of PMIDs. Returns parsed paper dicts."""
    if not pmids:
        return []

    _configure_entrez()
    all_papers = []
    batch_size = 50

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        await _rate_limiter.acquire()

        def _do_fetch(ids=batch):
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(ids),
                rettype="xml",
                retmode="xml",
            )
            xml_data = handle.read()
            handle.close()
            return xml_data

        xml_bytes = await asyncio.to_thread(_do_fetch)

        if isinstance(xml_bytes, str):
            xml_bytes = xml_bytes.encode("utf-8")

        root = ElementTree.fromstring(xml_bytes)
        papers = parse_pubmed_articles(root)
        all_papers.extend(papers)
        logger.info(f"Fetched batch {i // batch_size + 1}: {len(papers)} papers")

    return all_papers


async def search_and_fetch(
    query: str,
    min_year: int | None = None,
    max_year: int | None = None,
    retmax: int = 100,
) -> list[dict]:
    """Search PubMed and fetch all paper details in one call."""
    pmids = await search_pmids(query, min_year, max_year, retmax)
    return await fetch_papers(pmids)
