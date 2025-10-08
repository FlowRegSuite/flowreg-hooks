# flowreg-hooks

Pre-commit meta hooks for FlowRegSuite Python repositories. Single-repo solution with pinned, deterministic tool versions.

## Features

- **PyPI-safe README images** – Normalize relative image links to absolute GitHub URLs
- **Code quality** – Ruff linting and formatting with auto-fix
- **Documentation** – NumPy docstring validation
- **Project validation** – pyproject.toml structure checking
- **Standard housekeeping** – Whitespace, line endings, YAML/TOML syntax, merge conflicts

All hooks run locally, are fast, and only operate on changed files.

## Available Hooks

### Custom FlowRegSuite Hooks

| Hook ID | Description |
|---------|-------------|
| `check-readme-images` | Convert relative image paths to absolute GitHub raw URLs for PyPI compatibility |

### Code Quality (Ruff)

| Hook ID | Description |
|---------|-------------|
| `fr-ruff` | Ruff linting with auto-fix (includes import sorting, style checks) |
| `fr-ruff-format` | Ruff code formatter |

### Documentation

| Hook ID | Description |
|---------|-------------|
| `fr-numpydoc-validation` | Validate NumPy-style docstrings (excludes tests/examples/experiments/notebooks) |

### Project Validation

| Hook ID | Description |
|---------|-------------|
| `fr-validate-pyproject` | Validate pyproject.toml structure and dependencies |

### Standard Housekeeping

| Hook ID | Description |
|---------|-------------|
| `fr-trailing-whitespace` | Fix trailing whitespace |
| `fr-end-of-file-fixer` | Ensure files end with a newline |
| `fr-check-yaml` | Validate YAML syntax |
| `fr-check-toml` | Validate TOML syntax |
| `fr-check-merge-conflict` | Detect merge conflict markers |
| `fr-debug-statements` | Check for debug statements (pdb, ipdb, etc.) |
| `fr-mixed-line-ending` | Fix mixed line endings (enforces LF) |

## Quick Start

### 1. Create `.pre-commit-config.yaml` in your repository

**Minimal setup:**
```yaml
repos:
  - repo: https://github.com/FlowRegSuite/flowreg-hooks
    rev: v1.0.0
    hooks:
      - id: check-readme-images
      - id: fr-ruff
      - id: fr-ruff-format
```

**Recommended setup:**
```yaml
repos:
  - repo: https://github.com/FlowRegSuite/flowreg-hooks
    rev: v1.0.0
    hooks:
      - id: check-readme-images
      - id: fr-ruff
      - id: fr-ruff-format
      - id: fr-numpydoc-validation
      - id: fr-validate-pyproject
      - id: fr-trailing-whitespace
      - id: fr-end-of-file-fixer
      - id: fr-check-yaml
      - id: fr-check-toml
      - id: fr-check-merge-conflict
      - id: fr-debug-statements
      - id: fr-mixed-line-ending
```

### 2. Install and activate

```bash
pip install pre-commit
pre-commit install
```

### 3. Run hooks

```bash
# Run on staged files
git add .
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run fr-ruff --all-files
```

## Configuration

### Ruff Configuration (Optional)

Add to your `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "I", "D", "UP", "N"]
ignore = ["D100", "D104"]  # Customize as needed

[tool.ruff.lint.pydocstyle]
convention = "numpy"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D"]
```

### check-readme-images Options

```bash
# Check only (no modifications)
check-readme-images --check-only README.md

# Pin to specific git ref
check-readme-images --ref v1.0.0 README.md
```

## CI Integration

### GitHub Actions Example

```yaml
name: Quality Checks
on: [pull_request, push]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pipx run pre-commit run --all-files
```

### pre-commit.ci

Enable [pre-commit.ci](https://pre-commit.ci) for automatic hook execution on pull requests.

Add to `.pre-commit-config.yaml`:
```yaml
ci:
  autoupdate_schedule: monthly
```

## Versioning

This repository uses semantic versioning (`vX.Y.Z`). Tool versions are pinned via `additional_dependencies` in `.pre-commit-hooks.yaml`.

- **To update tool versions**: Bump versions in this repo, tag a new release
- **To update flowreg-hooks**: Update `rev` in your `.pre-commit-config.yaml`

```bash
# Update to latest version
pre-commit autoupdate
```

## Requirements

- Python ≥ 3.10
- Git repository with GitHub remote (for `check-readme-images`)

## License

CC BY-NC-SA 4.0
