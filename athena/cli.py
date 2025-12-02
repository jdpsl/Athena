"""CLI interface for Athena."""

import asyncio
import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from athena.models.config import AthenaConfig
from athena.agent.main_agent import MainAgent
from athena.tools.base import ToolRegistry
from athena.tools.file_ops import ReadTool, WriteTool, EditTool
from athena.tools.search import GlobTool, GrepTool
from athena.tools.bash import BashTool
from athena.tools.todo import TodoWriteTool
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.hooks.manager import HookManager
from athena.commands.loader import CommandLoader
from athena.config_manager import PersistentConfigManager


console = Console()


class AthenaSession:
    """Athena interactive session."""

    def __init__(self, config: AthenaConfig):
        """Initialize session.

        Args:
            config: Athena configuration
        """
        self.config = config
        self.job_queue: SQLiteJobQueue | None = None
        self.agent: MainAgent | None = None
        self.tool_registry = ToolRegistry()
        self.hook_manager = HookManager()
        self.command_loader = CommandLoader()
        self.config_manager = PersistentConfigManager()

    async def initialize(self) -> None:
        """Initialize the session."""
        # Initialize job queue
        self.job_queue = SQLiteJobQueue()
        await self.job_queue.initialize()

        # Register basic tools first
        self._register_tools()

        # Register Task tool (needs job queue)
        from athena.tools.task import TaskTool
        task_tool = TaskTool(
            config=self.config,
            tool_registry=self.tool_registry,
            job_queue=self.job_queue,
        )
        self.tool_registry.register(task_tool)

        # Initialize agent
        self.agent = MainAgent(self.config, self.tool_registry, self.job_queue)

        # Pass LLM client to WebFetch for AI-enhanced extraction
        if hasattr(self, '_web_fetch_tool'):
            self._web_fetch_tool.llm_client = self.agent.llm_client

        # Load slash commands
        self.command_loader.load_commands()

        # Add system prompt
        self.agent.add_system_message(self._get_system_prompt())

    def _register_tools(self) -> None:
        """Register all available tools."""
        from athena.tools.web import WebSearchTool, WebFetchTool
        from athena.tools.user_interaction import AskUserQuestionTool
        from athena.tools.git import GitStatusTool, GitDiffTool, GitCommitTool, GitLogTool, GitBranchTool
        from athena.tools.file_system import DeleteFileTool, MoveFileTool, CopyFileTool, ListDirTool, MakeDirTool

        # File operations
        self.tool_registry.register(ReadTool())
        self.tool_registry.register(WriteTool())
        self.tool_registry.register(EditTool())
        self.tool_registry.register(DeleteFileTool())
        self.tool_registry.register(MoveFileTool())
        self.tool_registry.register(CopyFileTool())
        self.tool_registry.register(ListDirTool())
        self.tool_registry.register(MakeDirTool())

        # Search tools
        self.tool_registry.register(GlobTool())
        self.tool_registry.register(GrepTool())

        # Execution
        self.tool_registry.register(BashTool(timeout_ms=self.config.tools.bash_timeout))

        # Task management
        self.tool_registry.register(TodoWriteTool())

        # Git tools
        self.tool_registry.register(GitStatusTool())
        self.tool_registry.register(GitDiffTool())
        self.tool_registry.register(GitCommitTool())
        self.tool_registry.register(GitLogTool())
        self.tool_registry.register(GitBranchTool())

        # Web tools
        self._web_search_tool = WebSearchTool(search_api=self.config.tools.search_api)
        self._web_search_tool.brave_api_key = self.config.tools.brave_api_key
        self._web_search_tool.google_api_key = self.config.tools.google_api_key
        self._web_search_tool.google_cx = self.config.tools.google_cx
        self._web_search_tool.searxng_url = self.config.tools.searxng_url
        self.tool_registry.register(self._web_search_tool)
        self._web_fetch_tool = WebFetchTool()  # Gets LLM client after agent is created
        self.tool_registry.register(self._web_fetch_tool)

        # User interaction
        self.tool_registry.register(AskUserQuestionTool())

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent.

        Returns:
            System prompt
        """
        return """You are Athena, an AI coding assistant. You help users with software engineering tasks.

