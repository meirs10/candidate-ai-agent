import copy
import json
import os
import re

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
        # deepcopy, not .copy(): a shallow copy hands every caller the SAME
        # "education" list object that lives in DEFAULT_FIELDS. The setup page
        # mutates that list in place (add/remove a degree), so a shallow copy
        # lets an unsaved edit leak into DEFAULT_FIELDS for the rest of the
        # process — and from there into the next session's "blank" profile.
        return copy.deepcopy(DEFAULT_FIELDS)
    with open(DATA_PATH) as f:
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


# Field names the router is likely to invent, mapped to the real keys. The
# router is told the exact field list, but a recruiter asks "what's their
# preferred work setup?" and the router paraphrases — and an unmatched name used
# to return "Not provided", which the agent then reported as "the candidate
# hasn't provided their availability", a confident false negative about data
# that was sitting right there. Getting the field name slightly wrong must
# degrade to a lookup, not to a denial.
_FIELD_ALIASES = {
    "name": "full_name",
    "fullname": "full_name",
    "email": "email_address",
    "mail": "email_address",
    "phone": "phone_number",
    "mobile": "phone_number",
    "telephone": "phone_number",
    "linkedin_url": "linkedin",
    "github_url": "github",
    "degree": "education",
    "university": "education",
    "school": "education",
    "gpa": "education",
    "experience": "years_of_experience",
    "years_experience": "years_of_experience",
    "seniority": "years_of_experience",
    "role": "current_role",
    "title": "current_role",
    "position": "current_role",
    "current_position": "current_role",
    "desired_role": "desired_job_title",
    "target_role": "desired_job_title",
    "summary": "job_description",
    "bio": "job_description",
    "about": "job_description",
    "salary": "monthly_salary_expectation",
    "salary_expectation": "monthly_salary_expectation",
    "compensation": "monthly_salary_expectation",
    "pay": "monthly_salary_expectation",
    "location": "preferred_location",
    "preferred_work_location": "preferred_location",
    "city": "preferred_location",
    "start_date": "availability",
    "notice_period": "availability",
    "when_can_they_start": "availability",
    "work_setup": "work_type",
    "preferred_work_setup": "work_type",
    "work_arrangement": "work_type",
    "work_preference": "work_type",
    "remote": "work_type",
    "hybrid": "work_type",
    "relocation": "open_to_relocation",
    "willing_to_relocate": "open_to_relocation",
}


def _canonical_field(field: str) -> list[str]:
    """Resolve a requested field name to one or more real profile keys.

    Handles three kinds of near-miss, in order: a compound request
    ("availability and work setup" — the router only gets one argument, but a
    recruiter routinely asks for two things at once), a known paraphrase, and a
    loose match against the real key names. Returns [] when nothing resembles a
    field, which the caller reports honestly rather than guessing.
    """
    raw = (field or "").strip().lower()
    if not raw:
        return []

    # Split a compound request into its parts before resolving each one.
    parts = [p.strip() for p in re.split(r",|;|\band\b|/|\+", raw) if p.strip()]
    resolved: list[str] = []

    for part in parts:
        norm = re.sub(r"[^a-z0-9]+", "_", part).strip("_")
        if not norm:
            continue
        if norm in DEFAULT_FIELDS or norm in ("skills", "skill_evidence", "education"):
            resolved.append(norm)
            continue
        if norm in _FIELD_ALIASES:
            resolved.append(_FIELD_ALIASES[norm])
            continue
        # Loose match: "preferred_work" -> preferred_location? No — require the
        # key's distinctive word, so a partial name only matches when it is
        # unambiguous.
        candidates = [k for k in [*list(DEFAULT_FIELDS), "skills", "skill_evidence"]
                      if norm in k or k in norm]
        if len(candidates) == 1:
            resolved.append(candidates[0])

    # De-duplicate, preserving order.
    seen, out = set(), []
    for k in resolved:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def get_field(field: str) -> str:
    """Look up one or more profile fields by name.

    Accepts a compound or paraphrased name and resolves it (see
    _canonical_field). With several fields resolved, each is returned on its own
    labelled line so the agent can answer a two-part question from one call.
    """
    resolved = _canonical_field(field)
    if len(resolved) > 1:
        lines = []
        for key in resolved:
            value = _get_one_field(key)
            label = key.replace("_", " ").capitalize()
            lines.append(f"{label}: {value}")
        return "\n".join(lines)
    if len(resolved) == 1:
        return _get_one_field(resolved[0])
    return _get_one_field(field)


def _get_one_field(field: str) -> str:
    data = load()

    # Handle education field specially — format all degrees into readable text
    if field == "education":
        entries = data.get("education", [])
        if not entries:
            return "Not provided"
        lines = []
        for _i, edu in enumerate(entries, 1):
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

    # dict.get's default only fires when the KEY IS ABSENT — but DEFAULT_FIELDS
    # initialises every optional field to "", so once a profile has been saved
    # the key exists and an unset field would return "" instead of
    # "Not provided". agent.agent._looks_empty() detects an empty structured
    # result with `.endswith("Not provided")`, so a blank value silently counted
    # as a hit and suppressed result-based escalation to document search.
    value = data.get(field)
    if value is None or not str(value).strip():
        return "Not provided"
    return value


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
