# {{project_name}}

{{description}}

A modern Python CLI application built with Click.

## Features

- **Click Framework**: Powerful CLI framework with great features
- **Modern Python**: Uses pyproject.toml, type hints, and best practices
- **Extensible**: Easy to add new commands
- **Well-tested**: Includes pytest tests
- **Type-safe**: Type hints throughout
- **CI/CD Ready**: GitHub Actions workflow included

## Installation

### Development Installation

```bash
# Clone or navigate to the project
cd {{project_name}}

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### User Installation

```bash
# Install from source
pip install .

# Or install from git
pip install git+https://github.com/yourusername/{{project_name}}.git
```

### Using pipx (Recommended for CLI tools)

```bash
# Install with pipx (isolated environment)
pipx install .

# Or from git
pipx install git+https://github.com/yourusername/{{project_name}}.git
```

## Usage

### Basic Commands

```bash
# Show help
{{project_name_snake}} --help

# Show version
{{project_name_snake}} --version

# Run hello command
{{project_name_snake}} hello

# Hello with custom name
{{project_name_snake}} hello --name Alice

# Multiple greetings
{{project_name_snake}} hello --name Alice --count 3
```

### Example Output

```
$ {{project_name_snake}} hello --name World
Hello, World!

$ {{project_name_snake}} hello --name Alice --count 3
Hello, Alice!
Hello, Alice!
Hello, Alice!
```

## Project Structure

```
{{project_name}}/
├── src/
│   └── {{project_name_snake}}/
│       ├── __init__.py          # Package info, version
│       ├── cli.py               # Main CLI entry point
│       └── commands/
│           ├── __init__.py
│           └── hello.py         # Example command
├── tests/
│   ├── __init__.py
│   └── test_cli.py              # CLI tests
├── pyproject.toml               # Project config & dependencies
├── README.md                    # This file
└── LICENSE                      # License file
```

## Adding New Commands

### Step 1: Create Command File

Create `src/{{project_name_snake}}/commands/mycommand.py`:

```python
"""My new command."""

import click


@click.command()
@click.option('--option', default='value', help='An option')
@click.argument('arg')
def mycommand(option: str, arg: str):
    """My new command description."""
    click.echo(f"Option: {option}, Arg: {arg}")
```

### Step 2: Register Command

In `src/{{project_name_snake}}/cli.py`:

```python
from {{project_name_snake}}.commands.mycommand import mycommand

# Add to CLI group
cli.add_command(mycommand)
```

### Step 3: Test It

```bash
{{project_name_snake}} mycommand --help
{{project_name_snake}} mycommand --option test myarg
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov={{project_name_snake}}

# Run specific test
pytest tests/test_cli.py::test_hello_default

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type checking (if you add mypy)
pip install mypy
mypy src/
```

### Building & Distribution

```bash
# Build distribution packages
pip install build
python -m build

# Install built package
pip install dist/{{project_name}}-0.1.0-py3-none-any.whl

# Upload to PyPI (if configured)
pip install twine
twine upload dist/*
```

## Click Features Used

### Options

```python
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--count', '-c', default=1, type=int, help='Number of times')
@click.option('--name', prompt='Your name', help='Name to greet')
```

### Arguments

```python
@click.argument('filename', type=click.Path(exists=True))
@click.argument('output', type=click.File('w'))
```

### Choices

```python
@click.option('--format', type=click.Choice(['json', 'yaml', 'csv']))
```

### Confirmation

```python
@click.confirmation_option(prompt='Are you sure?')
def dangerous_command():
    click.echo("Doing dangerous thing...")
```

### Progress Bars

```python
with click.progressbar(items, label='Processing') as bar:
    for item in bar:
        process(item)
```

### Colors

```python
click.echo(click.style('Success!', fg='green'))
click.echo(click.style('Error!', fg='red', bold=True))
```

## Configuration

### Environment Variables

Set via `.env` file or environment:

```bash
export {{project_name_snake|upper}}_DEBUG=1
export {{project_name_snake|upper}}_CONFIG=/path/to/config.yaml
```

Access in code:

```python
import os

debug = os.getenv('{{project_name_snake|upper}}_DEBUG', '0') == '1'
config_path = os.getenv('{{project_name_snake|upper}}_CONFIG')
```

### Config Files

Click supports config files via `click.get_app_dir()`:

```python
import click
import os
from pathlib import Path

config_dir = Path(click.get_app_dir('{{project_name_snake}}'))
config_file = config_dir / 'config.yaml'

# Read config
if config_file.exists():
    with open(config_file) as f:
        config = yaml.safe_load(f)
```

Common locations:
- **Linux**: `~/.config/{{project_name_snake}}/`
- **macOS**: `~/Library/Application Support/{{project_name_snake}}/`
- **Windows**: `%APPDATA%\{{project_name_snake}}\`

## Testing

### Writing Tests

```python
from click.testing import CliRunner
from {{project_name_snake}}.cli import cli

def test_my_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['mycommand', '--option', 'test'])

    assert result.exit_code == 0
    assert 'expected output' in result.output
```

### Temporary Files in Tests

```python
def test_with_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create temp files
        with open('input.txt', 'w') as f:
            f.write('test data')

        # Run command
        result = runner.invoke(cli, ['process', 'input.txt'])
        assert result.exit_code == 0
```

## Common Patterns

### Loading Spinner

```python
import click

with click.progressbar(length=100, label='Loading') as bar:
    for i in range(100):
        time.sleep(0.01)
        bar.update(1)
```

### Error Handling

```python
try:
    risky_operation()
except Exception as e:
    click.echo(click.style(f'Error: {e}', fg='red'), err=True)
    raise click.Abort()
```

### Verbose Output

```python
@click.command()
@click.option('--verbose', '-v', is_flag=True)
def mycommand(verbose):
    if verbose:
        click.echo('Verbose mode enabled')

    click.echo('Doing work...')

    if verbose:
        click.echo('Work complete!')
```

### Input Prompts

```python
name = click.prompt('Please enter your name')
password = click.prompt('Password', hide_input=True)
confirm = click.confirm('Do you want to continue?')
```

## Deployment

### PyPI Publication

1. Update version in `pyproject.toml`
2. Build package: `python -m build`
3. Upload: `twine upload dist/*`

### Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install .

ENTRYPOINT ["{{project_name_snake}}"]
CMD ["--help"]
```

Build and run:

```bash
docker build -t {{project_name_snake}} .
docker run {{project_name_snake}} hello --name Docker
```

### GitHub Releases

The included GitHub Actions workflow automatically:
- Runs tests on push
- Can be extended to publish releases

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Add tests for new features
- Run `black` and `ruff` before committing
- Update documentation for new commands
- Follow existing code style

## Troubleshooting

### Command Not Found

If `{{project_name_snake}}` is not found after installation:

```bash
# Make sure you're in the virtual environment
which {{project_name_snake}}

# Or use python -m
python -m {{project_name_snake}}.cli --help

# Check installation
pip show {{project_name_snake}}
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .

# Or force reinstall
pip install --force-reinstall .
```

### Virtual Environment Issues

```bash
# Deactivate and recreate
deactivate
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Resources

- **Click Documentation**: https://click.palletsprojects.com/
- **Python Packaging**: https://packaging.python.org/
- **pytest Documentation**: https://docs.pytest.org/
- **pipx**: https://pypa.github.io/pipx/

## License

{{license}}

## Credits

Created with [Athena AI](https://github.com/jdpsl/Athena)
