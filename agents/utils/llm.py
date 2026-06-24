"""
Centralized LLM client factory and robust JSON-response parsing.

All agents obtain their ChatGroq client from ``get_llm()`` so the model name and
JSON-mode configuration live in one place, and they parse model output through
``invoke_json()`` / ``extract_json()`` which tolerate Markdown code fences and
prose preambles (e.g. "Here is the JSON:") instead of crashing the pipeline.
"""
from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

MODEL_NAME = "llama-3.3-70b-versatile"


def get_llm(temperature: float = 0.0, json_mode: bool = True) -> ChatGroq:
    """Return a configured ChatGroq client.

    When ``json_mode`` is True the model is asked to emit a single JSON object
    via Groq's native ``response_format``, which dramatically reduces malformed
    output. The calling prompt must mention "json" for Groq to honour this.
    """
    model_kwargs: dict = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}
    return ChatGroq(
        model=MODEL_NAME,
        temperature=temperature,
        model_kwargs=model_kwargs,
    )


def extract_json(content: str) -> dict:
    """Parse a JSON object out of raw LLM text.

    Robust against Markdown code fences and surrounding prose: if a direct
    ``json.loads`` fails, the first ``{...}`` block is extracted via regex.
    Raises ``ValueError`` / ``json.JSONDecodeError`` only when no JSON object can
    be found at all.
    """
    if not content or not content.strip():
        raise ValueError("Empty LLM response")

    text = content.strip()

    # Strip a leading/trailing Markdown code fence if present.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def invoke_json(llm: ChatGroq, prompt: str) -> dict:
    """Invoke ``llm`` with a single human message and parse a JSON object."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return extract_json(response.content)
