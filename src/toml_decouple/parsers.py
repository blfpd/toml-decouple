import re
import tomllib
from collections.abc import Sequence as Seq
from dataclasses import is_dataclass
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

from .helpers import find_project_name
from .settings import TomlSettings
from .toml_types import TomlDict

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

ENV_FILES = (".env", ".env.local")
SECRETS_DIRS = ("/run/secrets",)
NULL_VALUES = {"none", "nil", "null"}


class TomlDecoupleError(ValueError):
    pass


class TomlDecouple:
    def __init__(
        self,
        env_files: Seq[str] = ENV_FILES,
        secret_dirs: Seq[str] = SECRETS_DIRS,
        initial: TomlDict | None = None,
        prefix: str | None = None,
    ):
        """
        Initializes the Parser instance for managing environment and secret configurations.

        This constructor sets up the parser's internal state, including the
        paths to search for environment files and secrets, an optional
        initial set of settings, and a prefix for filtering environment variables.

        Args:
            env_files: A sequence of filenames to search for environment variables.
                       These files are typically in key=value format (like .env).
                       Files are processed in the order provided, with later files
                       overriding values from earlier ones. Defaults to
                       `(".env", ".env.local")`).
            secret_dirs: A sequence of directory paths where secrets are stored.
                     Each file within these directories is treated as a secret,
                     with its name as the key and content as the value.
                     Only existing paths are considered. Defaults to
                     `("/run/secrets",)`).
            initial: An optional dictionary of initial settings. These settings
                     will be merged first and can be overridden by environment
                     variables or secrets. Defaults to an empty dictionary `{}`.
            prefix: An optional string prefix used to filter environment variables.
                    Only environment variables starting with this prefix (case-sensitive)
                    will be considered by the parser. If `None`, defaults to the value of
                    environment variable `CONFIG_PREFIX` (e.g.: `CONFIG_PREFIX=DJ_`)
                    or the name of the current working directory in uppercase (e.g.: `MY_PROJECT_`).

        Attributes:
            settings (TomlDict): The dictionary where parsed configuration values
                                 will be stored. Initially set to `initial` or `{}`.
            env_files (list[Path]): The list of .env file paths to be processed.
            secret_dirs (list[Path]): The list of `pathlib.Path` objects for existing
                                      secret directories.
            prefix (str): The environment variable prefix used by the parser.
                          Defaults to the current directory name if not provided.
        """
        self.env_files: list[Path] = [Path(p) for p in env_files if Path(p).exists()]
        self.secret_dirs: list[Path] = [
            Path(p) for p in secret_dirs if Path(p).exists()
        ]
        self.prefix: str = self.fix_prefix(prefix)
        self._initial: TomlDict = initial or {}
        self._settings: TomlSettings | None = None

    @property
    def configuration(self):
        """
        Return the Parser configuration for debugging purposes.
        """
        return {
            "initial": self._initial,
            "env_files": self.env_files,
            "secret_dirs": self.secret_dirs,
            "prefix": self.prefix,
        }

    @classmethod
    def fix_prefix(cls, prefix: str | None):
        if prefix is None:
            return environ.get("CONFIG_PREFIX") or cls.default_prefix()
        return f"{prefix.removesuffix('_')}_"

    @classmethod
    def default_prefix(cls):
        prefix = cls.find_default_prefix()
        # Reminder while running ./manage.py runserver
        if environ.get("RUN_MAIN") == "true" or "DEBUG" in environ:
            print(f"Using default env variable prefix: {prefix}")
        return prefix

    @staticmethod
    def find_default_prefix():
        if project_name := find_project_name():
            prefix = project_name.strip().upper().replace("-", "_")
            return f"{prefix}_"
        return f"{Path('.').absolute().name.upper()}_"

    def load(self) -> TomlSettings:
        if self._settings is None:
            self._settings = TomlSettings(
                dot_envs=self.parse_dot_envs(),
                secrets=self.parse_secrets(),
                env_vars=self.parse_env_vars(),
                initial=self._initial or {},
            )
        return self._settings

    def load_dataclass[D: DataclassInstance](self, dc: type[D]) -> D:
        if not is_dataclass(dc):
            raise TypeError(f"{dc!r} doesn’t seem to be a Dataclass")
        if not type(dc).__name__ == "type":
            raise TypeError(
                "The Dataclass should not be instanciated. "
                f"Try: TomlDecouple().load_dataclass({dc.__class__.__name__})"
            )

        settings = self.load()
        fields = dc.__dataclass_fields__.items()
        return dc(
            **{
                key: field.type(settings.get(key, field.default))
                for key, field in fields
                if key in settings
            }
        )

    def parse_dot_envs(self):
        settings: TomlDict = {}
        for path in self.env_files:
            with open(path) as f:
                content = f.read().strip()
            settings = {**settings, **self.parse_lines(content)}
        return settings

    def parse_secrets(self):
        settings: TomlDict = {}
        for secrets_path in self.secret_dirs:
            for secret_file in secrets_path.iterdir():
                with open(secret_file) as f:
                    content = f.read().strip()
                settings = {
                    **settings,
                    **self.parse_line(f"{secret_file.name} = {content}"),
                }
        return settings

    def parse_env_vars(self):
        vars: TomlDict = {}
        for k, v in environ.items():
            if k.startswith(self.prefix):
                vars.update(self.parse_line(f"{k.removeprefix(self.prefix)} = {v}"))
        return vars

    @classmethod
    def parse_lines(cls, content: str) -> TomlDict:
        content = content.replace(r"\r\n", r"\n").strip()
        dicts = [cls.parse_line(line.strip()) for line in content.splitlines()]
        parsed = {k: v for d in dicts for k, v in d.items()}
        return parsed

    @classmethod
    def parse_line(cls, line: str) -> TomlDict:
        """Takes liberties from TOML spec regarding strings and null values.

        >>> TomlDecouple.parse_line('key = "standard string"')
        {'key': 'standard string'}

        >>> TomlDecouple.parse_line('key = NudeString')
        {'key': 'NudeString'}

        >>> TomlDecouple.parse_line('key = NULL')
        {'key': None}

        >>> TomlDecouple.parse_line('key = ')
        {'key': ''}
        """
        line = line.strip()
        try:
            return tomllib.loads(line)
        except tomllib.TOMLDecodeError as error:
            if m := re.match(r"(?P<key>\w+) ?= ?(?P<value>\S+)?", line):
                return {m["key"]: cls.parse_value(m["value"])}

            msg = re.sub(r" \(.+\)", "", str(error))
            raise TomlDecoupleError(f"{msg}: '{line}'") from error

    @staticmethod
    def parse_value(value: str | None) -> str | None:
        """Interpret the value as string or None.

        >>> TomlDecouple.parse_value('string')
        'string'

        >>> TomlDecouple.parse_value('null')

        >>> TomlDecouple.parse_value(None)
        ''
        """
        if value is None:
            # Parse as empty string to be consistent with os.environ
            return ""
        return None if value.lower() in NULL_VALUES else value

    def debug(self):
        for key, value in sorted(self.load().items()):
            print(f"{key} = {repr(value)}")
