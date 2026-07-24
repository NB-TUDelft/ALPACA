import shutil
from typing import Annotated

import typer

from cli.tools.cache import PROJECT_ROOT, collect_files, get_cache_folder
from mypy import stubgen
import os
import toml
import importlib.metadata


def generate_stubs_cmd(pico_name: Annotated[str, typer.Argument(help="Pico name to generate stubs for i.e. student, helper...")]):
  src = collect_files(pico_name)

  stubs_folder = get_cache_folder() / "stubs"

  shutil.rmtree(stubs_folder, True)

  file_list = [str(p) for p in src] if isinstance(src, (list, tuple)) else [str(src)]

  options = stubgen.parse_options(["-o", str(stubs_folder.absolute()), "--include-docstrings", *file_list])
  stubgen.generate_stubs(options)

  shutil.copytree(PROJECT_ROOT / "typings", stubs_folder, dirs_exist_ok=True)

  for file in os.listdir(stubs_folder):
    if not file.endswith(".pyi"): continue

    base_name = file[:-4]

    os.mkdir(stubs_folder / base_name)

    os.replace(stubs_folder / file, stubs_folder / base_name / "__init__.pyi")

    (stubs_folder / file).unlink(True)


  (stubs_folder / "README.md").write_text(
    "Stubs for " +
    (PROJECT_ROOT / 'README.md').read_text(encoding='utf-8')
  )

  parent = toml.load(PROJECT_ROOT / "pyproject.toml")

  packages = [f for f in os.listdir(stubs_folder) if (stubs_folder / f).is_dir()]

  toml.dump({
    "project": {
      **{k: v for k, v in parent["project"].items() if isinstance(v, str)},
      "name": f"{parent['project']['name']}-stubs",
      "description": "Stub files for ALPACA 2.0 for NB2420 Electronic Instrumentation course of TU Delft"
    },
    "build-system": {
      "requires": ["setuptools>=61"],
      "build-backend": "setuptools.build_meta"
    },
    # Some pyright magic
    "tool": {
      "setuptools": {
        "packages": packages,
        "package-data": dict.fromkeys(packages, ["*.pyi"])
      }
    }
  }, (stubs_folder / "pyproject.toml").open("w+"))

  

