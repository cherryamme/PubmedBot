"""Parse PubMed EFetch XML into structured dicts."""

import json
from xml.etree.ElementTree import Element


def parse_pubmed_articles(root: Element) -> list[dict]:
    """Parse PubmedArticleSet XML into a list of paper dicts."""
    articles = []
    for article_elem in root.findall(".//PubmedArticle"):
        try:
            paper = _parse_single_article(article_elem)
            if paper:
                articles.append(paper)
        except Exception:
            continue
    return articles


def _parse_single_article(elem: Element) -> dict | None:
    medline = elem.find("MedlineCitation")
    if medline is None:
        return None

    pmid_elem = medline.find("PMID")
    pmid = pmid_elem.text if pmid_elem is not None else None
    if not pmid:
        return None

    article = medline.find("Article")
    if article is None:
        return None

    # Title
    title_elem = article.find("ArticleTitle")
    title = _get_text_content(title_elem) if title_elem is not None else ""

    # Abstract
    abstract_parts = []
    abstract_elem = article.find("Abstract")
    if abstract_elem is not None:
        for text in abstract_elem.findall("AbstractText"):
            label = text.get("Label", "")
            content = _get_text_content(text)
            if label and content:
                abstract_parts.append(f"{label}: {content}")
            elif content:
                abstract_parts.append(content)
    abstract = " ".join(abstract_parts) if abstract_parts else None

    # Journal
    journal_elem = article.find("Journal")
    journal_name = None
    issn = None
    year = None
    if journal_elem is not None:
        title_j = journal_elem.find("Title")
        if title_j is not None:
            journal_name = title_j.text
        issn_elem = journal_elem.find("ISSN")
        if issn_elem is not None:
            issn = issn_elem.text
        ji_elem = journal_elem.find("JournalIssue")
        if ji_elem is not None:
            pd = ji_elem.find("PubDate")
            if pd is not None:
                y = pd.find("Year")
                if y is not None and y.text:
                    try:
                        year = int(y.text)
                    except ValueError:
                        pass
                if year is None:
                    medline_date = pd.find("MedlineDate")
                    if medline_date is not None and medline_date.text:
                        try:
                            year = int(medline_date.text[:4])
                        except ValueError:
                            pass

    # Authors
    authors = []
    author_list = article.find("AuthorList")
    if author_list is not None:
        for i, auth in enumerate(author_list.findall("Author")):
            last = auth.find("LastName")
            fore = auth.find("ForeName")
            name_parts = []
            if last is not None and last.text:
                name_parts.append(last.text)
            if fore is not None and fore.text:
                name_parts.append(fore.text)
            if not name_parts:
                collective = auth.find("CollectiveName")
                if collective is not None and collective.text:
                    name_parts.append(collective.text)
            if name_parts:
                aff_elem = auth.find(".//Affiliation")
                authors.append({
                    "name": " ".join(name_parts),
                    "affiliation": aff_elem.text if aff_elem is not None else None,
                    "position": i,
                })

    # DOI
    doi = None
    article_data = elem.find("PubmedData")
    if article_data is not None:
        for aid in article_data.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text
                break

    # PMC ID
    pmcid = None
    if article_data is not None:
        for aid in article_data.findall(".//ArticleId"):
            if aid.get("IdType") == "pmc":
                pmcid = aid.text
                break

    # Keywords
    keywords = []
    kw_list = medline.find("KeywordList")
    if kw_list is not None:
        for kw in kw_list.findall("Keyword"):
            if kw.text:
                keywords.append(kw.text)

    # MeSH terms
    mesh_terms = []
    mesh_list = medline.find("MeshHeadingList")
    if mesh_list is not None:
        for mh in mesh_list.findall("MeshHeading"):
            desc = mh.find("DescriptorName")
            if desc is not None and desc.text:
                mesh_terms.append(desc.text)

    return {
        "pmid": pmid,
        "pmcid": pmcid,
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "journal": journal_name,
        "issn": issn,
        "year": year,
        "authors": authors,
        "keywords": json.dumps(keywords) if keywords else None,
        "mesh_terms": json.dumps(mesh_terms) if mesh_terms else None,
    }


def _get_text_content(elem: Element) -> str:
    """Get all text content from an element including mixed content (e.g. <i>, <b> tags)."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        if child.text:
            parts.append(child.text)
        if child.tail:
            parts.append(child.tail)
    return "".join(parts).strip()
