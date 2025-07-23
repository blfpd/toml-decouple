import re
import tomllib
from collections.abc import Sequence as Seq
from dataclasses import is_dataclass
from os import environ
from pathlib import Path
from typing import TypeVar


from .settings import TomlSettings
from .toml_types import TomlValue, TomlDict

ENV_FILES = (".env", ".env.local")
SECRETS_PATHS = ("/run/secrets",)

Dataclass = TypeVar("Dataclass", bound=object)


class TomlDecouple:
    def __init__(
        self,
        env_files: Seq[str] = ENV_FILES,
        secrets: Seq[str] = SECRETS_PATHS,
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
            secrets: A sequence of directory paths where secrets are stored.
                     Each file within these directories is treated as a secret,
                     with its name as the key and content as the value.
                     Only existing paths are considered. Defaults to
                     `("/run/secrets",)`).
            initial: An optional dictionary of initial settings. These settings
                     will be merged first and can be overridden by environment
                     variables or secrets. Defaults to an empty dictionary `{}`.
            prefix: An optional string prefix used to filter environment variables.
                    Only environment variables starting with this prefix (case-sensitive)
                    will be considered by the parser. If `None`, defaults to the name
                    of the current working directory in uppercase (e.g.: `MY_PROJECT_`).

        Attributes:
            settings (TomlDict): The dictionary where parsed configuration values
                                  will be stored. Initially set to `initial` or `{}`.
            env_files (list[str]): The list of .env file paths to be processed.
            secrets (list[Path]): The list of `pathlib.Path` objects for existing
                                  secret directories.
            prefix (str): The environment variable prefix used by the parser.
                          Defaults to the current directory name if not provided.
        """
        self.env_files: list[str] = list(env_files)
        self.secrets: list[Path] = [Path(p) for p in secrets if Path(p).exists()]
        self.prefix: str = prefix if prefix is not None else self.default_prefix()
        self._initial: dict[str, TomlValue] | None = initial
        self.settings: TomlDict = initial or {}

    @property
    def configuration(self):
        """
        Return the Parser configuration for debugging purposes.
        """
        return {
            "initial": self._initial,
            "env_files": self.env_files,
            "secrets": self.secrets,
            "prefix": self.prefix,
        }

    @staticmethod
    def default_prefix():
        return f"{Path('.').absolute().name}_"

    def load(self):
        self.settings = {
            **self.parse_env(),
            **self.parse_secrets(),
            **self.parse_env_vars(),
            **self.settings,
        }
        return TomlSettings(self.settings)

    def load_dataclass(self, dc: type[Dataclass]) -> Dataclass:
        if not is_dataclass(dc):
            raise TypeError(f"Object {dc!r} doesn’t seem to be a Dataclass")
        if not type(dc).__name__ == "type":
            dc_name = dc.__class__.__name__  # type: ignore
            raise TypeError(
                "The Dataclass should not be instanciated. "
                + f"Try: TomlDecouple().load({dc_name})"
            )
        fields = dc.__dataclass_fields__.items()

        self.load()

        return dc(
            **{
                key: field.type(self.settings.get(key, field.default))  # pyright: ignore[reportCallIssue]
                for key, field in fields
                if key in self.settings
            }
        )

    def parse_env(self):
        settings: TomlDict = {}
        for filename in self.env_files:
            try:
                with open(filename) as f:
                    content = f.read().strip()
            except FileNotFoundError:
                continue
            settings = {**settings, **self.parse_lines(content)}
        return settings

    def parse_secrets(self):
        settings: TomlDict = {}
        for secrets_path in self.secrets:
            for secret_file in secrets_path.iterdir():
                with open(secret_file) as f:
                    content = f.read().strip()
                settings = {
                    **settings,
                    **self.parse_line(f"{secret_file.name} = {content}"),
                }
        return settings

    def parse_env_vars(self):
        return {
            k.removeprefix(self.prefix): v
            for k, v in environ.items()
            if k.startswith(self.prefix)
        }

    @classmethod
    def parse_lines(cls, content: str) -> TomlDict:
        content = content.replace(r"\r\n", r"\n").strip()
        dicts = [cls.parse_line(line.strip()) for line in content.splitlines()]
        parsed = {k: v for d in dicts for k, v in d.items()}
        return parsed

    @classmethod
    def parse_line(cls, line: str) -> TomlDict:
        line = line.strip()
        try:
            return tomllib.loads(line)
        except tomllib.TOMLDecodeError as error:
            m = re.search(r"^(?P<key>\w+) ?= ?(?P<value>\S+)", line)
            if m is None:
                raise error
            return {m["key"]: m["value"]}

    def debug(self):
        for key, value in self.settings.items():
            print(f"{key} = {repr(value)}")
