"""
DeepEval evaluator — wraps DeepEval with a custom Ollama-based judge LLM.

Metrics computed (after removing redundancies with RAGAS):
  - GEval (Correctness):  Custom LLM-judge scoring answer correctness
                          (reference-based — all questions)

NOTE: HallucinationMetric was removed. It scored hallucination as the fraction
of retrieved chunks the answer "contradicted", treating the noisy retrieval pool
as authoritative ground truth, and the local judge conflated omission with
contradiction (it flagged verbatim-correct answers as 1.0). RAGAS faithfulness
already measures answer-grounding correctly, making it redundant.
"""

import json
import re

import pandas as pd
import ollama as ollama_client
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams


# ---------------------------------------------------------------------------
# Custom Ollama model adapter for DeepEval
# ---------------------------------------------------------------------------

class OllamaJudge(DeepEvalBaseLLM):
    """Wraps a local Ollama model so DeepEval can use it as evaluator.

    DeepEval's latest API passes a Pydantic ``schema`` to ``generate()``.
    When a schema is provided we force Ollama to return JSON and parse the
    response into the expected Pydantic model so that DeepEval can access
    attributes like ``.verdicts``, ``.truths``, ``.steps``, etc.
    """

    def __init__(self, model_name: str = "qwen3"):
        self._model_name = model_name

    def load_model(self):
        return self._model_name

    def _strip_think(self, text: str) -> str:
        """Remove <think>...</think> blocks produced by reasoning models."""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def generate(self, prompt: str, schema=None, **kwargs):
        """Generate a response, optionally parsed into a Pydantic schema."""
        chat_kwargs = dict(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            think=False,
        )
        # When DeepEval passes a schema, force JSON output
        if schema is not None:
            chat_kwargs["format"] = "json"

        response = ollama_client.chat(**chat_kwargs)
        content = self._strip_think(response["message"]["content"])

        if schema is not None:
            try:
                data = json.loads(content)
                return schema(**data)
            except (json.JSONDecodeError, Exception) as e:
                # If parsing fails, try to extract JSON from the response
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    return schema(**data)
                raise e

        return content

    async def a_generate(self, prompt: str, schema=None, **kwargs):
        return self.generate(prompt, schema=schema, **kwargs)

    def get_model_name(self) -> str:
        return self._model_name


# ---------------------------------------------------------------------------
# GEval evaluation (all questions — reference-based, no contexts needed)
# ---------------------------------------------------------------------------

def run_deepeval_geval(
    data: list[dict],
    judge_model: str = "qwen3",
) -> pd.DataFrame:
    """
    Run DeepEval GEval (Correctness) on all questions.

    Args:
        data: List of dicts with keys:
            - question (str)
            - answer (str)
            - ground_truth (str)
        judge_model: Ollama model name for LLM-as-judge

    Returns:
        DataFrame with per-question correctness scores.
    """
    model = OllamaJudge(model_name=judge_model)

    correctness = GEval(
        name="Correctness",
        # NOTE: do NOT specify a numeric scale here (e.g. "score 1 if correct").
        # GEval scores internally on a 0-10 scale and divides by 10, so telling
        # the judge "1 = fully correct" makes correct answers come back as 1/10 = 0.1.
        # Keep the criteria purely qualitative and let GEval handle the scale.
        criteria=(
            "Evaluate whether the Actual Output is factually correct and complete "
            "with respect to the Expected Output. The Actual Output is correct when "
            "it conveys the same facts as the Expected Output. Penalize factual "
            "contradictions and missing key facts. Do NOT penalize differences in "
            "wording, formatting (markdown, bold, links), verbosity, or additional "
            "relevant context, as long as the core facts agree with the Expected Output."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        model=model,
        threshold=0.5,
    )

    test_cases = []
    for d in data:
        test_cases.append(
            LLMTestCase(
                input=d["question"],
                actual_output=d["answer"],
                expected_output=d["ground_truth"],
            )
        )

    print(f"[DeepEval] Evaluating {len(test_cases)} test cases for GEval Correctness...")

    rows = []
    for i, tc in enumerate(test_cases):
        row = {
            "question": tc.input,
            "ground_truth": tc.expected_output,
            "actual_answer": tc.actual_output,
        }
        try:
            correctness.measure(tc)
            row["deepeval_correctness"] = correctness.score
            row["reason"] = correctness.reason
        except Exception as e:
            print(f"  [DeepEval] GEval failed on q{i+1}: {e}")
            row["deepeval_correctness"] = None
            row["reason"] = f"[ERROR] {e}"
        rows.append(row)

        if (i + 1) % 10 == 0:
            print(f"  [DeepEval] GEval progress: {i+1}/{len(test_cases)}")

    print(f"[DeepEval] GEval evaluation complete.")
    return pd.DataFrame(rows)
