import argparse

from statify import statify


def test_no_config(fs, mocker):
    print_mock = mocker.patch('builtins.print')

    statify._main(argparse.Namespace())

    assert print_mock.mock_calls == [
        mocker.call(
            'Invalid configuration. Please add your client_id and client_secret '
            'in /home/valentin/.config/statify.yaml:\n\nspotify_app:\n  '
            'client_id: your client ID\n  client_secret: your client secret'
        )
    ]
