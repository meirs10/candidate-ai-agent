import streamlit as st
import hashlib
import os

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`
from auth import require_auth
from rag.ingest import ingest_document, infer_doc_type
from store.structured import save, load, save_skill_results, DEFAULT_EDUCATION
from app_pages import ui

# Defense in depth. main.py already gates on the access code and only registers
# this page outside production — but this page can edit the profile and trigger
# ingestion, so it re-checks both rather than trusting that it was reached
# through the intended navigation.
require_auth()
if config.APP_MODE == "production":
    st.error("The Candidate Setup page is disabled in production.")
    st.stop()

CANDIDATE_ID = config.CANDIDATE_ID  # single source of truth: settings.py


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

ui.inject_css()

data = load()

ui.header(
    "Candidate Setup",
    "Build the profile your AI agent will represent you with",
    monogram=ui.initials(data.get("full_name", "")),
    badge="private",
)

# Completion meter. The form is long and its required fields are scattered across
# five sections, so without this the only way to discover what's still missing is
# to hit Save and read an error.
_done = len(REQUIRED_FIELDS) - len([
    k for k in REQUIRED_FIELDS if not str(data.get(k, "") or "").strip()
])
st.progress(_done / len(REQUIRED_FIELDS),
            text=f"{_done} of {len(REQUIRED_FIELDS)} required fields complete "
                 f"· fields marked :red[*] are required")

# Initialize education in session state
if "education" not in st.session_state:
    st.session_state.education = data.get("education", [DEFAULT_EDUCATION.copy()])

# ── Section 1: Upload Documents ─────────────────────────────────────────────

ui.section(1, "Upload documents",
           "Your CV, transcripts, certificates or project write-ups. These are what "
           "every answer will be grounded in, so the more evidence the better.")

# Document type selects the SUMMARY RUBRIC. Everything used to be ingested as
# "cv", so a project write-up was summarised against a rubric demanding a name,
# degree and years of experience — producing stored refusals ("Unable to provide
# requested summary") and, worse, summaries that adopted whatever name appeared
# in the text as the candidate's own.
#
# Every type lands in the candidate's own collection. The project knowledge base
# (search_project, "how does this assistant work?") is deliberately NOT reachable
# from this page: it describes the system, not any candidate, so it is built once
# from store/data/project/project_overview.txt by build_project_kb.py.
DOC_TYPE_LABELS = {
    "cv": "CV / Résumé",
    "certificate": "Certificate, transcript or award",
    "recommendation": "Recommendation letter",
    "readme": "Project write-up (your own work)",
}
_TYPE_ORDER = list(DOC_TYPE_LABELS)

uploaded_files = st.file_uploader(
    "Supported formats: PDF, DOCX, TXT, MD, PNG, JPG",
    type=["pdf", "docx", "txt", "md", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="uploader",
)

# Files already ingested in this session, keyed by content hash. This is load
# bearing, not an optimisation: st.file_uploader returns its files on EVERY
# rerun, and Streamlit reruns the whole script on any widget interaction. Without
# this guard, re-running ingestion would re-pay Voyage for embeddings and
# OpenRouter for a fresh summary of every document.
if "ingested_hashes" not in st.session_state:
    st.session_state.ingested_hashes = set()

if uploaded_files:
    # Hash the bytes rather than trusting the filename: re-uploading an edited
    # file under the same name must re-ingest, and an unchanged one must not.
    staged, already = [], 0
    for uf in uploaded_files:
        payload = uf.getvalue()
        digest = hashlib.sha256(payload).hexdigest()
        if digest in st.session_state.ingested_hashes:
            already += 1
        else:
            staged.append((uf.name, payload, digest))

    if already:
        st.caption(f"✓ {already} document(s) already indexed this session.")

    if staged:
        st.markdown("###### Set the type for each document")
        st.caption(
            "This decides how each one is summarised — a CV by who you are, a "
            "project write-up by what the work does. Defaults are guessed from "
            "the filename; correct any that are wrong."
        )

        # Choice is collected per file BEFORE anything is ingested, so a mixed
        # batch goes in correctly in one pass instead of forcing one upload round
        # per type.
        choices = {}
        for name, _payload, digest in staged:
            c_name, c_type = st.columns([3, 2], vertical_alignment="center")
            c_name.markdown(f"📄 `{name}`")
            default = infer_doc_type(name)
            choices[digest] = c_type.selectbox(
                f"Type for {name}",
                _TYPE_ORDER,
                index=_TYPE_ORDER.index(default),
                format_func=lambda t: DOC_TYPE_LABELS[t],
                key=f"doctype_{digest}",     # digest-keyed: stable across reruns
                label_visibility="collapsed",
            )

        # An explicit button, not automatic ingestion: the candidate needs a
        # chance to fix the guessed types first, and it makes the expensive step
        # something they trigger rather than something that fires on upload.
        if st.button(f"Ingest {len(staged)} document(s)", type="primary",
                     use_container_width=True):
            os.makedirs("uploads", exist_ok=True)
            # Ingestion is slow and synchronous: OCR for images, plus one LLM
            # call per document for the summary index. Streamlit dims the whole
            # page while a script runs, so without an explicit progress surface
            # the form below looks frozen when it is simply busy.
            total = len(staged)
            with st.status(f"Ingesting {total} document(s)…", expanded=True) as status:
                done = 0
                for name, payload, digest in staged:
                    doc_type = choices[digest]
                    st.write(f"Reading **{name}** as *{DOC_TYPE_LABELS[doc_type]}*…")
                    file_path = f"uploads/{name}"
                    with open(file_path, "wb") as f:
                        f.write(payload)
                    try:
                        ingest_document(file_path, CANDIDATE_ID, doc_type=doc_type)
                    except Exception as exc:
                        # One unreadable file must not abandon the rest of the
                        # batch, and the candidate needs to know which failed.
                        st.error(f"Could not ingest **{name}**: "
                                 f"{type(exc).__name__}: {exc}")
                        continue
                    # Recorded only after success, so a failed file is retried
                    # rather than silently marked as done.
                    st.session_state.ingested_hashes.add(digest)
                    done += 1
                    st.write(f"✓ Indexed **{name}**")
                status.update(
                    label=f"Ingested {done} of {total} document(s)",
                    state="complete" if done == total else "error",
                    expanded=done != total,
                )
            if done:
                st.success(
                    f"{done} document(s) indexed. Fill in the details below, then "
                    "run **Estimate Skill Proficiency** in step 6 before saving."
                )

st.divider()

# ── Section 2: Personal Details ─────────────────────────────────────────────

ui.section(2, "Personal details")

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

ui.section(3, "Education")

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

ui.section(4, "Experience")

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

ui.section(5, "Job preferences")

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

ui.section(6, "Skills")
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
