#!/usr/bin/python3

from .helpers import tuple_list  # noqa
from .settings import TomlSettings
from .parsers import ENV_FILES, SECRETS_PATHS, TomlDecouple

__all__ = [
    "config",
    "ENV_FILES",
    "SECRETS_PATHS",
    "TomlDecouple",
    "TomlSettings",
]

config = TomlDecouple().load()
