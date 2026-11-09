import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from alpaca.cli.main import app
from alpaca.cli.tools import install_origin
import importlib

sync_module = importlib.import_module("alpaca.cli.sync")


@pytest.mark.parametrize("origin, allowed", [
  (None, False),  # Package index / conda installation.
  ({"url": "file:///tmp/alpaca2.whl", "archive_info": {}}, False),
  ({"url": "https://example.com/alpaca2.tar.gz", "archive_info": {}}, False),
  ({"url": "file:///repo", "dir_info": {}}, True),
  ({"url": "file:///repo", "dir_info": {"editable": True}}, True),
  ({"url": "https://example.com/repo.git", "vcs_info": {"vcs": "git"}}, True),
  ({"url": "https://example.com/repo", "dir_info": {}}, False),
  ([], False),
])
def test_install_origin(origin, allowed, monkeypatch):
  monkeypatch.setattr(
    install_origin.importlib.metadata, "distribution",
    lambda name: SimpleNamespace(read_text=lambda path: json.dumps(origin) if origin else None),
  )
  assert install_origin.sync_allowed() is allowed


def test_malformed_metadata_blocks_sync(monkeypatch):
  monkeypatch.setattr(
    install_origin.importlib.metadata, "distribution",
    lambda name: SimpleNamespace(read_text=lambda path: "broken json"),
  )
  assert not install_origin.sync_allowed()


def test_release_sync_never_accesses_hardware(monkeypatch):
  monkeypatch.setattr(sync_module, "sync_allowed", lambda: False)
  monkeypatch.setattr(sync_module, "get_pico", lambda role: pytest.fail("Hardware accessed"))
  monkeypatch.setattr(sync_module, "collect_files", lambda role: pytest.fail("Files collected"))
  result = CliRunner().invoke(app, ["sync", "--connect", "student"])
  assert result.exit_code == 1
  assert "Sync is disabled in release installations" in result.output


def test_source_sync_still_uploads_both_boards(monkeypatch):
  uploaded, reset = [], []
  monkeypatch.setattr(sync_module, "sync_allowed", lambda: True)
  monkeypatch.setattr(sync_module, "collect_files", lambda role: role)
  monkeypatch.setattr(sync_module, "get_pico", lambda role: {"board": SimpleNamespace(
    sync=lambda src, **kwargs: uploaded.append(src),
    soft_reset=lambda: reset.append(role),
  )})
  result = CliRunner().invoke(app, ["sync"])
  assert result.exit_code == 0, result.output
  assert uploaded == ["student", "helper"]
  assert reset == ["student", "helper"]
