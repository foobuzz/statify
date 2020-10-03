from statify import spotify_client


def test_is_authenticated_with_cached_tokens_file(cached_token):
    # The cached_token fixture creates the tokens in the fake filesystem
    client = spotify_client.Spotify('test_client_id', 'test_client_secret')

    assert client.is_user_authenticated() is True


def test_not_authenticated_without_cached_tokens_file(fs):
    # The fs fixture creates a clean file system
    client = spotify_client.Spotify('test_client_id', 'test_client_secret')

    assert client.is_user_authenticated() is False
