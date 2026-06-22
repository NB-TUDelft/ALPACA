from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_cache_folder():
  alpaca_folder = PROJECT_ROOT / ".alpaca"

  alpaca_folder.mkdir(parents=True, exist_ok=True)

  return alpaca_folder