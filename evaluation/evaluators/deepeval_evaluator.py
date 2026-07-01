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
        # NOTE: do NOT specify a numeric scale in these steps (e.g. "give 1 if
        # correct"). GEval scores internally on a 0-10 scale and divides by 10, so
        # anchoring the judge to "1 = fully correct" makes correct answers come
        # back as 1/10 = 0.1. Keep the rubric qualitative and let GEval map it.
        #
        # Explicit evaluation_steps (instead of a free-form `criteria`) so the
        # judge follows a fixed rubric every run — no per-run step auto-generation.
        # The rubric is reference-INCLUSION, not reference-equality: the Expected
        # Output is the set of facts that MUST be present; an answer that contains
        # all of them is fully correct even if it adds more correct detail or is
        # phrased/formatted differently. The Input is provided so the judge knows
        # what was actually asked and which Expected facts are the key ones.
        evaluation_steps=[
            "Read the Input (the question), the Expected Output (the reference "
            "answer, treated as the set of correct key facts), and the Actual "
            "Output (the answer being judged).",
            "From the Expected Output, list the key facts needed to answer the "
            "Input. These are the ONLY facts required for a fully correct answer.",
            "The Actual Output is fully correct when it states every key fact from "
            "the Expected Output and contradicts none of them. It does NOT need to "
            "match the Expected Output word-for-word; a correct answer that also "
            "includes additional true, relevant detail is still fully correct.",
            "Reduce the score in proportion to how many key facts from the Expected "
            "Output are missing from the Actual Output.",
            "Strongly penalize any factual contradiction: a different value, name, "
            "date or number, or claiming the information is unavailable/unknown "
            "when the Expected Output provides it.",
            "Do NOT penalize differences in wording, phrasing, formatting (markdown, "
            "bold, links), length or verbosity, or extra correct context, as long "
            "as all key facts from the Expected Output are present and uncontradicted.",
        ],
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        model=model,
        threshold=0.5,
    )

    # Keep each source dict next to its test case so per-question metadata
    # (question_id / candidate_name / category / difficulty) lands in the CSV.
    test_cases = []
    for d in data:
        test_cases.append((
            d,
            LLMTestCase(
                input=d["question"],
                actual_output=d["answer"],
                expected_output=d["ground_truth"],
            ),
        ))

    print(f"[DeepEval] Evaluating {len(test_cases)} test cases for GEval Correctness...")

    rows = []
    for i, (d, tc) in enumerate(test_cases):
        row = {
            "question_id": d.get("id", ""),
            "candidate_name": d.get("candidate_name", ""),
            "category": d.get("category", ""),
            "difficulty": d.get("difficulty", ""),
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
