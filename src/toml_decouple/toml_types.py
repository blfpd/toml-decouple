from collections.abc import Sequence
from datetime import date, datetime, time
from typing import Literal

type TomlValue = (
    bool | date | datetime | float | int | str | time | Sequence[TomlValue] | TomlDict
)

type OptTomlValue = TomlValue | None

type TomlDict = dict[str, OptTomlValue]

type NoDefault = tuple[Literal["NO"], Literal["DEFAULT"]]  # optparse.NO_DEFAULT
