#!/usr/bin/env bash
# offload_job.sh <job> ["<args>"]
# Runs jobs/<job>.py on a GitHub Actions runner, waits, and downloads the out/ artifact.
# Config (env): OFFLOAD_REPO=<owner>/<repo> (required), OFFLOAD_WORKFLOW (default run-job.yml),
#               OFFLOAD_RESULTS_DIR (default ./results). Uses your existing `gh` login; never prints tokens.
set -euo pipefail
REPO="${OFFLOAD_REPO:?set OFFLOAD_REPO=<owner>/<repo>}"
WF="${OFFLOAD_WORKFLOW:-run-job.yml}"
RESULTS="${OFFLOAD_RESULTS_DIR:-./results}"
JOB="${1:?usage: offload_job.sh <job> \"<args>\"}"; ARGS="${2:-}"
[[ "$JOB" =~ ^[a-z0-9_-]+$ ]] || { echo "invalid job name (allowed: a-z0-9_-)" >&2; exit 2; }
JOB_ID="${JOB}-$(date +%Y%m%d-%H%M%S)-$RANDOM"
gh workflow run "$WF" -R "$REPO" -f job="$JOB" -f args="$ARGS" -f job_id="$JOB_ID" >/dev/null
echo "dispatched job=$JOB job_id=$JOB_ID"
RUN_ID=""
for _ in $(seq 1 30); do
  sleep 4
  RUN_ID=$(gh run list -R "$REPO" -w "$WF" -L 20 --json databaseId,displayTitle \
    -q ".[] | select(.displayTitle | contains(\"[$JOB_ID]\")) | .databaseId" | head -1)
  [ -n "$RUN_ID" ] && break
done
[ -n "$RUN_ID" ] || { echo "status=not_found job_id=$JOB_ID" >&2; exit 3; }
echo "run: https://github.com/$REPO/actions/runs/$RUN_ID"
gh run watch "$RUN_ID" -R "$REPO" --interval 15 >/dev/null 2>&1 || true
CONC=$(gh run view "$RUN_ID" -R "$REPO" --json conclusion -q .conclusion)
DEST="$RESULTS/$JOB_ID"; mkdir -p "$DEST"
if gh run download "$RUN_ID" -R "$REPO" -n "result-$JOB_ID" -D "$DEST" >/dev/null 2>&1; then DL=ok; else DL=failed; fi
echo "status=$CONC artifact_download=$DL path=$DEST"
if [ -f "$DEST/_run_meta.json" ]; then cat "$DEST/_run_meta.json"; echo; fi
[ "$CONC" = success ] && [ "$DL" = ok ]
