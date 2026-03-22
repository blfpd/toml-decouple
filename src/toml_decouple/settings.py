from collections.abc import Callable, Mapping
from optparse import NO_DEFAULT
from typing import Any, cast, override
from .toml_types import NoDefault, OptTomlValue, TomlDict


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

        self.__data = {**dot_envs, **secrets, **env_vars, **initial}

    def __dir__(self):
        return (
            a
            for a in (*self.__data.keys(), *super().__dir__())
            if not a.endswith("__data")
        )

    def __getitem__[T: OptTomlValue](self, key: str) -> T:
        return cast(T, self.__data[key])

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__data!r})"

    def __eq__(self, other):
        if isinstance(other, Mapping):
            return dict(self.items()) == dict(other.items())
        return NotImplemented

    @override
    def __hash__(self):
        # Required for being hashable (i.e. usable as dict keys or in sets)
        return hash(frozenset(self.__data.items()))

    def __call__[T](
        self,
        name: str,
        default: T | NoDefault = NO_DEFAULT,
        *,
        to: Callable[[Any], T] | None = None,
    ) -> T:
        val = (
            self.__data[name]
            if default is NO_DEFAULT
            else self.__data.get(name, default)
        )
        return to(val) if to else cast(T, val)

    def __getattr__[T: OptTomlValue](self, name: str, /) -> T:
        if name.startswith("__"):
            return super().__getattribute__(name)
        return cast(T, self.__data[name])

    def __setattr__(self, name: str, value: Any):
        if name == f"_{self.__class__.__name__}__data":
            super().__setattr__(name, value)
            return

        raise AttributeError(
            f"'{self.__class__.__name__}' object attribute '{name}' is read-only"
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}:\n" + "\n".join(
            [f"  {k} = {v!r}" for k, v in self.__data.items()]
        )
