import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RERANK_MODEL = "Qwen/Qwen3-Reranker-0.6B"

# The instruction the model conditions on. Qwen3-Reranker was trained to judge
# relevance *given an instruction*, so this is part of the scoring contract, not
# decoration. Tuned here for recruitment-document retrieval.
DEFAULT_INSTRUCTION = "Given a question about a job candidate, retrieve the resume passages that answer it."


class Qwen3Reranker:
    """
    Correct wrapper around Qwen/Qwen3-Reranker-0.6B.

    Qwen3-Reranker is a *causal LM*, not a sequence-classification cross-encoder.
    Loading it with sentence_transformers.CrossEncoder attaches a randomly
    initialized classification head, so scores are noise. The supported way to
    use it (per the model card) is:

        1. Wrap each (query, document) pair in the model's chat template with an
           instruction, ending right before the assistant turn.
        2. Run one forward pass and read the logits at the final position.
        3. Compare the logit of the "yes" token against the "no" token; the
           softmax probability of "yes" is the relevance score.

    Always score with rerank() - it preserves the (query, chunks, top_k) API the
    rest of the pipeline expects.
    """

    # Chat-template scaffolding around each query/document pair. The empty
    # <think> block matches the format the reranker was trained/served with.
    _PREFIX = (
        "<|im_start|>system\n"
        "Judge whether the Document meets the requirements based on the Query "
        'and the Instruct provided. Note that the answer can only be "yes" or '
        '"no".<|im_end|>\n'
        "<|im_start|>user\n"
    )
    _SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

    def __init__(self, max_length: int = 8192, batch_size: int = 16, device: str | None = None):
        # Use the GPU when one is available. bfloat16 avoids the overflow issues
        # float16 can hit in the logits, falling back to float16 on older cards.
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        if device == "cuda":
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            dtype = torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(RERANK_MODEL, padding_side="left")
        self.model = AutoModelForCausalLM.from_pretrained(RERANK_MODEL, dtype=dtype).to(device).eval()
        self.max_length = max_length
        self.batch_size = batch_size

        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")
        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.prefix_tokens = self.tokenizer.encode(self._PREFIX, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(self._SUFFIX, add_special_tokens=False)

    def _format(self, query: str, doc: str, instruction: str) -> str:
        return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"

    def _process(self, texts: list[str]) -> dict:
        # Reserve room for the fixed prefix/suffix so the wrapped sequence stays
        # within max_length even after truncating the document text.
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

    @torch.no_grad()
    def _score(self, texts: list[str]) -> list[float]:
        inputs = self._process(texts)
        logits = self.model(**inputs).logits[:, -1, :]  # last-position logits
        true_logits = logits[:, self.token_true_id]
        false_logits = logits[:, self.token_false_id]
        # log_softmax over just {no, yes}, then probability of "yes".
        # Upcast to float32 so the softmax is stable under fp16/bf16 logits.
        stacked = torch.stack([false_logits, true_logits], dim=1).float()
        probs = torch.nn.functional.log_softmax(stacked, dim=1)
        return probs[:, 1].exp().tolist()

    def rerank(
        self,
        query: str,
        chunks: list[str],
        top_k: int = 8,
        instruction: str = DEFAULT_INSTRUCTION,
    ) -> list[str]:
        if not chunks:
            return []
        texts = [self._format(query, chunk, instruction) for chunk in chunks]
        scores: list[float] = []
        for start in range(0, len(texts), self.batch_size):
            scores.extend(self._score(texts[start : start + self.batch_size]))
        scored = sorted(zip(scores, chunks, strict=False), key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]


class _LazyReranker:
    """Proxy that defers Qwen3Reranker() construction until first use.

    Importing this module no longer triggers a HuggingFace model download
    (~1.2 GB).  The actual model is loaded only when rerank() is first called.
    This lets the Streamlit server and Docker health-check start instantly.
    """

    def __init__(self):
        self._instance: Qwen3Reranker | None = None

    def _get(self) -> Qwen3Reranker:
        if self._instance is None:
            self._instance = Qwen3Reranker()
        return self._instance

    def rerank(
        self,
        query: str,
        chunks: list[str],
        top_k: int = 8,
        instruction: str = DEFAULT_INSTRUCTION,
    ) -> list[str]:
        return self._get().rerank(query, chunks, top_k, instruction)


# Single shared instance - import this everywhere
reranker = _LazyReranker()