You have access to tools for:
- File operations: Read, Write, Edit, Delete, Move, Copy, ListDir, MakeDir
- Search: Glob (find files by pattern), Grep (search file contents with regex)
- Execution: Bash (run shell commands - tests, builds, package management, git add, etc.)
- Git: GitStatus, GitDiff, GitCommit, GitLog, GitBranch
- Task management: TodoWrite for tracking multi-step tasks
- Agent spawning: Task tool to spawn specialized sub-agents for complex work
- Web access: WebSearch (internet search), WebFetch (fetch web pages)
- User interaction: AskUserQuestion (ask clarifying questions)

File Operations:
- Read - View file contents (ALWAYS use before Edit or Write!)
- Edit - Make precise changes to existing files (requires Read first)
- Write - Create new files or completely overwrite existing ones
- DeleteFile - Remove files/directories (use with caution!)
- MoveFile - Move or rename files
- CopyFile - Duplicate files/directories
- ListDir - List directory contents with details (better than 'ls')
- MakeDir - Create directories
IMPORTANT: You MUST Read a file before using Edit or Write on it!

Search Tools - Use for finding files and content:
- Glob - Find files by pattern:
  Examples: "**/*.py" (all Python files), "src/**/*.ts" (TypeScript in src)
  Use when: Finding files by name, extension, or path pattern
- Grep - Search file contents with regex:
  Examples: pattern="def main", pattern="class.*User", pattern="TODO:"
  Use when: Finding where code/text exists, searching for functions/classes
  Can use with -i for case-insensitive, output_mode for different views

