from collections.abc import Sequence as Seq

from .toml_types import TomlValue


def tuple_list(iterable: Seq[Seq[TomlValue]]) -> list[tuple[TomlValue, ...]]:
    return [tuple(val) for val in iterable]
