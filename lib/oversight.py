# -*- coding: utf-8 -*-

from pchtrakt.config import *
from lib.utilities import trakt_apiv2
import re
import os
import copy
OversightFile = '/share/Apps/oversight/index.db'
#OversightFile = 'D:\index.db'
Oversight_movies = []
Oversight_movies_seen = []
Oversight_movies_unseen = []
trakt_movies = []
trakt_shows = []

def OversightSync():
    if SyncCheck >= 0:
        if Oversightumc or Oversightumw:
            get_Oversight_movies()
            get_trakt_movies()
            if Oversightumc:
                Oversight_movies_to_trakt()
            if Oversightumw:
                Oversight_movies_watched_to_trakt()
                trakt_movies_watched_to_Oversight()
        if Oversightusc or Oversightusw:
            global Oversight_shows
            Oversight_shows = {}
            get_Oversight_shows()
            get_trakt_shows()
            if Oversightusc:
                Oversight_shows_to_trakt()
            if Oversightusw:
                Oversight_shows_watched_to_trakt()
                trakt_shows_watched_to_Oversight()
            del Oversight_shows
    #clear globals
    del Oversight_movies[:]
    del Oversight_movies_seen[:]
    del Oversight_movies_unseen[:]
    del trakt_movies[:]
    del trakt_shows[:]

def get_Oversight_movies():
    pchtrakt.logger.info('[Oversight] Getting movies from Oversight')
    f=open(OversightFile, 'r')
    for movie in f:
        if "\t_C\tM\t" in movie:
            if "\t_T\t" in movie:
                title = re.search("_T\t(.*?)\t", movie).group(1)
            if "\t_Y\t" in movie:
                try:
                    year = re.search("_Y\t(.*?)\t", movie).group(1)
                    if year != "":
                        year = int(year)+1942
                except:
                        year = 1900
            else:
                year = 1900

            Oversight_movie = {
               'title': title,
               'year': str(year)
            }

            if "\t_U\t imdb:" in movie:
                Oversight_movie['imdbnumber'] = re.search("(tt\d{7})", movie).group(1)
            else:
                Oversight_movie['imdbnumber'] = "0"
            if "\t_id\t" in movie:
                Oversight_movie['id'] = re.search("_id\t(.*?)\t", movie).group(1)
            if "themoviedb:" in movie:
                Oversight_movie['tmdb_id'] = re.search("themoviedb:(.*?)\t", movie).group(1)
            else:
                Oversight_movie['tmdb_id'] = "0"
            if "\t_w\t1\t" in movie:
                Oversight_movie['playcount'] = 1
            else:
                Oversight_movie['playcount'] = 0
            
            Oversight_movies.append(Oversight_movie)

            if "\t_w\t1\t" in movie:
                Oversight_movies_seen.append(Oversight_movie)
            else:
                Oversight_movies_unseen.append(Oversight_movie)
    f.close()

def get_trakt_movies():
    pchtrakt.logger.info('[Oversight] Getting movies from trakt.tv')

    # Collection
    url = '/user/library/movies/collection.json/%s/%s' % (TraktAPI, TraktUsername)
    movies = trakt_api('POST', url)
    
    for movie in movies:
        trakt_movie = {
            'title': movie['title'],
            'year': movie['year'],
        }

        if 'imdb_id' in movie:
            trakt_movie['imdb_id'] = movie['imdb_id']
        if 'tmdb_id' in movie:
            trakt_movie['tmdb_id'] = movie['tmdb_id']
        #trakt_movie['id'] = ""

        trakt_movies.append(trakt_movie)

    #Clean from collection, keep commented
    #url = 'https://api.trakt.tv/movie/unlibrary/' + TraktAPI
    #params = {'movies': trakt_movies}
    #response = trakt_api(url, params)
    # Seen
    url = '/user/library/movies/watched.json/%s/%s' % (TraktAPI, TraktUsername)
    seen_movies = trakt_api('POST', url)
    
    # Add playcounts to trakt collection
    for seen in seen_movies:
        if 'imdb_id' in seen:
            for movie in trakt_movies:
                if 'imdb_id' in movie:
                    if seen['imdb_id'] == movie['imdb_id']:
                        movie['plays'] = seen['plays']
        elif 'tmdb_id' in seen:
            for movie in trakt_movies:
                if 'tmdb_id' in movie:
                    if seen['tmdb_id'] == movie['tmdb_id']:
                        movie['plays'] = seen['plays']

        elif 'title' in seen:
            for movie in trakt_movies:
                if 'title' in movie:
                    if seen['title'] == movie['title']:
                        movie['plays'] = seen['plays']

    for movie in trakt_movies:
        if not 'plays' in movie:
            movie['plays'] = 0

