import pytest

from statify import (
    config,
    database_client,
)


def test_init_database_same_version(statify_directory, sql_spy):
    with open(str(database_client.DATABASE_VERSION_PATH), 'w') as version_file:
        version_file.write(config.VERSION)

    database_client.StatifyDatabase(':memory')

    assert sql_spy.mock_calls == []


def test_init_database_from_nothing(statify_directory, sql_spy, mocker):
    database_client.StatifyDatabase(':memory')

    assert sql_spy.mock_calls == [
        mocker.call(stmt) for stmt in database_client.V1_0_STATEMENTS
    ]


def test_init_from_database_from_up_version(statify_directory):
    with open(str(database_client.DATABASE_VERSION_PATH), 'w') as version_file:
        version_file.write('42424242.42.42')

    with pytest.raises(database_client.DowngradeVersionError):
        database_client.StatifyDatabase(':memory')
