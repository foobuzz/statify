from typing import List


def match_song_to_query(words: List[str], song: dict):
    score = 0
    for w in words:
        for field in ['name', 'artists_names']:
            if w in song[field].lower():
                score += 1
    return score
