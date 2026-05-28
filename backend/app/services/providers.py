"""Provider request forwarders. Async httpx calls; supports a mock mode for local dev."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

log = logging.getLogger(__name__)


def _mock_response_openai(model: str, prompt_text: str) -> dict[str, Any]:
    reply = f"[mock {model}] echo: {prompt_text[:120]}"
    in_tok = max(1, len(prompt_text) // 4)
    out_tok = max(1, len(reply) // 4)
    return {
        "id": "chatcmpl-mock-0001",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": in_tok, "completion_tokens": out_tok, "total_tokens": in_tok + out_tok},
    }


def _mock_response_anthropic(model: str, prompt_text: str) -> dict[str, Any]:
    reply = f"[mock {model}] echo: {prompt_text[:120]}"
    in_tok = max(1, len(prompt_text) // 4)
    out_tok = max(1, len(reply) // 4)
    return {
        "id": "msg_mock_0001",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": reply}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": in_tok, "output_tokens": out_tok},
    }


def _flatten_prompt_openai(payload: dict[str, Any]) -> str:
    msgs = payload.get("messages") or []
    parts: list[str] = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for item in c:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
    return "\n".join(parts)


def _flatten_prompt_anthropic(payload: dict[str, Any]) -> str:
    msgs = payload.get("messages") or []
    parts: list[str] = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for item in c:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
    sys_prompt = payload.get("system")
    if isinstance(sys_prompt, str):
        parts.insert(0, sys_prompt)
    return "\n".join(parts)


async def forward_openai(
    base_url: str, provider_api_key: str, payload: dict[str, Any], path: str = "/v1/chat/completions"
) -> tuple[dict[str, Any], int]:
    if base_url.startswith("mock://"):
        return _mock_response_openai(payload.get("model", "unknown"), _flatten_prompt_openai(payload)), 200
    headers = {"Authorization": f"Bearer {provider_api_key}", "Content-Type": "application/json"}
    url = base_url.rstrip("/") + path
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        return r.json(), r.status_code


async def forward_anthropic(
    base_url: str, provider_api_key: str, payload: dict[str, Any], path: str = "/v1/messages"
) -> tuple[dict[str, Any], int]:
    if base_url.startswith("mock://"):
        return _mock_response_anthropic(payload.get("model", "unknown"), _flatten_prompt_anthropic(payload)), 200
    headers = {
        "x-api-key": provider_api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    url = base_url.rstrip("/") + path
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        return r.json(), r.status_code


def extract_usage_openai(resp: dict[str, Any]) -> tuple[int | None, int | None]:
    u = resp.get("usage") or {}
    return u.get("prompt_tokens"), u.get("completion_tokens")


def extract_usage_anthropic(resp: dict[str, Any]) -> tuple[int | None, int | None]:
    u = resp.get("usage") or {}
    return u.get("input_tokens"), u.get("output_tokens")
