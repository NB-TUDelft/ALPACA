import importlib.metadata
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_distribution_name_is_alpaca2():
  project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]

  assert project["name"] == "alpaca2"
  assert importlib.metadata.version(project["name"]) == project["version"]


def test_collect_files_uses_cwd_cache_and_board_libs(tmp_path, monkeypatch):
  from alpaca.cli.tools.cache import collect_files

  monkeypatch.chdir(tmp_path)

  src = collect_files("student")

  assert src == tmp_path / ".alpaca" / "student_root"
  assert (src / "link.py").exists()  # copied from the shared "common" board libs
  assert (src / "helper.py").exists()  # copied from the "student" board libs
  assert (src / "version.py").read_text() == (
    f'ALPACA_FW_VER="{importlib.metadata.version("alpaca2")}"'
  )


def test_generated_stubs_project_is_alpaca2_stubs(tmp_path, monkeypatch):
  from alpaca.cli.generate_stubs import generate_stubs_cmd

  monkeypatch.chdir(tmp_path)
  generate_stubs_cmd("student")

  generated = tomllib.loads(
    (tmp_path / ".alpaca" / "stubs" / "pyproject.toml").read_text()
  )
  parent = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]

  assert generated["project"]["name"] == "alpaca2-stubs"
  assert generated["project"]["version"] == parent["version"]
