"""Centralised config for tools.

All tools that need an LLM or an external API key should import from here
instead of hardcoding values or duplicating os.environ calls.

Usage
-----
from workflow.tools.tools_config import DEEPSEEK_CHAT, TAVILY_API_KEY
"""
import os
from langchain_openai import ChatOpenAI
from workflow import config as _cfg

# ── LLM instance (DeepSeek-V3, shared across tools) ──────────────────────────
# Parameters come from workflow/config.py → env vars DEEPSEEK_API_KEY,
# DEEPSEEK_BASE_URL, DEEPSEEK_V3_MODEL.  Set those in your .env file.
DEEPSEEK_CHAT = ChatOpenAI(
    model=_cfg.DeepSeekV3_2.model,
    base_url=_cfg.DeepSeekV3_2.base_url,
    api_key=_cfg.DeepSeekV3_2.api_key,
    temperature=_cfg.DeepSeekV3_2.temperature,
)

# ── External API keys ─────────────────────────────────────────────────────────
TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")
