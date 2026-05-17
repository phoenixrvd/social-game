---
description: 'Runs the local release workflow. Usage: "release-finisher: <version>", "release: <version>", "create release", "squash merge"'
mode: subagent
model: github-copilot/gpt-5.4
permission:
  edit: allow
  bash: allow
---

## Rules (BLOCKER)
- **Never push.** Local commit only.
- No code changes outside the release workflow.
- Determine release, build, test, and dependency rules.
- Before the release, verify that `requirements.txt` is up to date with `requirements.in`.
- If `pip-compile requirements.in` changes `requirements.txt`, stop the release and report it as a blocker.
- Do not invent release commands; stop if ambiguous.

## Workflow
Local OpenCode release workflow according to `doc/guidelines/git-workflow.md`, without push.
1. Check the working tree.
2. Check `requirements.txt` freshness with `pip-compile requirements.in`; it must produce no diff.
3. Check `v1.x` and `main`.
4. Switch to `main`.
5. Run `git merge --squash --ff v1.x`.
6. Create the release commit.
7. Do not push.
8. Report the result completely.

## Commit-Format
`v<version>: <summary>` (Englisch)

## Output
- Commit subject
- Short description (1 line, English)
- Release notes (structured, using the `v1.22` release on `main` as the format reference)
- Branch, commit, file count
