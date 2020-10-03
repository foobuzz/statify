-- Top 100 songs most listened to

select max(song.artists_names), max(song.name), count(song_id) as play_count from listening
join song on listening.song_id = song.spotify_id
group by song_id
order by play_count desc
limit 100;


-- Top 100 artists most listened to

select artists_names, count(artists_names) as play_count from song
join listening on listening.song_id = song.spotify_id
group by artists_names
order by play_count desc
limit 100;


-- Top 100 albums most listened to

select album.name, count(*) as play_count from listening
join album on listening.album_id = album.spotify_id
where listening.context = 'album'
group by album_id
order by play_count desc
limit 100;


-- Most looped over songs
select
    song.artists_names,
    song.name,
    count(*) as nb_loops,
    sum(loop_count) as total_looped,
    max(loop_count) as longest_loop,
    avg(loop_count) as avg_loop_length
from (
    select song_id, count(*) as loop_count
    from (
        select
            song_id,
            (
                row_number() over (order by played_at desc) -
                row_number() over (partition by song_id order by played_at desc)
            ) as loop_id
        from listening
    )
    group by song_id, loop_id
) loops
join song on song.spotify_id = loops.song_id
where loops.loop_count > 1
group by loops.song_id
order by total_looped desc
limit 100;


-- Top 100 days by number of listenings

select substr(played_at, 0, 11) as day, count(*) as play_count from listening
group by day
order by play_count desc
limit 100;


-- Number of listenings per hour of the day

select substr(played_at, 12, 2) as hourofday, count(*) from listening
group by hourofday
order by hourofday;


-- Most popular songs on Spotify retrieved from your playlists and listenings

select group_concat(artist.name), max(song.name), max(song.popularity) from song
join songbyartist on song.spotify_id = songbyartist.song_id
join artist on songbyartist.artist_id = artist.spotify_id
group by song.spotify_id
order by song.popularity desc
limit 20;


-- Number of songs per decade in a given playlist

select substr(album.release_date, 0, 4)||'0' as decade, count(*) from song
join songinplaylist sip on sip.song_id = song.spotify_id
join playlist on playlist.spotify_id = sip.playlist_id
join album on album.spotify_id = song.album_id
where playlist.name = 'TOP SONGS'
group by decade
order by decade;