def convert_Oversight_movie_to_trakt(movie):
    trakt_movie = {}

    if 'imdbnumber' in movie:
        if movie['imdbnumber'].startswith('tt'):
            trakt_movie['imdb_id'] = movie['imdbnumber']
        else:
            trakt_movie['tmdb_id'] = movie['imdbnumber']

    if 'title' in movie:
        trakt_movie['title'] = movie['title']

    if 'year' in movie:
        trakt_movie['year'] = movie['year']

    if 'playcount' in movie:
        trakt_movie['plays'] = movie['playcount']

    return trakt_movie

def Oversight_movies_to_trakt():
    pchtrakt.logger.info('[Oversight] Checking for Oversight movies that are not in trakt.tv collection')
    Oversight_movies_to_trakt = []

    if trakt_movies and Oversight_movies:
        imdb_ids = [x['imdb_id'] for x in trakt_movies if 'imdb_id' in x]
        tmdb_ids = [x['tmdb_id'] for x in trakt_movies if 'tmdb_id' in x]
        titles = [x['title'] for x in trakt_movies if 'title' in x]

    if Oversight_movies:
        for movie in Oversight_movies:
            if 'imdbnumber' in movie:
                if movie['imdbnumber'].startswith('tt'):
                    if trakt_movies:
                        if not movie['imdbnumber'] in imdb_ids:
                            Oversight_movies_to_trakt.append(movie)
                            trakt_movie = convert_Oversight_movie_to_trakt(movie)
                            trakt_movie['plays'] = 0
                            trakt_movies.append(trakt_movie)
                    else:
                        Oversight_movies_to_trakt.append(movie)
                        trakt_movie = convert_Oversight_movie_to_trakt(movie)
                        trakt_movie['plays'] = 0
                        #trakt_movies.append(trakt_movie)
                else:
                    if trakt_movies:
                        if not movie['tmdb_id'] in tmdb_ids:
                            Oversight_movies_to_trakt.append(movie)
                            trakt_movie = convert_Oversight_movie_to_trakt(movie)
                            trakt_movie['plays'] = 0
                            trakt_movies.append(trakt_movie)
                    else:
                        Oversight_movies_to_trakt.append(movie)
                        trakt_movie = convert_Oversight_movie_to_trakt(movie)
                        trakt_movie['plays'] = 0
                        #trakt_movies.append(trakt_movie)
            elif not movie['title'] in titles and not movie in Oversight_movies_to_trakt:
                Oversight_movies_to_trakt.append(movie)
                trakt_movie = convert_Oversight_movie_to_trakt(movie)
                trakt_movie['plays'] = 0
                trakt_movies.append(trakt_movie)

    if Oversight_movies_to_trakt:
        pchtrakt.logger.info('[Oversight] Checking for %s movies will be added to trakt.tv collection' % len(Oversight_movies_to_trakt))

        for i in range(len(Oversight_movies_to_trakt)):
            #convert Oversight movie into something trakt will understand
            Oversight_movies_to_trakt[i] = convert_Oversight_movie_to_trakt(Oversight_movies_to_trakt[i])

        # Send request to add movies to trakt.tv
        url = '/movie/library/' + TraktAPI
        params = {'movies': Oversight_movies_to_trakt}

        try:
            pchtrakt.logger.info('[Oversight] Adding movies to trakt.tv collection...')
            response = trakt_api('POST', url, params)
            if response['inserted'] != 0:
                pchtrakt.logger.info('[Oversight] Successfully added %s out of %s to your collection' % (response['inserted'], response['inserted'] + response['skipped']))
            if response['skipped'] != 0:
                pchtrakt.logger.info('[Oversight] Failed to add the following %s titles to your collection' % response['skipped'])
                for failed in response['skipped_movies']:
                    pchtrakt.logger.info('[Oversight] Failed to add %s' % failed['title'].encode('utf-8', 'replace'))
        except Exception, e:
            pchtrakt.logger.info('[Oversight] Failed to add movies to trakt.tv collection')
            pchtrakt.logger.info(e)
            
    else:
        pchtrakt.logger.info('[Oversight] trakt.tv movie collection is up to date')

