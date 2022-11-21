from statify.webserver.search import match_song_to_query


def test_match_song_to_query():
    song = {
        'id': 1,
        'name': "You Need To Calm Down",
        'artists_names': "Taylor Swift",
    }

    queries = [
        "you need to calm down taylor swift",
        "you need to calm down taylor",
        "you need to calm down",
        "calm taylor swift",
        "you need",
        "calm down",
        "shakira",
    ]

    scores = [match_song_to_query(q.split(' '), song) for q in queries]

    assert sorted(scores, reverse=True) == scores
    assert len(set(scores)) == len(scores)
