import random
import string

from statify.database_client import Song, Listening

import responses


def add_current_user_playlists_response(playlists):
    responses.add(
        'GET',
        'https://api.spotify.com/v1/me/playlists',
        json={
            'items': playlists,
            'offset': 0,
            'total': len(playlists),
            'previous': None,
            'href': (
                'https://api.spotify.com/v1/users/test_user_id/playlists'
                '?offset=0&limit=50'
            ),
            'limit': 50,
            'next': None,
        },
        status=200,
    )


def add_playlist_tracks_response(tracks, playlist_id='test_playlist_id'):
    responses.add(
        'GET',
        'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id),
        json={
            'items': tracks,
            'offset': 0,
            'total': len(tracks),
            'previous': None,
            'href': (
                'https://api.spotify.com/v1/playlists/{}/tracks'
                '?offset=0&limit=100&additional_types=track'.format(playlist_id)
            ),
            'limit': 50,
            'next': None,
        },
        status=200,
    )


def add_current_user_recently_played_response(listenings):
    responses.add(
        'GET',
        'https://api.spotify.com/v1/me/player/recently-played',
        json={
            'items': listenings,
            'next': None,
            'cursors': {
                'after': None,
                'before': None,
            },
            'limit': 50,
            'href': 'https://api.spotify.com/v1/me/player/recently-played',
        }
    )


def spotify_playlist_factory(**data):
    playlist = {
        "tracks": {
            "href": ("https://api.spotify.com/v1/playlists/test_playlist_id"
                     "/tracks"),
            "total": 2
        },
        "owner": {
            "type": "user",
            "external_urls": {
                "spotify": "https://open.spotify.com/user/test_user_id"
            },
            "display_name": "Test User Name",
            "href": "https://api.spotify.com/v1/users/test_user_id",
            "id": "test_user_id",
            "uri": "spotify:user:test_user_id"
        },
        "name": "Test Playlist Name",
        "href": "https://api.spotify.com/v1/playlists/test_playlist_id",
        "collaborative": False,
        "description": "",
        "images": [
            {
                "width": 640,
                "url": "https://mosaic.scdn.co/640/test_url_token640",
                "height": 640
            },
            {
                "width": 300,
                "url": "https://mosaic.scdn.co/300/test_url_token300",
                "height": 300
            },
            {
                "width": 60,
                "url": "https://mosaic.scdn.co/60/test_url_token60",
                "height": 60
            }
        ],
        "type": "playlist",
        "external_urls": {
            "spotify": "https://open.spotify.com/playlist/test_playlist_id"
        },
        "primary_color": None,
        "uri": "spotify:playlist:test_playlist_id",
        "id": "test_playlist_id",
        "public": False,
        "snapshot_id": "test_snapshot_id",
    }
    playlist.update(data)
    return playlist


def spotify_playlist_track_factory(**data):
    playlist_track = {
        "is_local": False,
        "video_thumbnail": {
            "url": None
        },
        "track": spotify_track_factory(),
        "primary_color": None,
        "added_by": {
            "href": "https://api.spotify.com/v1/users/test_user_id",
            "id": "test_user_id",
            "type": "user",
            "external_urls": {
                "spotify": "https://open.spotify.com/user/test_user_id"
            },
            "uri": "spotify:user:test_user_id"
        },
        "added_at": "2020-01-01T01:02:03Z"
    }
    playlist_track.update(data)
    return playlist_track


def spotify_track_factory(**data):
    track = {
        "album": spotify_album_factory(),
        "is_local": False,
        "track_number": 15,
        "disc_number": 1,
        "popularity": 74,
        "external_ids": {
            "isrc": "test_isrc",
        },
        "track": True,
        "href": "https://api.spotify.com/v1/tracks/test_track_id",
        "type": "track",
        "explicit": False,
        "uri": "spotify:track:test_track_id",
        "id": "test_track_id",
        "preview_url": "https://p.scdn.co/mp3-preview/test_url_token1",
        "episode": False,
        "artists": [spotify_artist_factory()],
        "name": "Test Track Name",
        "duration_ms": 314159,
        "external_urls": {
            "spotify": "https://open.spotify.com/track/test_track_id"
        },
        "available_markets": ['FR', 'US', 'UK'],
    }
    track.update(data)
    return track


