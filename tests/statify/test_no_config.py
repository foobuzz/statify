import argparse

from statify import statify


def test_no_config(fs, mocker):
    print_mock = mocker.patch('builtins.print')

    statify._main(argparse.Namespace())

    _, args, _ = print_mock.mock_calls[0]
    assert args[0].startswith(
        'Invalid configuration. Please add your client_id and client_secret'
    ) is True
