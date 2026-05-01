import click
from src.checker import check_operation, cli as check_cli

@click.group()
def cli():
    """Main entry point for the CLI application."""
    pass

cli.add_command(check_cli)

if __name__ == '__main__':
    cli()