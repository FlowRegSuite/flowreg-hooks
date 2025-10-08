"""Pre-commit hooks for FlowRegSuite."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("flowreg-hooks")
except PackageNotFoundError:
    __version__ = "unknown"
