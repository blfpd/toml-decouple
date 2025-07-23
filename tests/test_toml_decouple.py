from dataclasses import dataclass
from unittest.mock import mock_open

import dj_database_url
import pytest

import toml_decouple as uut


def test_config(mocker):
    env_content = """
    # This is a comment
    APP_NAME = MyAwesomeApp
    DEBUG = true
    DATABASE_URL = sqlite:///my.db
    SOME_VAR_WITH_EQUALS=value=with=equals
    """
    mocker.patch("builtins.open", mock_open(read_data=env_content))

    config = uut.TomlDecouple().load()

    assert config.APP_NAME == "MyAwesomeApp"
    assert config.DEBUG is True
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
    assert config["SOME_VAR_WITH_EQUALS"] == "value=with=equals"


def test_config_as_dataclass(mocker):
    env_content = """
    # This is a comment
    APP_NAME = MyAwesomeApp
    """
    mocker.patch("builtins.open", mock_open(read_data=env_content))

    @dataclass
    class Config:
        APP_NAME: str
        SECRET_KEY: str = "S3cre7"

    config: Config = uut.TomlDecouple().load_dataclass(Config)

    assert config.APP_NAME == "MyAwesomeApp"
    assert config.SECRET_KEY == "S3cre7"
    with pytest.raises(AttributeError):
        config.OTHER  # type: ignore
