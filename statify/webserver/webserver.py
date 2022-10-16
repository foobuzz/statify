from datetime import datetime

import flask

from statify import database_client


app = flask.Flask(__name__)
db_client = database_client.StatifyDatabase()


# Front

@app.route('/song/<spotify_id>')
def song_page(spotify_id):
    song_data = db_client.select_song_by_spotify_id(spotify_id)
    return flask.render_template('song.html', song=song_data)


# API

@app.route('/api/listenings/<spotify_id>')
def song_endpoint(spotify_id):
    listenings = db_client.select_listenings_by_spotify_id(spotify_id)
    return flask.jsonify([listening_resource(l) for l in listenings])



def listening_resource(listening):
    return {
        **listening,
        'played_at': datetime.strptime(
            listening['played_at'][:19],
            '%Y-%m-%dT%H:%M:%S',
        ).timestamp()
    }


def main():
    app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
