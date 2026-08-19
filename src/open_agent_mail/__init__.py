"""Open Agent Mail: a small, local-first inbox for software agents."""


def main() -> None:
    """Run the server or an agent-oriented CLI command."""
    from .cli import main as run

    run()


__all__ = ["main"]
