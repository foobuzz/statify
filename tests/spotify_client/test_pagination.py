from statify import spotify_client


def test_paginate_spotipy_method(cached_token):
    client = spotify_client.Spotify(
        'test_client_id',
        'test_client_secret',
        throttling=0,
    )

    args_logger = []

    def fake_method(*args, **kwargs):
        args_logger.append((args, kwargs))
        if kwargs['offset'] < 3:
            items = ['item']
        else:
            items = []
        return {
            'items': items,
            'total': 3
        }

    results = list(client._paginate_spotipy_method(
        fake_method,
        'some_arg',
        page_size=1,
        some_kwarg='yo'
    ))

    assert results == 3*['item']
    assert args_logger == [
        (
            ('some_arg',),
            {'limit': 1, 'offset': 0, 'some_kwarg': 'yo'}
        ),
        (
            ('some_arg',),
            {'limit': 1, 'offset': 1, 'some_kwarg': 'yo'}
        ),
        (
            ('some_arg',),
            {'limit': 1, 'offset': 2, 'some_kwarg': 'yo'}
        ),
    ]


def test_paginate_bidirectional_spotipy_method(cached_token):
    client = spotify_client.Spotify(
        'test_client_id',
        'test_client_secret',
        throttling=0,
    )

    args_logger = []

    def fake_method(*args, **kwargs):
        args_logger.append((args, kwargs))
        if kwargs.get('before') is None:
            return {
                'items': ['item'],
                'cursors': {'before': 2},
            }
        elif kwargs['before'] == 2:
            return {
                'items': ['item'],
                'cursors': {'before': 1},
            }
        elif kwargs['before'] == 1:
            return {
                'items': ['item'],
                'cursors': None,
            }

    results = list(client._paginate_bidirectional_spotipy_method(
        fake_method,
        'some_arg',
        page_size=1,
        some_kwarg='yo'
    ))

    assert results == 3*['item']
    assert args_logger == [
        (
            ('some_arg',),
            {'limit': 1, 'before': None, 'some_kwarg': 'yo'}
        ),
        (
            ('some_arg',),
            {'limit': 1, 'before': 2, 'some_kwarg': 'yo'}
        ),
        (
            ('some_arg',),
            {'limit': 1, 'before': 1, 'some_kwarg': 'yo'}
        ),
    ]
