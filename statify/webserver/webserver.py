from datetime import datetime, timezone

import flask

from statify import database_client
from statify.webserver import search


app = flask.Flask(__name__)


@app.before_request
def ensure_db_client():
    flask.g.db_client = database_client.StatifyDatabase()


# Front

@app.route('/')
def front_page():
    return flask.render_template('index.html')


@app.route('/song/<spotify_id>')
def song_page(spotify_id):
    song_data = flask.g.db_client.select_song_by_spotify_id(spotify_id)
    return flask.render_template('song.html', song=song_data)


# API

@app.route('/api/listenings/<spotify_id>')
def listenings_endpoint(spotify_id):
    listenings = flask.g.db_client.select_listenings_by_spotify_id(spotify_id)
    return flask.jsonify([listening_resource(lisng) for lisng in listenings])


@app.route('/api/autocomplete')
def autocomplete_endpoint():
    query = flask.request.args['query']
    words = [w.lower() for w in query.split()]

    results = flask.g.db_client.search_songs(words)

    results.sort(
        key=lambda s: search.match_song_to_query(words=words, song=s),
        reverse=True,
    )

    return flask.jsonify(results)


def listening_resource(listening):
    return {
        **listening,
        'played_at': int(datetime.strptime(
            listening['played_at'][:19],
            '%Y-%m-%dT%H:%M:%S',
        ).replace(tzinfo=timezone.utc).timestamp())
    }


def main():
    app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
