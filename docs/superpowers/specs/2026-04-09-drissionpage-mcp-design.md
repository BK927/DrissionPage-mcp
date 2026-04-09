# DrissionPage MCP Server Design

**Date:** 2026-04-09

## Goal

Build a general-purpose MCP server for LLM agents on top of `DrissionPage` that feels easy to use like a standard browser automation server, while still exposing the strongest `DrissionPage` capabilities through optional extensions.

## Why This Exists

`DrissionPage` is strong at practical browser control, existing browser reuse, tab handling, downloads, and automation ergonomics. A good MCP server should preserve those strengths without forcing agents to learn `DrissionPage`-specific concepts before they can do basic work.

The server should therefore present:

- a predictable, agent-friendly core tool surface
- a smaller set of `DrissionPage` extension tools
- a safe-by-default execution model suitable for general-purpose agent use

## Primary Users

- LLM agents that need browser automation through MCP
- humans configuring those agents for local browser tasks

## Non-Goals

- designing a workflow-specific automation server for one website or business process
- exposing every `DrissionPage` API 1:1 through MCP
- optimizing the first version for remote multi-tenant hosting
- supporting every advanced browser/network feature in the initial release

## Product Shape

The server is a hybrid of two ideas:

1. A general-purpose browser MCP with intuitive tools such as navigation, clicking, typing, waiting, extraction, and screenshots.
2. A `DrissionPage`-specific extension layer for advanced capabilities such as attaching to an existing browser, download tracking, stronger session reuse, and deeper DOM handling.

This keeps the default experience simple while still making the project meaningfully better than a generic browser wrapper.

## Recommended Transport

The first version should support `stdio` only.

Reasons:

- easiest path for local agent integration
- smallest implementation surface for v0
- simplest operational model during stabilization

The code structure should keep transport-specific concerns isolated so `Streamable HTTP` can be added later without redesigning the core browser services.

## Architecture

The server should be split into four layers.

### 1. MCP Tool Layer

This layer defines the actual MCP tools, schemas, descriptions, and response shapes. It should be optimized for discoverability and predictable naming, not for mirroring internal `DrissionPage` terminology.

Responsibilities:

- define tool names and argument schemas
- validate and normalize agent input
- call service-layer operations
- convert internal errors into structured MCP results

### 2. Browser Service Layer

This layer manages browser lifecycle, sessions, tabs, timeouts, and policy-aware actions.

Responsibilities:

- create and destroy sessions
- provide access to the default persistent session
- create optional ephemeral sessions
- resolve page or tab targets
- coordinate downloads, waits, and action execution

### 3. Drission Adapter Layer

This layer wraps `DrissionPage` objects such as browser, page, tab, and element handles behind narrower project-specific interfaces.

Responsibilities:

- translate project actions into `DrissionPage` calls
- isolate version-specific `DrissionPage` behavior
- shield upper layers from library-specific object shapes

### 4. Safety and Policy Layer

This layer determines whether an action is allowed and how it should be constrained.

Responsibilities:

- safe mode enforcement
- dangerous feature gating
- timeout defaults
- download path restrictions
- optional domain allowlist checks
- upload path restrictions if uploads are added

## Session Model

The server should support both persistent and ephemeral browser sessions.

### Default Behavior

- Start with one default persistent browser session.
- If a tool call does not specify `session_id`, it uses the default session.
- The default session is intended for normal multi-step agent work such as logging in, navigating, and continuing tasks across calls.
- If startup persistence is enabled, the default session is created automatically during server startup.

### Optional Behavior

- Browser-related tools may accept `session_id` to target a specific session.
- The server should expose `session_create` to create a new session for isolated work.
- `session_create` should accept a mode flag so operators or agents can request `ephemeral` or `persistent` sessions when policy allows it.
- The server should expose `session_close` so non-default sessions can be closed explicitly when a task is done.

### Why This Model

This gives agents a low-friction default while still supporting isolation when needed for testing, risky actions, or independent workflows.

## Tool Surface

Tools should be grouped into three categories.

### Core Tools

These are the default, general-purpose tools any agent should understand quickly.

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

Design rules for core tools:

- use simple names that feel familiar to agent authors
- avoid `DrissionPage`-specific vocabulary unless necessary
- return compact, structured results that support next-step planning

### Extended Tools

These expose the parts that make `DrissionPage` especially valuable.

- `browser_attach`
- `browser_tabs`
- `download_wait`
- `cookies_export`
- `cookies_import`
- `storage_export`
- `run_js`
- `page_get_dom_snapshot`

Design rules for extended tools:

- keep them discoverable but clearly optional
- document policy requirements for dangerous actions
- prefer structured results over raw object dumps

### Introspection Tools

These help agents understand the server they are connected to.

- `server_get_capabilities`
- `server_get_policy`
- `browser_get_state`

These tools are especially useful for general-purpose agents because they reduce guessing and allow policy-aware behavior.

## Naming Strategy

The public API should be optimized for agent inference.

Use:

- `page_navigate`
- `element_click`
- `wait_for_element`

Avoid:

- raw library names that assume `DrissionPage` familiarity
- overloaded tools with too many unrelated modes
- leaking internal object types into tool contracts

