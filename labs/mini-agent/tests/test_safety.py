import pytest

from mini_claude_code.safety import SafetyError, assert_safe_command


def test_allows_normal_test_command() -> None:
    assert_safe_command("python3 -m pytest")


def test_blocks_destructive_command() -> None:
    with pytest.raises(SafetyError):
        assert_safe_command("rm -rf .")


def test_blocks_git_reset_hard() -> None:
    with pytest.raises(SafetyError):
        assert_safe_command("git reset --hard")
