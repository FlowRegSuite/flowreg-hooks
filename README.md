# flowreg-hooks

Pre-commit hooks for FlowRegSuite Python repositories. Fast, local, idempotent working‑tree changes and PyPI‑safe READMEs.

---

## Why
- Prevent broken images on PyPI by normalizing README links.
- Enforce NumPy‑style docstrings using mainstream linters.
- Keep heavy/branch‑wide fixes in CI; hooks operate only on changed files.

## Hooks

### `check-readme-images`
Ensures `README.md`/`README.rst` embeds use **absolute HTTPS URLs** that render on PyPI. Rewrites the file in place; exits non‑zero if changes were made (standard pre‑commit behavior).

**Rules**
- Convert relative image paths to absolute, raw Git URLs.
- Allow: `.png .jpg .jpeg .gif .svg`.
- Default ref pin: current commit `HEAD` (or use `--ref`).

**CLI**
```
check-readme-images [--check-only] [--ref <git-ref>]
```
- `--check-only`: no modifications; non‑zero exit if fixes needed.
- `--ref`: pin URLs to a tag/SHA (default: current commit).

---

### `validate-numpy-docstrings`
Thin wrapper that enforces NumPy docstring convention via `ruff` (preferred) or falls back to `pydocstyle`.

**Behavior**
- Uses `ruff --select D` when available, otherwise `pydocstyle --convention=numpy`.
- Respects project‑local configuration in `pyproject.toml`.

**CLI**
```
validate-numpy-docs
```

---

## Usage in a consumer repository

`.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/FlowRegSuite/flowreg-hooks
    rev: v1.0.0
    hooks:
      - id: check-readme-images
      - id: validate-numpy-docstrings
```

Install and run:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

**Recommended `pyproject.toml` (consumer)**
```toml
[project.optional-dependencies]
dev = [
  "pre-commit>=3.8",
  "ruff>=0.6",
  "pydocstyle>=6.3",
  "build>=1.2",
  "twine>=5.1",
]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E","F","I","D"]

[tool.ruff.lint.pydocstyle]
convention = "numpy"
```

---

## CI integration (consumer)

Minimal quality workflow:
```yaml
name: quality
on: [pull_request, push]
jobs:
  precommit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pipx run pre-commit run --all-files
  pypi-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install build twine
      - run: python -m build
      - run: twine check dist/*
```

Optional “autofix PR” (never push to default branch):
```yaml
  autofix:
    if: ${{ github.event_name == 'pull_request' && always() && (needs.precommit.result == 'failure') }}
    runs-on: ubuntu-latest
    needs: [precommit]
    steps:
      - uses: actions/checkout@v4
        with: { ref: ${{ github.head_ref }} }
      - uses: actions/setup-python@v5
      - run: pipx run pre-commit run --all-files || true
      - run: git config user.name "pre-commit-bot" && git config user.email "bot@example.com"
      - run: git add -A && (git commit -m "pre-commit autofix" || true)
      - uses: peter-evans/create-pull-request@v6
        with:
          branch: autofix/${{ github.head_ref }}
          title: "pre-commit autofix"
```

You may also enable [pre-commit.ci] to automatically apply hook fixes to PRs.

---

## Using the hooks locally without publishing

```bash
pre-commit try-repo https://github.com/FlowRegSuite/flowreg-hooks v1.0.0 check-readme-images --all-files
```

---

## Development

**Layout**
```
src/flowreg_hooks/
  __init__.py
  check_readme_images.py
  validate_docstrings.py
.pre-commit-hooks.yaml
pyproject.toml
README.md
```

**`pyproject.toml`**
```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "flowreg-hooks"
version = "1.0.0"
description = "Pre-commit hooks for FlowRegSuite (README image normalization, NumPy docstrings)"
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }
dependencies = ["pydocstyle>=6.3"]

[project.optional-dependencies]
ruff = ["ruff>=0.6"]

[project.scripts]
check-readme-images = "flowreg_hooks.check_readme_images:main"
validate-numpy-docs = "flowreg_hooks.validate_docstrings:main"

[tool.setuptools.packages.find]
where = ["src"]
```

**`.pre-commit-hooks.yaml`**
```yaml
- id: check-readme-images
  name: Check README has absolute image URLs (PyPI compatible)
  entry: check-readme-images
  language: python
  files: ^README\.(md|rst)$
  pass_filenames: true
  stages: [pre-commit, manual]

- id: validate-numpy-docstrings
  name: Validate NumPy docstring format
  entry: validate-numpy-docs
  language: python
  types: [python]
  stages: [pre-commit, manual]
```

---

## Versioning & pinning
- Tagged releases (`vX.Y.Z`) only; consumers must pin `rev`.
- Semantic versioning for behavior; breaking changes require a major bump.

## Invariants
- Hooks are fast, deterministic, idempotent, offline.
- Hooks may modify files or fail; they never create commits or contact remote services.
