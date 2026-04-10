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

    # Build paper context (put in user message, not system prompt —
    # many models ignore or truncate long system prompts)
    context_parts = [f"论文标题：{title}"]
    if journal:
        context_parts.append(f"期刊：{journal}")
    if year:
        context_parts.append(f"年份：{year}")
    if abstract:
        context_parts.append(f"\n摘要：\n{abstract}")
    if fulltext:
        truncated = truncate_to_tokens(fulltext, 8000)
        context_parts.append(f"\n全文内容（节选）：\n{truncated}")
    if summary_cn:
        context_parts.append(f"\nAI摘要整理：\n{summary_cn}")

    paper_context = "\n".join(context_parts)

    logger.info(
        f"stream_chat: context length={len(paper_context)} chars, "
        f"fulltext_included={'yes' if fulltext else 'no'}, "
        f"history_turns={len(chat_history)}"
    )

    messages = [{"role": "system", "content": settings.llm_prompt_chat}]

    # First turn: inject paper context + question together
    # Subsequent turns: re-inject context so the model always has it
    context_msg = f"以下是需要分析的论文内容：\n\n{paper_context}\n\n请根据以上论文内容回答我的问题：{user_message}"

    if chat_history:
        # Prepend context as first exchange so model sees it before history
        messages.append({"role": "user", "content": f"以下是需要分析的论文内容：\n\n{paper_context}\n\n我会基于这篇论文向你提问。"})
        messages.append({"role": "assistant", "content": "好的，我已仔细阅读了这篇论文的内容，请问您有什么问题？"})
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})
    else:
        messages.append({"role": "user", "content": context_msg})

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
