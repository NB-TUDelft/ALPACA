from pathlib import Path
import contextlib
import importlib.metadata
import importlib.resources
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[4]

# Must match [project] name in pyproject.toml.
DIST_NAME = "alpaca2"

def get_cache_folder():
  alpaca_folder = Path.cwd() / ".alpaca"

  alpaca_folder.mkdir(parents=True, exist_ok=True)

  return alpaca_folder

@contextlib.contextmanager
def _board_libs():
  # Running from a checkout: the board libraries live at the repository root.
  dev = PROJECT_ROOT / "alpaca"
  if (dev / "common").is_dir():
    yield dev
    return

  # Installed: the wheel ships them inside the host package (force-include).
  bundled = importlib.resources.files("alpaca") / "boardlibs"
  with importlib.resources.as_file(bundled) as path:
    yield path

def collect_files(pico_name: str):
  alpaca_folder = get_cache_folder()
  src = alpaca_folder / f"{pico_name}_root"

  shutil.rmtree(src, ignore_errors=True)

  ignore = shutil.ignore_patterns("__pycache__")

  with _board_libs() as libs:
    shutil.copytree(libs / "common", src, dirs_exist_ok=True, ignore=ignore)
    shutil.copytree(libs / pico_name, src, dirs_exist_ok=True, ignore=ignore)

  (src / "version.py").write_text(
    f"ALPACA_FW_VER=\"{importlib.metadata.version(DIST_NAME)}\""
  )

  return src
