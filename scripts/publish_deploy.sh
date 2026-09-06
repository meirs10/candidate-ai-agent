#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Publish the serve path to the PRIVATE deploy repo that Streamlit Cloud builds.
#
# Why this exists: `origin` is a PUBLIC portfolio repo, but the running app needs
# two artifacts that hold real PII — chroma_db/ (your embedded CV) and
# store/data/candidate.json (phone, email, salary expectation). Both are
# gitignored so they can never be pushed to origin by accident. This script
# force-adds them onto a commit that goes ONLY to the private `deploy` remote.
#
# It builds that commit in a throwaway git worktree, so your working tree, your
# current branch, and your index are never touched — and nothing is left behind
# if it fails halfway.
#
# One-time setup:
#   gh repo create candidate-ai-agent-live --private
#   git remote add deploy https://github.com/<you>/candidate-ai-agent-live.git
#
# Usage:  bash scripts/publish_deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REMOTE=deploy
BRANCH=main            # branch Streamlit Cloud is pointed at, in the PRIVATE repo
ARTIFACTS=(chroma_db store/data/candidate.json)

# Trees the SERVE path never touches, stripped from the deploy commit. Without
# this, Streamlit Cloud clones and builds ~47 MB it will never execute: the
# trained scorer's weights (27 MB) and the whole evaluation suite including its
# archived report snapshots (20 MB). Those stay in the public repo — they are the
# evidence of the work — they just have no business on the production host, which
# also keeps the eval fixtures' synthetic candidates off it.
#
# Safe because the only serve-path reference into them is
# store/skill_proficiency.py -> skill_proficiency_estimator/scoring_model, and
# that module is imported lazily by the Candidate Setup page, which is never
# registered when APP_MODE=production.
EXCLUDE=(evaluation skill_proficiency_estimator tests logs)

cd "$(git rev-parse --show-toplevel)"

die() { echo "  [FAIL] $*" >&2; exit 1; }
ok()  { echo "  [OK]   $*"; }

# Resolve the venv interpreter explicitly. A bare `python` here picks up the
# system one, which has no chromadb — the check below would then "fail" for a
# reason that has nothing to do with the artifacts.
for c in .venv/Scripts/python.exe .venv/bin/python; do
  [ -x "$c" ] && PY="$c" && break
done
PY="${PY:-python}"

echo "=== 1. Remote safety check ==="
git remote get-url "$REMOTE" >/dev/null 2>&1 \
  || die "no '$REMOTE' remote. Create the private repo, then:
         git remote add $REMOTE https://github.com/<you>/candidate-ai-agent-live.git"
DEPLOY_URL=$(git remote get-url "$REMOTE")
ORIGIN_URL=$(git remote get-url origin 2>/dev/null || echo "")

# The whole point of this script is that PII never reaches the public repo. If
# the two remotes resolve to the same place, that guarantee is gone.
[ "$DEPLOY_URL" != "$ORIGIN_URL" ] \
  || die "'$REMOTE' and 'origin' are the same repo ($DEPLOY_URL) — refusing to push PII there."
ok "deploy -> $DEPLOY_URL"

echo
echo "=== 2. Artifacts present ==="
for f in "${ARTIFACTS[@]}"; do
  [ -e "$f" ] || die "$f missing — run the Candidate Setup page first (APP_MODE=setup)."
  ok "$f"
done

echo
echo "=== 3. Artifacts actually usable ==="
# A present-but-empty index is the failure that looks like success: the app
# deploys fine and then answers every question with "I don't have that
# information". Check the collections the serve path really reads.
"$PY" - <<'PY' || die "artifact check failed (see above)"
import json
import sys

import chromadb

import agent.tools as tools  # CANDIDATE_ID / PROJECT_ID are the source of truth

counts = {c.name: c.count() for c in
          chromadb.PersistentClient(path="chroma_db").list_collections()}

problems = []
for cid in (tools.CANDIDATE_ID, tools.PROJECT_ID):
    n = counts.get(cid)
    if n is None:
        problems.append(f"collection '{cid}' does not exist")
    elif n == 0:
        problems.append(f"collection '{cid}' is empty")
    else:
        print(f"  [OK]   {cid}: {n} chunks")
    s = counts.get(f"{cid}_summaries")
    if not s:
        # Only BROAD-routed questions read the summary index, so this degrades
        # rather than breaks — worth a warning, not a hard stop.
        print(f"  [WARN] {cid}_summaries is empty - broad questions will fall back")

profile = json.load(open("store/data/candidate.json", encoding="utf-8"))
missing = [k for k in ("full_name", "current_role", "skills") if not profile.get(k)]
if missing:
    problems.append("candidate.json is missing: " + ", ".join(missing))
else:
    print(f"  [OK]   candidate.json: {profile['full_name']}, "
          f"{len(profile.get('skills') or [])} skills")

# Eval fixtures share the index. They are harmless (nothing queries them) but
# they are other people's data and they bloat the deploy, so say so.
strays = sorted(n for n in counts if n.startswith("eval_"))
if strays:
    print(f"  [WARN] {len(strays)} eval fixture collections will ship too "
          f"(harmless, but ~unused): {', '.join(strays[:3])}...")

if problems:
    print("\n".join(f"  [FAIL] {p}" for p in problems), file=sys.stderr)
    sys.exit(1)
PY

echo
echo "=== 4. Building deploy commit in a throwaway worktree ==="
WT=$(mktemp -d)
# Always clean up the worktree registration, even on failure — a stale entry
# makes every later run fail with "already exists".
cleanup() { git worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$WT"; }
trap cleanup EXIT

git worktree add --detach --quiet "$WT" HEAD
for f in "${ARTIFACTS[@]}"; do
  mkdir -p "$WT/$(dirname "$f")"
  cp -r "$f" "$WT/$(dirname "$f")/"
done

# Strip the build-only trees from the deploy commit (see EXCLUDE above).
for d in "${EXCLUDE[@]}"; do
  if [ -e "$WT/$d" ]; then
    sz=$(du -sh "$WT/$d" 2>/dev/null | cut -f1)
    git -C "$WT" rm -r -q --cached "$d" >/dev/null 2>&1 || true
    rm -rf "$WT/$d"
    ok "excluded $d/ (${sz:-?})"
  fi
done

git -C "$WT" add -f "${ARTIFACTS[@]}"
git -C "$WT" commit --quiet -a -m "deploy: profile artifacts from $(git rev-parse --short HEAD)"
ok "commit $(git -C "$WT" rev-parse --short HEAD) ($(git -C "$WT" rev-parse --short HEAD~1) + artifacts - build-only trees)"
ok "deploy tree: $(git -C "$WT" ls-tree -r --name-only HEAD | wc -l) files"

echo
echo "=== 5. Push ==="
# --force because each publish is a fresh snapshot, not an increment: the deploy
# branch is a build output, and its history has no value worth preserving.
git -C "$WT" push --force --quiet "$DEPLOY_URL" "HEAD:refs/heads/$BRANCH"
ok "pushed to $REMOTE/$BRANCH"

echo
echo "Done. Streamlit Cloud redeploys automatically on push (~1-2 min)."
