from functools import lru_cache
from pathlib import Path
import tomllib


@lru_cache(maxsize=1)
def get_app_version() -> str:
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as file_handle:
        pyproject = tomllib.load(file_handle)
    return pyproject["project"]["version"]
