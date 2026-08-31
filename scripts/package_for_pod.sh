#!/usr/bin/env bash
# Bundle everything the pod needs to score a local generation run (step 4 -> 5).
#
# chroma_db is included because `ingestion` and `retrieval_gates` read the LIVE
# collections, not pipeline_results.json. Ship it or those two components come
# back empty ("Collection [eval_cand_1] does not exist").
#
#   bash scripts/package_for_pod.sh
#   scp -P <port> -i ~/.ssh/id_ed25519 step4_for_pod.tar.gz .env root@<host>:/workspace/
set -uo pipefail
cd "$(dirname "$0")/.."

OUT=step4_for_pod.tar.gz
RESULTS=evaluation/reports/pipeline_results.json

[ -f "$RESULTS" ] || { echo "[FAIL] $RESULTS not found — run step 4 first"; exit 1; }
[ -d chroma_db ]  || { echo "[FAIL] chroma_db/ not found — run step 4 with reuse_ingestion=False"; exit 1; }

python - <<'PY'
import json, chromadb
d = json.load(open('evaluation/reports/pipeline_results.json', encoding='utf-8'))
print(f"  questions      : {len(d)}")
print(f"  candidates     : {len(sorted({r.get('candidate_name') for r in d}))}")
print(f"  with contexts  : {sum(1 for r in d if r.get('contexts'))}")
print(f"  with fused_pool: {sum(1 for r in d if r.get('fused_pool'))}  (retrieval_gates needs this)")
cols = chromadb.PersistentClient(path='./chroma_db').list_collections()
print(f"  collections    : {len(cols)}")
PY

tar -czf "$OUT" "$RESULTS" chroma_db
echo
echo "wrote $OUT ($(du -h "$OUT" | cut -f1))"
echo
echo "On the pod, after scp-ing it to /workspace/:"
echo "  cd /workspace/candidate_ai_agent && tar -xzf /workspace/$OUT"
echo "  /workspace/venv/bin/python -m scripts.step5_score"