Bash Tool - Use for shell operations:
- Running tests: pytest, npm test, cargo test
- Installing dependencies: pip install, npm install, cargo build
- Building projects: npm run build, make, go build
- Git staging: git add <files> (required before GitCommit)
- Package management: pip, npm, cargo, apt
- System commands: ls, find, grep (when specialized tools won't work)
- File manipulation that needs shell features
IMPORTANT: Proactively use Bash for these tasks - don't ask the user first!

Git Tools (use these for viewing/committing, but use Bash for 'git add'):
- GitStatus - See current changes, staged files, branch info
- GitDiff - View diffs (staged or unstaged)
- GitCommit - Create commits (use Bash to 'git add' files first!)
- GitLog - View commit history
- GitBranch - List, create, switch, or delete branches

User Interaction:
- AskUserQuestion - When you need clarification, ask the user!
  Examples: "Which approach?", "What should X be?", "Is this correct?"

Task Management:
- TodoWrite - Track progress on multi-step tasks:
  Use when: Task has 3+ steps, user gives multiple requests, complex planning needed
  Creates visible todo list so user can see your progress
  IMPORTANT: Use proactively! Update status as you work (pending → in_progress → completed)
  Examples: "Add dark mode" (multiple files), "Fix 5 bugs" (multiple items)

The Task tool lets you spawn specialized agents for complex work:
- Explore: Navigate and understand codebases
  Use when: User asks "where is X?", "how does Y work?", "find all Z"
  Example: "Where is authentication handled?" → spawn Explore agent
- Plan: Break down tasks into implementation steps
  Use when: Large features, architectural changes, unclear scope
  Example: "Add real-time updates" → spawn Plan agent to design approach
- code-reviewer: Review code quality and security
  Use when: After writing significant code, user asks for review
- test-runner: Run and analyze tests
  Use when: Need to run tests and debug failures
- general-purpose: Handle complex multi-step tasks
  Use when: Task requires multiple tools and careful coordination

Web Tools:
- WebSearch: Search the internet for information, documentation, examples
- WebFetch: Fetch and read content from URLs (converts HTML to clean text)
  - Simple mode: Just fetches and cleans the content
  - AI mode: Use extract_prompt parameter to extract specific information
- IMPORTANT: When using WebSearch, always include a "Sources:" section in your response with links

When working on tasks:
1. ALWAYS Read files before editing them (required for Edit/Write tools)
2. Use TodoWrite proactively for tasks with 3+ steps (helps user see progress)
3. Proactively use Bash for: tests, builds, installs, git add, shell operations
4. Use Search tools (Glob/Grep) to find files and code before making assumptions
5. Use AskUserQuestion if you're unsure about approach or details
6. Use specialized Git tools (GitStatus, GitDiff, etc.) for viewing git state
7. Use Task tool to spawn sub-agents for complex exploration or planning
8. Use WebSearch and WebFetch when you need docs or encounter unfamiliar tech
9. Use file operation tools (Read, Write, Edit) instead of cat/echo for file ops
10. Always test your changes by running tests with Bash
11. Be thorough and careful with code changes

You are running in a persistent session. The user is working on a coding project."""

    async def run_interactive(self) -> None:
        """Run interactive REPL."""
        console.print(
            Panel.fit(
                "[bold cyan]Athena AI[/bold cyan]\n"
                "Open-source AI agent for coding assistance\n"
                "Type [bold]/help[/bold] for commands, [bold]/exit[/bold] to quit",
                border_style="cyan",
            )
        )

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if not user_input.strip():
                    continue

                # Handle built-in commands
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        continue

                # Expand slash commands
                expanded_input = self.command_loader.expand_command(user_input)

                # Run agent
                console.print("\n[bold cyan]Athena[/bold cyan]")
                response = await self.agent.run(expanded_input)

                # Display response
                console.print(Markdown(response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                if self.config.debug:
                    import traceback

                    traceback.print_exc()

    async def _handle_command(self, command: str) -> bool:
        """Handle built-in commands.

        Args:
            command: Command string

        Returns:
            True if command was handled, False to continue processing
        """
        cmd = command.lower().split()[0]

        if cmd in ["/exit", "/quit"]:
            console.print("[cyan]Goodbye![/cyan]")
            if self.job_queue:
                await self.job_queue.close()
            exit(0)

        elif cmd == "/help":
            # Build help text with conditional commands
            brave_api_help = ""
            if self.config.tools.search_api == "brave":
                brave_api_help = "/braveapi [key] - Set Brave Search API key\n"

            console.print(
                Panel(
                    f"""[bold]Built-in Commands:[/bold]
/help - Show this help
/exit - Exit Athena
/clear - Clear conversation history
/config - Show current configuration
/model [name] - Show or set model
/api [url] - Show or set API base URL
/apikey [key] - Show or set API key
/temp [value] - Show or set temperature (0.0-1.0)
/fallback [on|off] - Toggle text-based tool calling fallback
/save - Save current settings to ~/.athena/config.json
/tools - List available tools
/commands - List slash commands

[bold]Web Search Commands:[/bold]
/use_brave - Use Brave Search API
/use_duckduckgo - Use DuckDuckGo (default, currently broken)
/use_searxng - Use SearXNG instance
{brave_api_help}
[bold]Examples:[/bold]
/model gpt-4
/api https://api.openai.com/v1
/apikey sk-1234567890abcdef
/temp 0.5
/fallback on
/use_brave
/save

[bold]Fallback Mode:[/bold]
Enable for models without native function calling support
Uses text format: TOOL[Name]{{"param": "value"}}

[bold]Persistent Settings:[/bold]
Settings saved with /save are automatically loaded on startup
Config location: ~/.athena/config.json

[bold]Custom Commands:[/bold]
Create .athena/commands/*.md files to define custom slash commands
""",
                    title="Athena Help",
                    border_style="cyan",
                )
            )
            return True

        elif cmd == "/clear":
            self.agent.clear_history()
            self.agent.add_system_message(self._get_system_prompt())
            console.print("[green]Conversation history cleared[/green]")
            return True

        elif cmd == "/config":
            api_status = ""
            if self.config.tools.search_api == "brave":
                api_status = f"\n[cyan]Brave API Key:[/cyan] {'Set' if self.config.tools.brave_api_key else 'Not set'}"
            elif self.config.tools.search_api == "google":
                api_status = f"\n[cyan]Google API Key:[/cyan] {'Set' if self.config.tools.google_api_key else 'Not set'}"
                api_status += f"\n[cyan]Google CX:[/cyan] {'Set' if self.config.tools.google_cx else 'Not set'}"
            elif self.config.tools.search_api == "searxng":
                api_status = f"\n[cyan]SearXNG URL:[/cyan] {self.config.tools.searxng_url or 'Not set'}"

            console.print(
                Panel(
                    f"[cyan]Model:[/cyan] {self.config.llm.model}\n"
                    f"[cyan]API Base:[/cyan] {self.config.llm.api_base}\n"
                    f"[cyan]Temperature:[/cyan] {self.config.llm.temperature}\n"
                    f"[cyan]Max Iterations:[/cyan] {self.config.agent.max_iterations}\n"
                    f"[cyan]Thinking Enabled:[/cyan] {self.config.agent.enable_thinking}\n"
                    f"[cyan]Fallback Mode:[/cyan] {self.config.agent.fallback_mode}\n"
                    f"[cyan]Search API:[/cyan] {self.config.tools.search_api}"
                    f"{api_status}",
                    title="Current Configuration",
                    border_style="cyan",
                )
            )
            return True

        elif cmd == "/model":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set model
                new_model = parts[1]
                self.config.llm.model = new_model
                # Update the LLM client with new model
                from athena.llm.thinking_injector import ThinkingInjector
                from athena.llm.client import LLMClient
                thinking_injector = ThinkingInjector(
                    enable_thinking=self.config.agent.enable_thinking,
                    thinking_budget=self.config.agent.thinking_budget,
                )
                self.agent.llm_client = LLMClient(self.config.llm, thinking_injector)
                console.print(f"[green]✓[/green] Model set to: [cyan]{new_model}[/cyan]")
            else:
                # Show current model
                console.print(f"[cyan]Current model:[/cyan] {self.config.llm.model}")
            return True

        elif cmd == "/api":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set API base
                new_api = parts[1]
                self.config.llm.api_base = new_api
                # Update the LLM client
                from athena.llm.thinking_injector import ThinkingInjector
                from athena.llm.client import LLMClient
                thinking_injector = ThinkingInjector(
                    enable_thinking=self.config.agent.enable_thinking,
                    thinking_budget=self.config.agent.thinking_budget,
                )
                self.agent.llm_client = LLMClient(self.config.llm, thinking_injector)
                console.print(f"[green]✓[/green] API base set to: [cyan]{new_api}[/cyan]")
            else:
                # Show current API base
                console.print(f"[cyan]Current API base:[/cyan] {self.config.llm.api_base}")
            return True

        elif cmd == "/temp":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set temperature
                try:
                    new_temp = float(parts[1])
                    if 0.0 <= new_temp <= 1.0:
                        self.config.llm.temperature = new_temp
                        console.print(f"[green]✓[/green] Temperature set to: [cyan]{new_temp}[/cyan]")
                    else:
                        console.print("[red]Error:[/red] Temperature must be between 0.0 and 1.0")
                except ValueError:
                    console.print("[red]Error:[/red] Temperature must be a number")
            else:
                # Show current temperature
                console.print(f"[cyan]Current temperature:[/cyan] {self.config.llm.temperature}")
            return True

        elif cmd == "/apikey":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set API key
                new_key = parts[1]
                self.config.llm.api_key = new_key
                # Update the LLM client
                from athena.llm.thinking_injector import ThinkingInjector
                from athena.llm.client import LLMClient
                thinking_injector = ThinkingInjector(
                    enable_thinking=self.config.agent.enable_thinking,
                    thinking_budget=self.config.agent.thinking_budget,
                )
                self.agent.llm_client = LLMClient(self.config.llm, thinking_injector)
                console.print(f"[green]✓[/green] API key set")
            else:
                # Show current API key (masked)
                if self.config.llm.api_key:
                    masked = self.config.llm.api_key[:8] + "..." if len(self.config.llm.api_key) > 8 else "***"
                    console.print(f"[cyan]Current API key:[/cyan] {masked}")
                else:
                    console.print("[yellow]No API key set[/yellow]")
            return True

        elif cmd == "/save":
            # Save current settings to ~/.athena/config.json
            settings = self.config_manager.get_current_settings(
                model=self.config.llm.model,
                api_base=self.config.llm.api_base,
                api_key=self.config.llm.api_key,
                temperature=self.config.llm.temperature,
                search_api=self.config.tools.search_api,
                brave_api_key=self.config.tools.brave_api_key,
                google_api_key=self.config.tools.google_api_key,
                google_cx=self.config.tools.google_cx,
                searxng_url=self.config.tools.searxng_url,
            )
            if self.config_manager.save(settings):
                console.print("[green]✓[/green] Settings saved to ~/.athena/config.json")
                console.print(f"  [cyan]Model:[/cyan] {settings['model']}")
                console.print(f"  [cyan]API Base:[/cyan] {settings['api_base']}")
                console.print(f"  [cyan]API Key:[/cyan] {'Set' if settings['api_key'] else 'Not set'}")
                console.print(f"  [cyan]Temperature:[/cyan] {settings['temperature']}")
                console.print(f"  [cyan]Search API:[/cyan] {settings['search_api']}")
            else:
                console.print("[red]Error:[/red] Failed to save settings")
            return True

        elif cmd == "/use_brave":
            self.config.tools.search_api = "brave"
            self._web_search_tool.search_api = "brave"
            console.print("[green]✓[/green] Switched to [bold]Brave Search API[/bold]")
            if not self.config.tools.brave_api_key:
                console.print("[yellow]⚠[/yellow] No Brave API key set. Use [cyan]/braveapi KEY[/cyan] to set it.")
                console.print("  Get a free API key at: https://brave.com/search/api/")
            else:
                console.print("  [dim]API key is configured[/dim]")
            return True

        elif cmd == "/use_duckduckgo":
            self.config.tools.search_api = "duckduckgo"
            self._web_search_tool.search_api = "duckduckgo"
            console.print("[green]✓[/green] Switched to [bold]DuckDuckGo[/bold]")
            console.print("[yellow]⚠[/yellow] Note: DuckDuckGo HTML scraping is currently broken due to CAPTCHA.")
            console.print("  Consider using Brave Search instead: [cyan]/use_brave[/cyan]")
            return True

        elif cmd == "/use_searxng":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set SearXNG URL
                url = parts[1]
                self.config.tools.searxng_url = url
                self._web_search_tool.searxng_url = url
                self.config.tools.search_api = "searxng"
                self._web_search_tool.search_api = "searxng"
                console.print(f"[green]✓[/green] Switched to [bold]SearXNG[/bold]")
                console.print(f"  [cyan]Instance URL:[/cyan] {url}")
            else:
                # Show usage
                if self.config.tools.searxng_url:
                    console.print("[yellow]Usage:[/yellow] /use_searxng [url]")
                    console.print(f"  [cyan]Current URL:[/cyan] {self.config.tools.searxng_url}")
                    console.print("  Or provide a new URL to change it")
                else:
                    console.print("[yellow]Usage:[/yellow] /use_searxng [url]")
                    console.print("  Example: /use_searxng http://localhost:8888")
                    console.print("  Learn more: https://docs.searxng.org/")
            return True

        elif cmd == "/braveapi":
            # Only available when Brave is selected
            if self.config.tools.search_api != "brave":
                console.print("[red]Error:[/red] /braveapi is only available when using Brave Search")
                console.print("  Use [cyan]/use_brave[/cyan] first to switch to Brave Search")
                return True

            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set Brave API key
                api_key = parts[1]
                self.config.tools.brave_api_key = api_key
                self._web_search_tool.brave_api_key = api_key
                console.print("[green]✓[/green] Brave API key set")
                console.print("  [dim]Use /save to persist this setting[/dim]")
            else:
                # Show current status
                if self.config.tools.brave_api_key:
                    masked = self.config.tools.brave_api_key[:8] + "..." if len(self.config.tools.brave_api_key) > 8 else "***"
                    console.print(f"[cyan]Current Brave API key:[/cyan] {masked}")
                else:
                    console.print("[yellow]No Brave API key set[/yellow]")
                    console.print("  Get a free key at: https://brave.com/search/api/")
            return True

        elif cmd == "/fallback":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set fallback mode
                value = parts[1].lower()
                if value in ['on', 'true', '1', 'yes']:
                    self.config.agent.fallback_mode = True
                    # Reinitialize agent with fallback parser
                    from athena.llm.fallback_parser import FallbackToolParser
                    self.agent.fallback_parser = FallbackToolParser()
                    # Re-inject system prompt with fallback instructions
                    if self.agent.messages and self.agent.messages[0].role.value == 'system':
                        original_prompt = self.agent.messages[0].content.split('\n\n## IMPORTANT: Tool Calling Format')[0]
                        self.agent.messages[0].content = self.agent.fallback_parser.inject_instructions(original_prompt)
                    console.print("[green]✓[/green] Fallback mode [bold]enabled[/bold]")
                    console.print("  [dim]Using text-based tool calling (TOOL[Name]{args})[/dim]")
                elif value in ['off', 'false', '0', 'no']:
                    self.config.agent.fallback_mode = False
                    self.agent.fallback_parser = None
                    # Restore system prompt without fallback instructions
                    if self.agent.messages and self.agent.messages[0].role.value == 'system':
                        self.agent.messages[0].content = self.agent.messages[0].content.split('\n\n## IMPORTANT: Tool Calling Format')[0]
                    console.print("[green]✓[/green] Fallback mode [bold]disabled[/bold]")
                    console.print("  [dim]Using native function calling[/dim]")
                else:
                    console.print("[red]Error:[/red] Use 'on' or 'off'")
            else:
                # Show current state
                status = "[green]enabled[/green]" if self.config.agent.fallback_mode else "[red]disabled[/red]"
                console.print(f"[cyan]Fallback mode:[/cyan] {status}")
                console.print("\n[dim]Fallback mode uses text-based tool calling for models")
                console.print("without native function calling support.[/dim]")
            return True

        elif cmd == "/tools":
            tools = self.tool_registry.list_tools()
            console.print("[bold cyan]Available Tools:[/bold cyan]")
            for tool in tools:
                console.print(f"  • [green]{tool.name}[/green]: {tool.description}")
            return True

        elif cmd == "/commands":
            commands = self.command_loader.list_commands()
            if commands:
                console.print("[bold cyan]Available Commands:[/bold cyan]")
                for cmd_name in commands:
                    console.print(f"  • /{cmd_name}")
            else:
                console.print("[yellow]No custom commands found[/yellow]")
            return True

        return False

    async def run_single_task(self, prompt: str) -> str:
        """Run a single task and return the result.

        Args:
            prompt: User prompt

        Returns:
            Agent response
        """
        response = await self.agent.run(prompt)
        if self.job_queue:
            await self.job_queue.close()
        return response

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.job_queue:
            await self.job_queue.close()


@click.command()
@click.option("-p", "--prompt", help="Single prompt to execute")
@click.option("--config", help="Path to config file")
@click.option("--model", help="Model name to use")
@click.option("--api-base", help="API base URL")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def main(prompt: str | None, config: str | None, model: str | None, api_base: str | None, debug: bool):
    """Athena - Open source AI agent for coding assistance."""

    # Load configuration
    if config and Path(config).exists():
        # Use specified config file
        athena_config = AthenaConfig.from_yaml(config)
    elif Path("config.yaml").exists():
        # Auto-detect config.yaml in current directory
        athena_config = AthenaConfig.from_yaml("config.yaml")
    else:
        # Fall back to environment variables
        athena_config = AthenaConfig.from_env()

    # Load saved settings from ~/.athena/config.json
    config_manager = PersistentConfigManager()
    saved_settings = config_manager.load()
    if saved_settings:
        console.print("[dim]Loading saved settings from ~/.athena/config.json[/dim]")
        config_manager.apply_to_config(athena_config, saved_settings)

    # Override with CLI args (these take precedence over saved settings)
    if model:
        athena_config.llm.model = model
    if api_base:
        athena_config.llm.api_base = api_base
    if debug:
        athena_config.debug = True

    # Run session
    async def run():
        session = AthenaSession(athena_config)
        await session.initialize()

        try:
            if prompt:
                # Single task mode
                response = await session.run_single_task(prompt)
                console.print(Markdown(response))
            else:
                # Interactive mode
                await session.run_interactive()
        finally:
            await session.cleanup()

    asyncio.run(run())


if __name__ == "__main__":
    main()
