from rag.retriever import retrieve
from store.structured import (
    PROFICIENCY_SCALE,
    get_field,
    get_skill_score,
    get_skill_scores,
)

CANDIDATE_ID = "candidate_001"  # later: dynamic per candidate

# Store the last retrieval metadata for evaluation access
_last_retrieval_meta = {}

# -- Tool schemas (sent to Ollama) ------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_structured_data",
            "description": (
                "Get fixed, guaranteed-accurate candidate information. "
                "ONLY use this tool for the following fields:\n"
                "  Personal: full_name, email_address, country_code, phone_number, linkedin, github\n"
                "  Education: education (returns all degrees, fields of study, institutions, and GPAs)\n"
                "  Experience: years_of_experience, current_role, desired_job_title, job_description\n"
                "  Preferences: monthly_salary_expectation, preferred_location, availability, work_type, open_to_relocation\n"
                "If the question does not match one of these fields, "
                "use search_documents instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": (
                            "One of: full_name, email_address, country_code, "
                            "phone_number, linkedin, github, education, "
                            "years_of_experience, current_role, desired_job_title, "
                            "job_description, monthly_salary_expectation, "
                            "preferred_location, availability, work_type, open_to_relocation"
                        ),
                    }
                },
                "required": ["field"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_skill_proficiency",
            "description": (
                "Get the candidate's proficiency LEVEL in a skill, on a 1-5 scale "
                "(1=awareness, 2=working familiarity, 3=competent, 4=strong, 5=expert), "
                "together with the document evidence behind it. The level is inferred "
                "from the candidate's uploaded documents by a trained scoring model — "
                "it is verified, not self-reported.\n"
                "USE THIS for any question about HOW GOOD / HOW STRONG / HOW PROFICIENT / "
                "HOW SKILLED / HOW EXPERIENCED the candidate is in a specific technology, "
                "tool, or skill; to rate or score a skill; or to rank/compare their skills "
                "(e.g. 'How good is she at Python?', 'Rate their AWS', 'What are their "
                "strongest skills?'). Pass the skill name; omit it to list every assessed "
                "skill with its level. If the skill was not assessed, this tool says so — "
                "then fall back to search_documents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": (
                            "The skill/technology to get the proficiency level for "
                            "(e.g. 'Python', 'AWS'). Leave empty to list all assessed "
                            "skills with their levels."
                        ),
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Search the candidate's uploaded documents (CV, grades, certificates). "
                "Use this for ANY question about the candidate that is not covered "
                "by get_structured_data or get_skill_proficiency — including projects, "
                "detailed experience, what they did with a technology, achievements, "
                "certifications, and more. Also use this as a fallback when a skill was "
                "not among the assessed proficiencies."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The question or topic to search for"}},
                "required": ["query"],
            },
        },
    },
]

# -- Tool execution functions ------------------------------------------------


def search_documents(**kwargs) -> str:
    global _last_retrieval_meta
    # Accept any argument name the LLM uses (query, field, etc.)
    query = kwargs.get("query", next(iter(kwargs.values()), ""))
    # Auto-recover if the LLM passes a dict instead of a string
    if isinstance(query, dict):
        query = query.get("query", query.get("description", str(query)))
    result = retrieve(str(query), CANDIDATE_ID)
    chunks = result["chunks"]
    # Store retrieval metadata for evaluation
    _last_retrieval_meta = {
        "route": result["route"],
        "expanded_queries": result["expanded_queries"],
        "chunks": chunks,
        "fused_pool": result.get("fused_pool"),
    }
    if not chunks:
        return "No relevant information found in documents."
    return "\n\n".join(chunks)


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
    """Return the candidate's model-estimated proficiency for a skill (read from
    the structured store, where it was saved at ingest time) plus its evidence."""
    # Accept any argument name the LLM uses (skill, query, field, ...)
    skill = kwargs.get("skill", next(iter(kwargs.values()), ""))
    if isinstance(skill, dict):
        skill = skill.get("skill", skill.get("description", str(skill)))
    skill = str(skill).strip()

    scores = get_skill_scores()
    if not scores:
        return (
            "No skill proficiency estimates are available for this candidate. "
            "Use search_documents to look for skill evidence in the documents."
        )

    # No specific skill → ranked overview of everything assessed
    if not skill:
        ranked = sorted(scores, key=lambda s: s.get("level", 0), reverse=True)
        lines = [f"- {s['skill']}: {s['level']}/5 ({PROFICIENCY_SCALE.get(s['level'], '')})" for s in ranked]
        return "Estimated skill proficiencies (1-5):\n" + "\n".join(lines)

    entry = get_skill_score(skill)
    if entry is None:
        listed = ", ".join(s["skill"] for s in scores)
        return (
            f"'{skill}' was not among the candidate's assessed skills "
            f"(assessed: {listed}). Use search_documents to check the documents directly."
        )

    level = entry.get("level", 0)
    lines = [
        f"{entry['skill']} — estimated proficiency: {level}/5 ({PROFICIENCY_SCALE.get(level, '')}).",
        "Scale: 1=awareness, 2=working familiarity, 3=competent, 4=strong, 5=expert.",
        "This is model-inferred from the candidate's documents, not self-reported.",
    ]
    chunks = entry.get("chunks", [])
    if chunks:
        lines.append("Evidence it was based on:")
        for c in chunks[:3]:
            preview = c[:300] + ("…" if len(c) > 300 else "")
            lines.append(f"- {preview}")
    return "\n".join(lines)


def get_last_retrieval_meta() -> dict:
    """Return the metadata from the last search_documents call."""
    return _last_retrieval_meta.copy()


# -- Dispatcher --------------------------------------------------------------

TOOL_FUNCTIONS = {
    "search_documents": search_documents,
    "get_structured_data": get_structured_data,
    "get_skill_proficiency": get_skill_proficiency,
}


def execute_tool(name: str, arguments: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return f"Unknown tool: {name}"
    return func(**arguments)
