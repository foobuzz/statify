import argparse
import hashlib
import logging
import os.path
import sys

import yaml
from pypika import Query, Order

from . import config
from . import database_client
from . import spotify_client


__version__ = config.VERSION


DEFAULT_LOGGING_FILE = config.STATIFY_PATH / 'statify.log'


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(prog='statify')
    subparsers = parser.add_subparsers(dest='command')

    pull_parser = subparsers.add_parser('pull')
    pull_parser.add_argument('what', nargs='?', default='all')

    auth_parser = subparsers.add_parser('auth')
    auth_parser.add_argument('--headless', action='store_true')

    args = parser.parse_args()

    code = _main(args)
    if code is None:
        code = 0
    sys.exit(code)


def _main(args):
    # Ensuring data directory exists
    if not os.path.exists(str(config.STATIFY_PATH)):
        os.makedirs(str(config.STATIFY_PATH))

    # Loading config
    conf = get_config()
    if conf is None:
        print(
            "Invalid configuration. Please add your client_id and client_secret "
            "in {}:\n\n"
            "spotify_app:\n"
            "  client_id: your client ID\n"
            "  client_secret: your client secret".format(config.CONFIG_PATH)
        )
        return 1

    # Logging
    conf_logging = conf.get('logging', {})
    if 'filepath' in conf_logging:
        logfile_path = conf_logging['filepath']
    else:
        logfile_path = str(DEFAULT_LOGGING_FILE)
    setup_logging(filepath=logfile_path)

    # Spotify client
    spotify_client_args = {
        'client_id': conf['spotify_app']['client_id'],
        'client_secret': conf['spotify_app']['client_secret'],
        'track_transformer': idify_local_track,
    }
    if conf.get('throttling') is not None:
        spotify_client_args['throttling'] = conf.get('throttling')
    spotify = spotify_client.Spotify(**spotify_client_args)

    # Database client
    try:
        database = database_client.StatifyDatabase()
    except database_client.DowngradeVersionError as err:
        print(
            "Statify version {} is running but the database is setup for "
            "version {}. Downgrading the database is not supported so you "
            "should install statify {} or higher.".format(
                __version__,
                err.version,
                err.version,
            )
        )
        return 1

    # Argument dispatching
    if args.command == 'auth':
        spotify.authenticate_user(args.headless)
    elif args.command == 'pull':
        if not spotify.is_user_authenticated():
            print("User not authenticated. Authenticate with `statify auth`")
        else:
            if args.what in ['playlists', 'all']:
                pull_playlists(spotify, database)
            if args.what in ['listenings', 'all']:
                pull_listenings(spotify, database)


def get_config():
    if os.path.exists(str(config.CONFIG_PATH)):
        with open(str(config.CONFIG_PATH)) as config_file:
            conf = yaml.safe_load(config_file)
        if any(
            conf.get('spotify_app', {}).get(key) is None for key in [
                'client_id', 'client_secret',
            ]
        ):
            conf = None
    else:
        conf = None
    return conf


def setup_logging(filepath=None):
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    logger.addHandler(stdout_handler)

    if filepath is not None:
        logfile_handler = logging.FileHandler(filepath)
        logfile_handler.setLevel(logging.DEBUG)
        logfile_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s (%(filename)s:%(lineno)d) [%(levelname)s] - '
                '%(message)s'
            )
        )
        logger.addHandler(logfile_handler)


def idify_local_track(resource):
    """
    Add a spoof ID to local tracks based on name, artists' names and
    duration, since Spotify gives no ID for local tracks. Mutate the
    resource in place and return it.
    """
    if resource['id'] is None and resource['is_local']:
        resource['id'] = get_local_song_id(resource)
    return resource


def get_local_song_id(resource):
    h = hashlib.sha256('{}:{}:{}'.format(
        resource.get('name'),
        denormalize_artists(resource),
        resource.get('duration')
    ).encode('utf8'))
    return 'local:{}'.format(h.hexdigest())


def denormalize_artists(resource):
    return ', '.join(sorted([a['name'] for a in resource['artists']]))


def pull_playlists(spotify, database):
    playlists = spotify.current_user_playlists()
    for playlist_resource in playlists:
        playlist_obj = playlist_from_resource(playlist_resource)
        database.insert_or_update(playlist_obj, 'spotify_id')
        database.commit()

        # Syncing playlist tracks
        spotify_tracks = list(spotify.playlist_tracks(playlist_obj.spotify_id))
        spotify_tracks_ids = set(t['track']['id'] for t in spotify_tracks)
        saved_tracks_ids = set(
            row[0] for row in database.select_from(
                'SongInPlaylist',
                ['song_id'],
                playlist_id=playlist_obj.spotify_id,
            )
        )

        # Removing tracks in the database but not in Spotify
        for track_id in saved_tracks_ids:
            if track_id not in spotify_tracks_ids:
                database.delete_from(
                    'SongInPlaylist',
                    song_id=track_id,
                    playlist_id=playlist_obj.spotify_id,
                )
                logger.info(
                    "Deleted song: %s in playlist %s (%s)",
                    track_id,
                    playlist_obj.spotify_id,
                    playlist_obj.name,
                )

        # Adding tracks in spotify but not in the database
        for track in spotify_tracks:
            if track['track']['id'] not in saved_tracks_ids:
                song_obj = song_from_resource(track['track'])
                # First insert track if not existing (or update)
                insert_song(database, track['track'])
                # Then insert association between track and playlist
                database.insert_into(
                    'SongInPlaylist',
                    song_id=song_obj.spotify_id,
                    playlist_id=playlist_obj.spotify_id,
                    added_at=track['added_at'],
                )
                logger.info(
                    "Added song: %s (%s) in playlist %s (%s)",
                    song_obj.spotify_id,
                    song_obj.name,
                    playlist_obj.spotify_id,
                    playlist_obj.name,
                )
        database.commit()


