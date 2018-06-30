
import lyricwikia
import json
import time
import sys

import urllib.request
import urllib.parse
import re

# https://www.codeproject.com/Articles/873060/Python-Search-Youtube-for-Video
def get_yt_url(keyword):
    query_string = urllib.parse.urlencode({"search_query" : keyword})
    html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
    return "http://www.youtube.com/watch?v=" + search_results[0]

first_unused_songid = 1
first_unused_albumid = 1
first_unused_artistid = 1

songs = []
albums = []
belongtos = []
artists = []
releases = []
artist2ArtistID = {}

yt_sleep_interval = 10
lyric_sleep_interval = 10

with open('mard/mard_metadata.json') as f:
    for line in f.readlines():
        data = json.loads(line)
        if 'salesRank' not in data:
            continue
        if 'Music' not in data['salesRank']:
            continue
        if data['salesRank']['Music'] > 1234: # we only care popular albums
            continue
        if 'artist' not in data:
            continue
        if 'songs' in data:
            for s in data['songs']:
                print("trying to get lyrics of {", "artist: ", data['artist'], "; album title: ", data['title'], "; track title: ", s['title'], "}", file=sys.stderr)
                lyrics = ""
                for attempt_lyric in range(3):
                    try:
                        time.sleep(lyric_sleep_interval)
                        lyrics = lyricwikia.get_lyrics(data['artist'], s['title'])
                    except lyricwikia.LyricsNotFound:
                        print("lyric not found")
                        break
                    except Exception as e:
                        print("failed to get lyric, retrying...")
                        lyric_sleep_interval *= 2
                    else:
                        break
                if lyrics != "":
                    youtube_link = ""
                    for attempt in range(10):
                        try:
                            time.sleep(yt_sleep_interval)
                            youtube_link = get_yt_url(data['artist'] + " " + s['title']);
                        except Exception as e:
                            print("youtube exception: ", e)
                            yt_sleep_interval *= 2
                            print("new yt_sleep_interval = ", yt_sleep_interval)
                        else:
                            print(youtube_link)
                            break
                    else:
                        print("fails to get the song link for the song...")
                        continue
                    songs.append( { "pk": first_unused_songid
                                  , "model": "music.song"
                                  , "fields": { "SongID": first_unused_songid
                                              , "SongName": s['title']
                                              , "SongLyrics": lyrics
                                              , "SongLink": youtube_link
                                              }
                                  }
                                )
                    belongtos.append( { "model": "music.belongto"
                                      , "fields": { "AlbumID": first_unused_albumid, "SongID": first_unused_songid }
                                      }
                                    )
                    first_unused_songid += 1
            if data['artist'] not in artist2ArtistID:
                artists.append( { "pk": first_unused_artistid
                                , "model": "music.artist"
                                , "fields": { "ArtistID": first_unused_artistid, "ArtistName": data['artist'] }
                                }
                              )
                artist2ArtistID[data['artist']] = first_unused_artistid
                first_unused_artistid += 1
            releases.append( { "model": "music.release"
                             , "fields": { "ArtistID": artist2ArtistID[data['artist']], "AlbumID": first_unused_albumid}
                             }
                           )
            albums.append( { "pk": first_unused_albumid
                           , "model": "music.album"
                           , "fields": { "AlbumID": first_unused_albumid, "AlbumName": data['title'] }
                           }
                         )
            first_unused_albumid += 1

with open('output.json', 'w') as outfile:
    json.dump(songs + albums + belongtos + artists + releases, outfile)

