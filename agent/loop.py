"""Claude Agent SDK setup and shared run() helper.

This module is the focus of workshop step 4 (★ "Anatomy of an Agent SDK Loop").
Participants read it top-to-bottom and answer:
    1. Where is the model picked per role?      → `pick_model()` in config.py
    2. Where are tools registered?               → `build_sdk_server()` below
    3. Where does the message loop run?          → `run_agent()` below

Keep this file small and readable. Real orchestration lives in agent/modes/*.py;
this file only owns the SDK plumbing.
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    create_sdk_mcp_server,
    tool,
)

from agent.config import (
    PROMPTS_DIR,
    Role,
    pick_model,
)
from agent.telemetry import TelemetryLogger
from agent.tools import git as git_tools
from agent.tools import github as github_tools
from agent.tools import repo as repo_tools
from agent.tools import tests as test_tools


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------
#
# Each entry below wraps a function from agent/tools/*.py as an SDK MCP tool.
# The wrapper is intentionally thin — it adapts {arg_name: value} kwargs to the
# wrapped function's signature and shapes the result as MCP `content` blocks.
#
# Participants reading step 4 should walk away knowing: every shell-side-effect
# the agent can take is one of these tools. Nothing escapes the toolset.

def _text(s: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": s}]}


@tool("gh_pr_diff", "Fetch the unified diff for a GitHub PR URL.", {"pr_url": str})
async def t_gh_pr_diff(args: dict) -> dict:
    return _text(github_tools.gh_pr_diff(args["pr_url"]))


@tool("gh_pr_files", "List files changed in a GitHub PR.", {"pr_url": str})
async def t_gh_pr_files(args: dict) -> dict:
    return _text(github_tools.gh_pr_files(args["pr_url"]))


@tool(
    "gh_pr_comment",
    "Post an inline comment on a PR. Honors dry_run.",
    {"pr_url": str, "path": str, "line": int, "body": str, "dry_run": bool},
)
async def t_gh_pr_comment(args: dict) -> dict:
    return _text(github_tools.gh_pr_comment(
        args["pr_url"], args["path"], args["line"], args["body"],
        dry_run=args.get("dry_run", True),
    ))


@tool(
    "gh_review_submit",
    "Submit a top-level PR review (COMMENT / APPROVE / REQUEST_CHANGES). Honors dry_run.",
    {"pr_url": str, "event": str, "body": str, "dry_run": bool},
)
async def t_gh_review_submit(args: dict) -> dict:
    return _text(github_tools.gh_review_submit(
        args["pr_url"], args["event"], args["body"],
        dry_run=args.get("dry_run", True),
    ))


@tool("gh_issue_read", "Fetch the body of a GitHub issue.", {"issue_url": str})
async def t_gh_issue_read(args: dict) -> dict:
    return _text(github_tools.gh_issue_read(args["issue_url"]))


@tool(
    "gh_pr_create",
    "Open a draft PR from a branch. Honors dry_run.",
    {"repo": str, "head": str, "base": str, "title": str, "body": str, "draft": bool, "dry_run": bool},
)
async def t_gh_pr_create(args: dict) -> dict:
    return _text(github_tools.gh_pr_create(
        repo=args["repo"], head=args["head"], base=args.get("base", "main"),
        title=args["title"], body=args["body"],
        draft=args.get("draft", True),
        dry_run=args.get("dry_run", True),
    ))


@tool("git_checkout", "Checkout a branch in the workspace clone.", {"branch": str, "create": bool})
async def t_git_checkout(args: dict) -> dict:
    return _text(git_tools.git_checkout(args["branch"], create=args.get("create", False)))


@tool(
    "git_apply",
    "Apply a unified diff string to the workspace clone.",
    {"diff": str, "dry_run": bool},
)
async def t_git_apply(args: dict) -> dict:
    return _text(git_tools.git_apply(args["diff"], dry_run=args.get("dry_run", True)))


@tool("git_commit", "Commit staged changes with a message. Honors dry_run.", {"message": str, "dry_run": bool})
async def t_git_commit(args: dict) -> dict:
    return _text(git_tools.git_commit(args["message"], dry_run=args.get("dry_run", True)))


@tool("git_push", "Push the current branch to origin. Honors dry_run.", {"dry_run": bool})
async def t_git_push(args: dict) -> dict:
    return _text(git_tools.git_push(dry_run=args.get("dry_run", True)))


@tool("read_file", "Read a file from the workspace clone (sandboxed).", {"path": str})
async def t_read_file(args: dict) -> dict:
    return _text(repo_tools.read_file(args["path"]))


@tool("grep", "Grep across the workspace clone.", {"pattern": str, "path": str})
async def t_grep(args: dict) -> dict:
    return _text(repo_tools.grep(args["pattern"], args.get("path", ".")))


@tool("glob", "Glob the workspace clone for files matching a pattern.", {"pattern": str})
async def t_glob(args: dict) -> dict:
    return _text(repo_tools.glob_files(args["pattern"]))


@tool("run_pytest", "Run pytest against the workspace clone. Returns stdout+stderr.", {"args": str})
async def t_run_pytest(args: dict) -> dict:
    return _text(test_tools.run_pytest(args.get("args", "")))


@tool("run_npm_test", "Run npm test in the workspace clone. Returns stdout+stderr.", {})
async def t_run_npm_test(_args: dict) -> dict:
    return _text(test_tools.run_npm_test())


# Tool registry: (name, callable). Order matches the discussion in step 4.
_TOOL_REGISTRY: list[tuple[str, Any]] = [
    ("gh_pr_diff", t_gh_pr_diff),
    ("gh_pr_files", t_gh_pr_files),
    ("gh_pr_comment", t_gh_pr_comment),
    ("gh_review_submit", t_gh_review_submit),
    ("gh_issue_read", t_gh_issue_read),
    ("gh_pr_create", t_gh_pr_create),
    ("git_checkout", t_git_checkout),
    ("git_apply", t_git_apply),
    ("git_commit", t_git_commit),
    ("git_push", t_git_push),
    ("read_file", t_read_file),
    ("grep", t_grep),
    ("glob", t_glob),
    ("run_pytest", t_run_pytest),
    ("run_npm_test", t_run_npm_test),
]

ALL_TOOLS = [t for _, t in _TOOL_REGISTRY]
# ALL_TOOL_NAMES is the canonical pre-approval list for ClaudeAgentOptions.
# Format follows the SDK convention: mcp__<server-name>__<tool-name>.
ALL_TOOL_NAMES = [f"mcp__agent_tools__{n}" for n, _ in _TOOL_REGISTRY]


def build_sdk_server():
    """Create the in-process MCP server that exposes all agent tools."""
    return create_sdk_mcp_server(name="agent_tools", version="0.1.0", tools=ALL_TOOLS)


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_prompt(name: str) -> str:
    """Load a prompt from prompts/<name>.md, stripping YAML frontmatter and
    HTML comment scaffolding.

    Scaffold prompts ship with frontmatter + a <!-- ... --> block of authoring
    instructions. Until the participant writes something OUTSIDE those comment
    blocks, this raises RuntimeError so step 7's "did you actually write the
    prompts?" check has bite.
    """
    import re

    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file missing: {path}. Did you author it in step 5 or 6?")
    text = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter.
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            body = text[end + 5 :]

    # Strip HTML comments (<!-- ... -->) — these are scaffold instructions, not prompts.
    real_body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
    if not real_body:
        raise RuntimeError(
            f"Prompt {path.name} has only frontmatter and scaffolding comments — "
            "author your actual prompt text outside the <!-- ... --> block."
        )
    return real_body


# ---------------------------------------------------------------------------
# Shared run helper
# ---------------------------------------------------------------------------

def build_options(role: Role, system_prompt: str) -> ClaudeAgentOptions:
    """Assemble ClaudeAgentOptions for a single role's run."""
    return ClaudeAgentOptions(
        model=pick_model(role),
        system_prompt=system_prompt,
        mcp_servers={"agent_tools": build_sdk_server()},
        allowed_tools=ALL_TOOL_NAMES,
    )


