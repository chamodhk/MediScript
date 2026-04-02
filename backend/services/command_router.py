from __future__ import annotations

from dataclasses import dataclass


ALIASES = {
    "/summery": "/summary",
    "/followup": "/followups",
    "/reminder": "/reminders",
}


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    args: list[str]
    raw: str


class CommandRouter:
    """Rule-based parser for slash commands.

    Example:
        router = CommandRouter()
        router.parse("/done 2")
    """

    def parse(self, text: str) -> ParsedCommand | None:
        stripped = (text or "").strip()
        if not stripped.startswith("/"):
            return None

        parts = stripped.split()
        command = parts[0].lower()
        command = ALIASES.get(command, command)
        return ParsedCommand(
            name=command,
            args=parts[1:],
            raw=stripped,
        )
