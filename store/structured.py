import json
import os

DATA_PATH = "./store/data/candidate.json"

DEFAULT_EDUCATION = {
    "degree_title": "",
    "field_of_study": "",
    "institution": "",
    "graduation_year": "",
    "gpa": "",
}

DEFAULT_FIELDS = {
    # Personal Details
    "full_name": "",
    "email_address": "",
    "country_code": "",
    "phone_number": "",
    "linkedin": "",
    "github": "",

    # Education (list of degrees)
    "education": [DEFAULT_EDUCATION.copy()],

    # Experience
    "years_of_experience": "",
    "current_role": "",
    "desired_job_title": "",
    "job_description": "",

    # Job Preferences
    "monthly_salary_expectation": "",
    "preferred_location": "",
    "availability": "",
    "work_type": "",         # Remote / Hybrid / Onsite / No Preference
    "open_to_relocation": "",

    # Skills
    "skills": [],            # raw skills the candidate listed (free text)
    "skill_evidence": [],    # per-skill evidence retrieved from the documents:
                             #   [{"skill", "chunks", "doc_ids"}]
                             # NOTE: the trained model's 1-5 proficiency score is
                             # deliberately NOT stored here. That number is shown
                             # to the CANDIDATE only (setup page), as private
                             # feedback to encourage adding more evidence for weak
                             # skills. Recruiters/the agent only ever see the
                             # evidence, never the model's rating.
}

# Human-readable meaning of each 1-5 proficiency level (matches the scoring
# model's ordinal scale). CANDIDATE-FACING ONLY — used on the setup page to give
# the candidate context for their private score. It is never surfaced to
# recruiters (the recruiter agent has no access to the numeric level at all).
PROFICIENCY_SCALE = {
    1: "awareness (a passing mention)",
    2: "working familiarity",
    3: "competent / day-to-day use",
    4: "strong / leads work in it",
    5: "expert / authority",
}


def load() -> dict:
    if not os.path.exists(DATA_PATH):
        return DEFAULT_FIELDS.copy()
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    # Migration: convert old flat education fields to list format
    if "education" not in data and "degree_title" in data:
        data["education"] = [{
            "degree_title": data.pop("degree_title", ""),
            "field_of_study": data.pop("field_of_study", ""),
            "institution": data.pop("institution", ""),
            "graduation_year": data.pop("graduation_year", ""),
            "gpa": data.pop("gpa", ""),
        }]
    # Migration: old profiles stored the model's 1-5 proficiency under
    # "skill_scores". The score is now candidate-private; strip the level and keep
    # only the evidence under "skill_evidence" so no rating survives on disk.
    if "skill_evidence" not in data and "skill_scores" in data:
        data["skill_evidence"] = [
            {"skill": s.get("skill", ""),
             "chunks": s.get("chunks", []),
             "doc_ids": s.get("doc_ids", [])}
            for s in data.get("skill_scores", [])
        ]
        data.pop("skill_scores", None)
    return data


def save(data: dict):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_field(field: str) -> str:
    data = load()

    # Handle education field specially — format all degrees into readable text
    if field == "education":
        entries = data.get("education", [])
        if not entries:
            return "Not provided"
        lines = []
        for i, edu in enumerate(entries, 1):
            title = edu.get("degree_title", "")
            if not title:
                continue
            parts = [title]
            if edu.get("field_of_study"):
                parts.append(f"in {edu['field_of_study']}")
            if edu.get("institution"):
                parts.append(f"from {edu['institution']}")
            if edu.get("graduation_year"):
                parts.append(f"({edu['graduation_year']})")
            if edu.get("gpa"):
                parts.append(f"- GPA: {edu['gpa']}")
            lines.append(" ".join(parts))
        return "\n".join(lines) if lines else "Not provided"

    # Handle phone_number specially — prepend country code
    if field == "phone_number":
        phone = data.get("phone_number", "Not provided")
        country_code = data.get("country_code", "")
        if country_code and phone != "Not provided":
            return f"{country_code} {phone}"
        return phone

    # Skills the candidate listed (raw, comma-joined)
    if field == "skills":
        skills = data.get("skills", [])
        return ", ".join(skills) if skills else "Not provided"

    # Assessed skills + the evidence found for each (no proficiency level — that
    # is candidate-private and never stored).
    if field == "skill_evidence":
        evidence = data.get("skill_evidence", [])
        if not evidence:
            return "Not provided"
        lines = []
        for e in evidence:
            n = len(e.get("chunks", []))
            lines.append(f"{e['skill']}: {n} evidence passage(s) from the documents")
        return "\n".join(lines)

    return data.get(field, "Not provided")


# -- Skill evidence accessors -----------------------------------------------
# These expose the per-skill EVIDENCE the scorer retrieved — never the model's
# 1-5 proficiency level (that is shown to the candidate on the setup page and is
# never persisted, so recruiters/the agent cannot surface it).

def get_skill_evidence() -> list[dict]:
    """Return the stored per-skill evidence (may be empty).

    Each entry: {"skill", "chunks", "doc_ids"} — no proficiency level.
    """
    return load().get("skill_evidence", [])


def get_skill_evidence_for(skill: str) -> dict | None:
    """Look up one skill's evidence (case-insensitive). None if not assessed."""
    target = skill.strip().lower()
    for entry in get_skill_evidence():
        if entry.get("skill", "").strip().lower() == target:
            return entry
    return None


def save_skill_results(skills: list[str], results: list[dict]) -> None:
    """Persist candidate-listed skills + the EVIDENCE found for each.

    `results` are the estimate_skills() outputs, which include the model's 1-5
    `level`. That level is deliberately DROPPED here: only the evidence (chunks +
    doc_ids) is written to disk, so the recruiter agent can ground skill answers
    in real passages without ever exposing the model's rating.

    Loads from disk first so this can run independently of the main profile
    form (it won't clobber already-saved fields).
    """
    data = load()
    data["skills"] = skills
    data["skill_evidence"] = [
        {"skill": r.get("skill", ""),
         "chunks": r.get("chunks", []),
         "doc_ids": r.get("doc_ids", [])}
        for r in results
    ]
    data.pop("skill_scores", None)  # drop any legacy scored field
    save(data)
