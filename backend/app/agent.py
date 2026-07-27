"""Samadhan agentic pipeline.

Given raw citizen input, the agent:
  1. Extracts a clean summary + location
  2. Classifies category and routes to the correct department
  3. Assigns priority using the department's policy SLA (RAG-grounded)
  4. Reads sentiment
  5. Drafts a suggested action citing official policy

Execution modes, chosen automatically by which key is set:
  - "gemini":     Google Gemini (free tier) — preferred
  - "llm":        Anthropic Claude
  - "rule-based": deterministic keyword engine, so the demo runs offline
The rule-based path guarantees the pipeline never breaks live.
"""
import json
import os

from . import providers
from .policies import POLICY_CORPUS, retrieve_policy

DEPARTMENTS = [d["department"] for d in POLICY_CORPUS]

CRITICAL_WORDS = [
    "emergency", "urgent", "danger", "dangerous", "fire", "electrocut", "live wire",
    "collapse", "collapsed", "accident", "death", "died", "injured", "contaminat",
    "outbreak", "flood", "gas leak", "child", "hospital", "unsafe", "shock", "threat",
]
HIGH_WORDS = [
    "no water", "power cut", "outage", "sewage", "overflow", "blocked", "days",
    "week", "elderly", "school", "many", "entire", "whole area", "repeated",
]


# ---------------------------------------------------------------------------
# Rule-based engine (always available)
# ---------------------------------------------------------------------------
def _rule_based(raw_text: str, location: str) -> dict:
    text_l = (raw_text or "").lower()

    # Route by best keyword overlap with policy corpus
    best_doc, best_score = POLICY_CORPUS[-1], 0
    for doc in POLICY_CORPUS:
        score = sum(1 for kw in doc["keywords"] if kw in text_l)
        if score > best_score:
            best_doc, best_score = doc, score

    department = best_doc["department"]
    category = department.split(" (")[0].split(" & ")[0].split(" / ")[0]

    # Priority
    if any(w in text_l for w in CRITICAL_WORDS):
        priority = "Critical"
    elif any(w in text_l for w in HIGH_WORDS):
        priority = "High"
    elif best_score == 0:
        priority = "Low"
    else:
        priority = "Medium"

    # Sentiment
    neg = ["angry", "frustrat", "worst", "terrible", "disgust", "fed up", "again", "still not", "no response"]
    sentiment = "Negative/Distressed" if any(w in text_l for w in neg) else "Neutral"

    summary = (raw_text or "").strip()
    if len(summary) > 180:
        summary = summary[:177].rsplit(" ", 1)[0] + "..."

    action = (
        f"Route to {department}. Per policy, acknowledge within SLA and dispatch the "
        f"relevant field team. Priority: {priority}."
    )
    return {
        "summary": summary or "(no description provided)",
        "category": category,
        "department": department,
        "priority": priority,
        "sentiment": sentiment,
        "location": location or "",
        "policy_basis": f"{best_doc['title']}: {best_doc['text']}",
        "suggested_action": action,
        "ai_mode": "rule-based",
    }


# ---------------------------------------------------------------------------
# LLM engine — Gemini (free tier) preferred, then Claude. Both grounded in RAG.
# ---------------------------------------------------------------------------
def _prompts(raw_text: str, location: str) -> tuple[str, str]:
    dept_list = "\n".join(f"- {d}" for d in DEPARTMENTS)
    # Give the model the full policy corpus as retrieval context (RAG).
    policy_context = "\n\n".join(f"[{d['title']}] ({d['department']})\n{d['text']}" for d in POLICY_CORPUS)

    system = (
        "You are Samadhan-Agent, an AI grievance-routing agent for Indian public "
        "governance. Analyze a citizen grievance and return STRICT JSON only. "
        "Ground your priority and suggested_action in the provided official policy "
        "context. Never invent policy beyond what is given.\n\n"
        f"Available departments:\n{dept_list}\n\n"
        f"OFFICIAL POLICY CONTEXT (RAG):\n{policy_context}"
    )
    user = (
        f"Citizen grievance:\n\"\"\"{raw_text}\"\"\"\n"
        f"Stated location: {location or 'unknown'}\n\n"
        "Return JSON with EXACTLY these keys: summary (<=30 words), category, "
        "department (must be one of the available departments verbatim), priority "
        "(one of Critical/High/Medium/Low), sentiment, location, policy_basis "
        "(quote the specific policy title + rule you relied on), suggested_action "
        "(one concrete next step for the assigned official)."
    )
    return system, user


def _finalize(data: dict, raw_text: str, location: str, mode: str) -> dict:
    if data.get("department") not in DEPARTMENTS:
        # Reconcile a hallucinated department with the closest known policy
        data["department"] = retrieve_policy(raw_text)["department"]
    data["ai_mode"] = mode
    data.setdefault("location", location or "")
    return data


def _gemini(raw_text: str, location: str) -> dict:
    from google import genai
    from google.genai import types

    system, user = _prompts(raw_text, location)
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    resp = client.models.generate_content(
        model=providers.gemini_model(),
        contents=[user],
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            max_output_tokens=800,
        ),
    )
    return _finalize(json.loads(resp.text), raw_text, location, "gemini")


def _anthropic(raw_text: str, location: str) -> dict:
    import anthropic

    system, user = _prompts(raw_text, location)
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=providers.anthropic_model(),
        max_tokens=700,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):text.rfind("}") + 1]
    return _finalize(json.loads(text), raw_text, location, "llm")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def analyze(raw_text: str, location: str = "") -> dict:
    """Run the agent, preferring an LLM and falling back gracefully."""
    provider = providers.active_provider()
    if provider == "rule-based":
        return _rule_based(raw_text, location)
    try:
        return _gemini(raw_text, location) if provider == "gemini" else _anthropic(raw_text, location)
    except Exception as e:  # noqa: BLE001 — demo must never crash
        result = _rule_based(raw_text, location)
        result["suggested_action"] += f"  [LLM unavailable, used rule-based fallback: {e}]"
        return result
