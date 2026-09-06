# Deploying the Recruiter Chat (always-on, all-API)

The app runs in two distinct modes:

| Mode | What runs | Where |
|---|---|---|
| **Build** | ingest docs → embed → estimate skills → produce `chroma_db/` + `store/data/candidate.json` | **your laptop** (`requirements-dev.txt`) |
| **Serve** | recruiter chat only: retrieval (Voyage) + LLM (OpenRouter) | **hosted, always on** (`requirements.txt`) |

The heavy models (DeBERTa skill scorer, document parsing/OCR, optional local
LLM/embeddings/reranker) are **build-time only** and never deploy. The serve path
imports no torch — verified.

---

## 0. Get API keys

- **OpenRouter** → https://openrouter.ai/keys (load a few $; serves Haiku 4.5 *and*
  Gemini Flash Lite through one key, which is what lets the three model roles differ)
- **Voyage AI** → https://dashboard.voyageai.com (embeddings + rerank; needs a
  payment method on file or you are capped at 3 requests/min)

Put them in `.env` at the repo root — copy `.env.example` and fill it in. That
single file is the only local secrets store; `settings.py` loads it automatically.

---

## 1. Build the profile locally (one-time, and whenever you update your CV)

```bash
pip install -r requirements-dev.txt
```

Set `APP_MODE=setup` in `.env` to expose the Candidate Setup page, then:

```bash
streamlit run main.py
```

On the **Candidate Setup** page: upload your documents, fill the profile, click
**Estimate Skill Proficiency** (runs the local DeBERTa scorer), then **Save Profile**.

This produces:
- `chroma_db/` — the Voyage-embedded vector index (`candidate_001` + `candidate_001_summaries`)
- `store/data/candidate.json` — your facts + precomputed skill evidence

> ⚠️ Keep `EMBED_PROVIDER=voyage` while building. Query and document embeddings
> must come from the same model — building with `nomic` and serving with `voyage`
> returns confident nonsense, not an error. Switching providers means re-ingesting.

### 1b. Build the project knowledge base (one-time)

So recruiters can also ask about *how this app was built* (the `search_project`
tool), ingest the project overview into its own collection with the **same**
embedding provider:

```bash
python build_project_kb.py
```

This populates `project_kb` (+ `project_kb_summaries`). Edit
`store/data/project/project_overview.txt` and re-run to update it — that file
holds no private data, so it stays in the public repo.

**Skipping this step is silent:** the tool still gets selected, returns nothing,
and the agent says it has no information. `publish_deploy.sh` checks for it.

---

## 2. One-time: create the private deploy repo

`origin` is your **public** portfolio repo. `chroma_db/` and
`store/data/candidate.json` hold real PII (CV content, phone, email, salary
expectation) and are gitignored so they can never land there by accident.

So the running app is deployed from a **separate private repo** that gets the same
code *plus* those two artifacts:

```bash
gh repo create candidate-ai-agent-live --private
```

```bash
git remote add deploy https://github.com/<you>/candidate-ai-agent-live.git
```

Then publish:

```bash
bash scripts/publish_deploy.sh
```

The script verifies the artifacts are present **and non-empty**, builds the commit
in a throwaway git worktree (your working tree, branch and index are never
touched), and force-pushes it to `deploy/main` only. It refuses to run if `deploy`
and `origin` resolve to the same repo.

It also **strips the build-only trees** from the deploy commit — `evaluation/`
(including the archived report snapshots), `skill_proficiency_estimator/`,
`tests/` and `logs/`. That is ~47 MB Streamlit Cloud would otherwise clone and
build but never execute, and it keeps the eval fixtures' synthetic candidates off
the production host. Those directories stay in the public repo untouched; adjust
the `EXCLUDE` list at the top of the script if you want a different split.

> The deploy commit is built from **`HEAD`**, so commit your code changes first —
> uncommitted edits are not published.

---

## 3. Deploy the serve path — Streamlit Community Cloud

1. https://share.streamlit.io → **New app**
2. Repository: **`<you>/candidate-ai-agent-live`** (the private one), branch `main`,
   main file `main.py`
