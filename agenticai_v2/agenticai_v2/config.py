from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str | None
    api_key: str
    model: str


_GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_OLLAMA_CLOUD_OPENAI_BASE_URL = "https://ollama.com/v1"

_API_KEY_ENV_VARS = {
    "openrouter": "OPENROUTER_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "ollama_cloud": "OLLAMA_API_KEY",
    "openai_compatible": "OPENAI_COMPATIBLE_API_KEY",
}


def get_provider_config(
    provider: str, *, api_key: str | None = None, base_url: str | None = None
) -> ProviderConfig:
    """Builds a provider config. api_key/base_url override the .env default when given
    (used when the user has set a key/URL at runtime via the Settings page)."""
    provider = provider.lower()

    if provider == "openrouter":
        return ProviderConfig(
            base_url=_OPENROUTER_BASE_URL,
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY", ""),
            model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )
    if provider == "gemini":
        return ProviderConfig(
            base_url=_GEMINI_OPENAI_BASE_URL,
            api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
            model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        )
    if provider == "openai":
        return ProviderConfig(
            base_url=None,
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        )
    if provider == "ollama_cloud":
        return ProviderConfig(
            base_url=_OLLAMA_CLOUD_OPENAI_BASE_URL,
            api_key=api_key or os.environ.get("OLLAMA_API_KEY", ""),
            model=os.environ.get("OLLAMA_MODEL", "gpt-oss:120b"),
        )
    if provider == "openai_compatible":
        return ProviderConfig(
            base_url=base_url or os.environ.get("OPENAI_COMPATIBLE_BASE_URL", ""),
            api_key=api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY", "unused"),
            model=os.environ.get("OPENAI_COMPATIBLE_MODEL", ""),
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def get_env_api_key(provider: str) -> str:
    """Raw .env default for a provider's API key (empty string if unset)."""
    env_var = _API_KEY_ENV_VARS.get(provider.lower())
    return os.environ.get(env_var, "") if env_var else ""


def get_env_openai_compatible_base_url() -> str:
    return os.environ.get("OPENAI_COMPATIBLE_BASE_URL", "")


def mask_secret(value: str) -> str:
    """Shows only head/tail of a secret, e.g. 'sk-or-v1-67cf…90767'."""
    if not value:
        return ""
    if len(value) <= 10:
        return "•" * len(value)
    return f"{value[:6]}…{value[-4:]}"


AVAILABLE_PROVIDERS = ["openrouter", "gemini", "openai", "ollama_cloud", "openai_compatible"]


def get_default_provider_and_model() -> tuple[str, str]:
    provider = os.environ.get("LLM_PROVIDER", "ollama_cloud").lower()
    return provider, get_provider_config(provider).model


def get_mcp_mssql_url() -> str:
    return os.environ.get("MCP_MSSQL_URL", "http://localhost:8080/mcp")


def get_app_host() -> str:
    return os.environ.get("APP_HOST", "0.0.0.0")


def get_app_port() -> int:
    return int(os.environ.get("APP_PORT", "80"))


def get_system_prompt() -> str:
    prompt_path = os.environ.get("SYSTEM_PROMPT_PATH", "prompts/system_prompt.md")
    with open(prompt_path, encoding="utf-8") as f:
        return f.read()
