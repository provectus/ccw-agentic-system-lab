#!/usr/bin/env bash
# Verify all prerequisites for the lab. Exits non-zero on the first failure.

set -u

ok=0
fail=0

green() { printf "\033[32m✓\033[0m %s\n" "$*"; ok=$((ok+1)); }
red()   { printf "\033[31m✗\033[0m %s\n" "$*"; fail=$((fail+1)); }

# 1. Python 3.11+
if command -v python3 >/dev/null 2>&1; then
  py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  py_major=$(python3 -c 'import sys; print(sys.version_info.major)')
  py_minor=$(python3 -c 'import sys; print(sys.version_info.minor)')
  if [[ $py_major -ge 3 && $py_minor -ge 11 ]]; then
    green "Python $py_ver"
  else
    red "Python $py_ver (need >= 3.11)"
  fi
else
  red "python3 not on PATH"
fi

# 2. uv
if command -v uv >/dev/null 2>&1; then
  green "uv $(uv --version | awk '{print $2}')"
else
  red "uv not on PATH. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# 3. gh CLI authenticated
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    gh_user=$(gh api user --jq .login 2>/dev/null || echo "unknown")
    green "gh authenticated as $gh_user"
  else
    red "gh present but not authenticated. Run: gh auth login"
  fi
else
  red "gh not on PATH. Install: https://cli.github.com/"
fi

# 3b. jq (used by setup-lab.sh and teardown.sh for JSON parsing)
if command -v jq >/dev/null 2>&1; then
  green "jq $(jq --version | sed 's/^jq-//')"
else
  red "jq not on PATH. Install: brew install jq (macOS) or apt install jq (Linux)"
fi

# 4. ANTHROPIC_API_KEY
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  green "ANTHROPIC_API_KEY is set"
else
  if [[ -f .env ]] && grep -q "^ANTHROPIC_API_KEY=." .env; then
    green "ANTHROPIC_API_KEY in .env"
  else
    red "ANTHROPIC_API_KEY not set (env or .env)"
  fi
fi

# 5. git config user
if git config user.email >/dev/null 2>&1 && git config user.name >/dev/null 2>&1; then
  green "git user: $(git config user.name) <$(git config user.email)>"
else
  red "git user.name / user.email not configured"
fi

echo
echo "  $ok ok, $fail failed"
[[ $fail -eq 0 ]]
