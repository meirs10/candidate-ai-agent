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
apt-get update -qq >/dev/null 2>&1
if command -v tesseract >/dev/null 2>&1; then
  ok "tesseract present: $(tesseract --version 2>&1 | head -1)"
else
  echo "  installing tesseract-ocr (candidate_5 is all-PNG; ingestion dies without it)..."
  apt-get install -y -qq tesseract-ocr >/dev/null 2>&1 \
    && ok "tesseract installed" || fail "tesseract install FAILED — candidate_5 will crash"
fi
# ollama's installer unpacks a zstd archive; without it the install aborts.
command -v zstd >/dev/null 2>&1 || apt-get install -y -qq zstd >/dev/null 2>&1

echo
echo "=== 1b. Python interpreter the venv was built against ==="
# The venv on the volume is pinned to the exact python MINOR version that built
# it (its bin/python is a symlink to /usr/bin/pythonX.Y, and site-packages holds
# version-specific .so files). Pod images vary — one shipping only 3.10/3.11
# leaves the venv with a dangling symlink: `ls` shows bin/python, but running it
# gives "No such file or directory". Reinstalling the interpreter revives the
# whole venv; rebuilding it from scratch would mean re-downloading ~19GB.
VENV_PY_VER=$(sed -n 's/^version *= *\([0-9]*\.[0-9]*\).*/\1/p' "$VENV/pyvenv.cfg" 2>/dev/null)
if [ -n "$VENV_PY_VER" ] && ! "$PY" --version >/dev/null 2>&1; then
  warn "venv python$VENV_PY_VER is missing on this image — installing it"
  apt-get install -y -qq "python$VENV_PY_VER" "python$VENV_PY_VER-venv" >/dev/null 2>&1
fi
"$PY" --version >/dev/null 2>&1 \
  && ok "venv python works: $("$PY" --version 2>&1)" \
  || fail "venv python$VENV_PY_VER unusable — install it, or rebuild the venv"

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
# OLLAMA_MODELS must point at the dir CONTAINING manifests/ and blobs/. Pointing
# one level too high makes `ollama list` come back empty and silently re-download
# 5.2GB, so derive it from where the manifests actually are.
OLLAMA_MODELS=$(dirname "$(dirname "$(find /workspace -type d -name manifests -path '*ollama*' 2>/dev/null | head -1)")" 2>/dev/null)
[ -d "${OLLAMA_MODELS:-}/manifests" ] || OLLAMA_MODELS=/workspace/.ollama/models
export OLLAMA_MODELS
ok "OLLAMA_MODELS=$OLLAMA_MODELS"

if ! command -v ollama >/dev/null 2>&1; then
  echo "  installing ollama..."
  curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1 \
    && ok "ollama installed" || fail "ollama install FAILED"
fi
if ! curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "  starting ollama server..."
  nohup env OLLAMA_MODELS="$OLLAMA_MODELS" ollama serve > /workspace/ollama.log 2>&1 &
  for i in $(seq 1 40); do
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
echo "=== 6. Step-5 inputs (generation ran on another machine) ==="
# Five components need only pipeline_results.json. `ingestion` and
# `retrieval_gates` additionally read the LIVE ChromaDB collections, which live
# wherever GENERATION ran — so chroma_db must be shipped over with the results
# or those two silently come back empty.
RES="$REPO/evaluation/reports/pipeline_results.json"
if [ -f "$RES" ]; then
  "$PY" - "$RES" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"  [OK]   pipeline_results.json: {len(d)} questions, "
      f"{len({r.get('candidate_name') for r in d})} collections")
n = sum(1 for r in d if r.get("fused_pool"))
print(f"  {'[OK]  ' if n else '[WARN]'} fused_pool on {n} rows (retrieval_gates needs it)")
PY
else
  fail "pipeline_results.json MISSING — scp step 4's output over"
fi
if [ -d "$REPO/chroma_db" ]; then
  "$PY" -c "
import chromadb
c = chromadb.PersistentClient(path='$REPO/chroma_db').list_collections()
print(f'  [OK]   chroma_db: {len(c)} collections')" 2>/dev/null \
    || fail "chroma_db present but unreadable"
else
  fail "chroma_db/ MISSING — 'ingestion' + 'retrieval_gates' will produce nothing"
  echo "         ship it:  bash scripts/package_for_pod.sh   (on the generating machine)"
fi

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
echo "Setup checks complete. Resolve any [FAIL] above before scoring."
echo "Then, to score the answers generated on the other machine:"
echo "  $PY -m scripts.step5_score"
echo
echo "Results land in $REPO/evaluation/reports/ — tar them back afterwards:"
echo "  cd $REPO/evaluation/reports && tar -czf /workspace/step5_results.tar.gz *.csv *.html *.json"
