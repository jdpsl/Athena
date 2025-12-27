"""Test that all modules can be imported successfully."""

import pytest


def test_models_import():
    """Test model imports."""
    from athena.models import (
        Message,
        Role,
        ToolCall,
        ToolResult,
        Tool,
        ToolParameter,
        Job,
        JobStatus,
        AthenaConfig,
        LLMConfig,
        AgentConfig,
        ToolsConfig,
    )
    assert Message is not None
    assert Role is not None
    assert Job is not None


def test_agent_import():
    """Test agent imports."""
    from athena.agent import MainAgent, SubAgent, ThinkingMode, AgentType

    assert MainAgent is not None
    assert SubAgent is not None
    assert ThinkingMode is not None
    assert AgentType is not None


def test_tools_import():
    """Test tool imports."""
    from athena.tools import (
        ToolRegistry,
        ReadTool,
        WriteTool,
        EditTool,
        GlobTool,
        GrepTool,
        BashTool,
        TodoWriteTool,
        TaskTool,
    )

    assert ToolRegistry is not None
    assert ReadTool is not None
    assert TaskTool is not None


def test_llm_import():
    """Test LLM imports."""
    from athena.llm import LLMClient, ThinkingInjector

    assert LLMClient is not None
    assert ThinkingInjector is not None


def test_queue_import():
    """Test queue imports."""
    from athena.queue import SQLiteJobQueue

    assert SQLiteJobQueue is not None


def test_hooks_import():
    """Test hooks imports."""
    from athena.hooks import HookManager, HookType

    assert HookManager is not None
    assert HookType is not None


def test_commands_import():
    """Test commands imports."""
    from athena.commands import CommandLoader

    assert CommandLoader is not None
