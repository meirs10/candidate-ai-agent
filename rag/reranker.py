"""
reranker.py — Pluggable cross-encoder reranking.

Three backends, selected via config.RERANK_PROVIDER:

    "voyage" → Voyage rerank API (no torch; production default).
    "qwen3"  → local Qwen3-Reranker-0.6B (the original local stack — a causal-LM
               reranker scored via the yes/no logits, per the model card).
    "none"   → no reranking; return the fused top-k as-is.

All expose: rerank(query, chunks, top_k) → list[str] (best first).

Import the shared lazy `reranker` singleton; the local torch model is only
constructed if RERANK_PROVIDER == "qwen3", so the production (Voyage) path never
imports torch.
"""

from __future__ import annotations

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`


class VoyageReranker:
    """Voyage rerank API (production default — no local model)."""

    def __init__(self):
        import voyageai

        self.model = config.VOYAGE_RERANK_MODEL
        self.client = voyageai.Client(api_key=config.VOYAGE_API_KEY or None)

    def rerank(self, query: str, chunks: list[str], top_k: int = 8) -> list[str]:
        if not chunks:
            return []
        res = self.client.rerank(query, chunks, model=self.model, top_k=top_k)
        return [r.document for r in res.results]


class NoopReranker:
    """Skip reranking — keep the fusion order, just cut to top_k."""

    def rerank(self, query: str, chunks: list[str], top_k: int = 8) -> list[str]:
        return chunks[:top_k]


class Qwen3Reranker:
    """
    Correct wrapper around Qwen/Qwen3-Reranker-0.6B (the original local stack).

    Qwen3-Reranker is a *causal LM*, not a sequence-classification cross-encoder.
    The supported way to use it (per the model card) is to wrap each
    (query, document) pair in the chat template, run one forward pass, and read
    the softmax probability of the "yes" token at the final position as the
    relevance score.
    """

    RERANK_MODEL = "Qwen/Qwen3-Reranker-0.6B"

    DEFAULT_INSTRUCTION = (
        "Given a question about a job candidate, retrieve the resume passages "
        "that answer it."
    )

    _PREFIX = (
        "<|im_start|>system\n"
        "Judge whether the Document meets the requirements based on the Query "
        'and the Instruct provided. Note that the answer can only be "yes" or '
        '"no".<|im_end|>\n'
        "<|im_start|>user\n"
    )
    _SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

    def __init__(self, max_length: int = 8192, batch_size: int = 16, device: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._torch = torch
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        if device == "cuda":
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            dtype = torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(self.RERANK_MODEL, padding_side="left")
        self.model = (
            AutoModelForCausalLM.from_pretrained(self.RERANK_MODEL, dtype=dtype)
            .to(device)
            .eval()
        )
        self.max_length = max_length
        self.batch_size = batch_size

        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")
        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.prefix_tokens = self.tokenizer.encode(self._PREFIX, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(self._SUFFIX, add_special_tokens=False)

    def _format(self, query: str, doc: str, instruction: str) -> str:
        return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"

    def _process(self, texts: list[str]) -> dict:
        budget = self.max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        inputs = self.tokenizer(
            texts,
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=budget,
        )
        for i, ids in enumerate(inputs["input_ids"]):
            inputs["input_ids"][i] = self.prefix_tokens + ids + self.suffix_tokens
        inputs = self.tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=self.max_length)
        return {k: v.to(self.model.device) for k, v in inputs.items()}

    def _score(self, texts: list[str]) -> list[float]:
        torch = self._torch
        with torch.no_grad():
            inputs = self._process(texts)
            logits = self.model(**inputs).logits[:, -1, :]
            true_logits = logits[:, self.token_true_id]
            false_logits = logits[:, self.token_false_id]
            stacked = torch.stack([false_logits, true_logits], dim=1).float()
            probs = torch.nn.functional.log_softmax(stacked, dim=1)
            return probs[:, 1].exp().tolist()

    def rerank(self, query: str, chunks: list[str], top_k: int = 8,
               instruction: str | None = None) -> list[str]:
        if not chunks:
            return []
        instruction = instruction or self.DEFAULT_INSTRUCTION
        texts = [self._format(query, chunk, instruction) for chunk in chunks]
        scores: list[float] = []
        for start in range(0, len(texts), self.batch_size):
            scores.extend(self._score(texts[start:start + self.batch_size]))
        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]


def _build_reranker():
    if config.RERANK_PROVIDER == "qwen3":
        return Qwen3Reranker()
    if config.RERANK_PROVIDER == "none":
        return NoopReranker()
    return VoyageReranker()


class _LazyReranker:
    """Defers construction until first use, so importing this module never loads
    torch in the production (Voyage) configuration."""

    _impl = None

    def _ensure(self):
        if _LazyReranker._impl is None:
            _LazyReranker._impl = _build_reranker()
        return _LazyReranker._impl

    def __getattr__(self, name):
        return getattr(self._ensure(), name)


# Single shared instance — import this everywhere.
reranker = _LazyReranker()


def get_reranker():
    """Explicit accessor (returns the same lazily-built backend)."""
    return reranker._ensure()
