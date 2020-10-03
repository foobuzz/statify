import binascii
import time
import os

import spotipy

from . import config


REDIRECT_URI = 'http://localhost:9090'
SCOPES = [
    'playlist-read-private',
    'user-read-recently-played',
]
OAUTH_TOKENS_PATH = config.STATIFY_PATH / 'oauth_tokens.json'


class Spotify:

    def __init__(
        self, client_id, client_secret, track_transformer=None, throttling=0.5,
    ):
        # Note: Spotify rate limit is not documented. The proper way to deal
        # with it is to look at the `Retry-After` HTTP header, but here we use
        # throttling with a fixed waiting time for simplicity.

        self.client_id = client_id
        self.client_secret = client_secret
        self.track_transformer = track_transformer

        self.oauth_manager = spotipy.oauth2.SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=' '.join(SCOPES),
            cache_path=str(OAUTH_TOKENS_PATH),
            redirect_uri=REDIRECT_URI,
            state=random_string(16),
            open_browser=False,
        )
        tokens_resource = self.oauth_manager.get_cached_token()
        if tokens_resource is None:
            self.token = None
            self.sp = None
        else:
            self.token = tokens_resource['access_token']
            self.sp = spotipy.client.Spotify(self.token)

        # Throttling
        self._last_call_time = 0
        self._throttling = throttling

    def authenticate_user(self, headless=False):
        code = self.oauth_manager.get_auth_response(open_browser=(not headless))
        self.token = self.oauth_manager.get_access_token(code, as_dict=False)
        self.sp = spotipy.client.Spotify(self.token)

    def is_user_authenticated(self):
        return self.token is not None

    def _check_user_authenticated(self):
        if not self.is_user_authenticated():
            raise Exception("User is not authenticated")

    def _throttle(self):
        time_passed = time.time() - self._last_call_time
        if time_passed < self._throttling:
            time.sleep(self._throttling - time_passed)
        self._last_call_time = time.time()

    def _paginate_spotipy_method(self, method, *args, page_size=50, **kwargs):
        retrieved = 0
        total = None
        page = 0
        while total is None or retrieved < total:
            self._throttle()
            paginated_resource = method(
                *args,
                limit=page_size,
                offset=page*page_size,
                **kwargs,
            )
            retrieved += len(paginated_resource['items'])
            total = paginated_resource['total']
            page += 1
            for item in paginated_resource['items']:
                yield item

    def _paginate_bidirectional_spotipy_method(
        self, method, *args, page_size=50, direction='before', **kwargs
    ):
        cursor = None
        over = None
        while not over:
            params = {
                'limit': page_size,
                direction: cursor,
                **kwargs,
            }
            self._throttle()
            paginated_resource = method(*args, **params)
            for item in paginated_resource['items']:
                yield item
            cursors = paginated_resource['cursors']
            if cursors is not None:
                new_cursor = cursors.get(direction)
            else:
                new_cursor = None
            if new_cursor is None or new_cursor == cursor:
                over = True
            else:
                cursor = new_cursor

    def current_user_playlists(self):
        self._check_user_authenticated()
        return self._paginate_spotipy_method(
            self.sp.current_user_playlists,
            page_size=50,  # Max allowed
        )

    def playlist_tracks(self, playlist_id):
        self._check_user_authenticated()
        for p_track in self._paginate_spotipy_method(
            self.sp.playlist_tracks,
            playlist_id,
            page_size=100,  # Max allowed
        ):
            if self.track_transformer is not None:
                p_track['track'] = self.track_transformer(p_track['track'])
            yield p_track

    def current_user_recently_played(self):
        self._check_user_authenticated()
        for listening in self._paginate_bidirectional_spotipy_method(
            self.sp.current_user_recently_played,
            page_size=50,  # Max allowed
        ):
            if self.track_transformer is not None:
                listening['track'] = self.track_transformer(listening['track'])
            yield listening


# Utils

def random_string(nb_bytes):
    return binascii.hexlify(os.urandom(nb_bytes)).decode('utf8')