def Oversight_movies_watched_to_trakt():
    pchtrakt.logger.info('[Oversight] Comparing Oversight watched movies against trakt.tv')
    Oversight_movies_to_trakt = []

    if trakt_movies and Oversight_movies:

        for i in range(len(trakt_movies)):
            for movie in Oversight_movies:
                if movie['playcount'] != 0:

                    if 'imdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['imdb_id']:
                            if trakt_movies[i]['plays'] < movie['playcount']:
                                Oversight_movies_to_trakt.append(convert_Oversight_movie_to_trakt(movie))

                    elif 'tmdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['tmdb_id']:
                            if trakt_movies[i]['plays'] < movie['playcount']:
                                Oversight_movies_to_trakt.append(convert_Oversight_movie_to_trakt(movie))

                    elif movie['title'] == trakt_movies[i]['title']:
                        if trakt_movies[i]['plays'] < movie['playcount']:
                            Oversight_movies_to_trakt.append(convert_Oversight_movie_to_trakt(movie))

    if Oversight_movies_to_trakt:
        pchtrakt.logger.info('[Oversight] %s movies playcount will be updated on trakt.tv' % len(Oversight_movies_to_trakt))

        # Send request to update playcounts on trakt.tv
        url = '/movie/seen/' + TraktAPI
        params = {'movies': Oversight_movies_to_trakt}

        try:
            pchtrakt.logger.info('[Oversight] Updating playcount for movies on trakt.tv...')
            trakt_api('POST', url, params)
            for movie in Oversight_movies_to_trakt:
                pchtrakt.logger.info('[Oversight]     -->%s' % movie['title'].encode('utf-8'))

        except Exception, e:
            pchtrakt.logger.info('[Oversight] Failed to update playcount for movies on trakt.tv')
            pchtrakt.logger.info(e)
    else:
        pchtrakt.logger.info('[Oversight] trakt.tv movie playcount is up to date')

def trakt_movies_watched_to_Oversight():
    pchtrakt.logger.info('[Oversight] Comparing trakt.tv watched movies against Oversight')

    trakt_movies_seen = []

    if trakt_movies and Oversight_movies_unseen:#Oversight_movies:
        for i in range(len(trakt_movies)):
            for movie in Oversight_movies_unseen:#Oversight_movies:
                if movie['playcount'] == 0 and trakt_movies[i]['plays'] != 0:

                    if 'imdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['imdb_id']:
                            trakt_movies[i]['movieid'] = movie['imdbnumber']
                            trakt_movies[i]['id'] = movie['id']

                    elif 'tmdb_id' in trakt_movies[i]:
                        if movie['tmdb_id'] == trakt_movies[i]['tmdb_id']:
                            trakt_movies[i]['movieid'] = movie['tmdb_id']
                            trakt_movies[i]['id'] = movie['id']

                    elif movie['title'] == trakt_movies[i]['title']:
                        trakt_movies[i]['movieid'] = movie['title']
                        trakt_movies[i]['id'] = movie['id']

    # Remove movies without a movieid
    if trakt_movies:

        for movie in trakt_movies:
            if 'movieid' in movie:
                trakt_movies_seen.append(movie)

    if trakt_movies_seen:
        data = "*("
        pchtrakt.logger.info('[Oversight] %s movies playcount will be updated on Oversight' % len(trakt_movies_seen))
        #addValue = "\t_w\t1\t"
        #checkvalue = "\t_w\t0\t"
        #myfile_list = open(OversightFile).readlines()
        #newList = []
        for movie in trakt_movies_seen:
            if movie['id']:# in movie:
                pchtrakt.logger.info('[Oversight]     -->%s' % movie['title'].encode('utf-8'))
                m = movie['id']
                if data == "*(":
                    data = data + m
                else:
                    data = data  + "|" + m
        WatchedOversight(data+")")
        data = ""
    else:
        pchtrakt.logger.info('[Oversight] Watched movies on Oversight are up to date')

