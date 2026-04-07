from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_SUMMARIZE_PROMPT = """你是一位生物医学研究助手。请分析以下论文并提供结构化评估。

请以JSON格式回答，包含以下字段：
- "summary_en": 英文摘要总结（3-5句话，概括关键发现）
- "summary_cn": 中文摘要总结（对应英文摘要的中文翻译）
- "innovation_points": 创新点列表（2-3条，中文，描述这项工作的新颖之处）
- "limitations": 不足之处列表（2-3条，中文，描述潜在的局限性或不足）

请确保回答为有效的JSON格式。"""

_DEFAULT_FULLTEXT_PROMPT = """你是一位资深的生物医学研究分析师。请对以下论文全文进行深度分析。

请用中文提供以下内容：
1. **研究背景与动机**：这项研究解决了什么问题？
2. **核心方法**：使用了哪些关键技术和实验方法？
3. **主要发现**：最重要的实验结果是什么？
4. **结论与意义**：这项研究的核心结论和学术价值是什么？
5. **创新点**：与现有研究相比有哪些突破？
6. **局限性**：研究存在哪些不足或可改进之处？
7. **未来方向**：作者建议或可能的后续研究方向。

请用Markdown格式组织回答。"""

_DEFAULT_CHAT_SYSTEM_PROMPT = """你是一位专业的生物医学文献阅读助手。你正在帮助用户分析一篇论文。

论文信息：
标题：{title}
期刊：{journal}
年份：{year}

{abstract_section}

{fulltext_section}

{summary_section}

请根据论文内容回答用户的问题。回答应准确、详细，优先使用中文。如果论文中没有相关信息，请如实说明。"""


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/pubmed_bot.db"

    # PubMed / NCBI
    ncbi_api_key: str = ""
    ncbi_email: str = ""
    ncbi_tool: str = "pubmed-bot"

    # EasyScholar
    easyscholar_secret_key: str = ""
    easyscholar_base_url: str = "https://www.easyscholar.cc/open/getPublicationRank"

    # LLM (OpenAI 兼容)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_max_tokens: int = 4096

    # LLM Prompts (可在 .env 中自定义)
    llm_prompt_summarize: str = _DEFAULT_SUMMARIZE_PROMPT
    llm_prompt_fulltext: str = _DEFAULT_FULLTEXT_PROMPT
    llm_prompt_chat: str = _DEFAULT_CHAT_SYSTEM_PROMPT

    # Unpaywall
    unpaywall_email: str = ""

    # Zotero
    zotero_library_id: str = ""
    zotero_library_type: str = "user"
    zotero_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PUBMED_BOT_",
        extra="ignore",
    )


settings = Settings()
