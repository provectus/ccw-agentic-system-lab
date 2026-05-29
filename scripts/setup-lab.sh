#!/usr/bin/env bash
# Set up the lab against ccw-inventory-management.
#
# Sequence (each step is announced before it executes):
#   1. Verify prereqs.
#   2. Fork provectus/ccw-inventory-management → participant's account (idempotent).
#   3. Clone the fork into ./workspace/ccw-inventory-management.
#   4. Create branch lab/agent-target from main.
#   5. Apply fixtures/prs/01-supplier-feature/patch.diff.
#   6. Commit and push.
#   7. Open a draft PR on the fork.
#   8. Open one canned issue from fixtures/issues/.
#   9. Write both URLs to .lab-state.json.
#
# --dry-run prints each command without executing.

set -euo pipefail

DRY_RUN=0
ISSUE_FIXTURE="${ISSUE_FIXTURE:-fixtures/issues/01-stock-calc-off-by-one.md}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ; shift ;;
    --issue) ISSUE_FIXTURE="$2" ; shift 2 ;;
    -h|--help)
      sed -n '1,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2 ; exit 2 ;;
  esac
done

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="$LAB_ROOT/workspace"
TARGET="$WORKSPACE/ccw-inventory-management"
UPSTREAM="provectus/ccw-inventory-management"
BRANCH="lab/agent-target"
PATCH="$LAB_ROOT/fixtures/prs/01-supplier-feature/patch.diff"
STATE="$LAB_ROOT/.lab-state.json"

# announce :: prints the next command in cyan; runs it unless DRY_RUN.
announce() {
  printf "\033[36m$\033[0m %s\n" "$*"
  if [[ $DRY_RUN -eq 0 ]]; then
    eval "$@"
  fi
}

# announce_block :: same, for multi-line shell blocks where eval is fragile.
heading() {
  printf "\n\033[1m▸ %s\033[0m\n" "$*"
}

# 1. Verify prereqs
heading "Step 1: verify prereqs"
if ! bash "$LAB_ROOT/scripts/verify-env.sh"; then
  echo "verify-env.sh failed; fix the above before continuing." >&2
  exit 1
fi

# Resolve participant's GitHub login.
GH_USER=$(gh api user --jq .login)
FORK="$GH_USER/ccw-inventory-management"

# 2. Fork (idempotent)
heading "Step 2: fork $UPSTREAM (skip if it exists)"
if gh repo view "$FORK" >/dev/null 2>&1; then
  echo "  fork $FORK already exists, skipping."
else
  announce gh repo fork "$UPSTREAM" --clone=false
fi

# GitHub disables issues on forks by default. The triage step needs to open a
# canned issue, so enable issues on the fork now (idempotent).
heading "Step 2b: enable issues on fork (needed for triage mode)"
issues_enabled=$(gh repo view "$FORK" --json hasIssuesEnabled --jq .hasIssuesEnabled 2>/dev/null || echo "false")
if [[ "$issues_enabled" == "true" ]]; then
  echo "  issues already enabled on $FORK."
else
  announce gh repo edit "$FORK" --enable-issues
fi

# 3. Clone fork
heading "Step 3: clone fork into $TARGET"
if [[ -d "$TARGET/.git" ]]; then
  echo "  $TARGET already cloned, skipping clone."
else
  announce mkdir -p "$WORKSPACE"
  announce gh repo clone "$FORK" "$TARGET"
fi

# 4. Create branch
heading "Step 4: create branch $BRANCH from main"
# Reset the workspace clone to a clean state in case a previous run died with
# the working tree dirty (e.g. mid-patch-apply). The workspace is owned by this
# script — no user work to preserve.
announce "git -C '$TARGET' reset --hard HEAD"
announce "git -C '$TARGET' clean -fd"
announce "git -C '$TARGET' fetch origin main"
announce "git -C '$TARGET' checkout main"
announce "git -C '$TARGET' pull --ff-only origin main"
announce "git -C '$TARGET' checkout -B '$BRANCH' main"

# 5. Apply patch
heading "Step 5: apply planted patch"
if [[ ! -f "$PATCH" ]]; then
  echo "Patch file missing: $PATCH" >&2
  exit 1