## Response Model

Tool results should be consistent and structured.

Recommended baseline fields:

```json
{
  "ok": true,
  "message": "Navigated successfully",
  "session_id": "default",
  "tab_id": "tab-1",
  "url": "https://example.com",
  "elapsed_ms": 412
}
```

Recommended error shape:

```json
{
  "ok": false,
  "error_code": "ELEMENT_NOT_FOUND",
  "message": "No element matched selector: text=Login",
  "retryable": true,
  "session_id": "default",
  "tab_id": "tab-1",
  "url": "https://example.com/login"
}
```

This gives agents enough context to decide whether to retry, inspect the page, or change strategy.

## Safety Model

The server should default to `safe` mode.

### Safe Mode Defaults

- `run_js` disabled
- browser attach disabled or limited to explicit local opt-in
- file upload disabled until path restrictions are implemented
- downloads allowed only into a configured directory
- per-tool default timeouts enabled
- optional domain restrictions available through configuration

### Configuration Direction

Configuration should be externalized so the operator can decide what to allow without code changes.

Example:

```toml
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

### Why This Matters

A general-purpose agent server must assume the connected model may try broad or risky actions. Safety defaults should make the easy path the safe path.

## Internal Components

Recommended internal responsibilities:

- `BrowserRegistry`: create, store, resolve, and close sessions
- `BrowserSession`: hold one browser instance and its session-specific policy state
- `PageService`: page navigation, extraction, and interaction workflows
- `DownloadService`: download waiting and file result tracking
- `PolicyEngine`: permission checks and path/domain enforcement
- `DrissionBrowserAdapter`: browser startup, attach, and tab enumeration
- `DrissionPageAdapter`: page-level actions and extraction
- `DrissionElementAdapter`: element lookup and interaction helpers

The important boundary is that only adapter classes should know the raw `DrissionPage` object model.

## Error Model

The project should standardize a small set of error codes early.

Recommended codes:

- `BROWSER_LAUNCH_FAILED`
- `SESSION_NOT_FOUND`
- `TAB_NOT_FOUND`
- `NAVIGATION_FAILED`
- `ELEMENT_NOT_FOUND`
- `ACTION_TIMEOUT`
- `DOWNLOAD_TIMEOUT`
- `POLICY_BLOCKED`
- `UNSUPPORTED_OPERATION`

These should be emitted consistently across tools and mapped into structured MCP responses.

## Observability

The server should include lightweight observability from the start.

Minimum needs:

- structured logs for tool start, completion, and failure
- elapsed time capture for each tool call
- session and tab identifiers in logs
- policy rejection logging

This is important both for debugging and for understanding how agents actually use the server.

## Testing Strategy

Testing should be split into four layers.

### Unit Tests

Cover:

- policy checks
- argument normalization
- error translation
- session registry behavior

### Integration Tests

Cover:

- MCP tool invocation through the tool layer
- service wiring and result structure
- safety gating behavior

### Browser E2E Tests

Cover:

- navigation
- element interaction
- text extraction
- screenshot capture
- download waiting

These tests should prefer local deterministic test pages instead of external websites to reduce flakiness.

### Contract Tests

Cover:

- tool names
- schema stability
- required result fields
- error response shape

## Phased Delivery

### v0

- `stdio` transport
- default persistent session
- optional ephemeral sessions
- core tool set
- safe mode defaults
- structured responses
- basic screenshots and text extraction

### v1

- browser attach
- tab management
- cookies import/export
- download waiting
- stronger session state inspection

### v2

- `Streamable HTTP` transport
- richer DOM snapshotting
- optional network-related features
- more advanced resources or prompts if useful

## Risks and Constraints

### 1. Library Policy and Usage Terms

The `DrissionPage` repository README includes restrictive usage language centered on legal, non-harmful, and non-commercial use. Before public distribution or commercial use of this MCP server, the operator should review `DrissionPage` licensing and usage terms carefully.

### 2. Browser Environment Variability

`DrissionPage` depends on a local Chromium-family browser environment. Startup and attach behavior may vary by operating system and user setup.

### 3. Agent Misuse Risk

A general-purpose agent can attempt actions beyond the operator's intent. Safe defaults and explicit opt-in controls are therefore part of the core design, not an optional extra.

## Recommended Repository Structure

```text
DrissionPage-mcp/
  pyproject.toml
  README.md
  src/drissionpage_mcp/
    __init__.py
    server.py
    config.py
    models.py
    errors.py
    policies.py
    tools/
      core.py
      extended.py
      introspection.py
    services/
      browser_registry.py
      browser_session.py
      page_service.py
      download_service.py
    adapters/
      drission_browser.py
      drission_page.py
      drission_element.py
  tests/
    unit/
    integration/
    e2e/
  docs/
    superpowers/
      specs/
      plans/
```

## Decision Summary

The recommended first implementation is:

- a `stdio` MCP server
- one default persistent browser session
- optional ephemeral sessions
- a clean core browser tool set
- a smaller `DrissionPage` extension tool set
- safe mode enabled by default
- structured responses, errors, and logs from the first release

This balances ease of use for general-purpose agents with the practical strengths that make `DrissionPage` worth choosing in the first place.
