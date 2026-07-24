from pathlib import Path
import importlib.metadata
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_cache_folder():
  alpaca_folder = PROJECT_ROOT / ".alpaca"

  alpaca_folder.mkdir(parents=True, exist_ok=True)

  return alpaca_folder

def collect_files(pico_name: str):
  alpaca_folder = get_cache_folder()
  src = alpaca_folder / f"{pico_name}_root"

  shutil.rmtree(src, ignore_errors=True)

  ignore = shutil.ignore_patterns("__pycache__")

  shutil.copytree(PROJECT_ROOT / "alpaca" / "common", src, dirs_exist_ok=True, ignore=ignore)
  shutil.copytree(PROJECT_ROOT / "alpaca" / pico_name, src, dirs_exist_ok=True, ignore=ignore)

  (src / "version.py").write_text(
    f"ALPACA_FW_VER=\"{importlib.metadata.version('alpaca')}\""
  )

  return src
