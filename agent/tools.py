from rag.retriever import retrieve
from store.structured import (
    get_field,
    get_skill_evidence,
    get_skill_evidence_for,
)
import settings as config  # module named `settings` to avoid shadowing the scorer's `config`

# Rebindable module attributes, not direct imports: the eval harness swaps them
# per candidate at runtime (evaluation/pipeline.set_candidate_id). Defaults come
# from settings.py so there is one source of truth.
CANDIDATE_ID = config.CANDIDATE_ID
PROJECT_ID = config.PROJECT_ID

# Store the last retrieval metadata for evaluation access
_last_retrieval_meta = {}

# -- Tool execution functions ------------------------------------------------


def get_structured_data(**kwargs) -> str:
    # Accept any argument name the LLM uses (field, query, etc.)
    field = kwargs.get("field", next(iter(kwargs.values()), ""))
    # Auto-recover if the LLM passes a dict instead of a string
    if isinstance(field, dict):
        raw = field.get("field", field.get("description", str(field)))
        field = raw.split(":")[0].strip()
    value = get_field(str(field))
    return f"{field}: {value}"


def get_skill_proficiency(**kwargs) -> str:
    """Return the curated document EVIDENCE for a candidate skill (read from the
    structured store, where it was saved at profile-setup time).

    Deliberately returns evidence only — never the trained model's 1-5 level,
    which is candidate-private and not persisted. The agent grounds its answer in
    these passages and describes the skill qualitatively.
    """
    # Accept any argument name the LLM uses (skill, query, field, ...)
    skill = kwargs.get("skill", next(iter(kwargs.values()), ""))
    if isinstance(skill, dict):
        skill = skill.get("skill", skill.get("description", str(skill)))
    skill = str(skill).strip()

    evidence = get_skill_evidence()
    if not evidence:
        return ("No curated skill evidence is available for this candidate. "
                "Use search_documents to look for skill evidence in the documents.")

    # No specific skill → list everything that was assessed
    if not skill:
        listed = ", ".join(e["skill"] for e in evidence)
        return ("Assessed skills (each has supporting evidence from the "
                f"documents): {listed}.\n"
                "Ask about any one of them to see the specific evidence, or use "
                "search_documents for more detail.")

    entry = get_skill_evidence_for(skill)
    if entry is None:
        listed = ", ".join(e["skill"] for e in evidence)
        return (f"'{skill}' was not among the candidate's assessed skills "
                f"(assessed: {listed}). Use search_documents to check the documents directly.")

    chunks = entry.get("chunks", [])
    if not chunks:
        return (f"'{entry['skill']}' was assessed but no supporting passages were "
                "retrieved for it. Use search_documents to check the documents directly.")

    lines = [
        f"Document evidence for '{entry['skill']}' (describe what it shows in your "
        "own words; do not state a numeric rating):",
    ]
    for c in chunks[:3]:
        preview = c[:300] + ("…" if len(c) > 300 else "")
        lines.append(f"- {preview}")
    return "\n".join(lines)


def get_last_retrieval_meta() -> dict:
    """Return the metadata from the last search_documents call."""
    return _last_retrieval_meta.copy()


# -- Dispatcher --------------------------------------------------------------

# Only the two non-retrieval tools dispatch through here. The search tools are
# executed by agent._run_one_tool, which calls retrieve() directly so each
# concurrent call keeps its own retrieval metadata instead of racing on a global.
TOOL_FUNCTIONS = {
    "get_structured_data": get_structured_data,
    "get_skill_proficiency": get_skill_proficiency,
}


def execute_tool(name: str, arguments: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return f"Unknown tool: {name}"
    return func(**arguments)
