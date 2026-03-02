from functools import lru_cache
from pathlib import Path
import tomllib


@lru_cache(maxsize=1)
def get_app_version() -> str:
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as file_handle:
        pyproject = tomllib.load(file_handle)
    version = pyproject["project"]["version"]
    version_date = pyproject.get("tool", {}).get("strategy_hub", {}).get("version_date")
    if version_date:
        return f"{version} ({version_date})"
    return version
