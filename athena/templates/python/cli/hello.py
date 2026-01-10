"""Hello command - example CLI command."""

import click


@click.command()
@click.option(
    "--name",
    "-n",
    default="World",
    help="Name to greet",
    show_default=True,
)
@click.option(
    "--count",
    "-c",
    default=1,
    type=int,
    help="Number of greetings",
    show_default=True,
)
@click.option(
    "--uppercase",
    "-u",
    is_flag=True,
    help="Convert output to uppercase",
)
def hello(name: str, count: int, uppercase: bool):
    """Say hello to NAME.

    This is an example command that demonstrates Click features:
    - Options with defaults
    - Type conversion (int)
    - Flags (boolean)
    - Multiple invocations

    Examples:

        \b
        # Basic usage
        $ {{project_name_snake}} hello
        Hello, World!

        \b
        # Custom name
        $ {{project_name_snake}} hello --name Alice
        Hello, Alice!

        \b
        # Multiple greetings
        $ {{project_name_snake}} hello --name Bob --count 3
        Hello, Bob!
        Hello, Bob!
        Hello, Bob!

        \b
        # Uppercase output
        $ {{project_name_snake}} hello --name Charlie --uppercase
        HELLO, CHARLIE!
    """
    for _ in range(count):
        message = f"Hello, {name}!"

        if uppercase:
            message = message.upper()

        click.echo(message)
