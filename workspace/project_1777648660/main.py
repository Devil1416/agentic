     main
from src.checker import cli as checker_cli

@click.group()
def cli():
    """Main entry point for the CLI application."""
    pass

cli.add_command(checker_cli)

if __name__ == '__main__':
    cli()    pass

cli.add_command(checker_cli)
 if __name__ == '__main__':
    cli()
