"""GitHub interactions via the `gh` CLI.

No PyGithub, no GitHub MCP server. All commands shell out to `gh`, which is
the prereq the workshop's setup-lab.sh has already verified.

Side-effecting functions accept dry_run=True (the default) and return a
structured preview string instead of touching GitHub.
"""

from __future__ import annotations

import re

from agent.tools._shell import dry_run_preview, run


_PR_URL_RE = re.compile(r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<num>\d+)")
_ISSUE_URL_RE = re.compile(r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<num>\d+)")


def _parse_pr_url(url: str) -> tuple[str, str, str]:
    m = _PR_URL_RE.search(url)
    if not m:
        raise ValueError(f"Not a recognizable GitHub PR URL: {url!r}")
    return m["owner"], m["repo"], m["num"]


def _parse_issue_url(url: str) -> tuple[str, str, str]:
    m = _ISSUE_URL_RE.search(url)
    if not m:
        raise ValueError(f"Not a recognizable GitHub issue URL: {url!r}")
    return m["owner"], m["repo"], m["num"]


# ---------------------------------------------------------------------------
# Read-only operations (always safe)
# ---------------------------------------------------------------------------

def gh_pr_diff(pr_url: str) -> str:
    """Return the unified diff for a PR."""
    owner, repo, num = _parse_pr_url(pr_url)
    result = run(["gh", "pr", "diff", num, "--repo", f"{owner}/{repo}"])
    if not result.ok:
        return f"gh pr diff failed:\n{result.render()}"
    return result.stdout


def gh_pr_files(pr_url: str) -> str:
    """List files changed in a PR with status and additions/deletions."""
    owner, repo, num = _parse_pr_url(pr_url)
    result = run([
        "gh", "pr", "view", num, "--repo", f"{owner}/{repo}",
        "--json", "files",
        "--jq", ".files[] | \"\\(.path)\\t+\\(.additions) -\\(.deletions)\"",
    ])
    if not result.ok:
        return f"gh pr files failed:\n{result.render()}"
    return result.stdout


def gh_issue_read(issue_url: str) -> str:
    """Return the full body of an issue plus title and labels."""
    owner, repo, num = _parse_issue_url(issue_url)
    result = run([
        "gh", "issue", "view", num, "--repo", f"{owner}/{repo}",
        "--json", "title,body,labels,state",
        "--template",
        "{{.title}}\n{{range .labels}}[{{.name}}] {{end}}\nState: {{.state}}\n\n{{.body}}",
    ])
    if not result.ok:
        return f"gh issue view failed:\n{result.render()}"
    return result.stdout


# ---------------------------------------------------------------------------
# Side-effecting operations (honor dry_run)
# ---------------------------------------------------------------------------

def gh_pr_comment(pr_url: str, path: str, line: int, body: str, dry_run: bool = True) -> str:
    """Post an inline comment on a PR. `gh` supports this via the API endpoint."""
    owner, repo, num = _parse_pr_url(pr_url)
    if dry_run:
        return dry_run_preview(
            "post inline PR comment",
            pr=pr_url, path=path, line=line, body=body,
        )
    # gh has no first-class inline-comment command; use the REST API.
    # commit_id is required for inline comments — fetch the PR head SHA.
    head_sha_res = run([
        "gh", "pr", "view", num, "--repo", f"{owner}/{repo}",
        "--json", "headRefOid", "--jq", ".headRefOid",
    ])
    if not head_sha_res.ok:
        return f"failed to look up PR head SHA:\n{head_sha_res.render()}"
    head_sha = head_sha_res.stdout.strip()

    result = run([
        "gh", "api",
        f"repos/{owner}/{repo}/pulls/{num}/comments",
        "-f", f"body={body}",
        "-f", f"commit_id={head_sha}",
        "-f", f"path={path}",
        "-F", f"line={line}",
        "-f", "side=RIGHT",
    ])
    return f"gh_pr_comment({path}:{line}):\n{result.render()}"


def gh_review_submit(pr_url: str, event: str, body: str, dry_run: bool = True) -> str:
    """Submit a top-level review. event in {COMMENT, APPROVE, REQUEST_CHANGES}."""
    if event not in {"COMMENT", "APPROVE", "REQUEST_CHANGES"}:
        raise ValueError(f"event must be COMMENT|APPROVE|REQUEST_CHANGES, got {event!r}")
    owner, repo, num = _parse_pr_url(pr_url)
    if dry_run:
        return dry_run_preview(
            "submit PR review",
            pr=pr_url, event=event, body=body,
        )
    flag = {"COMMENT": "--comment", "APPROVE": "--approve", "REQUEST_CHANGES": "--request-changes"}[event]
    result = run([
        "gh", "pr", "review", num, "--repo", f"{owner}/{repo}",
        flag, "--body", body,
    ])
    return f"gh_review_submit({event}):\n{result.render()}"


def gh_pr_create(
    repo: str,
    head: str,
    base: str = "main",
    *,
    title: str,
    body: str,
    draft: bool = True,
    dry_run: bool = True,
) -> str:
    """Open a PR. `repo` is owner/name. `head` is branch name (or owner:branch for cross-fork)."""
    if dry_run:
        return dry_run_preview(
            "open PR",
            repo=repo, head=head, base=base, title=title, body=body, draft=draft,
        )
    cmd = [
        "gh", "pr", "create", "--repo", repo,
        "--head", head, "--base", base,
        "--title", title, "--body", body,
    ]
    if draft:
        cmd.append("--draft")
    result = run(cmd)
    return f"gh_pr_create:\n{result.render()}"


__all__ = [
    "gh_pr_diff",
    "gh_pr_files",
    "gh_pr_comment",
    "gh_review_submit",
    "gh_issue_read",
    "gh_pr_create",
]
