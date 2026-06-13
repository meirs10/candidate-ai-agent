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
    "skill_scores": [],      # model-estimated proficiency:
                             #   [{"skill", "level" 1-5, "chunks", "doc_ids"}]
}

# Human-readable meaning of each 1-5 proficiency level (matches the scoring
# model's ordinal scale). Shown to recruiters so a bare number has context.
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

    # All estimated proficiencies, ranked high → low
    if field == "skill_scores":
        scores = data.get("skill_scores", [])
        if not scores:
            return "Not provided"
        ranked = sorted(scores, key=lambda s: s.get("level", 0), reverse=True)
        lines = [f"{s['skill']}: {s['level']}/5 ({PROFICIENCY_SCALE.get(s['level'], '')})"
                 for s in ranked]
        return "\n".join(lines)

    return data.get(field, "Not provided")


# -- Skill proficiency accessors --------------------------------------------

def get_skill_scores() -> list[dict]:
    """Return the stored list of estimated skill proficiencies (may be empty)."""
    return load().get("skill_scores", [])


def get_skill_score(skill: str) -> dict | None:
    """Look up one skill's estimate (case-insensitive). None if not estimated."""
    target = skill.strip().lower()
    for entry in get_skill_scores():
        if entry.get("skill", "").strip().lower() == target:
            return entry
    return None


def save_skill_results(skills: list[str], scores: list[dict]) -> None:
    """Persist candidate-listed skills + their estimated proficiencies.

    Loads from disk first so this can run independently of the main profile
    form (it won't clobber already-saved fields).
    """
    data = load()
    data["skills"] = skills
    data["skill_scores"] = scores
    save(data)
