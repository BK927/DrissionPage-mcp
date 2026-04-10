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

## Configuration

Create `drissionpage_mcp.toml` in the repository root when you want to override defaults.

```toml
server_name = "DrissionPage MCP"

[safety]
mode = "safe"
allow_run_js = false
allow_browser_attach = false
allow_file_upload = false
allow_download = true
download_dir = "./downloads"
default_timeout_ms = 10000

[browser]
persistent_on_startup = true
headless = false
```

## v0 Tools

- `session_create`
- `session_close`
- `page_navigate`
- `page_refresh`
- `page_go_back`
- `page_go_forward`
- `page_get_url`
- `page_get_html`
- `page_get_text`
- `page_screenshot`
- `element_find`
- `element_click`
- `element_type`
- `wait_for_element`
- `wait_time`
- `server_get_capabilities`
- `server_get_policy`
- `browser_get_state`

## Test

```bash
uv run pytest tests/unit tests/integration -v
uv run pytest tests/e2e/test_local_browser_flow.py -v
```

## Notes

- v0 ships only the safe core browser tools and introspection tools.
- Dangerous capabilities such as browser attach and arbitrary JavaScript execution are intentionally deferred.
- Review the upstream `DrissionPage` usage terms before distributing this project or using it commercially.
