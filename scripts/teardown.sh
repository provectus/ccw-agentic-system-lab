#!/usr/bin/env bash
# Clean up everything setup-lab.sh created:
#   - Close the draft PR
#   - Close the canned issue
#   - Delete the lab/agent-target branch on the fork
#   - Remove ./workspace/ and .lab-state.json
#
# Does NOT delete the fork itself — keep the fork to re-run the lab anytime.

set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="$LAB_ROOT/.lab-state.json"

if [[ ! -f "$STATE" ]]; then
  echo "No .lab-state.json found — nothing to clean up. Did you run setup-lab.sh?"
  exit 0
fi

FORK=$(jq -r .fork "$STATE")
BRANCH=$(jq -r .branch "$STATE")
PR_URL=$(jq -r .pr_url "$STATE")
ISSUE_URL=$(jq -r .issue_url "$STATE")

heading() { printf "\n\033[1m▸ %s\033[0m\n" "$*"; }

heading "Close PR: $PR_URL"
if [[ "$PR_URL" != "null" && -n "$PR_URL" ]]; then
  gh pr close "$PR_URL" --delete-branch || echo "  (could not close PR; skipping)"
fi

heading "Close issue: $ISSUE_URL"
if [[ "$ISSUE_URL" != "null" && -n "$ISSUE_URL" ]]; then
  gh issue close "$ISSUE_URL" || echo "  (could not close issue; skipping)"
fi

heading "Delete remote branch $BRANCH on $FORK (if still present)"
gh api -X DELETE "repos/$FORK/git/refs/heads/$BRANCH" 2>/dev/null \
  || echo "  (branch already deleted or never existed)"

heading "Remove ./workspace and .lab-state.json"
rm -rf "$LAB_ROOT/workspace" "$STATE"

heading "Done"
echo "  Re-run scripts/setup-lab.sh to start fresh."
