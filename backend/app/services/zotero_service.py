"""Zotero integration via Pyzotero (Web API v3).

Supports multiple Zotero accounts stored in the database.
"""

import asyncio
import logging

from pyzotero import zotero

logger = logging.getLogger(__name__)


def _get_zot(library_id: str, library_type: str, api_key: str):
    return zotero.Zotero(library_id, library_type, api_key)


async def export_paper(
    library_id: str,
    library_type: str,
    api_key: str,
    title: str,
    doi: str | None,
    journal: str | None,
    year: int | None,
    issn: str | None,
    authors: list[dict],
    abstract: str | None,
    summary_cn: str | None = None,
    innovation_points: str | None = None,
    limitations: str | None = None,
    fulltext_analysis: str | None = None,
    chat_messages: list[dict] | None = None,
    collection_key: str | None = None,
) -> dict:
    """Export a paper to a specific Zotero account."""

    def _do_export():
        zot = _get_zot(library_id, library_type, api_key)

        template = zot.item_template("journalArticle")
        template["title"] = title
        if doi:
            template["DOI"] = doi
        if journal:
            template["publicationTitle"] = journal
        if year:
            template["date"] = str(year)
        if abstract:
            template["abstractNote"] = abstract
        if issn:
            template["ISSN"] = issn

        template["creators"] = []
        for auth in authors:
            name = auth.get("name", "")
            parts = name.split(" ", 1)
            template["creators"].append({
                "creatorType": "author",
                "lastName": parts[0],
                "firstName": parts[1] if len(parts) > 1 else "",
            })

        if collection_key:
            template["collections"] = [collection_key]

        resp = zot.create_items([template])
        if not resp.get("successful") or "0" not in resp["successful"]:
            failed = resp.get("failed", {})
            raise RuntimeError(f"Zotero 创建条目失败: {failed}")

        item_data = resp["successful"]["0"]
        item_key = item_data["key"] if isinstance(item_data, dict) else item_data

        note_parts = []
        if summary_cn:
            note_parts.append(f"<h2>AI 摘要整理</h2><p>{_esc(summary_cn)}</p>")
        if innovation_points:
            note_parts.append(f"<h2>创新点</h2><p>{_esc(innovation_points).replace(chr(10), '<br/>')}</p>")
        if limitations:
            note_parts.append(f"<h2>不足之处</h2><p>{_esc(limitations).replace(chr(10), '<br/>')}</p>")
        if fulltext_analysis:
            # Convert markdown to simple HTML for Zotero note
            analysis_html = _markdown_to_html(fulltext_analysis)
            note_parts.append(f"<h2>AI 深度分析</h2>{analysis_html}")
        if chat_messages:
            note_parts.append("<h2>问答记录</h2>")
            for msg in chat_messages:
                role_label = "AI" if msg["role"] == "assistant" else "用户"
                note_parts.append(f"<p><b>{role_label}:</b> {_esc(msg['content'])}</p>")

        if note_parts:
            note_template = zot.item_template("note")
            note_template["note"] = "\n".join(note_parts)
            note_template["parentItem"] = item_key
            zot.create_items([note_template])

        logger.info(f"Exported to Zotero [{library_id}]: {title[:50]} -> {item_key}")
        return {"item_key": item_key}

    return await asyncio.to_thread(_do_export)


async def list_collections(library_id: str, library_type: str, api_key: str) -> list[dict]:
    """List collections for a specific Zotero account."""

    def _do_list():
        zot = _get_zot(library_id, library_type, api_key)
        collections = zot.collections()
        return [
            {"key": c["key"], "name": c.get("data", {}).get("name", ""), "parent": c.get("data", {}).get("parentCollection")}
            for c in collections
        ]

    return await asyncio.to_thread(_do_list)


async def check_connection(library_id: str, library_type: str, api_key: str) -> dict:
    """Test a Zotero account connection."""
    def _do_check():
        zot = _get_zot(library_id, library_type, api_key)
        info = zot.key_info()
        return {"ok": True, "user_id": info.get("userID"), "username": info.get("username")}

    try:
        return await asyncio.to_thread(_do_check)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _markdown_to_html(md: str) -> str:
    """Convert markdown to simple HTML for Zotero notes."""
    import re
    lines = md.split("\n")
    html_parts = []
    in_list = False
    in_table = False

    for line in lines:
        stripped = line.strip()

        # Headings
        if stripped.startswith("### "):
            if in_list: html_parts.append("</ul>"); in_list = False
            if in_table: html_parts.append("</table>"); in_table = False
            html_parts.append(f"<h3>{_esc(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            if in_list: html_parts.append("</ul>"); in_list = False
            if in_table: html_parts.append("</table>"); in_table = False
            html_parts.append(f"<h3>{_esc(stripped[3:])}</h3>")
        elif stripped.startswith("# "):
            if in_list: html_parts.append("</ul>"); in_list = False
            if in_table: html_parts.append("</table>"); in_table = False
            html_parts.append(f"<h2>{_esc(stripped[2:])}</h2>")
        # List items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>"); in_list = True
            content = _inline_format(stripped[2:])
            html_parts.append(f"<li>{content}</li>")
        elif re.match(r'^\d+\.\s', stripped):
            if not in_list:
                html_parts.append("<ul>"); in_list = True
            content = _inline_format(re.sub(r'^\d+\.\s', '', stripped))
            html_parts.append(f"<li>{content}</li>")
        # Table rows
        elif "|" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c) <= {"-", " ", ":"} for c in cells):
                continue  # separator row
            if not in_table:
                html_parts.append("<table>"); in_table = True
            row = "".join(f"<td>{_inline_format(c)}</td>" for c in cells)
            html_parts.append(f"<tr>{row}</tr>")
        # Empty line
        elif not stripped:
            if in_list: html_parts.append("</ul>"); in_list = False
            if in_table: html_parts.append("</table>"); in_table = False
        # Regular paragraph
        else:
            if in_list: html_parts.append("</ul>"); in_list = False
            if in_table: html_parts.append("</table>"); in_table = False
            html_parts.append(f"<p>{_inline_format(stripped)}</p>")

    if in_list: html_parts.append("</ul>")
    if in_table: html_parts.append("</table>")
    return "\n".join(html_parts)


def _inline_format(text: str) -> str:
    """Handle bold and inline code in text."""
    import re
    text = _esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text
