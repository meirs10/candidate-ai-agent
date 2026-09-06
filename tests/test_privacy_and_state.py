"""
Regression tests for the invariants that would be worst to break silently.

Each of these guards something that has no visible symptom when it regresses: a
leaked proficiency score reads like a normal answer, a reachable Setup page looks
like a working app, and a shared mutable default only shows up as "why does this
form remember things I didn't save?".
"""

import copy
import json
from pathlib import Path

import pytest

import settings as config
from store import structured

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def temp_profile(tmp_path, monkeypatch):
    """Point the profile store at a temp file so tests never touch the real one."""
    path = tmp_path / "candidate.json"
    monkeypatch.setattr(structured, "DATA_PATH", str(path))
    return path


# ── The 1-5 proficiency level is candidate-private ───────────────────────────

def test_skill_level_is_never_persisted(temp_profile):
    """save_skill_results must drop the model's level and keep only evidence.

    The whole privacy design rests on this: recruiters and the agent see the
    passages that support a skill, never a number. If a level ever reaches disk,
    get_field("skill_evidence") and any future consumer would happily serve it.
    """
    structured.save({"full_name": "Test"})  # initialise the file
    results = [
        {"skill": "Python", "level": 5, "chunks": ["built a trading bot"], "doc_ids": ["cv"]},
        {"skill": "Kafka", "level": 2, "chunks": ["mentioned in passing"], "doc_ids": ["cv"]},
    ]
    structured.save_skill_results(["Python", "Kafka"], results)

    raw = temp_profile.read_text(encoding="utf-8")
    assert '"level"' not in raw, "the 1-5 proficiency level reached disk"
    assert "skill_scores" not in raw, "legacy scored field reached disk"

    for entry in structured.load()["skill_evidence"]:
        assert "level" not in entry
        assert entry["chunks"], "evidence must survive even though the level does not"


def test_legacy_skill_scores_are_stripped_on_load(temp_profile):
    """An old profile that still has scores on disk must not surface them."""
    temp_profile.write_text(json.dumps({
        "full_name": "Old Profile",
        "skill_scores": [{"skill": "Python", "level": 4, "chunks": ["x"], "doc_ids": ["cv"]}],
    }), encoding="utf-8")

    data = structured.load()
    assert "skill_scores" not in data
    assert data["skill_evidence"][0]["skill"] == "Python"
    assert "level" not in data["skill_evidence"][0]


def test_skill_evidence_field_reports_no_number(temp_profile):
    """get_field must describe evidence by count, never by rating."""
    structured.save({"skill_evidence": [
        {"skill": "Python", "chunks": ["a", "b"], "doc_ids": ["cv"]}]})
    out = structured.get_field("skill_evidence")
    assert "Python" in out and "2 evidence passage" in out
    assert "/5" not in out and "level" not in out.lower()


# ── The Setup page must stay unreachable in production ───────────────────────

def test_no_directory_named_pages(tmp_path=None):
    """Streamlit auto-publishes every file in a top-level `pages/` directory as
    its own route. Those routes never execute main.py, so they bypass both the
    access-code gate and the APP_MODE check — a recruiter could open /setup and
    edit the profile. The app dir is called `app_pages/` precisely to avoid this;
    renaming it back would silently reopen the hole, with no failing test unless
    this one exists.
    """
    assert not (REPO_ROOT / "pages").is_dir(), (
        "a top-level pages/ directory re-enables Streamlit's auto-routing, "
        "which bypasses require_auth() and the APP_MODE production gate"
    )
    assert (REPO_ROOT / "app_pages").is_dir()


def test_main_hides_setup_page_in_production():
    """main.py must only register the Setup page outside production."""
    src = (REPO_ROOT / "main.py").read_text(encoding="utf-8")
    assert 'app_pages/setup.py' in src
    assert 'config.APP_MODE != "production"' in src, (
        "the Setup page registration is no longer gated on APP_MODE"
    )


def test_setup_page_guards_itself():
    """Defense in depth: the page re-checks auth and mode rather than trusting
    that it was reached through the intended navigation."""
    src = (REPO_ROOT / "app_pages" / "setup.py").read_text(encoding="utf-8")
    assert "require_auth()" in src
    assert 'config.APP_MODE == "production"' in src


# ── Profile defaults must not be shared between callers ──────────────────────

def test_load_returns_independent_defaults(temp_profile):
    """With no profile on disk, load() must deep-copy DEFAULT_FIELDS.

    A shallow copy handed every caller the SAME education list; the Setup page
    mutates that list in place, so an unsaved edit leaked into the module default
    and into the next session's "blank" form.
    """
    assert not temp_profile.exists()
    a, b = structured.load(), structured.load()
    assert a["education"] is not b["education"]
    assert a["education"] is not structured.DEFAULT_FIELDS["education"]

    before = copy.deepcopy(structured.DEFAULT_FIELDS)
    a["education"].append({"degree_title": "Mutated"})
    a["skills"].append("Mutated")
    assert structured.DEFAULT_FIELDS == before, "mutating a loaded profile changed the defaults"


# ── Unset fields must read as "Not provided" ─────────────────────────────────

def test_blank_field_reads_as_not_provided(temp_profile):
    """agent._looks_empty detects an empty structured result via the trailing
    "Not provided". DEFAULT_FIELDS stores unset optional fields as "", so
    dict.get's default never fired and a blank field counted as a hit —
    suppressing escalation to document search."""
    profile = copy.deepcopy(structured.DEFAULT_FIELDS)
    profile["full_name"] = "Real Name"
    structured.save(profile)

    assert structured.get_field("current_role") == "Not provided"
    assert structured.get_field("linkedin") == "Not provided"
    assert structured.get_field("full_name") == "Real Name"


@pytest.mark.parametrize("field_name", ["current_role", "preferred_location", "github"])
def test_blank_fields_trigger_escalation_signal(temp_profile, field_name):
    """The formatted tool output must end with "Not provided" so the agent's
    emptiness check fires."""
    from agent.agent import _looks_empty

    structured.save(copy.deepcopy(structured.DEFAULT_FIELDS))
    rendered = f"{field_name}: {structured.get_field(field_name)}"
    assert _looks_empty("get_structured_data", rendered)


# ── Single source of truth for identity/storage ──────────────────────────────

def test_collection_ids_come_from_settings():
    """agent.tools must derive its ids from settings, not redeclare them —
    otherwise ingestion and retrieval can address different collections."""
    import agent.tools as tools
    import rag.ingest as ingest
    import rag.retriever as retriever

    assert tools.CANDIDATE_ID == config.CANDIDATE_ID
    assert tools.PROJECT_ID == config.PROJECT_ID
    assert ingest.CHROMA_PATH == retriever.CHROMA_PATH == config.CHROMA_PATH
