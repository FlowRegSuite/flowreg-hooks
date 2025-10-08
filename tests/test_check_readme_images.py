"""Tests for flowreg_hooks.check_readme_images."""

import pytest

from flowreg_hooks.check_readme_images import main, normalize_image_urls, process_file

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
