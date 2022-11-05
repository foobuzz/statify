import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import jinja2
import pytest
import yaml

from statify import (
    config,
    database_client,
    spotify_client
)
from statify import webserver
from statify.webserver import webserver as statify_webserver


TEMPLATES = {}


def load_templates():
    """
    Templates need to be pre-loaded, since pyfakefs breaks dynamic loading
    (templates don't exist in the fake filesystem). There surely is a better way
    to handle this.
    """
    app = statify_webserver.app
    for template in (Path(webserver.__file__).parent / 'templates').iterdir():
        TEMPLATES[template.name] = app.jinja_loader.get_source(
            app.jinja_env,
            template.name,
        )


load_templates()


@pytest.fixture
def app():
    app = statify_webserver.app
    app.jinja_loader = jinja2.FunctionLoader(lambda name: TEMPLATES[name])
    return app


@pytest.fixture
def statify_directory(fs):
    os.makedirs(str(config.STATIFY_PATH), exist_ok=True)


@pytest.fixture
def statify_config(fs):
    os.makedirs(str(config.CONFIG_PATH.parent), exist_ok=True)
    with open(str(config.CONFIG_PATH), 'w') as config_file:
        yaml.dump(
            {
                'spotify_app': {
                    'client_id': 'test_client_id',
                    'client_secret': 'test_client_secret',
                },
                'throttling': 0,
            },
            config_file
        )


@pytest.fixture
def cached_token(fs, statify_directory):
    with open(str(spotify_client.OAUTH_TOKENS_PATH), 'w') as token_file:
        json.dump(
            {
                'token_type': 'Bearer',
                'expires_in': 3600,
                'expires_at': (datetime.utcnow()+timedelta(days=42)).timestamp(),
                'scope': 'playlist-read-private user-read-recently-played',
                'refresh_token': 'toto',
                'access_token': 'toto',
            },
            token_file
        )


@pytest.fixture
def in_memory_database(mocker, statify_directory):
    database = database_client.StatifyDatabase(':memory:')
    mocker.patch(
        'statify.statify.database_client.StatifyDatabase',
        return_value=database,
    )
    yield database
    database.close()


@pytest.fixture
def sql_spy(mocker):
    backup = database_client.StatifyDatabase._sql
    database_client.StatifyDatabase._sql = mocker.MagicMock()
    yield database_client.StatifyDatabase._sql
    database_client.StatifyDatabase._sql = backup
