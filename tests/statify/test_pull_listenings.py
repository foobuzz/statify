import argparse

import responses
from pypika import Query, Order

from statify import statify
from .. import utils


@responses.activate
def test_pull_listenings_no_previous_fetch(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    2 listenings, no previous listening in database.
    """
    utils.add_current_user_recently_played_response([
        utils.spotify_listening_factory(
            played_at="2020-07-07T16:53:23",
            track=utils.spotify_track_factory(
                id='t2',
                name="California Dreamin'",
                artists=[
                    utils.spotify_artist_factory(name="Bobby Womack"),
                ],
            ),
        ),
        utils.spotify_listening_factory(
            played_at="2020-07-07T16:48:45",
            track=utils.spotify_track_factory(
                id="t1",
                name="S.O.B.",
                artists=[
                    utils.spotify_artist_factory(name="Nathaniel Rateliff"),
                ],
            ),
        ),
    ])

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='listenings'))

    assert logging_mock.info.call_args_list == [
        mocker.call(
            'No match for previous listenings fetch. Hole between %s and %s',
            None, '2020-07-07T16:48:45',
        ),
        mocker.call(
            'Added %s listenings. Newest played_at is now %s',
            2, '2020-07-07T16:53:23',
        ),
    ]

    assert set(
        tuple(r) for r in in_memory_database.select_from('Song', ['*'])
    ) == {
        (
            't1',
            'https://api.spotify.com/v1/tracks/test_track_id',
            'https://open.spotify.com/track/test_track_id',
            'S.O.B.',
            'https://i.scdn.co/image/test_url_token640',
            314159,
            0,
            'test_isrc',
            0,
            74,
            'https://p.scdn.co/mp3-preview/test_url_token1',
            15,
            'test_album_id',
            'Test Album Name',
            'Nathaniel Rateliff',
        ),
        (
            't2',
            'https://api.spotify.com/v1/tracks/test_track_id',
            'https://open.spotify.com/track/test_track_id',
            "California Dreamin'",
            'https://i.scdn.co/image/test_url_token640',
            314159,
            0,
            'test_isrc',
            0,
            74,
            'https://p.scdn.co/mp3-preview/test_url_token1',
            15,
            'test_album_id',
            'Test Album Name',
            'Bobby Womack',
        ),
    }

    assert set(
        tuple(r) for r in in_memory_database.select_from('Listening', ['*'])
    ) == {
        (
            1,
            't2',
            '2020-07-07T16:53:23',
            'playlist',
            None,
            'test_playlist_id',
        ),
        (
            2,
            't1',
            '2020-07-07T16:48:45',
            'playlist',
            None,
            'test_playlist_id',
        ),
    }


@responses.activate
def test_pull_listenings_match_previous_fetch(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    3 remote listenings, number 2 matches the previous one in the database.
    """
    utils.add_current_user_recently_played_response([
        utils.spotify_listening_factory(
            played_at="2020-07-07T16:53:23",
            track=utils.spotify_track_factory(
                id='t2',
                name="California Dreamin'",
                artists=[
                    utils.spotify_artist_factory(name="Bobby Womack"),
                ],
            ),
        ),
        utils.spotify_listening_factory(
            played_at="2020-07-07T16:48:45",
            track=utils.spotify_track_factory(
                id="t1",
                name="S.O.B.",
                artists=[
                    utils.spotify_artist_factory(name="Nathaniel Rateliff"),
                ],
            ),
        ),
        utils.spotify_listening_factory(
            played_at="2020-07-07T16:45:57",
            track=utils.spotify_track_factory(
                id="t0",
                name="Wrench and Numbers",
                artists=[
                    utils.spotify_artist_factory(name="Jeff Russo"),
                ],
            ),
        ),
    ])

    in_memory_database.insert_into('Listening',
        song_id='t1',
        played_at="2020-07-07T16:48:45",
        context='playlist',
        album_id=None,
        playlist_id='test_playlist_id',
    )

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='listenings'))

    assert logging_mock.info.call_args_list == [
        mocker.call(
            'Match previous listenings fetch at %s',
            '2020-07-07T16:48:45'
        ),
        mocker.call(
            'Added %s listenings. Newest played_at is now %s',
            1, '2020-07-07T16:53:23',
        ),
    ]

    latest = in_memory_database.query(
        Query
        .from_('Listening')
        .select('*')
        .orderby('played_at', order=Order.desc)
        .limit(1)
    ).fetchone()

    assert tuple(latest) == (
        2, 't2', '2020-07-07T16:53:23', 'playlist', None, 'test_playlist_id'
    )


@responses.activate
def test_pull_listenings_no_new_listening(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    1 remote listenings, matches the previous one in the database.
    """
    utils.add_current_user_recently_played_response([
        utils.spotify_listening_factory(
            played_at="2020-07-07T16:53:23",
            track=utils.spotify_track_factory(
                id='t2',
                name="California Dreamin'",
                artists=[
                    utils.spotify_artist_factory(name="Bobby Womack"),
                ],
            ),
        ),
    ])

    in_memory_database.insert_into('Listening',
        song_id='t2',
        played_at="2020-07-07T16:53:23",
        context='playlist',
        album_id=None,
        playlist_id='test_playlist_id',
    )

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='listenings'))

    assert logging_mock.info.call_args_list == [
        mocker.call(
            'Match previous listenings fetch at %s',
            '2020-07-07T16:53:23'
        ),
        mocker.call(
            'Added %s listenings. Newest played_at is now %s',
            0, '2020-07-07T16:53:23'
        ),
    ]

    latest = in_memory_database.query(
        Query
        .from_('Listening')
        .select('*')
        .orderby('played_at', order=Order.desc)
        .limit(1)
    ).fetchone()

    assert tuple(latest) == (
        1, 't2', '2020-07-07T16:53:23', 'playlist', None, 'test_playlist_id'
    )
