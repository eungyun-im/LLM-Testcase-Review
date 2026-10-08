"""LLM clients behind one small interface.

Every client implements complete(prompt, kind, meta) and returns an
LLMResponse. kind labels the call for cost accounting (generate, feedback,
cross_check). meta carries structured context that only the simulator reads;
a real model sees the prompt text and nothing else.
"""

import time
from dataclasses import dataclass

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"
MAX_TOKENS = 16000


@dataclass(frozen=True)
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0


class LLMError(RuntimeError):
    """The model returned no usable answer (refusal or truncated output)."""


class AnthropicClient:
    """Claude through the official SDK.

    The model and effort are fixed for a whole experiment and recorded with
    every run. Sampling parameters such as temperature are not sent: current
    Claude models reject them, so run-to-run variation is measured by
    repetition instead of being pinned.

    No fallback model is configured on purpose. A silent switch to another
    model would change the treatment under study, so a refusal is raised and
    the run is recorded as failed.
    """

    name = "anthropic"

    def __init__(self, model=DEFAULT_MODEL, effort=DEFAULT_EFFORT, max_tokens=MAX_TOKENS):
        import anthropic

        self._client = anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens

    def complete(self, prompt, kind="generate", meta=None):
        started = time.monotonic()
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "refusal":
            raise LLMError(f"model refused the request ({kind})")
        if response.stop_reason == "max_tokens":
            raise LLMError(f"output was cut off at max_tokens ({kind})")
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            duration_ms=round((time.monotonic() - started) * 1000),
        )


class ScriptedClient:
    """Returns prepared answers in order. For tests and for replaying stored outputs."""

    name = "scripted"
    model = "scripted"
    effort = "none"

    def __init__(self, answers):
        self._answers = list(answers)
        self.calls = []

    def complete(self, prompt, kind="generate", meta=None):
        self.calls.append((kind, prompt))
        if not self._answers:
            raise LLMError("scripted client ran out of answers")
        return LLMResponse(text=self._answers.pop(0))
