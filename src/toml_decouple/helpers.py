from collections.abc import Sequence as Seq
from pathlib import Path
import tomllib as toml

from .toml_types import TomlValue

__all__ = ["tuple_list", "find_project_name"]


def tuple_list(iterable: Seq[Seq[TomlValue]]) -> list[tuple[TomlValue, ...]]:
    return [tuple(val) for val in iterable]


def _find_file_up(file_name: str, directory: Path, depth: int):
    if depth < 1 or directory.name == "/":
        raise RecursionError

    try:
        return list(directory.glob(file_name)).pop()
    except IndexError:
        pass

    return _find_file_up(file_name, directory.parent, depth - 1)


def find_file_up(file_name, current, depth=5) -> Path | None:
    directory = current.resolve()
    try:
        return _find_file_up(file_name, directory, depth)
    except RecursionError:
        return None


def find_project_name() -> str | None:
    if pyproject := find_file_up("pyproject.toml", Path(".")):
        content = toml.load(pyproject.open("rb"))
        return content.get("project", {}).get("name")
