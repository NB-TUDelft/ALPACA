"""Restrict board deployment to explicitly installed development sources."""

import importlib.metadata
import json
from urllib.parse import urlsplit

from alpaca.cli.tools.cache import DIST_NAME


def sync_allowed() -> bool:
  """Allow local source and Git installs using installer-recorded provenance.

  Index, wheel, and source archive installs fail closed. The working directory
  is deliberately irrelevant: entering a checkout cannot unlock a release.
  """
  try:
    raw = importlib.metadata.distribution(DIST_NAME).read_text("direct_url.json")
    origin = json.loads(raw) if raw else {}
    if not isinstance(origin, dict):
      return False
    vcs = origin.get("vcs_info")
    if isinstance(vcs, dict) and vcs.get("vcs") == "git":
      return True
    url = origin.get("url")
    return (
      isinstance(origin.get("dir_info"), dict)
      and isinstance(url, str)
      and urlsplit(url).scheme == "file"
    )
  except (importlib.metadata.PackageNotFoundError, OSError, ValueError, TypeError):
    return False
