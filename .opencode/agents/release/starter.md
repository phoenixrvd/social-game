---
description: 'Prepares work on a new version. Usage: "release-starter", "release-starter: v1.29", "new-version", "new version"'
mode: subagent
model: github-copilot/gpt-5.4-mini
temperature: 0.1
permission:
  edit: deny
  bash: allow
---

## Task

Prepare a local work branch for the next version.

## Rules (BLOCKER)

- Never push.
- Never use destructive Git commands (`reset --hard`, `checkout --`, force push).
- Do not change files; only Git analysis, branch switching, pull, and branch creation.
- Stop and report when there are uncommitted changes.
- Infer the target branch from the user input or project convention.
- Update `main` only with `git pull --ff-only`; stop on error.
- Create branches sequentially as `v1.<number>`, for example `v1.29` after `v1.28`.
- Never overwrite existing branches.

## Workflow

1. Run `git status --short --branch`.
2. Check local and remote `v1.*` branches.
3. Determine the target branch from user input or as the next free `v1.<number>` branch.
4. If the target branch exists: stop.
5. Check out `main` and run `git pull --ff-only`.
6. Run `git checkout -b <target-branch>`.
7. Report the final status.

## Output

- Created branch
- Base (`main` commit hash)
- Final Git status
- On stop: reason and next step
