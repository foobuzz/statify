import collections
import os
import sqlite3
import threading

import pkg_resources
from pypika import Query, PostgreSQLQuery, Parameter, Table

from . import config


DATABASE_PATH = config.STATIFY_PATH / 'statify.sqlite'
DATABASE_VERSION_PATH = config.STATIFY_PATH / 'database_version'


Song = collections.namedtuple('Song', [
    'spotify_id',
    'web_url',
    'api_url',
    'duration',
    'explicit',
    'isrc',
    'is_local',
    'name',
    'popularity',
    'preview_url',
    'track_number',
    'album_id',
    'cover_url',
    'album_name',
    'artists_names',
])


Artist = collections.namedtuple('Artist', [
    'spotify_id',
    'web_url',
    'api_url',
    'name',
])


Album = collections.namedtuple('Album', [
    'spotify_id',
    'web_url',
    'api_url',
    'name',
    'release_date',
    'release_date_precision',
    'type',
    'cover_url',
])


Playlist = collections.namedtuple('Playlist', [
    'spotify_id',
    'web_url',
    'api_url',
    'cover_url',
    'name',
    'owner_name',
    'is_public',
])


Listening = collections.namedtuple('Listening', [
    'song_id',
    'played_at',
    'context',      # 'playlist' or 'album' or None
    'album_id',     # if context == 'album'
    'playlist_id',  # if context == 'playlist'
])


class StatifyDatabase:

    def __init__(self, path=str(DATABASE_PATH)):
        self.path = path
        self.connections = {}

        found_version = _get_database_version()

        parse_version = pkg_resources.parse_version
        if (
            found_version is None or
            parse_version(found_version) < parse_version(config.VERSION)
        ):
            updates = _get_database_updates(found_version)
            for sql_statement in updates:
                self._sql(sql_statement)
            self.commit()
            _set_database_version(config.VERSION)
        elif parse_version(found_version) == parse_version(config.VERSION):
            pass
        else:
            raise DowngradeVersionError(
                "Cannot downgrade database.",
                version=found_version,
            )

    def _execute(self, query, params=None):
        return self._sql(str(query), params)

    def _sql(self, query, params=None):
        current_thread_id = threading.get_ident()
        if self.connections.get(current_thread_id) is None:
            connection = sqlite3.connect(self.path)
            self.connections[current_thread_id] = connection
        else:
            connection = self.connections[current_thread_id]
        c = connection.cursor()
        if params is None:
            c.execute(query)
        else:
            c.execute(query, params)
        return c

    def insert(self, data):
        tuple_type = type(data)
        q = (
            Query.into(tuple_type.__name__)
            .columns(*tuple_type._fields)
            .insert(*_pypika_params(len(tuple_type._fields)))
        )
        c = self._execute(q, data)
        return c.rowcount > 0

    def insert_or_update(self, data, conflict_column):
        tuple_type = type(data)
        q = self._insert_on_conflict(data, conflict_column)
        for field_name, value in zip(tuple_type._fields, data):
            q = q.do_update(field_name, Parameter('?'))
        # 2*data = one time for insert and second time for do update
        c = self._execute(q, 2 * data)
        return c.rowcount > 0

    def insert_or_leave(self, data, conflict_column):
        q = self._insert_on_conflict(data, conflict_column)
        q = q.do_nothing()
        c = self._execute(q, data)
        return c.rowcount > 0

    def _insert_on_conflict(self, data, conflict_column):
        tuple_type = type(data)
        return (
            PostgreSQLQuery.into(tuple_type.__name__)
            .columns(*tuple_type._fields)
            .insert(*_pypika_params(len(tuple_type._fields)))
            .on_conflict(conflict_column)
        )

    def select_from(self, table_name, columns, **selectors):
        table = Table(table_name)
        q = Query.from_(table).select(*columns)
        params = []
        for col, value in selectors.items():
            q = q.where(getattr(table, col) == Parameter('?'))
            params.append(value)
        return self._execute(q, tuple(params)).fetchall()

    def delete_from(self, table_name, **selectors):
        table = Table(table_name)
        q = Query.from_(table).delete()
        params = []
        for col, value in selectors.items():
            q = q.where(getattr(table, col) == Parameter('?'))
            params.append(value)
        return self._execute(q, tuple(params))

    def insert_into(self, table_name, **values):
        values = [(col, val) for col, val in values.items()]
        q = (Query.into(table_name)
             .columns(*(t[0] for t in values))
             .insert(*_pypika_params(len(values))))
        return self._execute(q, tuple(t[1] for t in values))

    def query(self, q, *params):
        return self._execute(q, params)

    def commit(self):
        connection = self.connections.get(threading.get_ident())
        if connection is not None:
            connection.commit()

    def close(self):
        connection = self.connections.get(threading.get_ident())
        if connection is not None:
            connection.close()


class DowngradeVersionError(Exception):

    def __init__(self, message, version):
        super().__init__(message)
        self.version = version