def get_Oversight_shows():
    pchtrakt.logger.info('[Oversight] Getting TV shows from Oversight')
    f=open(OversightFile, 'r')
    for movie in f:
        if "_C	T" in movie:
            if "\t_e\t"in movie:
                try:
                    episode = re.search("\t_e\t(.*?)\t_", movie).group(1)
                    
                    if episode == "FILE":
                        continue
                except:
                    continue
            else:
                continue
            if "_s\t" in movie:
                season = int(re.search("\t_s\t(.*?)\t_", movie).group(1))
            else:
                continue
            if "_T\t" in movie:
                title = re.search("\t_T\t(.*?)\t", movie).group(1)
            else:
                continue
            if "imdb:" in movie:
                imdb_id = re.search("(tt\d{7})", movie).group(1)
            else:
                imdb_id = "0"
            if "thetvdb:" in movie:
                thetvdb = re.search("thetvdb:(.*?)[\t| imdb:]", movie).group(1)
            else:
                thetvdb = "0"
            if "\t_w\t1\t" in movie:
                played = 1
            else:
                played = 0
            ids = re.search("_id\t(.*?)\t", movie).group(1)

            if title not in Oversight_shows:
                shows = Oversight_shows[title] = {'episodes': []}  # new show dictionary
            else:
                shows = Oversight_shows[title]
            if 'title' in shows and title in shows['title']:
                if "," in episode:
                    for x in episode.split(","):
                        ep = {'episode': int(x), 'season': season}
                        ep['playcount'] = played
                        ep['double'] = "True",
                        ep['ids'] = ids
                        shows['episodes'].append(ep)
                else:
                    ep = {'episode': int(episode), 'season': season}
                    ep['playcount'] = played
                    ep['double'] = "False",
                    ep['ids'] = ids
                    shows['episodes'].append(ep)
            else:
                if thetvdb != "0":
                    shows['imdbnumber'] = thetvdb
                elif imdb_id and imdb_id.startswith('tt'):
                    shows['imdbnumber'] = imdb_id

                if title:
                    shows['title'] = title
                    if "," in episode:
                        for x in episode.split(","):
                            ep = {'episode': int(x), 'season': season}
                            ep['playcount'] = played
                            ep['double'] = "True",
                            ep['ids'] = ids
                            shows['episodes'].append(ep)
                    else:
                        ep = {'episode': int(episode), 'season': season}
                        ep['playcount'] = played
                        ep['double'] = "False",
                        ep['ids'] = ids
                        shows = shows['episodes'].append(ep)
                
    f.close()

def get_trakt_shows():
    pchtrakt.logger.info('[Oversight] Getting TV shows from trakt')

    # Collection
    url = '/user/library/shows/collection.json/%s/%s' % (TraktAPI, TraktUsername)
    collection_shows = trakt_api('POST', url)
    
    for show in collection_shows:
        trakt_show = {
            'title': show['title'],
            'episodes': []
        }

        if 'imdb_id' in show:
            trakt_show['imdb_id'] = show['imdb_id']
        if 'tvdb_id' in show:
            trakt_show['tvdb_id'] = show['tvdb_id']

        for season in show['seasons']:
            for episode in season['episodes']:
                ep = {'season': season['season'], 'episode': episode, 'plays': 0}
                trakt_show['episodes'].append(ep)

        #Clean from collection, keep commented
        #url = 'https://api.trakt.tv/show/episode/unlibrary/' + TraktAPI
        #params = trakt_show
        #response = trakt_api(url, params)
        trakt_shows.append(trakt_show)

    # Seen
    url = '/user/library/shows/watched.json/%s/%s' % (TraktAPI, TraktUsername)
    seen_shows = trakt_api('POST', url)
    
    for show in seen_shows:
        for season in show['seasons']:
            for episode in season['episodes']:
                for trakt_show in trakt_shows:
                    if 'imdb_id' in show and 'imdb_id' in trakt_show and show['imdb_id'] == trakt_show['imdb_id']:
                        for trakt_episode in trakt_show['episodes']:
                            if trakt_episode['season'] == season['season'] and trakt_episode['episode'] == episode:
                                trakt_episode['plays'] = 1

                    elif 'tvdb_id' in show and 'tvdb_id' in trakt_show and show['tvdb_id'] == trakt_show['tvdb_id']:
                        for trakt_episode in trakt_show['episodes']:
                            if trakt_episode['season'] == season['season'] and trakt_episode['episode'] == episode:
                                trakt_episode['plays'] = 1

                    elif show['title'] == trakt_show['title']:
                        for trakt_episode in trakt_show['episodes']:
                            if trakt_episode['season'] == season['season'] and trakt_episode['episode'] == episode:
                                trakt_episode['plays'] = 1

