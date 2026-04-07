"""LLM service: summarization, full-text analysis, and chat."""

import json
import logging
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from ..config import settings
from ..utils.text_processor import truncate_to_tokens

logger = logging.getLogger(__name__)


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


async def summarize_abstract(title: str, abstract: str) -> dict:
    """Generate structured summary for a paper abstract."""
    client = _get_client()
    user_content = f"Title: {title}\n\nAbstract: {abstract}"

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": settings.llm_prompt_summarize},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.llm_max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        content = _strip_code_fence(content)
        result = json.loads(content)

        # Normalize list fields to strings
        for key in ("innovation_points", "limitations"):
            val = result.get(key, "")
            if isinstance(val, list):
                result[key] = "\n".join(f"• {item}" for item in val)

        return {
            "summary_en": result.get("summary_en", ""),
            "summary_cn": result.get("summary_cn", ""),
            "innovation_points": result.get("innovation_points", ""),
            "limitations": result.get("limitations", ""),
            "model_used": settings.llm_model,
        }
    except json.JSONDecodeError:
        raw = response.choices[0].message.content
        return {
            "summary_en": raw,
            "summary_cn": "",
            "innovation_points": "",
            "limitations": "",
            "model_used": settings.llm_model,
        }
    except Exception as e:
        logger.error(f"LLM summarization failed: {e}")
        raise


async def analyze_fulltext(title: str, fulltext: str) -> str:
    """Deep analysis of a full paper text."""
    client = _get_client()
    truncated = truncate_to_tokens(fulltext, 12000)
    user_content = f"论文标题：{title}\n\n全文内容：\n{truncated}"

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": settings.llm_prompt_fulltext},
            {"role": "user", "content": user_content},
        ],
        max_tokens=settings.llm_max_tokens,
        temperature=0.3,
    )
    text = response.choices[0].message.content
    return _strip_code_fence(text)


async def stream_chat(
    title: str,
    journal: str,
    year: int | None,
    abstract: str | None,
    fulltext: str | None,
    summary_cn: str | None,
    chat_history: list[dict],
    user_message: str,
) -> AsyncGenerator[str, None]:
    """Stream a chat response about a paper."""
    client = _get_client()

    abstract_section = f"摘要：\n{abstract}" if abstract else "（无摘要）"
    fulltext_section = ""
    if fulltext:
        truncated = truncate_to_tokens(fulltext, 8000)
        fulltext_section = f"全文内容（节选）：\n{truncated}"
    summary_section = f"AI摘要整理：\n{summary_cn}" if summary_cn else ""

    system_msg = settings.llm_prompt_chat.format(
        title=title,
        journal=journal or "未知",
        year=year or "未知",
        abstract_section=abstract_section,
        fulltext_section=fulltext_section,
        summary_section=summary_section,
    )

    messages = [{"role": "system", "content": system_msg}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        max_tokens=settings.llm_max_tokens,
        temperature=0.5,
        stream=True,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


import re

def _strip_code_fence(text: str) -> str:
    """Strip wrapping ```markdown ... ``` code fences and <think> tags from LLM output."""
    if not text:
        return text
    stripped = text.strip()
    # Strip <think>...</think> blocks (qwen models)
    stripped = re.sub(r'<think>[\s\S]*?</think>\s*', '', stripped).strip()
    # Strip wrapping code fences
    m = re.match(r'^```(?:markdown|md|text)?\s*\n([\s\S]*?)\n```\s*$', stripped)
    if m:
        return m.group(1)
    return stripped
