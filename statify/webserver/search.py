from typing import List


def match_song_to_query(words: List[str], song: dict):
    score = 0
    for w in words:
        for field in ['name', 'artists_names']:
            value = song[field].lower()
            value_tokens = value.split()

            if w in value:
                score += 1
            if value.startswith(w):
                score += 1
            if w in value_tokens:
                score += 1
            if value_tokens[0] == w:
                score += 1
            if w == value:
                score += 1

    print(song['name'], song['artists_names'], score)
    return score
