# Bug to Fix

An agentic pipeline that takes a GitHub repository and a plain-language bug description, localizes the bug, fixes it in an isolated sandbox, independently verifies the fix, and produces a detailed report for human review.

## Why this exists

Most AI coding assistants work as a black box: the model reads some code, does some things, and hands you an answer. If a tool call fails or the model goes down the wrong path, you usually can't tell where or why — you just see the final result, or the model silently retries until something breaks.

This project is built around the opposite idea: **every stage of the process is a separate, inspectable step.** Localizing the bug, fixing it, and verifying the fix are three distinct agents with three distinct jobs, each one committing its work and its reasoning to disk before the next stage ever starts. Nothing is hidden — a failed attempt isn't erased, it's kept as its own git branch, renamed to say it failed, so a human can go look at exactly what was tried and why it didn't work.

## How it works

```
GitHub URL + bug description
        │
        ▼
  Clone the repo, list its files
        │
        ▼
  LLM1 — Localizer
  Reads the repo, runs the code, reasons about where the bug is
  and why, writes llm1_report.json
        │
        ▼
  LLM2 — Fixer
  Creates an isolated git worktree + branch, edits the code, tests
  the fix by actually running it, commits the attempt (whether it
  worked or not), writes llm2_report.json
        │
        ▼
  LLM3 — Verifier
  Independently re-checks the fix against the original baseline
  output — it did not write the fix, so it isn't grading its own
  work — and writes llm3_report.md for human review
```

Each stage is a separate LLM agent that can be backed by a **different model** — diagnosis, implementation, and verification don't have to use the same underlying model, and swapping any of them is a one-line `.env` change via OpenRouter.

## Design decisions worth knowing about

**Isolation is done with `git worktree`, not Docker or plain file copies.** Every fix attempt gets its own branch and its own working directory, sharing the same repo history. A failed attempt never touches the original clone — it just gets its worktree removed and its branch renamed to `bugfix/<job>-attempt-N-failed`, so it stays around as a real, inspectable commit history instead of being thrown away.

**LLMs never write to disk directly.** Each agent's job ends by calling a dedicated `submit_*` tool with structured arguments (its diagnosis, its fix summary, its verdict) — the tool itself does nothing; it only forces the model's output into a fixed schema. The actual file write is done by plain Python code that reads those arguments and calls a shared `report_write` tool, so a stage can never accidentally overwrite another stage's report or produce a malformed file.

**Each agent runs its own bounded tool-calling loop**, built on top of a small reusable `Agent` class (LangGraph under the hood): read/search/run, observe the result, decide the next step, repeat — up to a hard iteration cap per stage, so a stuck agent fails loudly and visibly instead of burning through tokens indefinitely.

**Fault localization for silent bugs** (no traceback, just a wrong output) works by having LLM1 actually run the code, compare real output against what the bug report implies, and read outward from there — the buggy function, its docstring, its callers, its existing tests — rather than reading the whole repository blind or trusting a single input/output example, which is enough to accidentally curve-fit a wrong fix onto one example.

## Stack

- **LangChain / LangGraph** — agent orchestration and the tool-calling loop
- **LangSmith** — tracing every LLM call and tool call across all three stages, for debugging and auditability
- **OpenRouter** — single API surface for swapping the model behind each stage
- **GitPython** — repo cloning, worktrees, branching, commits

## Project structure

```
bug-to-fix-agent/
├── .env                      # API keys, per-stage model names
├── requirements.txt
├── target_repo/              # the cloned repo being debugged
├── sandbox/                  # per-attempt worktrees
├── report/                   # llm1_report.json, llm2_report.json, llm3_report.md
├── tools/
│   ├── clone_repo.py
│   ├── list_files.py
│   ├── read_file.py
│   ├── write_file.py
│   ├── edit_file.py
│   ├── search_code.py
│   ├── run_shell.py
│   ├── report_write.py
│   ├── sandbox_manager.py    # create_branch, commit_changes, discard_attempt
│   ├── submit_context_report.py
│   ├── submit_fix_result.py
│   └── submit_verdict.py
├── graph/
│   └── Agent.py              # reusable agent loop shared by all three stages
└── pipeline.py                # the outer LangGraph wiring everything together
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENROUTER_API_KEY=your_key_here
LLM1=openai/gpt-4o
LLM2=anthropic/claude-3.5-sonnet
LLM3=google/gemini-2.0-flash
```

## Running it

```bash
python pipeline.py
```

You'll be prompted for a GitHub repo URL and a description of the bug. The pipeline clones the repo, runs the three-stage process, and leaves its findings in `report/`.

## Current limitations (v2 roadmap)

This is an early, working version, built to prove the core pipeline end to end — a few things are known gaps rather than oversights:

- The verified fix isn't automatically merged back into the target repo's main branch yet — the branch is left ready, but the merge step is manual for now.
- No Docker or other execution-level sandboxing yet — `git worktree` isolates branches and history, not what the executed code itself can do to the machine it runs on.
- No support yet for repos that need a running server (frontend bugs) or that call external, keyed APIs — both need a headless browser and request mocking respectively, and are deliberately out of scope for this version.
- Commit granularity is one commit per attempt, not per edit — a failed attempt can't be selectively rolled back to a "good" partial state, only retried from scratch with the accumulated failure report as guidance.
- No cleanup step yet between runs — `target_repo/`, `sandbox/`, and `report/` need to be cleared manually before running the pipeline again on a new job.
