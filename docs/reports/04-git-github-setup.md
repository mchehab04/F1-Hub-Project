# Stage 04 — Git and GitHub setup

**Date**: 2026-08-20
**Status**: Complete

## What was done

User asked whether GitHub was a good idea for this project (relevant given the plan to have two different AI coding agents build backend/frontend in parallel — version control isn't optional there).

Investigation found the git repo root was `C:\Users\mcheh` — the entire home directory — not the project folder, discovered via `git rev-parse --show-toplevel`. Fixed by running `git init` inside the project folder itself (git nests fine; the inner repo takes over for everything inside it, the outer one untouched), then adding a `.gitignore` scoped to the planned stack (Python, Node/Next.js, SQLite, FastF1 cache, secrets).

## GitHub remote

`gh` CLI wasn't installed. Installed it via `winget`, but the device-code login (`gh auth login --web`) got stuck mid-flow in the tool's sandboxed shell environment and was abandoned per the user's request ("deal with GitHub later").

It turned out to be a non-issue: the user separately used VS Code's own "Publish to GitHub" flow (with its own authenticated session, unrelated to the stuck CLI login), which created `github.com/mchehab04/F1-Hub-Project`, renamed the local branch to `main`, and pushed an initial commit — discovered when a routine `git status` showed an unexpected `M README.md` and a second commit (`cf56b91`) that hadn't been made through this session. Verified via `git fetch` that nothing was lost or diverged before proceeding.

## Outcome

- Local repo properly scoped to the project folder, with a correct `.gitignore`.
- Remote live at `github.com/mchehab04/F1-Hub-Project`, `main` branch, in sync.

## Files created/touched

- `.gitignore`
- (repo-level `.git/` — not a tracked file)

## Next stage

Repo structure scaffolding (see `05-repo-scaffolding.md`).
