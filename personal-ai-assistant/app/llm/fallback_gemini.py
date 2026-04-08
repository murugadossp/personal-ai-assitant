"""Try Gemini models in order until one succeeds; used for quota / 429 fallbacks."""

from __future__ import annotations

import contextlib
import logging
from typing import AsyncGenerator

from google.genai.errors import ClientError
from pydantic import Field
from typing_extensions import override

from google.adk.models.base_llm import BaseLlm
from google.adk.models.base_llm_connection import BaseLlmConnection
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.models.registry import LLMRegistry

logger = logging.getLogger("adk_agents")


def _is_quota_or_rate_limit(exc: BaseException) -> bool:
    if isinstance(exc, ClientError) and getattr(exc, "code", None) == 429:
        return True
    msg = str(exc).lower()
    return (
        "resource_exhausted" in msg
        or "429" in msg
        or "quota" in msg
        or "rate limit" in msg
    )


class FallbackGeminiLlm(BaseLlm):
    """Delegates to ADK Gemini backends, trying `model` then each entry in `fallbacks`."""

    fallbacks: list[str] = Field(default_factory=list)

    def _chain(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for name in [self.model, *self.fallbacks]:
            s = str(name).strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        if not out:
            raise RuntimeError("No models in fallback chain")
        return out

    @contextlib.asynccontextmanager
    async def connect(self, llm_request: LlmRequest):
        primary = LLMRegistry.new_llm(self._chain()[0])
        async with primary.connect(llm_request) as conn:
            yield conn

    @override
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        chain = self._chain()

        for idx, model_id in enumerate(chain):
            req = llm_request.model_copy(deep=True)
            req.model = model_id
            backend = LLMRegistry.new_llm(model_id)
            yielded = 0
            try:
                logger.info(
                    "[llm] generate_content model=%s attempt=%d/%d stream=%s chain=%s",
                    model_id,
                    idx + 1,
                    len(chain),
                    stream,
                    chain,
                )
                async for part in backend.generate_content_async(req, stream=stream):
                    yielded += 1
                    yield part
                return
            except BaseException as e:
                if yielded > 0:
                    raise
                if _is_quota_or_rate_limit(e) and idx < len(chain) - 1:
                    logger.warning(
                        "[llm] model=%s failed (%s); retrying with next in chain",
                        model_id,
                        e,
                    )
                    continue
                raise
