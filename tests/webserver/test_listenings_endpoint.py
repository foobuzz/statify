import flask

from .. import utils


def test_listenings_endpoint(client, in_memory_database):
    song = utils.song_factory(in_memory_database)
    listenings = [
        utils.listening_factory(
            in_memory_database, song=song, played_at=played_at
        )
        for played_at in [
            '2020-07-08T20:30:31.881Z',
            '2020-07-08T20:38:45.472Z',
            '2022-10-03T14:35:02.333Z',
        ]
    ]

    response = client.get(flask.url_for(
        'listenings_endpoint',
        spotify_id=song.spotify_id,
    ))

    assert response.status_code == 200
    assert len(response.json) == 3
    assert response.json[0] == {
        'album_id': None,
        'context': None,
        'listening_id': 1,
        'played_at': 1594233031,
        'playlist_id': None,
        'song_id': '1OppEieGNdItZbE14gLBEv',
    }
