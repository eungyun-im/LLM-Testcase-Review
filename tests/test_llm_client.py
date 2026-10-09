"""The OpenAI-compatible client against a small local server."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tcgen.llm import LLMError, OpenAICompatibleClient


@pytest.fixture
def server():
    """A server that answers with the prepared (status, body) pairs in order."""
    state = {"answers": [], "requests": []}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append((self.path, self.headers.get("Authorization"), body))
            status, payload = state["answers"].pop(0)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{httpd.server_port}/v1"
    yield state
    httpd.shutdown()


def answer(text, finish_reason="stop"):
    return 200, {
        "choices": [{"message": {"content": text}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7},
    }


def test_returns_text_and_token_counts(server):
    server["answers"] = [answer("tc_id,req_id")]
    client = OpenAICompatibleClient("some-model", base_url=server["url"], api_key="secret")
    response = client.complete("write tests")
    assert (response.text, response.input_tokens, response.output_tokens) == ("tc_id,req_id", 11, 7)
    path, authorization, body = server["requests"][0]
    assert path == "/v1/chat/completions"
    assert authorization == "Bearer secret"
    assert body["model"] == "some-model"
    assert body["messages"] == [{"role": "user", "content": "write tests"}]
    assert "temperature" not in body


def test_no_authorization_header_without_a_key(server):
    server["answers"] = [answer("ok")]
    OpenAICompatibleClient("m", base_url=server["url"]).complete("x")
    assert server["requests"][0][1] is None


def test_waits_and_retries_when_rate_limited(server, monkeypatch):
    waits = []
    monkeypatch.setattr("tcgen.llm.time.sleep", waits.append)
    server["answers"] = [(429, {}), (503, {}), answer("ok")]
    assert OpenAICompatibleClient("m", base_url=server["url"]).complete("x").text == "ok"
    assert waits == [1, 2]


def test_other_http_errors_are_not_retried(server):
    server["answers"] = [(401, {})]
    with pytest.raises(LLMError, match="HTTP 401"):
        OpenAICompatibleClient("m", base_url=server["url"]).complete("x")
    assert len(server["requests"]) == 1


def test_truncated_output_is_an_error(server):
    server["answers"] = [answer("tc_id,req", finish_reason="length")]
    with pytest.raises(LLMError, match="cut off"):
        OpenAICompatibleClient("m", base_url=server["url"]).complete("x")


def test_empty_answer_is_an_error(server):
    server["answers"] = [answer("  ")]
    with pytest.raises(LLMError, match="no text"):
        OpenAICompatibleClient("m", base_url=server["url"]).complete("x")


def test_unreachable_server_is_an_error():
    with pytest.raises(LLMError, match="cannot reach"):
        OpenAICompatibleClient("m", base_url="http://127.0.0.1:1/v1", timeout_s=2).complete("x")


def test_a_given_temperature_is_sent_and_recorded(server):
    server["answers"] = [answer("ok")]
    client = OpenAICompatibleClient("m", base_url=server["url"], temperature=0.3)
    client.complete("x")
    assert server["requests"][0][2]["temperature"] == 0.3
    assert client.effort == "temperature 0.3"


def test_a_vote_temperature_reaches_the_votes_and_not_the_generation(server):
    server["answers"] = [answer("tests"), answer("FAULT"), answer("table")]
    client = OpenAICompatibleClient("m", base_url=server["url"], vote_temperature=0.3)
    client.complete("x", kind="generate")
    client.complete("x", kind="cross_check")
    client.complete("x", kind="formalize")
    sent = [request[2].get("temperature") for request in server["requests"]]
    assert sent == [None, 0.3, 0.3]
    assert client.effort == "votes at temperature 0.3"
