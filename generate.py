#!/Users/ctrl/Developer/miniconda3/bin/python
import os
import spotipy
import pandas as pd
from datetime import datetime, timedelta
from credentials import client_id, client_secret
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

scope = 'user-library-read'
username = 'Christian Tirol'

user = '125065858'

def playlists():
    playlists = sp.user_playlists(user)
    zodiac = []
    while playlists:

        for i, playlist in enumerate(playlists['items']):
            if '*' not in playlist['name']:
                playlist_id, playlist_name, playlist_uri = playlist['id'], playlist['name'], playlist['uri']

                tracks = sp.user_playlist_tracks(user=user,playlist_id=playlist_id)
                tracklist = tracks['items']
                for track in tracklist:
                    track_info = track['track']
                    track_id, track_name, track_uri, added_on = track_info['id'], track_info['name'], track_info['uri'], track['added_at']

                    zodiac.append([playlist_id, playlist_name, playlist_uri, track_id, track_name, track_uri, added_on])


        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

    delimiter = '\t'
    with open('spotify_playlist_info.csv','w') as f:
        f.writelines(delimiter.join(['playlist_id','playlist_name','playlist_uri','track_id','track_name','track_uri','added_on']) + '\n')
        for song in zodiac:
            f.writelines(delimiter.join(song) + '\n')

    print()
    print('Generated spotify_playlist_info.csv')
    
def tracks(df):
    #####

    # generate the arrays first

    playlists = sp.user_playlists(user)
    arr = []

    while playlists:

        for i, playlist in enumerate(playlists['items']):
            if '*' not in playlist['name']:
                print(playlist['name'])
                playlist_length = 0

                playlist_id, playlist_name, playlist_uri = playlist['id'], playlist['name'], playlist['uri']

                tracks = sp.user_playlist_tracks(user=user,playlist_id=playlist_id)
                tracklist = tracks['items']
                for track in tracklist:
                    track_info = track['track']
                    track_id, track_name, track_popularity, track_uri, added_on = track_info['id'], track_info['name'], track_info['popularity'], track_info['uri'], track['added_at']
                    playlist_length += 1
                    print('Song count:', playlist_length, end='\r')

                    track_arr = [playlist_id, playlist_name, playlist_uri, track_id, track_name, track_popularity, track_uri, added_on]
                    #feature_arr = list(sp.audio_features(tracks=['2uPc8UjfmiuzmAJj3VBs8N'])[0].values()) #this takes too long!
                    arr.append(track_arr)# + feature_arr)

                print()

        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

    # either write data to file line by line within loops, or take all arrays, stuff them into a dataframe, and write to csv

    df = pd.DataFrame(arr,columns=[
        'playlist_id', 
        'playlist_name', 
        'playlist_uri', 
        'track_id', 
        'track_name', 
        'track_popularity', 
        'track_uri', 
        'added_on'])
    df.to_csv('spotify_playlist_info.csv',index=False)

    counter = 0
    for track_id in df['track_id']:
        counter += 1
        d = sp.audio_features(tracks=[track_id])[0]
        for i in d:
            print('\r',len(df)-counter,'of',len(df),'remaining |',end='')
            df.loc[df['track_id'] == d['id'],i] = d[i]

    df['time_added'] = [datetime.strptime(dt,'%Y-%m-%dT%H:%M:%SZ').time() for dt in df['added_on']]
    df['date_added'] = [datetime.strptime(dt,'%Y-%m-%dT%H:%M:%SZ').date() for dt in df['added_on']]
    df['hour_added'] = [datetime.strptime(dt,'%Y-%m-%dT%H:%M:%SZ').hour for dt in df['added_on']]
    df['day_added'] = [datetime.strptime(dt,'%Y-%m-%dT%H:%M:%SZ').isoweekday() for dt in df['added_on']]
    df['month_added'] = [datetime.strptime(dt,'%Y-%m-%dT%H:%M:%SZ').month() for dt in df['added_on']]

    print()
    df.to_csv('spotify_track_info.csv',index=False)

    print('Generated spotify_track_info.csv')
    
def artists(df):
    #####
    df['artist_id'] = pd.Series()
    start = datetime.now()
    counter = 0
    for track_id in df['track_id'].unique():
        counter += 1
        if any(df.loc[df['track_id'] == track_id].artist_id.isnull()):
            #print(track_id)
            track_info = sp.track(track_id=track_id)
            featuring = []
            for i in enumerate(track_info['artists']):
                if i[0] == 0: #if this is the first artist of many, make this the recording artist
                    df.loc[df['track_id'] == track_id,'track_artist'] = i[1]['name']
                    df.loc[df['track_id'] == track_id,'artist_id'] = i[1]['id']
                    #print('By:',i[1]['name'])
                else: #otherwise, add any other artists as feature artists
                    featuring.append(i[1]['name'])

            df.loc[df['track_id'] == track_id,'featured_artists'] = ', '.join(featuring)
            #print('Featuring:',', '.join(featuring))
        sec_elapsed = (datetime.now() - start).total_seconds()
        tps = counter/sec_elapsed
        tracks_left = len(df.track_id.unique()) - counter
        min_left = tracks_left / tps  / 60
        total_count = len(df.track_id.unique())
        print('\r', sec_elapsed,'seconds elapsed |',tps,'tps |',min_left,'minutes remaining |',tracks_left,'of',total_count,'remaining',end='')
        print()

    df.to_csv('spotify_track_with_artist_info.csv',index=False)
    print('Generated spotify_track_with_artist_info.csv')
    
def genres(df):
    #####
    df['artist_genres'] = pd.Series()
    start = datetime.now()
    counter = 0

    for artist_id in df['artist_id'].unique():
        counter += 1
        if any(df.loc[df['artist_id'] == artist_id].artist_genres.isnull()):
            artist_info = sp.artist(artist_id)
            df.loc[df['artist_id'] == artist_id,'artist_popularity'] = artist_info['popularity']
            df.loc[df['artist_id'] == artist_id,'artist_followers'] = artist_info['followers']['total']
            df.loc[df['artist_id'] == artist_id,'artist_genres'] = ', '.join(artist_info['genres'])

            sec_elapsed = (datetime.now() - start).total_seconds()
            aps = counter / sec_elapsed
            artists_left = len(df.artist_id.unique()) - counter
            sec_left = artists_left / aps
            total_count = len(df.artist_id.unique())
        print('\r',sec_elapsed,'seconds elapsed |',aps,'aps |',sec_left,'seconds remaining |',artists_left,'of',total_count,'remaining',end='')

    df.to_csv('spotify_track_with_genres.csv',index=False)
    print('Generated spotify_track_with_genres.csv')
    
def main():
    print(os.getcwd())
    try: 
        os.lstat('spotify_playlist_info.csv')
        print('Skipping playlists()...')
    except FileNotFoundError as err:
        playlists()

    try:
        os.lstat('spotify_track_info.csv')
        print('Skipping tracks()...')
    except FileNotFoundError as err:
        df = pd.read_csv('spotify_playlist_info.csv',delimiter='\t')
        tracks(df)
    
    try:
        os.lstat('spotify_track_with_artist_info.csv')
        print('Skipping artists()...')
    except FileNotFoundError as err:
        df = pd.read_csv('spotify_track_info.csv')
        artists(df)

    try:
        os.lstat('spotify_track_with_genres.csv')
        print('Done!')
    except FileNotFoundError as err:
        df = pd.read_csv('spotify_track_with_artist_info.csv')
        genres(df)
    
if __name__ == '__main__':
    main()