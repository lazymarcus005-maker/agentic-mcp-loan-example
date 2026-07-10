from __future__ import annotations

from openai import OpenAI

from agenticai_v2.config import get_provider_config


def build_llm_client(
    provider: str, model: str, *, api_key: str | None = None, base_url: str | None = None
) -> tuple[OpenAI, str]:
    """Returns (client, model_name) configured for the given provider.

    OpenRouter, OpenAI, Gemini (via its OpenAI-compat endpoint) and any generic
    OpenAI-compatible endpoint all speak the same Chat Completions API, so a
    single OpenAI SDK client covers every provider by swapping base_url/api_key/model.

    api_key/base_url, when given, override the .env default (set at runtime via Settings).
    """
    cfg = get_provider_config(provider, api_key=api_key, base_url=base_url)
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    return client, model
