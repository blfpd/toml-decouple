from collections.abc import Callable, Mapping
from optparse import NO_DEFAULT
from typing import Any, cast, override

from .toml_types import NoDefault, OptTomlValue, TomlDict

_reserved = ("_data", "get", "items", "keys", "values")


class TomlSettings(Mapping):
    def __init__(
        self,
        dot_envs: TomlDict,
        secrets: TomlDict,
        env_vars: TomlDict,
        initial: TomlDict,
    ):
        for d in [dot_envs, secrets, env_vars, initial]:
            if not isinstance(d, Mapping):
                raise TypeError(f"{d} is not a dict")

        # Make a shallow copy to ensure immutability:
        self._data = dict({**dot_envs, **secrets, **env_vars, **initial})

        self.__slots__ = tuple(sorted(self._data.keys())) + _reserved

    @override
    def __getitem__[T: OptTomlValue](self, key: str) -> T:
        return cast(T, self._data[key])

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

    def __call__[T](
        self,
        name: str,
        default: T | NoDefault = NO_DEFAULT,
        to: Callable[[Any], T] | None = None,
    ) -> T:
        val = (
            self._data[name] if default is NO_DEFAULT else self._data.get(name, default)
        )
        return to(val) if to else cast(T, val)

    @override
    def __getattribute__[T: OptTomlValue](self, name: str, /) -> T:
        if name.startswith("__") or name in _reserved:
            return super().__getattribute__(name)
        return cast(T, self._data[name])

    @override
    def __str__(self) -> str:
        return "TomlSettings:\n" + "\n".join(
            [f"  {k} = {v!r}" for k, v in self._data.items()]
        )
