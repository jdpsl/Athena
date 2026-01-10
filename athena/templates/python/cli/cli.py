"""Main CLI entry point for {{project_name}}."""

import click

from {{project_name_snake}} import __version__
from {{project_name_snake}}.commands.hello import hello


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """{{description}}

    A modern Python CLI application built with Click.
    """
    # Ensure ctx.obj exists for passing data between commands
    ctx.ensure_object(dict)


# Register commands
cli.add_command(hello)


if __name__ == "__main__":
    cli()
