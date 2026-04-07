"""Text processing utilities for LLM context management."""


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1 token per 4 chars for English, ~1 token per 2 chars for Chinese."""
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other_chars = len(text) - chinese_chars
    return chinese_chars // 2 + other_chars // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximate token limit."""
    if estimate_tokens(text) <= max_tokens:
        return text
    # Binary search for the right cutoff point
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if estimate_tokens(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "\n\n[... 内容已截断 ...]"


def chunk_fulltext_sections(bioc_passages: list[dict]) -> list[dict]:
    """Organize BioC passages into labeled sections."""
    sections = []
    for passage in bioc_passages:
        infons = passage.get("infons", {})
        section_type = infons.get("section_type", infons.get("type", "other"))
        text = passage.get("text", "")
        if text.strip():
            sections.append({
                "type": section_type,
                "text": text.strip(),
                "tokens": estimate_tokens(text),
            })
    return sections


def build_context_from_sections(
    sections: list[dict], max_tokens: int = 8000
) -> str:
    """Build LLM context from sections, prioritizing Results and Discussion."""
    priority_order = [
        "RESULTS", "DISCUSS", "CONCLUSIONS", "INTRO", "METHODS",
        "ABSTRACT", "TITLE", "other"
    ]

    by_type: dict[str, list[dict]] = {}
    for sec in sections:
        key = sec["type"].upper()
        matched = "other"
        for p in priority_order:
            if p in key:
                matched = p
                break
        by_type.setdefault(matched, []).append(sec)

    parts = []
    used_tokens = 0
    for ptype in priority_order:
        for sec in by_type.get(ptype, []):
            if used_tokens + sec["tokens"] > max_tokens:
                remaining = max_tokens - used_tokens
                if remaining > 200:
                    parts.append(truncate_to_tokens(sec["text"], remaining))
                return "\n\n".join(parts)
            parts.append(sec["text"])
            used_tokens += sec["tokens"]
    return "\n\n".join(parts)
