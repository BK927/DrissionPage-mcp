from __future__ import annotations

from pathlib import Path

import pytest

from drissionpage_mcp import server as server_module
from drissionpage_mcp.config import ConfigError


def test_main_exits_with_code_2_on_config_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    malformed = tmp_path / "drissionpage_mcp.toml"
    malformed.write_text("this = is = not = toml", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        server_module.main()

    assert exit_info.value.code == 2
    captured = capsys.readouterr()
    assert "drissionpage-mcp" in captured.err
    assert "Failed to parse config" in captured.err


def test_load_config_then_main_propagates_other_errors_as_is(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_path: str | None) -> None:
        raise RuntimeError("unexpected")

    monkeypatch.setattr(server_module, "load_config", boom)

    with pytest.raises(RuntimeError, match="unexpected"):
        server_module.main()


def test_main_calls_close_all_on_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class StubServer:
        def run(self) -> None:
            calls.append("run")

    class StubRegistry:
        def close_all(self) -> None:
            calls.append("close_all")

    class StubDeps:
        registry = StubRegistry()

    def fake_build_server(_config: object) -> tuple[StubServer, StubDeps]:
        return StubServer(), StubDeps()

    monkeypatch.setattr(server_module, "build_server", fake_build_server)
    monkeypatch.setattr(server_module, "load_config", lambda _path: object())

    server_module.main()

    assert calls == ["run", "close_all"]


def test_main_calls_close_all_even_when_run_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class StubServer:
        def run(self) -> None:
            calls.append("run")
            raise RuntimeError("run failed")

    class StubRegistry:
        def close_all(self) -> None:
            calls.append("close_all")

    class StubDeps:
        registry = StubRegistry()

    def fake_build_server(_config: object) -> tuple[StubServer, StubDeps]:
        return StubServer(), StubDeps()

    monkeypatch.setattr(server_module, "build_server", fake_build_server)
    monkeypatch.setattr(server_module, "load_config", lambda _path: object())

    with pytest.raises(RuntimeError, match="run failed"):
        server_module.main()

    assert calls == ["run", "close_all"]


def test_config_error_inherits_from_exception() -> None:
    assert issubclass(ConfigError, Exception)