def spotify_artist_factory(**data):
    artist = {
        "id": "test_artist_id",
        "href": "https://api.spotify.com/v1/artists/test_artist_id",
        "name": "Test Artist Name",
        "type": "artist",
        "external_urls": {
            "spotify": "https://open.spotify.com/artist/test_artist_id",
        },
        "uri": "spotify:artist:test_artist_id",
    }
    artist.update(data)
    return artist


def spotify_album_factory(**data):
    album = {
        "href": "https://api.spotify.com/v1/albums/test_album_id",
        "images": [
            {
                "height": 640,
                "width": 640,
                "url": "https://i.scdn.co/image/test_url_token640"
            },
            {
                "height": 300,
                "width": 300,
                "url": "https://i.scdn.co/image/test_url_token300"
            },
            {
                "height": 64,
                "width": 64,
                "url": "https://i.scdn.co/image/test_url_token64"
            }
        ],
        "release_date_precision": "day",
        "id": "test_album_id",
        "album_type": "album",
        "artists": [spotify_artist_factory()],
        "uri": "spotify:album:test_album_id",
        "release_date": "1999-03-10",
        "total_tracks": 12,
        "name": "Test Album Name",
        "external_urls": {
            "spotify": "https://open.spotify.com/album/test_album_id"
        },
        "type": "album",
        "available_markets": ['FR', 'US', 'UK']
    }
    album.update(data)
    return album


def spotify_listening_factory(**data):
    listening = {
        'track': spotify_track_factory(),
        'played_at': '2020-05-23T11:46:13.123Z',
        'context': spotify_listening_context_factory(),
    }
    listening.update(data)
    return listening


def spotify_listening_context_factory(**data):
    listening_context = {
        'external_urls': {
            'spotify': 'https://open.spotify.com/playlist/test_playlist_id',
        },
        'href': 'https://api.spotify.com/v1/playlists/test_playlist_id',
        'type': 'playlist',
        'uri': 'spotify:playlist:test_playlist_id',
    }
    listening_context.update(data)
    return listening_context


def song_factory(database, **data):
    spotify_id = spotify_id_factory()

    song_data = {
        'spotify_id': spotify_id,
        'web_url': f'https://open.spotify.com/track/{spotify_id}',
        'api_url': f'https://api.spotify.com/v1/tracks/{spotify_id}',
        'duration': 167933,
        'explicit': 0,
        'isrc': 'USMO16600346',
        'is_local': 0,
        'name': "You Can't Hurry Love",
        'popularity': 74,
        'preview_url': 'https://p.scdn.co/mp3-preview/toto',
        'track_number': 15,
        'album_id': '5fpOmAuZaVyEXPlQ4oOqJ6',
        'cover_url': 'https://i.scdn.co/image/tada',
        'album_name': "The Supremes A' Go-Go (Expanded Edition)",
        'artists_names': 'The Supremes'
    }
    song_data.update(data)
    song =  Song(**song_data)
    database.insert(song)
    return song


def spotify_id_factory():
    return ''.join([
        random.choice(string.ascii_letters + string.digits)
        for _ in range(22)
    ])


def listening_factory(database, **data):
    song = data.pop('song', None)
    if song is None:
        song = song_factory(database, **data.pop('song_data', {}))
    listening_data = {
        'song_id': song.spotify_id,
        'played_at': '2020-07-08T20:30:31.881Z',
        'context': None,
        'album_id': None,
        'playlist_id': None,
    }
    listening_data.update(data)
    listening = Listening(**listening_data)
    database.insert(listening)
    return listening
