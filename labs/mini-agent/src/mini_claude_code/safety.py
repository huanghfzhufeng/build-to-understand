from __future__ import annotations

import shlex


class SafetyError(RuntimeError):
    pass


BLOCKED_COMMANDS = {
    "rm",
    "mv",
    "dd",
    "mkfs",
    "shutdown",
    "reboot",
}

BLOCKED_GIT_PATTERNS = [
    ["git", "reset", "--hard"],
    ["git", "checkout", "--"],
    ["git", "clean"],
]


def assert_safe_command(command: str) -> None:
    parts = shlex.split(command)
    if not parts:
        raise SafetyError("empty command is not allowed")

    executable = parts[0].split("/")[-1]

    if executable in BLOCKED_COMMANDS:
        raise SafetyError(f"blocked command: {parts[0]}")

    for pattern in BLOCKED_GIT_PATTERNS:
        if parts[: len(pattern)] == pattern:
            raise SafetyError(f"blocked git command: {' '.join(pattern)}")