# SQL utils

def _pypika_params(n):
    return [Parameter('?') for _ in range(n)]


# Database version management

def _get_database_version():
    if not os.path.exists(str(DATABASE_VERSION_PATH)):
        return None
    with open(str(DATABASE_VERSION_PATH)) as f:
        return f.read().strip()


def _set_database_version(version):
    with open(str(DATABASE_VERSION_PATH), 'w') as f:
        f.write(version)


V1_0_STATEMENTS = [
    """
    CREATE TABLE `Artist` (
        `spotify_id` TEXT PRIMARY KEY,
        `api_url`    TEXT,
        `web_url`    TEXT,
        `name`       TEXT
    );
    """,
    """
    CREATE TABLE `Album` (
        `spotify_id`             TEXT PRIMARY KEY,
        `api_url`                TEXT,
        `web_url`                TEXT,
        `cover_url`              TEXT,
        `name`                   TEXT,
        `release_date`           TEXT,
        `release_date_precision` TEXT,
        `type`                   TEXT
    );
    """,
    """
    CREATE TABLE `Playlist` (
        `spotify_id`   TEXT PRIMARY KEY,
        `api_url`      TEXT,
        `web_url`      TEXT,
        `cover_url`    TEXT,
        `name`         TEXT,
        `is_public`    TEXT,
        `owner_name`   TEXT
    );
    """,
    """
    CREATE TABLE `Song` (
        `spotify_id`    TEXT PRIMARY KEY,
        `api_url`       TEXT,
        `web_url`       TEXT,
        `name`          TEXT,
        `cover_url`     TEXT,
        `duration`      INTEGER,
        `explicit`      INTEGER,
        `isrc`          TEXT,
        `is_local`      INTEGER,
        `popularity`    INTEGER,
        `preview_url`   TEXT,
        `track_number`  INTEGER,
        `album_id`      TEXT,
        `album_name`    TEXT,
        `artists_names` TEXT,

        FOREIGN KEY(`album_id`) REFERENCES Album(`spotify_id`)
    );
    """,
    """
    CREATE TABLE `SongByArtist` (
        `song_id`   TEXT,
        `artist_id` TEXT,

        FOREIGN KEY(song_id) REFERENCES Song(spotify_id),
        FOREIGN KEY(artist_id) REFERENCES Artist(spotify_id)
    );
    """,
    """
    CREATE INDEX `ArtistFromSongIx` ON `SongByArtist` (`song_id`, `artist_id`);
    """,
    """
    CREATE INDEX `SongFromArtistIx` ON `SongByArtist` (`artist_id`, `song_id`);
    """,
    """
    CREATE TABLE `SongInPlaylist` (
        `song_id`     TEXT,
        `playlist_id` TEXT,
        `added_at`    TEXT,

        FOREIGN KEY(song_id) REFERENCES Song(spotify_id),
        FOREIGN KEY(playlist_id) REFERENCES Playlist(spotify_id)
    );
    """,
    """
    CREATE INDEX `PlaylistFromSongIx`
    ON `SongInPlaylist` (`song_id`, `playlist_id`);
    """,
    """
    CREATE INDEX `SongFromPlayilstIx`
    ON `SongInPlaylist` (`playlist_id`, `song_id`);
    """,
    """
    CREATE TABLE `Listening` (
        `listening_id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `song_id`      TEXT,
        `played_at`    TEXT,
        `context`      TEXT,
        `album_id`     TEXT,
        `playlist_id`  TEXT,

        FOREIGN KEY(album_id) REFERENCES Album(spotify_id),
        FOREIGN KEY(playlist_id) REFERENCES Playlist(spotify_id)
    );
    """,
    """
    CREATE INDEX `SongListeningIx` ON `Listening` (`song_id`);
    """,
    """
    CREATE TABLE `ListeningsRetrieval` (
        `from_after`        INTEGER,
        `to_after`          INTEGER,
        `from_listening_id` INTEGER,
        `to_listening_id`   INTEGER,
        `date`              TEXT,
        `nb_retrieved`      INTEGER,

        FOREIGN KEY(from_listening_id) REFERENCES Listening(listening_id),
        FOREIGN KEY(to_listening_id) REFERENCES Listening(listening_id)
    );
    """,
    """
    CREATE INDEX `RetrievalDateIx` ON `ListeningsRetrieval` (`date`);
    """
]


SQL_INIT_STATEMENTS = V1_0_STATEMENTS


# {version_number: index of the last SQL statement for this version}
SQL_INIT_VERSIONS = {
    '1.0': len(V1_0_STATEMENTS),
}


def _get_database_updates(from_version):
    if from_version is None:
        from_index = 0
    else:
        from_index = SQL_INIT_VERSIONS[from_version] + 1
    to_index = SQL_INIT_VERSIONS[config.VERSION] + 1
    return SQL_INIT_STATEMENTS[from_index:to_index]
