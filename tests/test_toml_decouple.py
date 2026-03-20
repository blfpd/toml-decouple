import logging
import os
from dataclasses import dataclass
from pathlib import Path, PosixPath
from textwrap import dedent
from unittest import mock
from unittest.mock import mock_open

import pytest

import toml_decouple as uut  # type: ignore[import-not-found]


@pytest.fixture
def env(mocker):
    env_content = """
    # This is a comment
    APP_NAME = MyAwesomeApp
    DEBUG = true
    DATABASE_URL = sqlite:///my.db
    SOME_VAR_WITH_EQUALS=value=with=equals
    SOME_NULL_VALUE = NIL
    SOME_EMPTY_VALUE=
    """
    mocker.patch("builtins.open", mock_open(read_data=env_content))


@pytest.fixture
def config(env):
    return uut.TomlDecouple().load()


def test_config(config):
    assert config.APP_NAME == "MyAwesomeApp"
    assert config.DEBUG is True
    assert config["SOME_VAR_WITH_EQUALS"] == "value=with=equals"
    assert config.SOME_NULL_VALUE is None
    assert config.SOME_EMPTY_VALUE == ""


def test_secrets_dirs(mocker):
    secret_dir = Path(__file__).parent / "secrets"
    mocker.patch("pathlib.Path.exists", lambda _: True)
    mocker.patch("pathlib.PosixPath.iterdir", secret_dir.iterdir)
    assert uut.TomlDecouple().parse_secrets() == {"TEST": "test"}


def test_config_fail(mocker):
    mocker.patch("builtins.open", mock_open(read_data="INVALID_VALUE"))
    with pytest.raises(uut.parsers.TomlDecoupleError, match=": 'INVALID_VALUE'"):
        uut.TomlDecouple().load()


def test_config_with_db_url(config):
    import dj_database_url

    assert config("DATABASE_URL", to=dj_database_url.parse) == {
        "CONN_HEALTH_CHECKS": False,
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": False,
        "ENGINE": "django.db.backends.sqlite3",
        "HOST": "",
        "NAME": "my.db",
        "PASSWORD": "",
        "PORT": "",
        "USER": "",
    }


def test_config_with_key_error(config):
    with pytest.raises(KeyError, match="XxX"):
        config["XxX"]
    with pytest.raises(KeyError, match="XxX"):
        config.XxX


def test_config_as_dataclass(env):
    @dataclass
    class Config:
        APP_NAME: str
        SECRET_KEY: str = "S3cre7"

    config = uut.TomlDecouple().load_dataclass(Config)

    assert config.APP_NAME == "MyAwesomeApp"
    assert config.SECRET_KEY == "S3cre7"
    with pytest.raises(AttributeError, match="object has no attribute 'OTHER'"):
        config.OTHER  # type: ignore[attr-defined]


def test_config_as_dataclass_fail(env):
    @dataclass
    class Dummy:
        pass

    with pytest.raises(TypeError, match="<class 'int'> doesn’t seem to be a Dataclass"):
        uut.TomlDecouple().load_dataclass(int)  # type: ignore[type-var]

    with pytest.raises(TypeError, match="The Dataclass should not be instanciated."):
        uut.TomlDecouple().load_dataclass(Dummy())  # type: ignore[arg-type]


@mock.patch.dict(
    os.environ, {"UUT_APP_NAME": "App", "UUT_LIST": "[1, 2, 3]", "UUT_NONE": ""}
)
def test_config_from_envvars():
    config = uut.TomlDecouple(prefix="UUT_").load()
    assert config.APP_NAME == "App"
    assert config.LIST == [1, 2, 3]
    assert config.NONE == ""


def test_prefix_from_pyproject():
    assert uut.TomlDecouple.default_prefix() == "TOML_DECOUPLE_"


@mock.patch.dict(os.environ, {"RUN_MAIN": "true"})
def test_default_prefix_on_runserver(caplog):
    caplog.set_level(logging.DEBUG)

    uut.TomlDecouple.default_prefix()
    assert "parsers.py" in caplog.text
    assert "Using default env variable prefix: TOML_DECOUPLE_" in caplog.text


@mock.patch.dict(os.environ, {"CONFIG_PREFIX": "DJ_"})
def test_prefix_from_env_var():
    assert uut.TomlDecouple().prefix == "DJ_"


@mock.patch("toml_decouple.helpers.find_file_up")
def test_prefix_from_config_directory(find_file_up):
    find_file_up.return_value = None
    current_dir = Path(".").absolute()
    assert uut.TomlDecouple.default_prefix() == f"{current_dir.name.upper()}_"


def test_failing_find_project_name():
    assert uut.helpers.find_project_name("unknown.toml") is None


def test_tuple_list():
    assert uut.tuple_list([["Admin", "admin@example.com"]]) == [
        ("Admin", "admin@example.com")
    ]


def test_incorrect_args_in_toml_settings_init():
    with pytest.raises(TypeError, match="missing 4 required positional arguments"):
        uut.TomlSettings()  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="None is not a dict"):
        uut.TomlSettings(None, None, None, None)
    with pytest.raises(TypeError, match="42 is not a dict"):
        uut.TomlSettings(42, None, None, None)  # type: ignore[arg-type]


def test_show_configuration(env):
    decouple = uut.TomlDecouple()
    assert decouple.configuration == {
        "env_files": [PosixPath(".env.local")],
        "initial": {},
        "prefix": "TOML_DECOUPLE_",
        "secret_dirs": [],
    }


def test_iter(config):
    assert tuple(config) == (
        "APP_NAME",
        "DEBUG",
        "DATABASE_URL",
        "SOME_VAR_WITH_EQUALS",
        "SOME_NULL_VALUE",
        "SOME_EMPTY_VALUE",
    )


def test_len(config):
    assert len(config) == 6


def test_eq(config):
    equality = config == config
    assert equality


def test_eq_fail(config):
    equality = config == 42
    assert not equality


def test_hash(config):
    assert isinstance(hash(config), int)


def test_str(config):
    string = dedent("""
        TomlSettings:
          APP_NAME = 'MyAwesomeApp'
          DEBUG = True
          DATABASE_URL = 'sqlite:///my.db'
          SOME_VAR_WITH_EQUALS = 'value=with=equals'
          SOME_NULL_VALUE = None
          SOME_EMPTY_VALUE = ''
     """)
    assert str(config) == string.strip()


def test_repr(config):
    assert repr(config) == (
        "TomlSettings({'APP_NAME': 'MyAwesomeApp', "
        "'DEBUG': True, "
        "'DATABASE_URL': 'sqlite:///my.db', "
        "'SOME_VAR_WITH_EQUALS': 'value=with=equals', "
        "'SOME_NULL_VALUE': None, "
        "'SOME_EMPTY_VALUE': ''})"
    )


def test_debug(env):
    assert uut.TomlDecouple().debug() is None