fi
announce "git -C '$TARGET' apply --whitespace=fix '$PATCH'"

# 6. Commit + push
heading "Step 6: commit and push $BRANCH"
announce "git -C '$TARGET' add -A"
announce "git -C '$TARGET' commit -m 'feat: add supplier management (planted PR for lab)'"
# Fetch the remote branch (if it exists) so --force-with-lease has a reference
# point. The lab branch is owned by this script; force-with-lease protects
# against the unlikely case of a concurrent push without the risk of plain --force.
announce "git -C '$TARGET' fetch origin '$BRANCH' 2>/dev/null || true"
announce "git -C '$TARGET' push --force-with-lease -u origin '$BRANCH'"

# 7. Open draft PR
heading "Step 7: open draft PR"
PR_TITLE="feat: add supplier management"
PR_BODY="Adds a basic Supplier model, GET/POST /api/suppliers endpoints, and a Suppliers.vue page.

This is the lab's planted PR for the CCW Agentic System workshop. See agent/prompts/reviewer.md for what your Reviewer should look for."

PR_URL=""
if [[ $DRY_RUN -eq 0 ]]; then
  # Reuse an existing PR for this branch if one is already open (idempotent re-run).
  existing_pr=$(gh pr list --repo "$FORK" --head "$BRANCH" --state open --json url --jq '.[0].url' 2>/dev/null || echo "")
  if [[ -n "$existing_pr" && "$existing_pr" != "null" ]]; then
    PR_URL="$existing_pr"
    echo "  PR already exists for $BRANCH: $PR_URL"
  else
    PR_URL=$(gh pr create \
      --repo "$FORK" \
      --head "$BRANCH" --base main --draft \
      --title "$PR_TITLE" \
      --body "$PR_BODY")
    echo "  PR opened: $PR_URL"
  fi
else
  printf "\033[36m$\033[0m gh pr create --repo %s --head %s --base main --draft --title %s --body ...\n" "$FORK" "$BRANCH" "$PR_TITLE"
fi

# 8. Open canned issue
heading "Step 8: open canned issue ($ISSUE_FIXTURE)"
if [[ ! -f "$LAB_ROOT/$ISSUE_FIXTURE" ]]; then
  echo "Issue fixture missing: $LAB_ROOT/$ISSUE_FIXTURE" >&2
  exit 1
fi
ISSUE_TITLE=$(awk -F'"' '/^title:/{print $2; exit}' "$LAB_ROOT/$ISSUE_FIXTURE")
ISSUE_BODY=$(awk '/^---$/{c++; next} c==2{print}' "$LAB_ROOT/$ISSUE_FIXTURE")

ISSUE_URL=""
if [[ $DRY_RUN -eq 0 ]]; then
  # Reuse an existing open issue with the same title (idempotent re-run).
  # Using jq --arg avoids shell-escape pitfalls with backticks/quotes in titles.
  existing_issue=$(gh issue list --repo "$FORK" --state open --json url,title \
    | jq -r --arg t "$ISSUE_TITLE" '.[] | select(.title == $t) | .url' | head -n 1)
  if [[ -n "$existing_issue" ]]; then
    ISSUE_URL="$existing_issue"
    echo "  Issue already open: $ISSUE_URL"
  else
    ISSUE_URL=$(gh issue create \
      --repo "$FORK" \
      --title "$ISSUE_TITLE" \
      --body "$ISSUE_BODY")
    echo "  Issue opened: $ISSUE_URL"
  fi
else
  printf "\033[36m$\033[0m gh issue create --repo %s --title %s --body ...\n" "$FORK" "$ISSUE_TITLE"
fi

# 9. Write state file
heading "Step 9: write .lab-state.json"
if [[ $DRY_RUN -eq 0 ]]; then
  cat > "$STATE" <<EOF
{
  "fork": "$FORK",
  "branch": "$BRANCH",
  "pr_url": "$PR_URL",
  "issue_url": "$ISSUE_URL",
  "patched_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
  echo "  wrote $STATE"
else
  echo "  (dry-run) would write $STATE"
fi

heading "Done"
echo "  Try:  python -m agent review --dry-run"
echo "  Then: python -m agent triage --dry-run"
