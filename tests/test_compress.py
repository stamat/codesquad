"""Compression checkpoint — digests oversized context at agent boundaries,
logs before/after token counts, originals stay in the JSONL. Offline (model stubbed)."""

import json
from pathlib import Path

import pytest

from squad import compress as comp
from squad.config import CompressorConfig, load_config
from squad.interceptor import RunLog

CONFIG = Path(__file__).parent.parent / "squad.yaml"


@pytest.fixture
def fake_llm(monkeypatch):
    """Stub the local model: 'summarizes' to a fixed short digest."""
    real = comp.litellm.completion  # capture before patch — the module attr is global

    def fake_completion(model, messages, **kw):
        return real(model=model, messages=messages, mock_response="DIGEST: the gist")
    monkeypatch.setattr(comp.litellm, "completion", fake_completion)


def records(log):
    if not log.path.exists():  # nothing logged yet
        return []
    return [json.loads(line) for line in log.path.read_text().splitlines()]


def test_below_threshold_untouched(tmp_path, fake_llm):
    log = RunLog.start(tmp_path)
    cfg = CompressorConfig(trigger_tokens=1000)
    text = "short context"
    assert comp.compress(text, cfg) == text
    assert [r for r in records(log) if r["kind"] == "compress"] == []


def test_above_threshold_digested_and_logged(tmp_path, fake_llm):
    log = RunLog.start(tmp_path)
    cfg = CompressorConfig(trigger_tokens=20)
    text = "word " * 500  # way past 20 tokens
    out = comp.compress(text, cfg)
    assert out == "DIGEST: the gist"
    (rec,) = [r for r in records(log) if r["kind"] == "compress"]
    assert rec["tokens"]["in"] > rec["tokens"]["out"] > 0
    assert rec["payload"]["original"].startswith("word word")  # original preserved in log


def test_delegate_compresses_oversized_context(tmp_path, fake_llm):
    from langchain_core.messages import AIMessage

    from squad.graph import build_delegate

    cfg = load_config(CONFIG)
    cfg.compressor.trigger_tokens = 20

    class FakeAgent:
        def invoke(self, payload, config=None):
            self.seen = payload["messages"][0]["content"]
            return {"messages": [AIMessage(content="done")]}

    log = RunLog.start(tmp_path)
    fake = FakeAgent()
    delegate = build_delegate({"coder": fake}, cfg, max_cost=1.0)
    delegate.invoke({"role": "coder", "task": "do it", "context": "word " * 500})

    assert "DIGEST: the gist" in fake.seen          # subagent got the digest…
    assert "word word word" not in fake.seen        # …not the flood
    handoff_in = next(r for r in records(log) if r["kind"] == "handoff" and r["direction"] == "in")
    assert handoff_in["payload"]["context"] == "DIGEST: the gist"
