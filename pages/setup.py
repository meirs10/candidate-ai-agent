import streamlit as st
import os
from rag.ingest import ingest_document
from store.structured import save, load, save_skill_results, DEFAULT_EDUCATION

CANDIDATE_ID = "candidate_001"  # later: dynamic per candidate


def parse_skills(raw: str) -> list[str]:
    """Parse a free-text skills box (newline- or comma-separated) into a clean,
    de-duplicated (case-insensitive) ordered list."""
    parts = [s.strip() for s in raw.replace(",", "\n").splitlines()]
    seen, out = set(), []
    for s in parts:
        key = s.lower()
        if s and key not in seen:
            seen.add(key)
            out.append(s)
    return out

# -- Required fields definition -----------------------------------------------

REQUIRED_FIELDS = {
    "full_name": "Full Name",
    "email_address": "Email Address",
    "phone_number": "Phone Number",
    "years_of_experience": "Years of Experience",
    "desired_job_title": "Desired Job Title",
    "availability": "Available From",
}

NO_EDUCATION_DETAILS = {"", "No Formal Education", "High School Diploma"}
DEGREE_OPTIONS = ["", "No Formal Education", "High School Diploma", "Associate", "Bachelor's", "Master's", "PhD", "Other"]


def required_label(label: str) -> str:
    """Append a red asterisk to a label to indicate it's required."""
    return f"{label} :red[*]"


def validate_profile(data: dict) -> list[str]:
    """Return a list of missing required field labels."""
    missing = []

    # Check flat required fields
    for field_key, field_label in REQUIRED_FIELDS.items():
        value = data.get(field_key, "")
        if not value or not str(value).strip():
            missing.append(field_label)

    # Check education: at least one entry must have a degree selected
    education = data.get("education", [])
    if not education or not any(e.get("degree_title") for e in education):
        missing.append("Degree Title (at least one education entry)")
    else:
        # For entries with Associate+, require field_of_study and institution
        for i, edu in enumerate(education):
            degree = edu.get("degree_title", "")
            if degree and degree not in NO_EDUCATION_DETAILS:
                num = f" (Education #{i + 1})"
                if not edu.get("field_of_study", "").strip():
                    missing.append(f"Field of Study{num}")
                if not edu.get("institution", "").strip():
                    missing.append(f"Institution{num}")

    return missing


# -- Page layout --------------------------------------------------------------

st.title("Candidate Setup")
st.caption("Fill in your profile so the AI agent can represent you to recruiters.")
st.markdown("Fields marked with :red[*] are required.")

data = load()

# Initialize education in session state
if "education" not in st.session_state:
    st.session_state.education = data.get("education", [DEFAULT_EDUCATION.copy()])

# ── Section 1: Upload Documents ─────────────────────────────────────────────

st.header("Upload Documents")
st.markdown("Upload your CV, transcripts, certificates, or any supporting documents.")

