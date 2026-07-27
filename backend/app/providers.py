"""Which AI provider is active, chosen by whichever key is set.

Precedence: Gemini (free tier) → Anthropic (Claude) → rule-based fallback.
Centralised here so the agent, the OCR extractor, and the health endpoint all
agree on the current mode.
"""
import os


def active_provider() -> str:
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "rule-based"


def gemini_model() -> str:
    # Alias that resolves to a current model with quota; safer than a pinned id,
    # since some accounts have zero free-tier quota for e.g. gemini-2.0-flash.
    return os.getenv("GEMINI_MODEL", "gemini-flash-latest")


def anthropic_model() -> str:
    return os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")


def active_model() -> str:
    p = active_provider()
    if p == "gemini":
        return gemini_model()
    if p == "anthropic":
        return anthropic_model()
    return "none"
