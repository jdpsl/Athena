"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from {{project_name_snake}}.cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that --help works."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "{{description}}" in result.output


def test_cli_version(runner):
    """Test that --version works."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_hello_default(runner):
    """Test hello command with default parameters."""
    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def test_hello_custom_name(runner):
    """Test hello command with custom name."""
    result = runner.invoke(cli, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output


def test_hello_count(runner):
    """Test hello command with count parameter."""
    result = runner.invoke(cli, ["hello", "--count", "3"])
    assert result.exit_code == 0
    assert result.output.count("Hello, World!") == 3


def test_hello_uppercase(runner):
    """Test hello command with uppercase flag."""
    result = runner.invoke(cli, ["hello", "--name", "Bob", "--uppercase"])
    assert result.exit_code == 0
    assert "HELLO, BOB!" in result.output


def test_hello_combined_options(runner):
    """Test hello command with multiple options."""
    result = runner.invoke(
        cli, ["hello", "--name", "Charlie", "--count", "2", "--uppercase"]
    )
    assert result.exit_code == 0
    assert result.output.count("HELLO, CHARLIE!") == 2


def test_hello_short_options(runner):
    """Test hello command with short option flags."""
    result = runner.invoke(cli, ["hello", "-n", "Dave", "-c", "2"])
    assert result.exit_code == 0
    assert result.output.count("Hello, Dave!") == 2


def test_hello_help(runner):
    """Test hello command help."""
    result = runner.invoke(cli, ["hello", "--help"])
    assert result.exit_code == 0
    assert "Say hello to NAME" in result.output
    assert "--name" in result.output
    assert "--count" in result.output


def test_invalid_command(runner):
    """Test that invalid commands show error."""
    result = runner.invoke(cli, ["nonexistent"])
    assert result.exit_code != 0
    assert "Error" in result.output or "No such command" in result.output