uploaded_files = st.file_uploader(
    "Supported formats: PDF, DOCX, TXT, MD, PNG, JPG",
    type=["pdf", "docx", "txt", "md", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files:
    os.makedirs("uploads", exist_ok=True)
    for uploaded_file in uploaded_files:
        file_path = f"uploads/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        ingest_document(file_path, CANDIDATE_ID)
        st.success(f"Ingested: {uploaded_file.name}")

st.divider()

# ── Section 2: Personal Details ─────────────────────────────────────────────

st.header("Personal Details")

data["full_name"] = st.text_input(required_label("Full Name"), value=data.get("full_name", ""), key="full_name")
data["email_address"] = st.text_input(required_label("Email Address"), value=data.get("email_address", ""), key="email_address")

col1, col2 = st.columns([1, 3])
with col1:
    data["country_code"] = st.text_input("Country Code", value=data.get("country_code", "+"))
with col2:
    data["phone_number"] = st.text_input(required_label("Phone Number"), value=data.get("phone_number", ""), key="phone_number")

col3, col4 = st.columns(2)
with col3:
    data["linkedin"] = st.text_input("LinkedIn URL", value=data.get("linkedin", ""))
with col4:
    data["github"] = st.text_input("GitHub URL", value=data.get("github", ""))

st.divider()

# ── Section 3: Education ────────────────────────────────────────────────────

st.header("Education")

for i, edu in enumerate(st.session_state.education):
    if i > 0:
        st.markdown("---")

    current_degree = edu.get("degree_title", "")
    degree_idx = DEGREE_OPTIONS.index(current_degree) if current_degree in DEGREE_OPTIONS else 0

    col_deg, col_field = st.columns(2)
    with col_deg:
        edu["degree_title"] = st.selectbox(
            required_label("Degree Title"),
            DEGREE_OPTIONS,
            index=degree_idx,
            key=f"degree_title_{i}",
        )
    with col_field:
        if edu["degree_title"] and edu["degree_title"] not in NO_EDUCATION_DETAILS:
            edu["field_of_study"] = st.text_input(
                required_label("Field of Study"),
                value=edu.get("field_of_study", ""),
                placeholder="e.g. Computer Science",
                key=f"field_of_study_{i}",
            )

    if edu["degree_title"] and edu["degree_title"] not in NO_EDUCATION_DETAILS:
        col_inst, col_year, col_gpa = st.columns([3, 1, 1])
        with col_inst:
            edu["institution"] = st.text_input(
                required_label("Institution"),
                value=edu.get("institution", ""),
                placeholder="e.g. Tel Aviv University",
                key=f"institution_{i}",
            )
        with col_year:
            edu["graduation_year"] = st.text_input(
                "Year",
                value=edu.get("graduation_year", ""),
                placeholder="e.g. 2023",
                key=f"graduation_year_{i}",
            )
        with col_gpa:
            edu["gpa"] = st.text_input(
                "GPA",
                value=edu.get("gpa", ""),
                placeholder="e.g. 85",
                key=f"gpa_{i}",
            )

    if i > 0:
        if st.button("Remove", key=f"remove_edu_{i}"):
            st.session_state.education.pop(i)
            st.rerun()

if st.button("+ Add Education"):
    st.session_state.education.append(DEFAULT_EDUCATION.copy())
    st.rerun()

st.divider()

# ── Section 4: Experience ───────────────────────────────────────────────────

st.header("Experience")

col9, col10 = st.columns(2)
with col9:
    data["years_of_experience"] = st.text_input(
        required_label("Years of Experience"),
        value=data.get("years_of_experience", ""),
        placeholder="e.g. 3",
        key="years_of_experience",
    )
with col10:
    data["current_role"] = st.text_input(
        "Current / Last Role",
        value=data.get("current_role", ""),
        placeholder="e.g. Backend Developer at Wix",
    )

JOB_DESC_LIMIT = 500
data["job_description"] = st.text_area(
    f"Describe what you do ({JOB_DESC_LIMIT} char limit)",
    value=data.get("job_description", ""),
    max_chars=JOB_DESC_LIMIT,
    height=120,
    placeholder="e.g. I'm a backend developer with 3 years of experience in Python and cloud infrastructure.",
)

st.divider()

# ── Section 5: Job Preferences ──────────────────────────────────────────────

st.header("Job Preferences")

col11, col12 = st.columns(2)
with col11:
    data["desired_job_title"] = st.text_input(
        required_label("Desired Job Title"),
        value=data.get("desired_job_title", ""),
        placeholder="e.g. Machine Learning Engineer",
        key="desired_job_title",
    )
with col12:
    data["monthly_salary_expectation"] = st.text_input(
        "Monthly Salary Expectation",
        value=data.get("monthly_salary_expectation", ""),
        placeholder="e.g. 25,000 ILS",
    )

col15, col16 = st.columns(2)
with col15:
    data["preferred_location"] = st.text_input(
        "Preferred Location",
        value=data.get("preferred_location", ""),
        placeholder="e.g. Tel Aviv, Israel",
    )
with col16:
    data["availability"] = st.text_input(
        required_label("Available From"),
        value=data.get("availability", ""),
        placeholder="e.g. Immediately / July 2026",
        key="availability",
    )

col13, col14 = st.columns(2)
with col13:
    work_types = ["Remote", "Hybrid", "Onsite", "No Preference"]
    current_work = data.get("work_type", "Remote")
    work_idx = work_types.index(current_work) if current_work in work_types else 0
    data["work_type"] = st.selectbox("Work Type", work_types, index=work_idx)
with col14:
    reloc_options = ["Yes", "No"]
    current_reloc = data.get("open_to_relocation", "Yes")
    reloc_idx = reloc_options.index(current_reloc) if current_reloc in reloc_options else 0
    data["open_to_relocation"] = st.selectbox("Open to Relocation?", reloc_options, index=reloc_idx)

st.divider()

# ── Section 6: Skills ───────────────────────────────────────────────────────

st.header("Skills")
st.markdown(
    "List the skills you want assessed (one per line, or comma-separated). "
    "Once your documents are uploaded above, a trained model estimates how much "
    "**evidence** your documents show for each skill, on a **1–5** scale.\n\n"
    ":gray[This score is private feedback for **you** — it helps you see which "
    "skills are well-supported and which need more evidence. It is **not** shared "
    "with recruiters and the AI agent never reports it. Only the underlying "
    "evidence passages are saved, so the agent can answer skill questions from "
    "real material in your documents.]"
)

skills_text = st.text_area(
    "Your skills",
    value="\n".join(data.get("skills", [])),
    placeholder="Python\nAWS\nDocker\nReact",
    height=120,
    key="skills_input",
)

if st.button("Estimate Skill Proficiency"):
    skills_list = parse_skills(skills_text)
    if not skills_list:
        st.warning("Add at least one skill first.")
    else:
        with st.spinner(
            f"Estimating proficiency for {len(skills_list)} skill(s) from your documents… "
            "(first run loads the scoring model and may take a while)"
        ):
            # Imported lazily so the page (and torch/transformers) only load when
            # estimation is actually requested.
            from store.skill_proficiency import estimate_skills

            results = estimate_skills(CANDIDATE_ID, skills_list)
            save_skill_results(skills_list, results)
        st.session_state["skill_scores"] = results
        st.success("Skill proficiency estimated and saved.")

# Show the latest estimates. The score is only ever in memory this run — it is
# NOT read back from disk (only evidence is persisted), so previously-saved
# skills show as evidence-only after a reload.
skill_results = st.session_state.get("skill_scores", [])
if skill_results:
    st.subheader("Your evidence strength by skill")
    st.caption(
        "Ranked from strongest to weakest evidence. This view is just for you."
    )
    # Level → (label, Streamlit color token, emoji) for a visually perceptive
    # ranking that reads at a glance.
    SCALE = {
        5: ("expert",              "green",  "🟢"),
        4: ("strong",              "green",  "🟢"),
        3: ("competent",           "orange", "🟡"),
        2: ("working familiarity", "orange", "🟠"),
        1: ("awareness",           "red",    "🔴"),
    }
    weak = []
    for r in sorted(skill_results, key=lambda x: x.get("level", 0), reverse=True):
        level = int(r.get("level", 0))
        label, color, dot = SCALE.get(level, ("", "gray", "⚪"))
        st.markdown(
            f"{dot} **{r['skill']}** — :{color}[{level}/5 · {label}]"
        )
        st.progress(level / 5)
        if level <= 2:
            weak.append(r["skill"])
            st.caption(
                "⚠️ Limited evidence. Consider uploading a document (CV bullet, "
                "project write-up, recommendation) that shows this skill in "
                "action to strengthen it."
            )
        with st.expander("Evidence found for this skill"):
            chunks = r.get("chunks", [])
            if chunks:
                for c in chunks:
                    preview = c[:300] + ("…" if len(c) > 300 else "")
                    st.markdown(f"- {preview}")
            else:
                st.caption("No supporting text was retrieved from the documents.")

    if weak:
        st.info(
            "**Tip:** these skills have the weakest evidence — "
            f"**{', '.join(weak)}**. Adding documents that demonstrate them will "
            "give the AI agent stronger material to represent you with."
        )

st.divider()

# ── Save ────────────────────────────────────────────────────────────────────

# Sync education + skills from this run's inputs into data before saving.
# Only the EVIDENCE is persisted — the model's 1-5 level is dropped so it never
# reaches recruiters or the agent.
data["education"] = st.session_state.education
data["skills"] = parse_skills(skills_text)
if "skill_scores" in st.session_state:
    data["skill_evidence"] = [
        {"skill": r.get("skill", ""),
         "chunks": r.get("chunks", []),
         "doc_ids": r.get("doc_ids", [])}
        for r in st.session_state["skill_scores"]
    ]
data.pop("skill_scores", None)  # never persist the score

if st.button("Save Profile", type="primary", use_container_width=True):
    missing = validate_profile(data)
    if missing:
        st.error(f"Please fill in the following required fields: **{', '.join(missing)}**")
    else:
        save(data)
        st.success(
            "Profile saved. Deploy the app (see DEPLOY.md) and share the hosted "
            "Recruiter Chat link + access code with recruiters."
        )
