"""Portable dbt CLI entry point for environments where user-level scripts are not on PATH."""

from dbt.cli.main import cli

if __name__ == "__main__":
    cli()
