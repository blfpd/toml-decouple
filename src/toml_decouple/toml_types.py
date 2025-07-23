from datetime import date, datetime, time

type TomlValue = (
    bool | date | datetime | time | TomlDict | float | int | list[TomlValue] | str
)
type TomlDict = dict[str, TomlValue]
