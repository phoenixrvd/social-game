# Git Workflow

## Branch Strategy

### Release Branches

* Work is grouped in version branches:

  * `v1.2`
  * `v1.3`
  * `v1.x`

### Rules

* All planned changes for a release go into the corresponding `v1.x` branch
* No direct work on `main`
* `main` always represents a clean, squashed release state

## Commit Messages

### Format

```
<type>: <description>
```

### Types (based on usage)

* `refactor:` → structural/code improvements
* `feature:` → new functionality
* `fix:` → bug fixes
* `add:` → new files or setup (e.g. LICENSE, SECURITY)
* `feature:` → new files or setup (e.g. LICENSE, SECURITY)

### Rules

* lowercase type
* concise and clear description
* describe what changed

### Examples

* `refactor: simplify message handling and improve loading state`
* `refactor: enhance input handling to maintain focus`
* `add: LICENSE and SECURITY policy documents`

## Working in Release Branch

* Multiple commits are allowed
* History can be messy
* Focus is on progress, not cleanliness

## Squash Merge to Main

When the release is ready, everything is squashed into a single commit.

### Steps

Changes are merged from `v1.x` to `main` using squash merge:

```bash
git checkout main
git merge --squash --ff v1.x
git commit
```

Update the main branch with the new release commit:

```bash
git push origin main
```

## Commit Message for Release

* Should summarize the full release
* Can reuse release notes

Example:

```
v1.2: simplified UI, reduced codebase, improved state handling
```

### Rules

* Entire release = one commit in `main`
* No merge commits
* No detailed history kept in `main`

## Principles

* Clean `main`
* Dirty working branches are allowed
* Final result matters, not intermediate steps
