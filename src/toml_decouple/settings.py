from collections.abc import Mapping
from optparse import NO_DEFAULT
from typing import Any, Callable, override, TypedDict

try:
    from dj_database_url import DBConfig
except ModuleNotFoundError:

    class DBConfig(TypedDict, total=False):
        pass


from .toml_types import TomlValue

_reserved = ("_data", "get", "items", "keys", "values")


def TomlSettings(mapping: dict[str, Any]):
    class Settings(Mapping):
        __slots__ = tuple(sorted(mapping.keys())) + _reserved

        def __init__(self, data: Mapping[str, Any]):
            if not isinstance(data, Mapping):
                raise TypeError("TomlSettings requires a Mapping")
            # Make a shallow copy to ensure immutability:
            self._data = dict(data)

        @override
        def __getitem__(self, key):
            return self._data[key]

        @override
        def __iter__(self):
            return iter(self._data)

        @override
        def __len__(self):
            return len(self._data)

        @override
        def __repr__(self):
            return f"{self.__class__.__name__}({self._data!r})"

        @override
        def __eq__(self, other):
            if isinstance(other, Mapping):
                return dict(self.items()) == dict(other.items())
            return NotImplemented

        @override
        def __hash__(self):
            # Required for being hashable (i.e. usable as dict keys or in sets)
            return hash(frozenset(self._data.items()))

        def __call__(
            self,
            name: str,
            default=NO_DEFAULT,
            to: Callable[..., TomlValue | DBConfig] | None = None,
        ) -> TomlValue | DBConfig | None:
            val = (
                self._data[name]
                if default is NO_DEFAULT
                else self._data.get(name, default)
            )
            return to(val) if to else val

        @override
        def __getattribute__(self, name: str, /) -> TomlValue:
            if name.startswith("__") or name in _reserved:
                return super().__getattribute__(name)
            return self._data[name]

        @override
        def __str__(self) -> str:
            return "TomlSettings:\n" + "\n".join(
                [f"  {k} = {v!r}" for k, v in self._data.items()]
            )

    return Settings(mapping)
