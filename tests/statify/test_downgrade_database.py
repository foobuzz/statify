import argparse

from statify import database_client
from statify import statify


def test_downgrade_database(fs, statify_directory, statify_config, mocker):
    print_mock = mocker.patch('builtins.print')
    with open(str(database_client.DATABASE_VERSION_PATH), 'w') as db_version_file:
        db_version_file.write('42424242.42.42')

    statify._main(argparse.Namespace(command=None))

    assert print_mock.mock_calls == [
        mocker.call(
            'Statify version 1.0 is running but the database is setup for '
            'version 42424242.42.42. Downgrading the database is not supported '
            'so you should install statify 42424242.42.42 or higher.'
        )
    ]
