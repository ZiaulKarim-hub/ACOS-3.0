---
name: mcp-setup
description: Guidance for configuring MCP (Model Context Protocol) servers in ACOS projects. Covers configuration conventions, project-specific vs framework-level MCPs, and agent access patterns.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# MCP Setup Skill

## Purpose

This skill provides guidance for adding MCP (Model Context Protocol) servers to an ACOS project. MCP servers extend agent capabilities with external integrations — GitHub, databases, linting tools, security scanners, and more.

## When to Use

Apply this skill when:
- Adding MCP server integrations to a project
- Configuring agent access to MCP-provided tools
- Setting up project-specific vs framework-level MCP servers
- Troubleshooting MCP connectivity

## MCP Configuration in Claude Code

MCP servers are configured in `.claude/settings.local.json` under the `mcpServers` key.

### Configuration Structure

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "API_KEY": "..."
      }
    }
  }
}
```

### Configuration Locations

| File | Scope | Use For |
|------|-------|---------|
| `.claude/settings.local.json` | Project | Project-specific MCPs (this project's GitHub, DB, etc.) |
| `~/.claude/settings.json` | User | Personal MCPs used across all projects |

## ACOS Conventions for MCP Servers

### Framework-Level vs Project-Level

**Framework-level MCPs** (configured in the ACOS framework itself):
- Should be rare — ACOS is toolchain-agnostic
- Only add MCPs that benefit all ACOS projects regardless of domain
- Example: A GitHub MCP if all projects use GitHub

**Project-level MCPs** (configured in the target project):
- The normal case — most MCPs are project-specific
- Configured in the target project's `.claude/settings.local.json`
- Example: A PostgreSQL MCP for a project using Postgres

### Agent Access to MCP Tools

MCP-provided tools are automatically available to agents that have matching tool permissions. Key considerations:

1. **Reviewer agents** have restricted tool lists — MCP tools that write data should NOT be available to reviewers
2. **Developer agents** can use MCP tools for implementation (e.g., database queries, API calls)
3. **Architect agents** can use MCP tools for research and planning

### Security Considerations

- **Never commit API keys** — use environment variables or `.env` files
- **Scope MCP access** — if an MCP provides write operations, ensure only appropriate agents can access it
- **Audit MCP usage** — MCP tool calls appear in the evidence trail via post-write-evidence.sh

## Skill Protocol

### Phase 1: Identify Needed Integrations

1. What external services does the project interact with?
2. Which agents need access to these services?
3. Are there existing MCP servers available for these services?

### Phase 2: Configure MCP Servers

1. Add server configuration to the appropriate settings file
2. Set up required environment variables
3. Verify the server starts and responds

### Phase 3: Validate Agent Access

1. Confirm agents can discover MCP-provided tools
2. Verify reviewer agents cannot access write-capable MCP tools
3. Test tool calls work end-to-end

## Common MCP Servers

| Server | Use Case | Package |
|--------|----------|---------|
| GitHub | PR management, issue tracking | `@modelcontextprotocol/server-github` |
| Filesystem | Extended file operations | `@modelcontextprotocol/server-filesystem` |
| PostgreSQL | Database queries | `@modelcontextprotocol/server-postgres` |
| Brave Search | Web search | `@modelcontextprotocol/server-brave-search` |
| Memory | Persistent knowledge graph | `@modelcontextprotocol/server-memory` |

Check the MCP server registry for additional options.

## Troubleshooting

| Issue | Check |
|-------|-------|
| MCP server not starting | Verify `command` and `args` are correct, check `npx` path |
| Tools not appearing | Restart Claude Code after config changes |
| Permission errors | Check `env` variables are set, API keys are valid |
| Timeout errors | Increase timeout in server config if supported |

---

*MCP Setup Skill - Extending agent capabilities with external integrations.*
