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

* Must summarize the full release
* Must follow the release hook format on `main`
* Must be written in English
* Must include a structured body for non-trivial releases

Example:

```
v1.11: theming improvements, image rendering fixes, and gallery architecture cleanup

Theming and metadata
- Enhanced theme handling with dynamic color adaptation.
- Refined app capability metadata and naming references.

Image rendering
- Fixed positioning and scaling behavior in the scene image slot for consistent visual output.

Component architecture
- Removed unused NPC/scene gallery components to reduce frontend complexity.
- Improved maintainability with clearer HTML/CSS template markers for editor highlighting.
- Added line clamping in context gallery text blocks for cleaner truncation behavior.

Project hygiene
- Updated .gitignore for local editor artifacts.
```

### Rules

* Entire release = one commit in `main`
* No merge commits
* No detailed history kept in `main`
* Subject line format on `main`: `vX.Y: <summary>`
* Do not use generic headings like `Release notes`
* Use domain-based section headings in the body
* Do not use trailing colons in section headings

## Release Tags

* Tags are optional and can be omitted
* If a release tag is used, keep subject and body aligned with the release commit message

## Principles

* Clean `main`
* Dirty working branches are allowed
* Final result matters, not intermediate steps
