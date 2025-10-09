"""Tests for flowreg_hooks.check_readme_images."""

import subprocess
import pytest

from flowreg_hooks.check_readme_images import get_git_info, main, normalize_image_urls, process_file

BASE = "https://raw.githubusercontent.com/owner/repo/sha/"


@pytest.mark.parametrize(
    "content,expected",
    [
        ("![alt](docs/img.png)", "![alt](" + BASE + "docs/img.png)"),
        ("![x](./assets/Logo.JPG)", "![x](" + BASE + "assets/Logo.JPG)"),
        ("![y](http://example.com/p.png)", "![y](http://example.com/p.png)"),
        ("![z](https://example.com/p.png)", "![z](https://example.com/p.png)"),
        ("![notimg](docs/file.txt)", "![notimg](docs/file.txt)"),
    ],
)
def test_normalize_markdown_images(content, expected):
    """Test Markdown image URL normalization."""
    out = normalize_image_urls(content, BASE)
    assert out == expected


def test_normalize_html_img_double_quotes():
    """Test HTML img tag normalization with double quotes."""
    content = '<p><img src="img/logo.svg" alt="logo"></p>'
    expected = '<p><img src="' + BASE + 'img/logo.svg" alt="logo"></p>'
    out = normalize_image_urls(content, BASE)
    assert out == expected


def test_idempotence():
    """Test that normalization is idempotent."""
    content = "![alt](pics/a.jpg)"
    once = normalize_image_urls(content, BASE)
    twice = normalize_image_urls(once, BASE)
    assert once == twice


def test_process_file_check_only(tmp_path):
    """Test process_file with check_only=True."""
    p = tmp_path / "README.md"
    p.write_text("![a](img/x.png)", encoding="utf-8")
    changed = process_file(p, BASE, check_only=True)
    assert changed
    assert p.read_text(encoding="utf-8") == "![a](img/x.png)"


def test_process_file_writes(tmp_path):
    """Test process_file writes changes."""
    p = tmp_path / "README.md"
    p.write_text("![a](img/x.png)", encoding="utf-8")
    changed = process_file(p, BASE, check_only=False)
    assert changed
    assert p.read_text(encoding="utf-8") == "![a](" + BASE + "img/x.png)"


def test_main_exit_codes(monkeypatch, tmp_path):
    """Test main function exit codes."""
    readme = tmp_path / "README.md"
    readme.write_text("![a](img/x.png)", encoding="utf-8")

    def fake_git_info():
        return ("owner/repo", "sha")

    monkeypatch.setattr("flowreg_hooks.check_readme_images.get_git_info", fake_git_info)

    # Check-only mode should return 1 (changes needed)
    rc = main([str(readme), "--check-only"])
    assert rc == 1
    assert readme.read_text(encoding="utf-8") == "![a](img/x.png)"

    # Write mode should return 1 (changes made)
    rc = main([str(readme)])
    assert rc == 1
    assert readme.read_text(encoding="utf-8") == "![a](" + BASE + "img/x.png)"

    # Check-only on normalized file should return 0 (no changes needed)
    rc = main([str(readme), "--check-only"])
    assert rc == 0


def test_get_git_info_no_commits(tmp_path, monkeypatch):
    """Test get_git_info() when there are no commits yet (initial commit scenario)."""
    # Create a fresh git repo with no commits
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "remote", "add", "origin", "https://github.com/owner/repo.git"], check=True)

    # Should return None gracefully when no HEAD exists
    result = get_git_info()
    assert result is None


def test_get_git_info_no_origin(tmp_path, monkeypatch):
    """Test get_git_info() when there's no origin remote configured."""
    # Create a git repo with commits but no origin
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)

    # Create a commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    # Should return None gracefully when no origin exists
    result = get_git_info()
    assert result is None


def test_get_git_info_non_github_remote(tmp_path, monkeypatch):
    """Test get_git_info() when remote is not a GitHub URL."""
    # Create a git repo with a non-GitHub remote
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)

    # Create a commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    # Add a non-GitHub remote
    subprocess.run(["git", "remote", "add", "origin", "https://gitlab.com/owner/repo.git"], check=True)

    # Should return None gracefully for non-GitHub remotes
    result = get_git_info()
    assert result is None


def test_main_with_no_origin(tmp_path, monkeypatch):
    """Test that main() fails gracefully when no origin is configured."""
    # Create a git repo with no origin
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)

    # Create README with relative image
    readme = tmp_path / "README.md"
    readme.write_text("![alt](img/test.png)", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    # Should skip processing gracefully and return 0
    rc = main([str(readme)])
    assert rc == 0

    # File should remain unchanged
    assert readme.read_text(encoding="utf-8") == "![alt](img/test.png)"
