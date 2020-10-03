import argparse

import responses

from statify import statify
from .. import utils


@responses.activate
def test_pull_playlist_add_playlist(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    1 playlist with 2 tracks. All to be added to a blank database.
    """

    utils.add_current_user_playlists_response([
        utils.playlist_factory(
            name="Tarantino",
            owner={
                'display_name': "Valentin",
            },
        )
    ])

    utils.add_playlist_tracks_response(
        [
            utils.playlist_track_factory(
                added_at='2020-01-16T08:00:00Z',
                track=utils.track_factory(
                    id='t1',
                    name='Son of a Preacher Man',
                    artists=[
                        utils.artist_factory(name='Dusty Springfield'),
                    ],
                    album=utils.album_factory(name='Dusty in Memphis'),
                ),
            ),
            utils.playlist_track_factory(
                added_at='2020-01-16T08:05:00Z',
                track=utils.track_factory(
                    id=None,
                    is_local=True,
                    name='Jungle Boogie',
                    artists=[
                        utils.artist_factory(name='Kool & The Gang'),
                    ],
                    album=utils.album_factory(name='Wild And Peaceful'),
                ),
            ),
        ]
    )

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='playlists'))

    local_song_id = (
        'local:'
        'c2ddcb93619fcea2b7463048d14fb33'
        'c09c46d1c7e7dd5b352e8e9bd604d27b8'
    )

    assert logging_mock.info.call_args_list == [
        mocker.call(
            'Added song: %s (%s) in playlist %s (%s)',
            't1',
            'Son of a Preacher Man',
            'test_playlist_id',
            'Tarantino'
        ),
        mocker.call(
            'Added song: %s (%s) in playlist %s (%s)',
            local_song_id,
            'Jungle Boogie',
            'test_playlist_id',
            'Tarantino'
        )
    ]

    assert in_memory_database.select_from('Playlist', ['*']) == [(
        'test_playlist_id',
        'https://api.spotify.com/v1/playlists/test_playlist_id',
        'https://open.spotify.com/playlist/test_playlist_id',
        'https://mosaic.scdn.co/640/test_url_token640',
        'Tarantino',
        '0',
        'Valentin'
    )]

    assert set(in_memory_database.select_from('Song', ['*'])) == {
        (
            't1',
            'https://api.spotify.com/v1/tracks/test_track_id',
            'https://open.spotify.com/track/test_track_id',
            'Son of a Preacher Man',
            'https://i.scdn.co/image/test_url_token640',
            314159,
            0,
            'test_isrc',
            0,
            74,
            'https://p.scdn.co/mp3-preview/test_url_token1',
            15,
            'test_album_id',
            'Dusty in Memphis',
            'Dusty Springfield',
        ),
        (
            local_song_id,
            'https://api.spotify.com/v1/tracks/test_track_id',
            'https://open.spotify.com/track/test_track_id',
            'Jungle Boogie',
            'https://i.scdn.co/image/test_url_token640',
            314159,
            0,
            'test_isrc',
            1,
            74,
            'https://p.scdn.co/mp3-preview/test_url_token1',
            15,
            'test_album_id',
            'Wild And Peaceful',
            'Kool & The Gang',
        ),
    }

    assert set(in_memory_database.select_from('SongInPlaylist', ['*'])) == {
        ('t1', 'test_playlist_id', '2020-01-16T08:00:00Z'),
        (local_song_id, 'test_playlist_id', '2020-01-16T08:05:00Z')
    }


@responses.activate
def test_pull_playlist_update_playlist(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    1 playlist with 0 tracks. Updated on Spotify, to be updated in database.
    """
    in_memory_database.insert_into('Playlist',
        spotify_id='test_playlist_id',
        api_url='https://api.spotify.com/v1/playlists/test_playlist_id',
        web_url='https://open.spotify.com/playlist/test_playlist_id',
        cover_url='https://mosaic.scdn.co/640/test_url_token640',
        name='Tarantino',
        is_public=False,
        owner_name='Valentin',
    )
    in_memory_database.commit()

    utils.add_current_user_playlists_response([
        utils.playlist_factory(
            name="Tarantino Tunes",
            owner={
                'display_name': "Valentin",
            },
        )
    ])

    utils.add_playlist_tracks_response([])

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='playlists'))

    assert logging_mock.info.call_args_list == []

    assert in_memory_database.select_from('Playlist', ['name']) == [
        ('Tarantino Tunes',),
    ]