async def run_agent(
    role: Role,
    system_prompt: str,
    user_message: str,
    telemetry: TelemetryLogger,
    span_name: str,
) -> str:
    """Run one agent turn: send user_message, return concatenated text response.

    This is the canonical message loop. Modes (review.py, triage.py) call this
    once per role per work unit, and assemble the results themselves.

    Telemetry: opens a model_call span around the SDK call and records its
    duration. Token accounting is left to a follow-up exercise (bonus step 15).
    """
    options = build_options(role, system_prompt)
    with telemetry.span(span_name, kind="model_call", role=role, model=options.model):
        async with ClaudeSDKClient(options=options) as client:
            await client.query(user_message)
            chunks: list[str] = []
            async for msg in client.receive_response():
                # Best-effort text extraction. The SDK yields a few message shapes;
                # we collect any .text fields we can find.
                text = _extract_text(msg)
                if text:
                    chunks.append(text)
            return "\n".join(chunks).strip()


def _extract_text(msg: Any) -> str:
    """Pull any text content out of an SDK message in a shape-tolerant way."""
    # Common shapes the SDK emits:
    #   - {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}}
    #   - {"type": "text", "text": "..."}
    #   - objects with a .content attribute
    if isinstance(msg, dict):
        if msg.get("type") == "text" and isinstance(msg.get("text"), str):
            return msg["text"]
        message = msg.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                return "".join(
                    b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                )
            if isinstance(content, str):
                return content
    content = getattr(msg, "content", None)
    if isinstance(content, list):
        parts = []
        for b in content:
            t = getattr(b, "text", None) or (b.get("text") if isinstance(b, dict) else None)
            if t:
                parts.append(t)
        return "".join(parts)
    if isinstance(content, str):
        return content
    return ""