3. **Advanced settings → Python version**: 3.11 or newer
4. **Advanced settings → Secrets**: paste in TOML form —

   ```toml
   OPENROUTER_API_KEY = "sk-or-..."
   VOYAGE_API_KEY = "pa-..."
   APP_PASSWORD = "choose-a-shared-code"
   ADMIN_PASSWORD = "a-different-secret"
   APP_MODE = "production"
   LLM_PROVIDER = "openrouter"
   EMBED_PROVIDER = "voyage"
   RERANK_PROVIDER = "voyage"
   ```

   `APP_MODE = "production"` is what hides the Candidate Setup page. Without it a
   recruiter can edit your profile and trigger ingestion.

5. Deploy. The platform installs `requirements.txt` (lean, no torch) and serves
   over HTTPS. Share the URL + access code with recruiters.

The app sleeps after long idle and wakes in seconds. To keep it warm, point a free
uptime pinger (UptimeRobot, every 5 min) at the URL.

### Hugging Face Spaces (alternative)

Create a **private Streamlit Space**, push the same deploy branch, and set the
same keys under **Settings → Variables and secrets**.

---

## 4. Verify

- Visit the URL → you hit the **access-code gate** (proves `APP_PASSWORD` works).
- Enter the code → **only** the Recruiter Chat appears, no Setup page in the
  sidebar (proves `APP_MODE=production` works).
- Ask a profile question ("How strong is the candidate in Python?") → grounded answer.
- Ask a project question ("How does the retrieval work?") → proves `project_kb` shipped.
- Ask an out-of-scope question ("Is the candidate married?") → polite refusal.

---

## 4b. Monitoring what it costs and what recruiters ask

Every turn is logged with its cost, latency, selected tools, retrieval route, and
the full question and answer.

**The durable sink is stdout.** Streamlit Cloud's filesystem is ephemeral, so
`logs/turns.jsonl` is wiped on every redeploy and sleep. Each turn also prints one
`[turn] {...}` JSON line, which survives in the platform's log viewer ("Manage
app" → logs). If you want history that outlives a restart, that is the copy to
collect — an external sink (S3/R2) would be the next step.

**The dashboard** lives at:

```
https://<your-app>.streamlit.app/?admin=<ADMIN_PASSWORD>
```

Total spend, cost per model role and per model, p50/p95 latency, error count, a
searchable table of every conversation, and CSV/JSONL download. It is registered
only when that query parameter matches, and never appears in the sidebar — a
recruiter with the chat access code cannot discover it exists.

Keep `ADMIN_PASSWORD` **different from `APP_PASSWORD`**: the chat code is handed
out to strangers, and this dashboard shows every conversation. Leave
`ADMIN_PASSWORD` unset and the dashboard does not exist at all.

Set `TELEMETRY_ENABLED=0` to turn logging off entirely.

---

## 5. Updating

Whenever you change code, update your CV, or rebuild the index:

```bash
bash scripts/publish_deploy.sh
```

Push code to the public repo as usual (`git push origin main`) — the two remotes
are independent, and the artifacts stay out of the public one either way.

---

## Notes

- **sqlite:** ChromaDB needs sqlite ≥ 3.35. If the host's Python links an older
  system sqlite, `settings._ensure_modern_sqlite()` transparently swaps in the
  `pysqlite3-binary` wheel (Linux-only, in `requirements.txt`). It is a no-op on a
  modern runtime.
- **Eval fixtures ship too.** `chroma_db/` also contains the `eval_*` collections
  from the evaluation harness. Nothing queries them and they are synthetic, but
  they add bulk; `publish_deploy.sh` warns about them.

---

## Switching back to the 100%-local stack (portfolio story / free eval)

Nothing was removed — flip the providers in `.env`:

```bash
LLM_PROVIDER=ollama
EMBED_PROVIDER=nomic
RERANK_PROVIDER=qwen3
```

Rebuild the index (nomic ≠ voyage dimensions) and run as before. The eval harness
(`evaluation/`) keeps its local Ollama judges regardless of `LLM_PROVIDER` and
stays free.
