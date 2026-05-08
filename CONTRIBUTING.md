# Contributing to Auto Chart Engine

This document outlines the process for reporting bugs, proposing features, and submitting pull requests.

## Table of Contents

- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Branch Strategy](#branch-strategy)
- [Commit Guidelines](#commit-guidelines)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Release Process](#release-process)
- [Coding Standards](#coding-standards)

## Reporting Bugs

1. **Search existing issues** before opening a new one to avoid duplicates.
2. Open a new issue using the **Bug Report** template.
3. Include the following:
   - A clear and descriptive title
   - Steps to reproduce the problem
   - Expected vs. actual behavior
   - Your Python version and OS
   - Any relevant error messages or stack traces

## Suggesting Features

1. Open an issue using the **Feature Request** template.
2. Describe the problem your feature solves and your proposed solution.
3. Features are discussed in the issue before any code is written.

## Branch Strategy

This project uses two permanent branches:

- **`main`** — stable, release-only. Never commit here directly. Only receives squash merges from `dev` at release time.
- **`dev`** — active development. All feature branches merge here.

When working on something new, branch off `dev` using a descriptive name:

```
feature/<short-description>   # new functionality
fix/<short-description>        # bug fixes
docs/<short-description>       # documentation only
refactor/<short-description>   # code cleanup with no behavior change
```

**Examples:**
```bash
git checkout dev
git pull --rebase origin dev
git checkout -b feature/add-drum-detection
```

When your work is done, open a PR targeting `dev` — not `main`.

## Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <short description>
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `refactor` | Code restructuring with no behavior change |
| `test` | Adding or updating tests |
| `chore` | Dependency updates, config changes, etc. |

**Examples:**
```
feat: add support for .wav audio output
fix: handle empty MIDI track in parser
docs: update installation steps in README
refactor: simplify tempo detection logic
test: add edge case coverage for note parser
```

**Tips:**
- Keep the description short and in the present tense ("add support" not "added support")
- Each commit should do one logical thing
- Never commit debug prints, commented-out code, or build artifacts (`dist/`, `build/`, `*.egg-info/`)

## Submitting a Pull Request

1. Make sure your branch is up to date with `dev`:
   ```bash
   git pull --rebase origin dev
   ```
2. Push your branch and open a PR targeting `dev`.
3. Fill out the PR template — describe what changed and why, and link any related issues.
4. Ensure all status checks pass before requesting a review.
5. A maintainer will review and either approve or request changes.
6. PRs are merged using a **merge commit** to preserve full history on `dev`.

## Release Process

Releases are managed by maintainers only.

1. When `dev` is stable and ready, a PR is opened from `dev` → `main`.
2. It is squash merged into `main` as a single release commit.
3. `main` is tagged with the version number:
   ```bash
   git tag -a v1.0.0 -m "v1.0.0"
   git push origin main --tags
   ```
4. A GitHub Release is created from the tag with a summary of changes.
5. The new version is published to PyPI.

This project follows [Semantic Versioning](https://semver.org/):
- `MAJOR` — breaking changes
- `MINOR` — new backwards-compatible features
- `PATCH` — backwards-compatible bug fixes

## Coding Standards

This project uses [pre-commit](https://pre-commit.com/) to automatically enforce code standards on every commit. All checks must pass before a PR will be accepted.

### Setup

Install the development dependencies and set up the pre-commit hooks:

```bash
pip install pre-commit black isort flake8
pre-commit install
```

After running `pre-commit install`, the following checks will run automatically on every `git commit`:

| Tool | Purpose |
|---|---|
| [Black](https://github.com/psf/black) | Formats code to a consistent style |
| [isort](https://pycqa.github.io/isort/) | Sorts and organizes imports |
| [Flake8](https://flake8.pycqa.org/) | Catches errors and style violations Black doesn't cover |

You can also run all checks manually at any time:

```bash
pre-commit run --all-files
```

### Other Standards

- All public functions and classes should have docstrings
- New features should include corresponding unit tests