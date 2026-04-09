# DrissionPage MCP

`DrissionPage MCP` is a general-purpose MCP server for local LLM agents that need browser automation over `stdio`.

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run drissionpage-mcp
```

## Notes

- v0 ships only the safe core browser tools and introspection tools.
- Dangerous capabilities such as browser attach and arbitrary JavaScript execution are intentionally deferred.
- Review the upstream `DrissionPage` usage terms before distributing this project or using it commercially.
