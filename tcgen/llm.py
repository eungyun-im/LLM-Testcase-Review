"""LLM clients behind one small interface.

Every client implements complete(prompt, kind, meta) and returns an
LLMResponse. kind labels the call for cost accounting (generate, feedback,
cross_check). meta carries structured context that only the simulator reads;
a real model sees the prompt text and nothing else.
"""

import json
import time
import urllib.error
import urllib.request
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


class OpenAICompatibleClient:
    """Any server that speaks the OpenAI chat completions protocol.

    That covers a model running on this machine (Ollama, llama.cpp, vLLM) and
    most hosted services. Only the base URL and the model name differ:

        Ollama on this machine   http://localhost:11434/v1
        a hosted service         its base URL, with the key in an environment variable

    No sampling parameter is sent unless a temperature is given, so the server's
    defaults apply and run-to-run variation is measured by repetition. A
    temperature that is given is recorded with every run. The model name is recorded
    with every run. A hosted model can change behind its name, a local model
    file cannot: for results that have to be reproduced, prefer the latter.
    """

    name = "openai-compatible"

    def __init__(self, model, base_url="http://localhost:11434/v1", api_key=None,
                 max_tokens=MAX_TOKENS, timeout_s=600, retries=5, temperature=None):
        self.model = model
        self.temperature = temperature
        self.effort = "none" if temperature is None else f"temperature {temperature:g}"
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._retries = retries

    def _post(self, body):
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=json.dumps(body).encode(), headers=headers
        )
        for attempt in range(self._retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as error:
                # Rate limits and server hiccups are worth waiting for. Anything else is not.
                if error.code not in (429, 500, 502, 503, 529) or attempt == self._retries:
                    raise LLMError(f"HTTP {error.code} from {self.base_url}") from error
                time.sleep(min(60, 2 ** attempt))
            except urllib.error.URLError as error:
                raise LLMError(f"cannot reach {self.base_url}: {error.reason}") from error
        raise LLMError("unreachable")

    def complete(self, prompt, kind="generate", meta=None):
        started = time.monotonic()
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        data = self._post(body)
        choice = data["choices"][0]
        if choice.get("finish_reason") == "length":
            raise LLMError(f"output was cut off at max_tokens ({kind})")
        text = choice["message"].get("content") or ""
        if not text.strip():
            raise LLMError(f"model returned no text ({kind})")
        usage = data.get("usage") or {}
        return LLMResponse(
            text=text,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
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
