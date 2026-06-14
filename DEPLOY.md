# Deploying the Recruiter Chat (Option A — all-API, always-on)

The app runs in two distinct modes:

| Mode | What runs | Where |
|---|---|---|
| **Build** | ingest docs → embed → estimate skills → produce `chroma_db/` + `store/data/candidate.json` | **your laptop** (`requirements-dev.txt`) |
| **Serve** | recruiter chat only: retrieval (Voyage) + LLM (Claude) | **hosted, always on** (`requirements.txt`) |

The heavy models (DeBERTa skill scorer, document parsing, optional local LLM/embeddings/reranker) are **build-time only** and never deploy.

---

## 0. Get API keys
- **Anthropic** → https://console.anthropic.com (load ~$5 credit)
- **Voyage AI** → https://dashboard.voyageai.com (generous free tier covers this app)

---

## 1. Build the profile locally (one-time, and whenever you update your CV)

```bash
pip install -r requirements-dev.txt

# Use the API providers so the index is embedded with Voyage (must match serve).
export ANTHROPIC_API_KEY=sk-ant-...
export VOYAGE_API_KEY=pa-...
export APP_MODE=setup            # exposes the Candidate Setup page
export EMBED_PROVIDER=voyage     # IMPORTANT: index must be built with the same
export RERANK_PROVIDER=voyage    # embedder the serve path queries with

streamlit run main.py
```

On the **Candidate Setup** page: upload your documents, fill the profile, click
**Estimate Skill Proficiency** (runs the local DeBERTa scorer), then **Save Profile**.

This produces:
- `chroma_db/` — the Voyage-embedded vector index
- `store/data/candidate.json` — your facts + precomputed skill scores

> ⚠️ Re-run this whenever you switch `EMBED_PROVIDER` — query and document
> embeddings must come from the same model.

### 1b. Build the project knowledge base (one-time)

So recruiters can also ask about *how the app itself was built* (the `search_project`
tool), ingest the project overview into its own collection with the **same**
embedding provider:

```bash
EMBED_PROVIDER=voyage VOYAGE_API_KEY=pa-... ANTHROPIC_API_KEY=sk-ant-... \
  python build_project_kb.py
```

This populates the `project_kb` (+ `project_kb_summaries`) collections in
`chroma_db/`. Edit `store/data/project/project_overview.txt` and re-run to update
it. The file contains no private data or keys, so it can stay in the repo.

---

## 2. Get the built artifacts to the host (privately)

`chroma_db/` and `store/data/candidate.json` contain your real PII, so keep them
out of any public repo. Options:
- Deploy from a **private** GitHub repo that includes them, **or**
- Keep the repo public but upload the two artifacts via the host's private file
  storage / a private branch.

(`.gitignore` already excludes `chroma_db` and `store/data` by default — adjust
for your chosen private channel.)

---

## 3. Deploy the serve path

### Streamlit Community Cloud (free, recommended)
1. Push the repo (private) to GitHub.
2. https://share.streamlit.io → New app → pick the repo, `main.py`.
3. **Advanced settings → Secrets**: paste from `secrets.toml.example`
   (`ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `APP_PASSWORD`, `APP_MODE="production"`).
4. Deploy. The platform installs `requirements.txt` (lean, no torch) and serves
   over HTTPS. Share the URL + access code with recruiters.

### Hugging Face Spaces (free alternative)
Create a **Streamlit** Space, push the repo, set the same keys under
**Settings → Variables and secrets**.

Either platform sleeps on long idle and wakes in seconds on visit. To keep it
warm, point a free uptime pinger (e.g. UptimeRobot, every 5 min) at the URL.

---

## 4. Verify
- Visit the URL → you should hit the **access-code gate** (proves `APP_PASSWORD` works).
- Enter the code → only the **Recruiter Chat** appears (no Setup page → `APP_MODE=production` works).
- Ask a question (e.g. "How strong is the candidate in Python?") → grounded answer.

---

## Switching back to the 100%-local stack (for the portfolio story / free eval)
Nothing was removed — flip the providers:
```bash
export LLM_PROVIDER=ollama EMBED_PROVIDER=nomic RERANK_PROVIDER=qwen3
```
Rebuild the index (nomic ≠ voyage dimensions) and run as before. The eval
harness (`evaluation/`) keeps its local Ollama judges and stays free.
