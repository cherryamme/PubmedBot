"""Full text retrieval: PMC BioC API + Unpaywall + PDF download & parsing."""

import io
import json
import logging
from dataclasses import dataclass

import httpx
import pdfplumber

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class FullTextResult:
    content: str | None = None
    source: str | None = None
    content_type: str | None = None
    oa_url: str | None = None
    available: bool = False


async def convert_pmid_to_pmcid(pmid: str) -> str | None:
    """Convert PMID to PMCID using NCBI ID Converter."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
                params={"ids": pmid, "format": "json", "tool": "pubmed-bot"},
            )
            resp.raise_for_status()
            data = resp.json()
        records = data.get("records", [])
        if records and records[0].get("pmcid"):
            return records[0]["pmcid"]
    except Exception as e:
        logger.warning(f"PMID-to-PMCID conversion failed for {pmid}: {e}")
    return None


async def fetch_pmc_fulltext(pmcid: str) -> FullTextResult:
    """Fetch full text from PMC BioC API."""
    if not pmcid:
        return FullTextResult()
    try:
        pmc_num = pmcid.replace("PMC", "")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmc_num}/unicode"
            )
            if resp.status_code == 404:
                return FullTextResult()
            resp.raise_for_status()
            data = resp.json()

        passages = []
        for doc in data.get("documents", []):
            for passage in doc.get("passages", []):
                passages.append(passage)

        if passages:
            return FullTextResult(
                content=json.dumps(passages, ensure_ascii=False),
                source="pmc_bioc",
                content_type="json",
                oa_url=f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
                available=True,
            )
    except Exception as e:
        logger.warning(f"PMC BioC fetch failed for {pmcid}: {e}")
    return FullTextResult()


async def _download_and_parse_pdf(url: str) -> str | None:
    """Download a PDF from URL and extract text using pdfplumber."""
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (pubmed-bot; academic research)",
                "Accept": "application/pdf,*/*",
            })
            if resp.status_code != 200:
                logger.warning(f"PDF download failed: HTTP {resp.status_code} from {url}")
                return None

            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type and not resp.content[:5] == b"%PDF-":
                logger.warning(f"Not a PDF: content-type={content_type} from {url}")
                return None

            pdf_bytes = io.BytesIO(resp.content)
            text_parts = []
            with pdfplumber.open(pdf_bytes) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            if text_parts:
                full_text = "\n\n".join(text_parts)
                logger.info(f"PDF parsed: {len(text_parts)} pages, {len(full_text)} chars from {url}")
                return full_text
            else:
                logger.warning(f"PDF parsed but no text extracted from {url}")
                return None
    except Exception as e:
        logger.warning(f"PDF download/parse failed for {url}: {e}")
        return None


async def fetch_unpaywall(doi: str) -> FullTextResult:
    """Fetch OA information from Unpaywall API, then download and parse PDF if available."""
    if not doi:
        return FullTextResult()
    email = settings.unpaywall_email or settings.ncbi_email or "pubmed-bot@example.com"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.unpaywall.org/v2/{doi}",
                params={"email": email},
            )
            if resp.status_code == 404:
                return FullTextResult()
            resp.raise_for_status()
            data = resp.json()

        if not data.get("is_oa"):
            return FullTextResult()

        best = data.get("best_oa_location", {})
        pdf_url = best.get("url_for_pdf")
        html_url = best.get("url")
        oa_url = pdf_url or html_url

        # Try to download and parse the PDF
        if pdf_url:
            text = await _download_and_parse_pdf(pdf_url)
            if text:
                return FullTextResult(
                    content=text,
                    source="unpaywall_pdf",
                    content_type="text",
                    oa_url=oa_url,
                    available=True,
                )

        # If no PDF or parse failed, return URL-only result for user to access manually
        if oa_url:
            return FullTextResult(
                content=None,
                source="unpaywall",
                content_type="url",
                oa_url=oa_url,
                available=True,
            )
    except Exception as e:
        logger.warning(f"Unpaywall query failed for {doi}: {e}")
    return FullTextResult()


async def get_fulltext(
    pmid: str, pmcid: str | None = None, doi: str | None = None
) -> FullTextResult:
    """Try all channels to get full text."""
    # 1. Try PMC BioC (best: structured JSON)
    if not pmcid:
        pmcid = await convert_pmid_to_pmcid(pmid)
    if pmcid:
        result = await fetch_pmc_fulltext(pmcid)
        if result.available:
            return result

    # 2. Try Unpaywall (downloads + parses PDF)
    if doi:
        result = await fetch_unpaywall(doi)
        if result.available:
            return result

    return FullTextResult()
