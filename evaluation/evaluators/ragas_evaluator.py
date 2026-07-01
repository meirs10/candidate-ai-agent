"""
RAGAS evaluator — wraps the RAGAS framework with local Ollama LLM as judge.

Metrics computed:
  - Faithfulness:      Is the answer grounded in retrieved context?
  - AnswerRelevancy:   Does the answer address the question?
  - ContextPrecision:  Are relevant chunks ranked higher?
  - ContextRecall:     Does the context contain needed information?
"""

import pandas as pd
from ragas import evaluate, EvaluationDataset, SingleTurnSample, RunConfig
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings


def _build_llm(model: str = "qwen3"):
    """Create a RAGAS-compatible LLM wrapper around Ollama."""
    return LangchainLLMWrapper(ChatOllama(model=model, reasoning=False))


def _build_embeddings(model: str = "nomic-ai/nomic-embed-text-v1.5"):
    """Create a RAGAS-compatible embeddings wrapper."""
    return LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"trust_remote_code": True},
            encode_kwargs={"normalize_embeddings": True},
        )
    )


def run_ragas_evaluation(
    data: list[dict],
    judge_model: str = "qwen3",
    embed_model: str = "nomic-ai/nomic-embed-text-v1.5",
) -> pd.DataFrame:
    """
    Run RAGAS evaluation on collected pipeline results.

    Args:
        data: List of dicts with keys:
            - question (str)
            - answer (str)
            - contexts (list[str])
            - ground_truth (str)
        judge_model: Ollama model name for LLM-as-judge
        embed_model: Sentence-transformers model for embeddings

    Returns:
        DataFrame with per-question metric scores.
    """
    llm = _build_llm(judge_model)
    embeddings = _build_embeddings(embed_model)

    samples = []
    for d in data:
        samples.append(
            SingleTurnSample(
                user_input=d["question"],
                response=d["answer"],
                retrieved_contexts=d["contexts"],
                reference=d["ground_truth"],
            )
        )

    dataset = EvaluationDataset(samples=samples)

    metrics = [
        Faithfulness(llm=llm),
        ResponseRelevancy(llm=llm, embeddings=embeddings),
        LLMContextPrecisionWithReference(llm=llm),
        LLMContextRecall(llm=llm),
    ]

    print(f"[RAGAS] Evaluating {len(samples)} samples with judge='{judge_model}'...")
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        run_config=RunConfig(timeout=600, max_workers=4, max_retries=3),
    )

    df = results.to_pandas()

    # RAGAS returns one row per sample in input order, but drops our metadata.
    # Prepend question_id / candidate_name / category / difficulty by position so
    # the CSV carries the same identifying columns as every other component report.
    if len(df) == len(data):
        meta = pd.DataFrame([{
            "question_id": d.get("id", ""),
            "candidate_name": d.get("candidate_name", ""),
            "category": d.get("category", ""),
            "difficulty": d.get("difficulty", ""),
        } for d in data])
        df = pd.concat([meta.reset_index(drop=True), df.reset_index(drop=True)], axis=1)
    else:
        print(f"[RAGAS] WARNING: {len(df)} score rows != {len(data)} inputs — "
              f"skipping metadata columns to avoid misalignment.")

    print(f"[RAGAS] Evaluation complete.")
    return df
