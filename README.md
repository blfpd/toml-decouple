# TOML-decouple

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/blfpd/toml-decouple/publish.yaml)
![PyPI - Version](https://img.shields.io/pypi/v/toml-decouple)
![Pypi - Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![PyPI - Downloads](https://img.shields.io/pypi/dm/toml-decouple)
![License](https://img.shields.io/github/license/blfpd/toml-decouple)

## TOML powered .env file configuration and secrets

Package available in [PyPI](https://pypi.org/project/toml-decouple/).

## Getting Started

### Install the library

Using pip:
```sh
pip install toml-decouple
```

Using uv:
```sh
uv add toml-decouple
```

### Basic Usage

```toml
# my_project/.env
SECRET_KEY = "S3cre7"
DEBUG = true
DB = postgresql://USER:PASSWORD@HOST:PORT/NAME
```

```python
import dj_database_url
from toml_decouple import config

SECRET_KEY = config.SECRET_KEY
DEBUG = config("DEBUG", false)
DATABASES["default"] = config("DB", to=dj_database_url.parse)
```

Assuming this environment variable is set:
```sh
MY_PROJECT_DEBUG=true
```

Create your configuration dataclass and parse config and env into it:

```python
from dataclasses import dataclass
from toml_decouple import TomlDecouple

@dataclass
class Config:
    SECRET_KEY: str = ""
    DEBUG: bool = False

config: Config = TomlDecouple().load_dataclass(Config)
```

You can now access the fields of your fully typed config Class
that contains values from a TOML config file and the environment.

For example:

```python
SECRET_KEY = config.SECRET_KEY
DEBUG = config("DEBUG", False)
print(SECRET_KEY)  # prints "S3cre7"
print(DEBUG)  # prints True
print(config.DB)  # raise AttributeError: 'Config' object has no attribute 'DB'
```

## Configuration

To configure, you have to use `TomlDecouple(**options).load()`, like:

```python
from toml_decouple import TomlDecouple

config = TomlDecouple(
    env_files=[".env.docker"],
    secrets=["/run/secrets"],  # this is the default
    initial={"DEBUG": True}
    prefix="BACKEND_",  # to use env variables BACKEND_ENV_VAR=value
).load()
```

## Tests

Run tests from the project root with:
```sh
make test
```

## Issues

Feel free to send issues or suggestions to https://github.com/blfpd/toml-decouple/issues.
