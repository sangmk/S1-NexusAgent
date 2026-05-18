"""LLM model singletons — provider-agnostic factory.

All node models go through ONE function: _make_chat_model().
Swap providers by changing env vars (DEEPSEEK_BASE_URL, DEEPSEEK_V3_2_MODEL, etc.)
— no code changes needed. ChatDeepSeek is replaced with ChatOpenAI throughout
because the DeepSeek API is fully OpenAI-compatible.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from workflow import config as science_config
from workflow.prompt import (
    planner_output,
    supervisor_output,
    talk_check_output,
    intent_output,
    skill_match_output,
    reflection_output,
)

# ---------------------------------------------------------------------------
# Shared factory — single point of configuration
# ---------------------------------------------------------------------------


def _make_chat_model(model_name: str, **overrides) -> ChatOpenAI:
    """Build a ChatOpenAI with the current config, optionally overriding fields.

    All parameters come from env vars via workflow.config, so swapping
    providers is just a .env change.
    """
    cfg = science_config.DeepSeekV3_2  # default config class
    kwargs = {
        "model": cfg.model,
        "base_url": cfg.base_url,
        "api_key": cfg.api_key,
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    kwargs.update(overrides)
    return ChatOpenAI(**kwargs)


def _make_execute_model() -> ChatOpenAI:
    """Execute model: needs longer timeout for code-act loops."""
    cfg = science_config.DeepSeekV3_2
    return ChatOpenAI(
        model=cfg.model,
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        temperature=0.3,
        max_tokens=8192,
        timeout=30,
    )


def _make_supervisor_model() -> ChatOpenAI:
    """Supervisor model uses DeepSeekV3 (not V3_2) — separate config."""
    cfg = science_config.DeepSeekV3
    return ChatOpenAI(
        model=cfg.model,
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        temperature=0.3,
        max_tokens=8192,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

_planner_model = None
_execute_model = None
_supervisor_model = None
_classify_model = None
_normal_chat_model = None
_intent_model = None
_skill_match_model = None
_reflection_model = None
_report_model = None


def get_planner_model():
    global _planner_model
    if _planner_model is None:
        _planner_model = _make_chat_model("planner").with_structured_output(
            planner_output.UnknownPlan
        )
    return _planner_model


def get_execute_model():
    global _execute_model
    if _execute_model is None:
        _execute_model = _make_execute_model()
    return _execute_model


def get_supervisor_model():
    global _supervisor_model
    if _supervisor_model is None:
        _supervisor_model = _make_supervisor_model().with_structured_output(
            supervisor_output.SubtaskReview
        )
    return _supervisor_model


def get_classify_model():
    global _classify_model
    if _classify_model is None:
        _classify_model = _make_chat_model("classify").with_structured_output(
            talk_check_output.Result
        )
    return _classify_model


def get_normal_chat_model():
    global _normal_chat_model
    if _normal_chat_model is None:
        _normal_chat_model = _make_chat_model(
            "chat", temperature=science_config.DeepSeekV3_2.temperature
        )
    return _normal_chat_model


def get_intent_model():
    global _intent_model
    if _intent_model is None:
        _intent_model = _make_chat_model(
            "intent", max_tokens=4096
        ).with_structured_output(intent_output.IntentSchema)
    return _intent_model


def get_skill_match_model():
    global _skill_match_model
    if _skill_match_model is None:
        _skill_match_model = _make_chat_model(
            "skill_match", temperature=0.0
        ).with_structured_output(skill_match_output.SkillMatchResult)
    return _skill_match_model


def get_reflection_model():
    global _reflection_model
    if _reflection_model is None:
        _reflection_model = _make_chat_model(
            "reflection", timeout=30
        ).with_structured_output(reflection_output.Result)
    return _reflection_model


def get_report_model():
    global _report_model
    if _report_model is None:
        _report_model = _make_chat_model("report", temperature=0.2)
    return _report_model
