import flask

from .. import utils


def test_autocomplete_endpoint(client, in_memory_database):
    song1 = utils.song_factory(in_memory_database, name="Aliens are awesome")
    song2 = utils.song_factory(in_memory_database, name="Pew pew pew")

    response1 = client.get(
        flask.url_for('autocomplete_endpoint'),
        query_string={
            'query': "awesome",
        },
    )

    assert response1.status_code == 200
    assert len(response1.json) == 1
    assert response1.json[0]['spotify_id'] == song1.spotify_id

    response2 = client.get(
        flask.url_for('autocomplete_endpoint'),
        query_string={
            'query': "pew",
        },
    )

    assert response2.status_code == 200
    assert len(response2.json) == 1
    assert response2.json[0]['spotify_id'] == song2.spotify_id
