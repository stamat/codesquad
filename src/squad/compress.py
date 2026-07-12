"""Compression checkpoint: context crossing an agent boundary above the trigger
gets digested by the local model. Nothing is lost — the original text goes into
the JSONL compress record; only live context shrinks."""

import litellm

from squad.config import CompressorConfig
from squad.interceptor import current_log

_PROMPT = (
    "Compress the following working context for another AI agent. Keep every "
    "fact, decision, file path, identifier, and open question; drop repetition "
    "and prose. Be dense, use bullet points.\n\n"
)


def count_tokens(text: str, model: str) -> int:
    try:
        return litellm.token_counter(model=model, text=text)
    except Exception:
        return len(text) // 4  # crude fallback; only gates a threshold


def compress(text: str, cfg: CompressorConfig) -> str:
    """Digest text if it exceeds the trigger; otherwise return it unchanged."""
    before = count_tokens(text, cfg.model)
    if before <= cfg.trigger_tokens:
        return text
    resp = litellm.completion(
        model=cfg.model, messages=[{"role": "user", "content": _PROMPT + text}]
    )
    digest = resp.choices[0].message.content
    after = count_tokens(digest, cfg.model)
    if log := current_log.get():
        log.write("compress", payload={"original": text, "digest": digest},
                  tokens={"in": before, "out": after})
    return digest
