# MCP (Model Context Protocol) Usage Guide

Athena now has full MCP client support with dynamic server management via slash commands!

## Quick Start

### 1. Add an MCP Server

```bash
/mcp-add test stdio python3 test_mcp_server.py
```

This will:
- ✅ Add the server to your config
- ✅ Connect immediately
- ✅ Discover and register all tools
- ✅ Make tools available to the agent

### 2. View Your MCP Servers

```bash
/mcp-list
```

Shows:
- Server name and status (● enabled / ○ disabled)
- Connection status (✓ connected / ✗ disconnected)
- Transport type (stdio or http)
- Command/URL details
- Available tools from each server

### 3. Use MCP Tools

Once connected, MCP tools appear with the prefix `server-name:tool-name`:

```bash
# Ask the agent to use them
> Use the test:echo tool to echo "Hello MCP!"
```

The agent can now use `test:echo` and `test:add` just like built-in tools!

### 4. Save Configuration

```bash
/save
```

Saves all MCP servers to `~/.athena/config.json` so they auto-load on next startup.

## All MCP Commands

### `/mcp-list`
List all configured MCP servers with their status and tools.

### `/mcp-add <name> <transport> <command/url> [args...]`
Add and connect to a new MCP server.

**Examples:**

```bash
# Stdio transport (subprocess)
/mcp-add test stdio python3 test_mcp_server.py
/mcp-add postgres stdio python -m mcp_server_postgres
/mcp-add filesystem stdio python -m mcp_server_filesystem /path/to/directory

# HTTP transport (remote server)
/mcp-add api http http://localhost:8000/mcp
```

### `/mcp-remove <name>`
Remove an MCP server (disconnects and removes all tools).

```bash
/mcp-remove test
```

### `/mcp-enable <name>`
Enable a disabled server (connects immediately).

```bash
/mcp-enable test
```

### `/mcp-disable <name>`
Disable an enabled server (disconnects and removes tools from registry).

```bash
/mcp-disable test
```

## Complete Example Session

```bash
$ athena

> /mcp-list
No MCP servers configured

> /mcp-add test stdio python3 test_mcp_server.py
✓ Added MCP server: test
Connecting to test...
✓ Connected successfully!
   Tools available: test:echo, test:add

> /mcp-list
MCP Servers:

● test (stdio) [✓]
   Command: python3 test_mcp_server.py
   Tools: test:echo, test:add

> /tools
Available Tools:
  • Read: Reads a file from the filesystem
  • Write: Writes a file to the filesystem
  ...
  • test:echo: [MCP:test] Echo back the input message
  • test:add: [MCP:test] Add two numbers together

> Use test:add to add 5 and 3
[Agent uses test:add tool]
Result: 5 + 3 = 8

> /save
✓ Settings saved to ~/.athena/config.json
  Model: local-model
  API Base: http://localhost:1234/v1
  API Key: Set
  Temperature: 0.7
  MCP Servers: 1 saved

> /exit
```

## Configuration File Format

### config.yaml
```yaml
mcp:
  enabled: true
  servers:
    - name: test
      transport: stdio
      command: python3
      args: ["test_mcp_server.py"]
      enabled: true

    - name: postgres
      transport: stdio
      command: python
      args: ["-m", "mcp_server_postgres"]
      env:
        DATABASE_URL: "postgresql://localhost/mydb"
      enabled: false
```

### ~/.athena/config.json (auto-generated with /save)
```json
{
  "model": "local-model",
  "api_base": "http://localhost:1234/v1",
  "api_key": "...",
  "temperature": 0.7,
  "mcp_servers": [
    {
      "name": "test",
      "transport": "stdio",
      "command": "python3",
      "args": ["test_mcp_server.py"],
      "env": {},
      "url": null,
      "enabled": true,
      "timeout": 30
    }
  ]
}
```

## Popular MCP Servers

### Official MCP Servers

Install from the official MCP servers repository:

```bash
# Filesystem server
pip install mcp-server-filesystem
/mcp-add fs stdio python -m mcp_server_filesystem /path/to/root

# Postgres database
pip install mcp-server-postgres
/mcp-add postgres stdio python -m mcp_server_postgres

# Git operations
pip install mcp-server-git
/mcp-add git stdio python -m mcp_server_git /path/to/repo

# GitHub integration
pip install mcp-server-github
/mcp-add github stdio python -m mcp_server_github
```

### Community Servers

Search for MCP servers on GitHub:
- `github.com/modelcontextprotocol/servers`
- Search: "mcp-server-*"

## Dynamic Reconnection

All MCP commands support **dynamic reconnection**:

- `/mcp-add` → Connects immediately
- `/mcp-enable` → Reconnects immediately
- `/mcp-disable` → Disconnects and removes tools
- `/mcp-remove` → Disconnects permanently

No restart required! Add/remove servers on the fly.

## Best Practices

1. **Test first**: Add servers, test them, then `/save`
2. **Disable unused**: Use `/mcp-disable` for servers you're not using
3. **Use /mcp-list**: Check connection status before debugging
4. **Save often**: `/save` after adding servers you want to keep
5. **Check tools**: Use `/tools` to verify MCP tools are registered

## Troubleshooting

### Server won't connect
```bash
> /mcp-add test stdio python3 wrong_server.py
✗ Failed to connect: [Errno 2] No such file or directory
Server added to config but not connected
```

**Solution**: Fix the command/path, then:
```bash
/mcp-remove test
/mcp-add test stdio python3 test_mcp_server.py
```

### Tools not showing up
```bash
> /tools
# No MCP tools listed
```

**Check**:
```bash
> /mcp-list
# Look for [✗] (not connected)
```

**Solution**:
```bash
/mcp-enable server-name
```

### Server keeps disconnecting

Check server logs or increase timeout:
```yaml
mcp:
  servers:
    - name: slow-server
      timeout: 60  # Increase from default 30s
```

## Advanced: HTTP Transport

For remote MCP servers:

```bash
# Start a remote MCP server (example)
$ mcp-server-http --port 8000

# Connect from Athena
> /mcp-add remote http http://localhost:8000/mcp
✓ Connected successfully!
```

## Tips

- MCP tools are prefixed with `server-name:` to avoid conflicts
- Servers auto-load from `~/.athena/config.json` on startup
- Use descriptive server names (`postgres` not `db1`)
- Test servers with `/mcp-add` before adding to `config.yaml`
- The agent sees MCP tools as regular tools (seamless integration)

## Summary

MCP support in Athena gives you:

✅ **Dynamic server management** - Add/remove without restart
✅ **Persistent configuration** - Saves to ~/.athena/config.json
✅ **Both transports** - Stdio (local) and HTTP (remote)
✅ **Tool discovery** - Automatic registration
✅ **Clean integration** - MCP tools work like built-in tools
✅ **Status monitoring** - `/mcp-list` shows everything

Enjoy unlimited tool expansion through the MCP ecosystem! 🚀
