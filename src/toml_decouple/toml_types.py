from typing import Literal
from datetime import date, datetime, time

type TomlValue = (
    bool | date | datetime | time | TomlDict | float | int | list[TomlValue] | str
)
type OptTomlValue = TomlValue | None
type TomlDict = dict[str, OptTomlValue]
type NoDefault = tuple[Literal["NO"], Literal["DEFAULT"]]  # optparse.NO_DEFAULT
