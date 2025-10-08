"""Normalize README image links to absolute HTTPS URLs for PyPI compatibility.

This hook rewrites relative image paths to absolute GitHub raw URLs.
Exits with non-zero code if changes were made (standard pre-commit behavior).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg"}


def get_git_info() -> tuple[str, str]:
    """Get GitHub repository info from git remote.

    Returns:
        tuple: (owner/repo, current commit SHA)

    Raises:
        RuntimeError: If git commands fail or remote URL is invalid
    """
    try:
        # Get remote URL
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        # Parse owner/repo from various GitHub URL formats
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote_url)
        if not match:
            raise RuntimeError(f"Could not parse GitHub repo from remote URL: {remote_url}")

        repo_path = match.group(1)

        # Get current commit SHA (default ref)
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        return repo_path, commit_sha

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e}") from e


def normalize_image_urls(
    content: str,
    base_url: str,
    allowed_extensions: set[str] = ALLOWED_EXTENSIONS,
) -> str:
    """Convert relative image URLs to absolute GitHub raw URLs.

    Args:
        content: File content to process
        base_url: Base URL for absolute links (e.g., https://raw.githubusercontent.com/owner/repo/ref/)
        allowed_extensions: Set of allowed image file extensions

    Returns:
        str: Content with normalized image URLs
    """

    def is_allowed_image(path: str) -> bool:
        """Check if path has an allowed image extension."""
        return any(path.lower().endswith(ext) for ext in allowed_extensions)

    def normalize_path(path: str) -> str:
        """Normalize relative path by removing leading ./ and ensuring it's not absolute URL."""
        if path.startswith(("http://", "https://")):
            return path  # Already absolute
        return path.lstrip("./")

    # Handle Markdown image syntax: ![alt](url)
    def replace_markdown(match):
        prefix = match.group(1)
        url = match.group(2)
        suffix = match.group(3)

        # Skip if already absolute URL
        if url.startswith(("http://", "https://")):
            return match.group(0)

        # Only process allowed image extensions
        if not is_allowed_image(url):
            return match.group(0)

        normalized = normalize_path(url)
        return f"{prefix}{base_url}{normalized}{suffix}"

    content = re.sub(
        r'(!\[[^\]]*\]\()((?!https?://)[^)]+)(\))',
        replace_markdown,
        content,
    )

    # Handle HTML img tags: <img src="url">
    def replace_html(match):
        prefix = match.group(1)
        url = match.group(2)
        suffix = match.group(3)

        # Skip if already absolute URL
        if url.startswith(("http://", "https://")):
            return match.group(0)

        # Only process allowed image extensions
        if not is_allowed_image(url):
            return match.group(0)

        normalized = normalize_path(url)
        return f"{prefix}{base_url}{normalized}{suffix}"

    content = re.sub(
        r'(<img\s+[^>]*src=")([^"]+)("[^>]*>)',
        replace_html,
        content,
        flags=re.IGNORECASE,
    )

    return content


def process_file(
    filepath: Path,
    base_url: str,
    check_only: bool = False,
) -> bool:
    """Process a single README file.

    Args:
        filepath: Path to README file
        base_url: Base URL for absolute image links
        check_only: If True, only check without modifying

    Returns:
        bool: True if changes were made/needed, False otherwise
    """
    if not filepath.exists():
        print(f"Warning: {filepath} not found, skipping", file=sys.stderr)
        return False

    try:
        original_content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return False

    normalized_content = normalize_image_urls(original_content, base_url)

    if normalized_content == original_content:
        # No changes needed
        return False

    if check_only:
        print(f"{filepath}: Image URLs need normalization (use without --check-only to fix)")
        return True

    # Write changes
    try:
        filepath.write_text(normalized_content, encoding="utf-8")
        print(f"{filepath}: Normalized image URLs")
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}", file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> int:
    """Main entry point for check-readme-images hook.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        int: 0 if no changes needed, 1 if changes were made/needed
    """
    parser = argparse.ArgumentParser(
        description="Normalize README image links to absolute HTTPS URLs for PyPI compatibility"
    )
    parser.add_argument(
        "filenames",
        nargs="+",
        help="Files to process (typically README.md or README.rst)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if normalization is needed, don't modify files",
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Git ref to pin URLs to (default: current commit SHA)",
    )

    args = parser.parse_args(argv)

    # Get repository info
    try:
        repo_path, default_ref = get_git_info()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("This hook requires a GitHub repository with a configured origin remote.", file=sys.stderr)
        return 1

    # Use specified ref or default to current commit
    ref = args.ref if args.ref else default_ref
    base_url = f"https://raw.githubusercontent.com/{repo_path}/{ref}/"

    # Process all files
    any_changes = False
    for filename in args.filenames:
        filepath = Path(filename)
        if process_file(filepath, base_url, check_only=args.check_only):
            any_changes = True

    # Exit with non-zero if any changes were made (pre-commit convention)
    return 1 if any_changes else 0


if __name__ == "__main__":
    sys.exit(main())
