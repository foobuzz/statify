import flask

from .. import utils


def test_front_page(client, in_memory_database):
    response = client.get(
        flask.url_for('front_page')
    )

    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/html')


def test_song_page(client, in_memory_database):
    song = utils.song_factory()
    in_memory_database.insert(song)

    response = client.get(
        flask.url_for(
            'song_page',
            spotify_id=song.spotify_id,
        )
    )

    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/html')
