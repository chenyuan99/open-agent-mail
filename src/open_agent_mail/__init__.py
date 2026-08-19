"""Open Agent Mail: a small, local-first inbox for software agents."""


def main() -> None:
    """Start the web application from the installed console script."""
    from .server import main as run

    run()


__all__ = ["main"]