@responses.activate
def test_pull_playlist_add_track(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    1 playlist with 1 tracks. 1 new track in Spotify, to be added in database.
    """
    in_memory_database.insert_into('Playlist',
        spotify_id='test_playlist_id',
        api_url='https://api.spotify.com/v1/playlists/test_playlist_id',
        web_url='https://open.spotify.com/playlist/test_playlist_id',
        cover_url='https://mosaic.scdn.co/640/test_url_token640',
        name='Tarantino',
        is_public=False,
        owner_name='Valentin',
    )

    in_memory_database.insert_into('Song',
        spotify_id='t1',
        api_url='https://api.spotify.com/v1/tracks/test_track_id',
        web_url='https://open.spotify.com/track/test_track_id',
        name='Son of a Preacher Man',
        cover_url='https://i.scdn.co/image/test_url_token640',
        duration=314159,
        explicit=False,
        isrc='test_isrc',
        is_local=False,
        popularity=74,
        preview_url='https://p.scdn.co/mp3-preview/test_url_token1',
        track_number=15,
        album_id='test_album_id',
        album_name='Dusty in Memphis',
        artists_names='Dusty Springfield',
    )

    in_memory_database.insert_into('SongInPlaylist',
        song_id='t1',
        playlist_id='test_playlist_id',
        added_at='2020-01-16T08:00:00Z',
    )

    utils.add_current_user_playlists_response([
        utils.playlist_factory(
            name="Tarantino",
            owner={
                'display_name': "Valentin",
            },
        )
    ])

    utils.add_playlist_tracks_response([
        utils.playlist_track_factory(
            added_at='2020-01-16T08:00:00Z',
            track=utils.track_factory(
                id='t1',
                name='Son of a Preacher Man',
                artists=[
                    utils.artist_factory(name='Dusty Springfield'),
                ],
                album=utils.album_factory(name='Dusty in Memphis'),
            ),
        ),
        utils.playlist_track_factory(
            added_at='2020-01-16T08:05:00Z',
            track=utils.track_factory(
                id='t2',
                name='Jungle Boogie',
                artists=[
                    utils.artist_factory(name='Kool & The Gang'),
                ],
                album=utils.album_factory(name='Wild And Peaceful'),
            ),
        ),
    ])

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='playlists'))

    assert logging_mock.info.call_args_list == [
        mocker.call(
            'Added song: %s (%s) in playlist %s (%s)',
            't2', 'Jungle Boogie',
            'test_playlist_id', 'Tarantino',
        )
    ]

    assert set(in_memory_database.select_from('SongInPlaylist', ['*'])) == {
        ('t1', 'test_playlist_id', '2020-01-16T08:00:00Z'),
        ('t2', 'test_playlist_id', '2020-01-16T08:05:00Z'),
    }


@responses.activate
def test_pull_playlist_delete_track(
    statify_config, cached_token, in_memory_database, mocker
):
    """
    1 playlist with 2 tracks. 1 track removed from playlist, association to be
    removed in database.
    """
    in_memory_database.insert_into('Playlist',
        spotify_id='test_playlist_id',
        api_url='https://api.spotify.com/v1/playlists/test_playlist_id',
        web_url='https://open.spotify.com/playlist/test_playlist_id',
        cover_url='https://mosaic.scdn.co/640/test_url_token640',
        name='Tarantino',
        is_public=False,
        owner_name='Valentin',
    )

    in_memory_database.insert_into('Song',
        spotify_id='t1',
        api_url='https://api.spotify.com/v1/tracks/test_track_id',
        web_url='https://open.spotify.com/track/test_track_id',
        name='Son of a Preacher Man',
        cover_url='https://i.scdn.co/image/test_url_token640',
        duration=314159,
        explicit=False,
        isrc='test_isrc',
        is_local=False,
        popularity=74,
        preview_url='https://p.scdn.co/mp3-preview/test_url_token1',
        track_number=15,
        album_id='test_album_id',
        album_name='Dusty in Memphis',
        artists_names='Dusty Springfield',
    )
    in_memory_database.insert_into('Song',
        spotify_id='t2',
        api_url='https://api.spotify.com/v1/tracks/test_track_id',
        web_url='https://open.spotify.com/track/test_track_id',
        name='Jungle Boogie',
        cover_url='https://i.scdn.co/image/test_url_token640',
        duration=314159,
        explicit=0,
        isrc='test_isrc',
        is_local=0,
        popularity=74,
        preview_url='https://p.scdn.co/mp3-preview/test_url_token1',
        track_number=15,
        album_id='test_album_id',
        album_name='Wild And Peaceful',
        artists_names='Kool & The Gang',
    )

    in_memory_database.insert_into('SongInPlaylist',
        song_id='t1',
        playlist_id='test_playlist_id',
        added_at='2020-01-16T08:00:00Z',
    )
    in_memory_database.insert_into('SongInPlaylist',
        song_id='t2',
        playlist_id='test_playlist_id',
        added_at='2020-01-16T08:05:00Z',
    )

    utils.add_current_user_playlists_response([
        utils.playlist_factory(
            name="Tarantino",
            owner={
                'display_name': "Valentin",
            },
        )
    ])

    utils.add_playlist_tracks_response([
        utils.playlist_track_factory(
            added_at='2020-01-16T08:00:00Z',
            track=utils.track_factory(
                id='t1',
                name='Son of a Preacher Man',
                artists=[
                    utils.artist_factory(name='Dusty Springfield'),
                ],
                album=utils.album_factory(name='Dusty in Memphis'),
            ),
        ),
    ])

    logging_mock = mocker.patch('statify.statify.logger')

    statify._main(argparse.Namespace(command='pull', what='playlists'))

    assert logging_mock.info.call_args_list == [
        mocker.call(
            'Deleted song: %s in playlist %s (%s)',
            't2',
            'test_playlist_id', 'Tarantino'
        ),
    ]

    assert set(in_memory_database.select_from('SongInPlaylist', ['*'])) == {
        ('t1', 'test_playlist_id', '2020-01-16T08:00:00Z'),
    }


@responses.activate
def test_pull_playlist_user_not_authenticated(
    statify_config, in_memory_database, mocker
):
    print_mock = mocker.patch('builtins.print')

    statify._main(argparse.Namespace(command='pull', what='playlists'))

    assert print_mock.mock_calls == [
        mocker.call('User not authenticated. Authenticate with `statify auth`')
    ]
