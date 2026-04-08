"""
ConfigManager — singleton that loads config.yaml and .env once,
and provides clean accessor methods for agent settings.
"""

from __future__ import annotations

import os
from typing import Union

import yaml
from dotenv import load_dotenv

from google.adk.models.base_llm import BaseLlm


class ConfigManager:
    """Centralized configuration manager for the application."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        load_dotenv()

        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)

    def _agent_cfg(self, agent_key: str) -> dict:
        """YAML block for `coordinator` or `workspace`."""
        agents_cfg = self._config.get("agents", {})
        agent_cfg = agents_cfg.get(agent_key)
        return agent_cfg if isinstance(agent_cfg, dict) else {}

    def get_agent_model_fallback_chain(self, agent_key: str) -> list[str]:
        """Ordered model IDs: primary first; later entries used on quota/429 when wrapped."""
        agent_cfg = self._agent_cfg(agent_key)
        candidates = agent_cfg.get("model_candidates")
        if isinstance(candidates, list) and candidates:
            out = [str(x).strip() for x in candidates if str(x).strip()]
            if out:
                return out
        single = agent_cfg.get("model")
        if single and str(single).strip():
            return [str(single).strip()]
        return ["gemini-2.5-flash"]

    def get_agent_model(self, agent_key: str) -> str:
        """Primary model id (first entry in the fallback chain)."""
        return self.get_agent_model_fallback_chain(agent_key)[0]

    def resolve_agent_model(self, agent_key: str) -> Union[str, BaseLlm]:
        """String model id, or FallbackGeminiLlm when multiple candidates are configured."""
        chain = self.get_agent_model_fallback_chain(agent_key)
        if len(chain) == 1:
            return chain[0]
        from app.llm.fallback_gemini import FallbackGeminiLlm

        return FallbackGeminiLlm(model=chain[0], fallbacks=chain[1:])

    @property
    def raw(self) -> dict:
        return self._config


config_manager = ConfigManager()


def get_agent_model(agent_key: str) -> str:
    return config_manager.get_agent_model(agent_key)


def get_agent_model_fallback_chain(agent_key: str) -> list[str]:
    return config_manager.get_agent_model_fallback_chain(agent_key)


def resolve_agent_model(agent_key: str) -> Union[str, BaseLlm]:
    return config_manager.resolve_agent_model(agent_key)
