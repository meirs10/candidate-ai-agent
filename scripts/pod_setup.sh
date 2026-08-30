#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# RunPod setup for an eval run with REMOTE generation + LOCAL (pod) judges.
#
#   generation : OpenRouter (Haiku 4.5) + Voyage embed/rerank   <- needs .env keys
#   judging    : ollama qwen3 + local nomic embeddings (GPU)    <- needs ollama
#
# The /workspace network volume persists the venv, model weights, and repo.
# The pod's ROOT filesystem does NOT — so apt packages and the ollama binary
# must be reinstalled on every fresh pod. That is what bit run #2 (tesseract).
#
# Usage:  bash scripts/pod_setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

REPO=/workspace/candidate_ai_agent
VENV=/workspace/venv
PY="$VENV/bin/python"

ok()   { echo "  [OK]   $*"; }
warn() { echo "  [WARN] $*"; }
fail() { echo "  [FAIL] $*"; }

echo "=== 1. Ephemeral system packages (gone on every fresh pod) ==="
if command -v tesseract >/dev/null 2>&1; then
  ok "tesseract present: $(tesseract --version 2>&1 | head -1)"
else
  echo "  installing tesseract-ocr (candidate_5 is all-PNG; ingestion dies without it)..."
  apt-get update -qq && apt-get install -y -qq tesseract-ocr >/dev/null 2>&1 \
    && ok "tesseract installed" || fail "tesseract install FAILED — candidate_5 will crash"
fi

echo
echo "=== 2. Python deps (venv is on the volume, but these are new) ==="
# python-dotenv is a HARD blocker: settings.py imports it at module top, so
# without it every single module in the project fails to import.
for pkg in python-dotenv voyageai; do
  mod=$(echo "$pkg" | tr '-' '_'); [ "$pkg" = "python-dotenv" ] && mod=dotenv
  if "$PY" -c "import $mod" >/dev/null 2>&1; then
    ok "$pkg already installed"
  else
    "$PY" -m pip install -q "$pkg" && ok "$pkg installed" || fail "$pkg install FAILED"
  fi
done

echo
echo "=== 3. Ollama (judges) — binary is ephemeral, qwen3 weights persist ==="
export OLLAMA_MODELS=/workspace/ollama_models   # keep weights on the volume
if ! command -v ollama >/dev/null 2>&1; then
  echo "  installing ollama..."
  curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1 \
    && ok "ollama installed" || fail "ollama install FAILED"
fi
if ! curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "  starting ollama server..."
  nohup ollama serve > /workspace/ollama.log 2>&1 &
  for i in $(seq 1 30); do
    curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1 && break; sleep 1
  done
fi
if curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  ok "ollama serving"
  ollama list 2>/dev/null | grep -qi qwen3 && ok "qwen3 present" \
    || warn "qwen3 NOT found — run: OLLAMA_MODELS=$OLLAMA_MODELS ollama pull qwen3"
else
  fail "ollama not responding — judges (GEval/RAGAS/ingestion) will fail"
fi

echo
echo "=== 4. Provider env vars — stale exports silently win over settings.py ==="
# settings.py resolves env var FIRST, so a leftover LLM_PROVIDER=ollama from the
# old local-stack runs would silently run the WRONG stack and look successful.
for v in LLM_PROVIDER EMBED_PROVIDER RERANK_PROVIDER AGENT_MODEL ROUTER_MODEL; do
  if [ -n "${!v:-}" ]; then
    warn "$v is exported as '${!v}' — unset it so .env/defaults apply"
  fi
done
grep -qsE '^\s*export\s+(LLM|EMBED|RERANK)_PROVIDER' /workspace/env.sh 2>/dev/null \
  && warn "/workspace/env.sh still exports provider vars — edit or stop sourcing it" \
  || ok "no provider exports in /workspace/env.sh"

echo
echo "=== 5. Secrets (.env is gitignored — must be copied to the pod manually) ==="
if [ -f "$REPO/.env" ]; then
  for k in OPENROUTER_API_KEY VOYAGE_API_KEY; do
    grep -qE "^$k=.+" "$REPO/.env" && ! grep -qE "^$k=(your-|sk-or-\.\.\.|pa-\.\.\.)" "$REPO/.env" \
      && ok "$k set" || fail "$k missing or still a placeholder in .env"
  done
else
  fail "$REPO/.env NOT FOUND — scp it over (git will never bring it)"
fi

echo
echo "=== 6. Stale state from the previous LOCAL-stack run ==="
# Old ChromaDB holds 768-dim nomic vectors; Voyage queries are 1024-dim.
# A non-resume run wipes + re-ingests automatically, so this is belt-and-braces
# — but RESUME=True would skip re-ingestion and blow up on dimension mismatch.
if [ -d "$REPO/chroma_db" ]; then
  warn "chroma_db exists (nomic-era vectors). Safe ONLY if RESUME=False."
  echo "         to be certain:  rm -rf $REPO/chroma_db"
fi
if [ -d "$REPO/evaluation/reports/partial" ]; then
  warn "reports/partial/ has checkpoints from the local-stack run."
  echo "         to be certain:  rm -rf $REPO/evaluation/reports/partial"
fi
grep -qE '^RESUME\s*=\s*False' "$REPO/evaluation/run_eval.py" \
  && ok "RESUME = False in run_eval.py" || fail "RESUME is not False — fix before running"

echo
echo "=== 7. ragas / langchain shim (patched into site-packages on the volume) ==="
"$PY" -c "import ragas" >/dev/null 2>&1 && ok "ragas imports" \
  || fail "ragas import FAILED — reapply the langchain_community ChatVertexAI stub"

echo
echo "=== 8. Config as the code will actually see it ==="
cd "$REPO" && "$PY" - <<'PYEOF'
try:
    import settings as c
    m = lambda v: (v[:6] + "..." + v[-4:]) if v and len(v) > 12 else ("(EMPTY)" if not v else "set")
    print(f"  LLM      : {c.LLM_PROVIDER} / agent={c.AGENT_MODEL} router={c.ROUTER_MODEL}")
    print(f"  EMBED    : {c.EMBED_PROVIDER} / {c.VOYAGE_EMBED_MODEL}")
    print(f"  RERANK   : {c.RERANK_PROVIDER} / {c.VOYAGE_RERANK_MODEL}")
    print(f"  THRESHOLD: {c.TOOL_SELECT_THRESHOLD}  escalate={c.TOOL_ESCALATE_ON_EMPTY}")
    print(f"  OPENROUTER_API_KEY: {m(c.OPENROUTER_API_KEY)}")
    print(f"  VOYAGE_API_KEY    : {m(c.VOYAGE_API_KEY)}")
    bad = [n for n, v in (("LLM", c.LLM_PROVIDER), ("EMBED", c.EMBED_PROVIDER),
                          ("RERANK", c.RERANK_PROVIDER))
           if v not in ("openrouter", "voyage")]
    print("\n  [FAIL] NOT the remote stack: " + ", ".join(bad) if bad
          else "\n  [OK]   remote generation stack confirmed")
except Exception as e:
    print(f"  [FAIL] settings import failed: {type(e).__name__}: {e}")
PYEOF

echo
echo "Setup checks complete. Resolve any [FAIL] above before running the eval."
echo "Then, in order:"
echo "  1) python -m evaluation.collect_tool_scores --workers 6   # threshold probe"
echo "  2) QUESTION_LIMIT=6 / CANDIDATES=[1] in run_eval.py        # smoke subset"
echo "  3) python -m evaluation.run_eval                           # full eval"