def convert_Oversight_show_to_trakt(show):
    trakt_show = {'episodes': []}

    if 'imdbnumber' in show:
        if show['imdbnumber'].startswith('tt'):
            trakt_show['imdb_id'] = show['imdbnumber']
        else:
            trakt_show['tvdb_id'] = show['imdbnumber']

    if 'title' in show:
        trakt_show['title'] = show['title']

    if 'episodes' in show and show['episodes']:
        for episode in show['episodes']:
            ep = {'episode': episode['episode'], 'season': episode['season']}

            if 'playcount' in episode:
                 ep['plays'] = episode['playcount']

            trakt_show['episodes'].append(ep)

    return trakt_show

def Oversight_shows_to_trakt():
    pchtrakt.logger.info('[Oversight] Checking for Oversight episodes that are not in trakt.tv collection')
    Oversight_shows_to_trakt = []

    def clean_episodes(shows):
        if shows:
            for show in shows:
                episodes = []
                for episode in show['episodes']:
                    episodes.append({'season': episode['season'], 'episode': episode['episode']})
                show['episodes'] = episodes

        return shows

    if Oversight_shows:
        if trakt_shows:

            t_shows = copy.deepcopy(trakt_shows)
            t_shows = clean_episodes(t_shows)
        x_shows = copy.deepcopy(Oversight_shows.values())
        x_shows = clean_episodes(x_shows)

        tvdb_ids = {}
        imdb_ids = {}

        if trakt_shows:
            for i in range(len(t_shows)):
                if 'tvdb_id' in t_shows[i]:
                    tvdb_ids[t_shows[i]['tvdb_id']] = i

                if 'imdb_id' in t_shows[i]:
                    imdb_ids[t_shows[i]['imdb_id']] = i

        for show in x_shows:
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if not show['imdbnumber'] in imdb_ids.keys():
                        Oversight_shows_to_trakt.append(show)

                        trakt_show = convert_Oversight_show_to_trakt(show)
                        for episode in trakt_show['episodes']:
                            episode['plays'] = 0

                        trakt_shows.append(trakt_show)

                    else:
                        t_index = imdb_ids[show['imdbnumber']]

                        Oversight_show = {
                            'title': show['title'],
                            'imdbnumber': show['imdbnumber'],
                            'episodes': []
                        }

                        for episode in show['episodes']:
                            if episode not in t_shows[t_index]['episodes']:
                                Oversight_show['episodes'].append(episode)

                                trakt_shows[t_index]['episodes'].append(episode)
                                trakt_shows[t_index]['episodes'][-1]['plays'] = 0

                        if Oversight_show['episodes']:
                            Oversight_shows_to_trakt.append(Oversight_show)

                else:
                    if not show['imdbnumber'] in tvdb_ids.keys():
                        Oversight_shows_to_trakt.append(show)

                        trakt_show = convert_Oversight_show_to_trakt(show)
                        for episode in trakt_show['episodes']:
                            episode['plays'] = 0

                        trakt_shows.append(trakt_show)

                    else:
                        t_index = tvdb_ids[show['imdbnumber']]

                        Oversight_show = {
                            'title': show['title'],
                            'imdbnumber': show['imdbnumber'],
                            'episodes': []
                        }

                        for episode in show['episodes']:
                            if episode not in t_shows[t_index]['episodes']:
                                Oversight_show['episodes'].append(episode)

                                trakt_shows[t_index]['episodes'].append(episode)
                                trakt_shows[t_index]['episodes'][-1]['plays'] = 0

                        if Oversight_show['episodes']:
                            Oversight_shows_to_trakt.append(Oversight_show)

        if Oversight_shows_to_trakt:
            pchtrakt.logger.info('[Oversight] %s TV shows have episodes missing from trakt.tv collection' % len(Oversight_shows_to_trakt))

            for i in range(len(Oversight_shows_to_trakt)):
                #convert Oversight show into something trakt will understand
                Oversight_shows_to_trakt[i] = convert_Oversight_show_to_trakt(Oversight_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = '/show/episode/library/' + TraktAPI

            for show in Oversight_shows_to_trakt:
                try:
                    pchtrakt.logger.info('[Oversight]     -->%s' % show['title'].encode('utf-8'))
                    trakt = trakt_api('POST', url, show)
                    pchtrakt.logger.info('[Oversight]       %s' % trakt['message'])
                except Exception, e:
                    pchtrakt.logger.info('[Oversight] Failed to add %s\'s new episodes to trakt.tv collection' % show['title'].encode('utf-8'))
                    pchtrakt.logger.info(e)

        else:
            pchtrakt.logger.info('[Oversight] trakt.tv TV show collection is up to date')

def Oversight_shows_watched_to_trakt():
    pchtrakt.logger.info('[Oversight] Comparing Oversight watched TV shows against trakt.tv')
    Oversight_shows_to_trakt = []

    if Oversight_shows and trakt_shows:

        tvdb_ids = {}
        imdb_ids = {}

        for i in range(len(trakt_shows)):
            if 'tvdb_id' in trakt_shows[i]:
                tvdb_ids[trakt_shows[i]['tvdb_id']] = i

            if 'imdb_id' in trakt_shows[i]:
                imdb_ids[trakt_shows[i]['imdb_id']] = i

        for show in Oversight_shows.values():
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if show['imdbnumber'] in imdb_ids.keys():
                        trakt_show = trakt_shows[imdb_ids[show['imdbnumber']]]

                        trakt_show_watched = {
                            'title': show['title'],
                            'imdb_id': show['imdbnumber'],
                            'episodes': []
                        }

                        for Oversight_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == Oversight_ep['season']:
                                    if trakt_ep['episode'] == Oversight_ep['episode']:
                                        if trakt_ep['plays'] == 0 and Oversight_ep['playcount'] >= 1:

                                            trakt_show_watched['episodes'].append(
                                                {
                                                    'season': Oversight_ep['season'],
                                                    'episode': Oversight_ep['episode']
                                                }
                                            )

                        if trakt_show_watched['episodes']:
                            Oversight_shows_to_trakt.append(trakt_show_watched)

                else:
                    if show['imdbnumber'] in tvdb_ids.keys():
                        trakt_show = trakt_shows[tvdb_ids[show['imdbnumber']]]

                        trakt_show_watched = {
                            'title': show['title'],
                            'tvdb_id': show['imdbnumber'],
                            'episodes': []
                        }

                        for Oversight_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == Oversight_ep['season']:
                                    if trakt_ep['episode'] == Oversight_ep['episode']:
                                        if trakt_ep['plays'] == 0 and Oversight_ep['playcount'] >= 1:

                                            trakt_show_watched['episodes'].append(
                                                {
                                                    'season': Oversight_ep['season'],
                                                    'episode': Oversight_ep['episode']
                                                }
                                            )

                        if trakt_show_watched['episodes']:
                            Oversight_shows_to_trakt.append(trakt_show_watched)

        if Oversight_shows_to_trakt:
            pchtrakt.logger.info('[Oversight] %s TV shows have episodes that will be marked as watched in trakt.tv collection' % len(Oversight_shows_to_trakt))

            for i in range(len(Oversight_shows_to_trakt)):
                #convert Oversight show into something trakt will understand
                Oversight_shows_to_trakt[i] = convert_Oversight_show_to_trakt(Oversight_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = '/show/episode/seen/' + TraktAPI

            for show in Oversight_shows_to_trakt:
                try:
                    pchtrakt.logger.info('[Oversight]     -->%s' % show['title'].encode('utf-8'))
                    trakt = trakt_api('POST', url, show)
                    pchtrakt.logger.info('[Oversight]       %s' % trakt['message'])
                except Exception, e:
                    pchtrakt.logger.info('[Oversight] Failed to mark %s\'s episodes as watched in trakt.tv collection' % show['title'].encode('utf-8'))
                    pchtrakt.logger.info(e)

        else:
            pchtrakt.logger.info('[Oversight] trakt.tv TV show watched status is up to date')

def trakt_shows_watched_to_Oversight():
    pchtrakt.logger.info('[Oversight] Comparing trakt.tv watched TV shows against Oversight')
    trakt_shows_seen = []

    if Oversight_shows and trakt_shows:

        tvdb_ids = {}
        imdb_ids = {}

        for i in range(len(trakt_shows)):
            if 'tvdb_id' in trakt_shows[i]:
                tvdb_ids[trakt_shows[i]['tvdb_id']] = i

            if 'imdb_id' in trakt_shows[i]:
                imdb_ids[trakt_shows[i]['imdb_id']] = i

        for show in Oversight_shows.values():
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if show['imdbnumber'] in imdb_ids.keys():
                        trakt_show = trakt_shows[imdb_ids[show['imdbnumber']]]

                        Oversight_show = {'title': show['title'], 'episodes': []}

                        for Oversight_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == Oversight_ep['season']:
                                    if trakt_ep['episode'] == Oversight_ep['episode']:
                                        if trakt_ep['plays'] == 1 > Oversight_ep['playcount']:

                                            Oversight_show['episodes'].append(
                                                {
                                                    'season': Oversight_ep['season'],
                                                    'playcount': Oversight_ep['playcount'],
                                                    'episode': Oversight_ep['episode'],
                                                    'double': Oversight_ep['double'],
                                                    'ids': Oversight_ep['ids']
                                                }
                                            )

                        if Oversight_show['episodes']:
                            trakt_shows_seen.append(Oversight_show)

                else:
                    if show['imdbnumber'] in tvdb_ids.keys():
                        trakt_show = trakt_shows[tvdb_ids[show['imdbnumber']]]

                        Oversight_show = {'title': show['title'], 'episodes': []}

                        for Oversight_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == Oversight_ep['season']:
                                    if trakt_ep['episode'] == Oversight_ep['episode']:
                                        if trakt_ep['plays'] == 1 > Oversight_ep['playcount']:

                                            Oversight_show['episodes'].append(
                                                {
                                                    'season': Oversight_ep['season'],
                                                    'playcount': Oversight_ep['playcount'],
                                                    'episode': Oversight_ep['episode'],
                                                    'double': Oversight_ep['double'],
                                                    'ids': Oversight_ep['ids']
                                                }
                                            )

                        if Oversight_show['episodes']:
                            trakt_shows_seen.append(Oversight_show)



        #http://192.168.123.154:8883/oversight/oversight.cgi?select=Mark&action=watch&actionids=*(90)
        if trakt_shows_seen:
            pchtrakt.logger.info('[Oversight] %s TV shows episodes watched status will be updated in Oversight' % len(trakt_shows_seen))
            data = "*("
            with open(OversightFile, 'r') as infile:
                for show_dict in trakt_shows_seen:
                    pchtrakt.logger.info('[Oversight]     -->%s' % show_dict["title"].encode('utf-8'))
                    for episode in show_dict['episodes']:
                        pchtrakt.logger.info('[Oversight]       Season %i - Episode %i' % (episode['season'], episode['episode']))
                        m = episode['ids']
                        
                        if data == "*(":
                            data = data + m
                        else:
                            data = data  + "|" + m
            WatchedOversight(data+")")
            data = ""
        else:
            pchtrakt.logger.info('[Oversight] Watched TV shows on Oversight are up to date')

def WatchedOversight(data):
    pchtrakt.logger.info('[Oversight] sending to Oversight')
    url = data + '"'
    #command = 'wget "http://%s:8883/oversight/oversight.cgi?action=watch&actionids=%s > /dev/null 2>&1' % (ipPch, url)
    os.system('wget "http://%s:8883/oversight/oversight.cgi?action=watch&actionids=%s > /dev/null 2>&1' % (ipPch, url))
    #request = urllib2.Request("http://127.0.0.1:8883/oversight/oversight.cgi?action=watch&actionids="+data)
    #try:
    #    response = urllib2.urlopen(request).read()
    #except urllib2.URLError, e:
    #    quit(e.reason)
    data = ""