def pull_listenings(spotify, database):
    last_known_listening = database.query(
        Query
        .from_('Listening')
        .select('played_at')
        .orderby('played_at', order=Order.desc)
        .limit(1)
    ).fetchone()

    if last_known_listening is None:
        last_known_played_at = None
    else:
        last_known_played_at = last_known_listening[0]

    listenings = spotify.current_user_recently_played()
    newest_played_at = None
    oldest_played_at = None
    nb_inserted = 0
    for i, listening in enumerate(listenings):
        listening_obj = listening_from_resource(listening)
        if i == 0:
            newest_played_at = listening_obj.played_at
        if listening_obj.played_at == last_known_played_at:
            logger.info(
                "Match previous listenings fetch at %s", last_known_played_at
            )
            break
        insert_song(database, listening['track'])
        database.insert(listening_obj)
        nb_inserted += 1
        oldest_played_at = listening_obj.played_at
    else:
        logger.info(
            "No match for previous listenings fetch. Hole between "
            "%s and %s", last_known_played_at, oldest_played_at,
        )

    database.commit()
    logger.info(
        "Added %s listenings. Newest played_at is now %s",
        nb_inserted, newest_played_at
    )


def insert_song(database, track):
    # Insert album
    if not track['is_local']:
        album_resource = track.get('album')
        if album_resource is not None:
            album_obj = album_from_resource(album_resource)
            database.insert_or_leave(album_obj, 'spotify_id')

    # Insert song
    # The song object contains the album_id
    song_obj = song_from_resource(track)
    added_song = database.insert_or_leave(song_obj, 'spotify_id')

    # Insert arists
    if added_song and not track['is_local']:
        for artist_resource in track['artists']:
            artist_obj = artist_from_resource(artist_resource)
            added_artist = database.insert_or_leave(artist_obj, 'spotify_id')
            if added_artist:
                database.insert_into(
                    'SongByArtist',
                    song_id=song_obj.spotify_id,
                    artist_id=artist_obj.spotify_id,
                )


def song_from_resource(resource):
    album_resource = resource.get('album')
    cover_url = None
    if album_resource is not None:
        cover_url = get_cover_url(album_resource)

    return database_client.Song(
        name=resource['name'],
        cover_url=cover_url,
        duration=resource['duration_ms'],
        explicit=resource['explicit'],
        isrc=resource.get('external_ids', {}).get('isrc'),
        is_local=resource['is_local'],
        popularity=resource['popularity'],
        preview_url=resource['preview_url'],
        track_number=resource['track_number'],
        album_id=album_resource.get('id'),
        album_name=album_resource.get('name'),
        artists_names=denormalize_artists(resource),
        **get_resource_basics(resource),
    )


def album_from_resource(resource):
    return database_client.Album(
        name=resource['name'],
        release_date=resource['release_date'],
        release_date_precision=resource['release_date_precision'],
        type=resource['album_type'],
        cover_url=get_cover_url(resource),
        **get_resource_basics(resource),
    )


def artist_from_resource(resource):
    return database_client.Artist(
        name=resource['name'],
        **get_resource_basics(resource),
    )


def playlist_from_resource(resource):
    return database_client.Playlist(
        cover_url=get_cover_url(resource),
        name=resource['name'],
        owner_name=resource.get('owner', {}).get('display_name'),
        is_public=resource.get('public'),
        **get_resource_basics(resource),
    )


def listening_from_resource(resource):
    context = None
    album_id = None
    playlist_id = None

    context_resource = resource.get('context')
    if context_resource is not None:
        context = context_resource['type']
        context_id = parse_id_from_context(context_resource)
        if context == 'album':
            album_id = context_id
        if context == 'playlist':
            playlist_id = context_id

    return database_client.Listening(
        song_id=resource['track']['id'],
        played_at=resource['played_at'],
        context=context,
        album_id=album_id,
        playlist_id=playlist_id,
    )


def parse_id_from_context(context_resource):
    uri = context_resource.get('uri')
    if uri is None:
        logger.error("Missing URI in context: %s", context_resource)
        return None
    try:
        return uri.split(':')[2]
    except IndexError:
        logger.error("Unparsable URI: %s", uri)
        return None


def get_resource_basics(resource):
    return {
        'spotify_id': resource['id'],
        'api_url': resource.get('href'),
        'web_url': resource.get('external_urls', {}).get('spotify'),
    }


def get_cover_url(resource):
    if 'images' in resource and len(resource['images']) > 0:
        return resource['images'][0].get('url')
    return None


if __name__ == '__main__':
    main()
