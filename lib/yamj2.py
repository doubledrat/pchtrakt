# -*- coding: utf-8 -*-

from pchtrakt.config import *
from lib.utilities import trakt_api
from xml.etree import ElementTree
from urllib import unquote_plus
import re
import os
import copy
config_file = 'pchtrakt.ini'
name = YamjPath + 'CompleteMovies.xml'
#name = 'E:\\Desktop\\CompleteMovies.xml'
YAMJ_movies = []
YAMJ_movies_seen = []
YAMJ_movies_unseen = []
trakt_movies = []
trakt_shows = []

def YAMJSync():
    if YAMJSyncCheck >= 0:
        tree = ElementTree.parse(name)
        if YAMJumc or YAMJumw:
            get_YAMJ_movies(tree)
            get_trakt_movies()
            if YAMJumc:
                YAMJ_movies_to_trakt()
            if YAMJumw:
                get_trakt_movies() #Need to re-get trakt films in case they were updated above
                YAMJ_movies_watched_to_trakt()
                trakt_movies_watched_to_YAMJ()
        if YAMJusc or YAMJusw:
            global YAMJ_shows
            YAMJ_shows = {}
            get_YAMJ_shows(tree)
            get_trakt_shows()
            if YAMJusc:
                YAMJ_shows_to_trakt()
            if YAMJusw:
                get_trakt_shows() #Need to re-get trakt shows in case they were updated above
                YAMJ_shows_watched_to_trakt()
                trakt_shows_watched_to_YAMJ()
            del YAMJ_shows
    #clear globals
    del YAMJ_movies[:]
    del YAMJ_movies_seen[:]
    del YAMJ_movies_unseen[:]
    del trakt_movies[:]
    del trakt_shows[:]
    config.set('YAMJ2', 'boot_time_sync', '-1')
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def get_YAMJ_movies(tree):
    pchtrakt.logger.info('[YAMJ] Getting movies from YAMJ')
    for movie in tree.findall('movies'):
        if movie.get('isTV') == 'false':
            YAMJ_movie = {
                          'title': movie.find('originalTitle').text.encode('utf-8'),
                          'imdbnumber': movie.find("id/[@movieDatabase='imdb']").text
                          }

            year = movie.find('files/file/info').attrib['year']
            if year != "-1":
                YAMJ_movie['year'] = year
            else:
                YAMJ_movie['year'] = '1900'

            watched = movie.find('isWatched').text
            watchedDate = movie.find('files/file/watchedDateString').text

            YAMJ_movie['path'] = unquote_plus(movie.find('files/file/fileURL').text)
            
            if watched == 'true':
                YAMJ_movie['playcount'] = 1
                YAMJ_movie['date'] = watchedDate
            else:
                YAMJ_movie['playcount'] = 0
                YAMJ_movie['date'] = "0"
            YAMJ_movies.append(YAMJ_movie)

            if watched == 'true':
                YAMJ_movies_seen.append(YAMJ_movie)
            else:
                YAMJ_movies_unseen.append(YAMJ_movie)

def get_trakt_movies():
    pchtrakt.logger.info('[YAMJ] Getting movies from trakt.tv')

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
    #url = '/movie/unlibrary/' + TraktAPI
    #params = {'movies': trakt_movies}
    #response = trakt_api('POST', url, params)
    #url = '/movie/unseen/' + TraktAPI
    #response = trakt_api('POST', url, params)

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

def convert_YAMJ_movie_to_trakt(movie):
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

    #if 'playcount' in movie:
    #    trakt_movie['plays'] = movie['playcount']

    if 'date' in movie:
        trakt_movie['last_played'] = movie['date']

    return trakt_movie

def YAMJ_movies_to_trakt():
    pchtrakt.logger.info('[YAMJ] Checking for YAMJ movies that are not in trakt.tv collection')
    YAMJ_movies_to_trakt = []

    if trakt_movies and YAMJ_movies:
        imdb_ids = [x['imdb_id'] for x in trakt_movies if 'imdb_id' in x]
        tmdb_ids = [x['tmdb_id'] for x in trakt_movies if 'tmdb_id' in x]
        titles = [x['title'] for x in trakt_movies if 'title' in x]

    if YAMJ_movies:
        for movie in YAMJ_movies:
            if 'imdbnumber' in movie:
                if movie['imdbnumber'].startswith('tt'):
                    if trakt_movies:
                        if not movie['imdbnumber'] in imdb_ids:
                            YAMJ_movies_to_trakt.append(movie)
                            trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                            trakt_movie['plays'] = 0
                            trakt_movies.append(trakt_movie)
                    else:
                        YAMJ_movies_to_trakt.append(movie)
                        trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                        trakt_movie['plays'] = 0
                        #trakt_movies.append(trakt_movie)
                else:
                    if trakt_movies:
                        if not movie['imdbnumber'] in tmdb_ids:
                            YAMJ_movies_to_trakt.append(movie)
                            trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                            trakt_movie['plays'] = 0
                            trakt_movies.append(trakt_movie)
                    else:
                        YAMJ_movies_to_trakt.append(movie)
                        trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                        trakt_movie['plays'] = 0
                        #trakt_movies.append(trakt_movie)
            elif not movie['title'] in titles and not movie in YAMJ_movies_to_trakt:
                YAMJ_movies_to_trakt.append(movie)
                trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                trakt_movie['plays'] = 0
                trakt_movies.append(trakt_movie)

    if YAMJ_movies_to_trakt:
        pchtrakt.logger.info('[YAMJ] Checking for %s movies will be added to trakt.tv collection' % len(YAMJ_movies_to_trakt))

        for i in range(len(YAMJ_movies_to_trakt)):
            #convert YAMJ movie into something trakt will understand
            YAMJ_movies_to_trakt[i] = convert_YAMJ_movie_to_trakt(YAMJ_movies_to_trakt[i])

        # Send request to add movies to trakt.tv
        url = '/movie/library/' + TraktAPI
        params = {'movies': YAMJ_movies_to_trakt}

        try:
            pchtrakt.logger.info('[YAMJ] Adding movies to trakt.tv collection...')
            response = trakt_api('POST', url, params)
            if response['inserted'] != 0:
                pchtrakt.logger.info('[YAMJ] Successfully added %s out of %s to your collection' % (response['inserted'], response['inserted'] + response['skipped']))
            if response['skipped'] != 0:
                pchtrakt.logger.info('[YAMJ] Failed to add the following %s titles to your collection' % response['skipped'])
                for failed in response['skipped_movies']:
                    pchtrakt.logger.info('[YAMJ] Failed to add %s' % failed['title'].encode('utf-8', 'replace'))
        except Exception, e:
            pchtrakt.logger.info('[YAMJ] Failed to add movies to trakt.tv collection')
            pchtrakt.logger.info(e)
            
    else:
        pchtrakt.logger.info('[YAMJ] trakt.tv movie collection is up to date')

def YAMJ_movies_watched_to_trakt():
    pchtrakt.logger.info('[YAMJ] Comparing YAMJ watched movies against trakt.tv')
    YAMJ_movies_to_trakt = []

    if trakt_movies and YAMJ_movies:

        for i in range(len(trakt_movies)):
            for movie in YAMJ_movies:
                if movie['playcount'] != 0:

                    if 'imdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['imdb_id']:
                            if trakt_movies[i]['plays'] < movie['playcount']:
                                YAMJ_movies_to_trakt.append(convert_YAMJ_movie_to_trakt(movie))

                    elif 'tmdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['tmdb_id']:
                            if trakt_movies[i]['plays'] < movie['playcount']:
                                YAMJ_movies_to_trakt.append(convert_YAMJ_movie_to_trakt(movie))

                    elif movie['title'] == trakt_movies[i]['title']:
                        if trakt_movies[i]['plays'] < movie['playcount']:
                            YAMJ_movies_to_trakt.append(convert_YAMJ_movie_to_trakt(movie))

    if YAMJ_movies_to_trakt:
        pchtrakt.logger.info('[YAMJ] %s movies playcount will be updated on trakt.tv' % len(YAMJ_movies_to_trakt))

        # Send request to update playcounts on trakt.tv
        url = '/movie/seen/' + TraktAPI
        params = {'movies': YAMJ_movies_to_trakt}

        try:
            pchtrakt.logger.info('[YAMJ] Updating playcount for movies on trakt.tv...')
            response = trakt_api('POST', url, params)

            pchtrakt.logger.info('[YAMJ]     Added %s out of %s' % (response['inserted'], len(YAMJ_movies_to_trakt)))

            for skip in response[u'skipped_movies']:
                pchtrakt.logger.info('[YAMJ]     -->%s' % skip['title'].encode('utf-8'))

        except Exception, e:
            pchtrakt.logger.info('[YAMJ] Failed to update playcount for movies on trakt.tv')
            pchtrakt.logger.info(e)
    else:
        pchtrakt.logger.info('[YAMJ] trakt.tv movie playcount is up to date')

def trakt_movies_watched_to_YAMJ():
    pchtrakt.logger.info('[YAMJ] Comparing trakt.tv watched movies against YAMJ')

    trakt_movies_seen = []

    if trakt_movies and YAMJ_movies_unseen:#YAMJ_movies:
        for i in range(len(trakt_movies)):
            for movie in YAMJ_movies_unseen:#YAMJ_movies:
                if movie['playcount'] == 0 and trakt_movies[i]['plays'] != 0:

                    if 'imdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['imdb_id']:
                            trakt_movies[i]['movieid'] = movie['imdbnumber']
                            trakt_movies[i]['path'] = movie['path']

                    elif 'tmdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['tmdb_id']:
                            trakt_movies[i]['movieid'] = movie['tmdb_id']
                            trakt_movies[i]['path'] = movie['path']

                    elif movie['title'] == trakt_movies[i]['title']:
                        trakt_movies[i]['movieid'] = movie['title']
                        trakt_movies[i]['id'] = movie['id']

    # Remove movies without a movieid
    if trakt_movies:

        for movie in trakt_movies:
            if 'movieid' in movie:
                trakt_movies_seen.append(movie)

    if trakt_movies_seen:
        pchtrakt.logger.info('[YAMJ] %s movie watched files will be created' % len(trakt_movies_seen))
        WatchedYAMJmv(trakt_movies_seen)
    else:
        pchtrakt.logger.info('[YAMJ] No watched files ned to be created')

def get_YAMJ_shows(tree):
    pchtrakt.logger.info('[YAMJ] Getting TV shows from YAMJ2')
    for movie in tree.findall('movies'):
        if movie.get('isTV') == 'true':
            title = movie.find('originalTitle').text.encode('utf-8')
            id = movie.find('id').text
            zpath = "files/file"
            for x in movie.findall(zpath):
                watchedDate = x.find('watchedDateString').text
                firstPart = x.get('firstPart')
                lastPart = x.get('lastPart')
                season = int(x.find('info').attrib['season'])
                path = unquote_plus(x.find('fileURL').text)
                if x.find('watched').text == 'true':
                    watched = 1
                else:
                    watched = 0

                if title not in YAMJ_shows:
                    shows = YAMJ_shows[title] = {'episodes': []}  # new show dictionary
                else:
                    shows = YAMJ_shows[title]
                if 'title' in shows and title in shows['title']:
                    if firstPart != lastPart:
                        for eps in firstPart, lastPart:
                            ep = {'episode': int(eps), 'season': season, 'date': watchedDate}
                            ep['playcount'] = watched
                            ep['double'] = "True"
                            ep['path'] = path
                            shows['episodes'].append(ep)
                    else:
                        ep = {'episode': int(firstPart), 'season': season, 'date': watchedDate}
                        ep['playcount'] = watched
                        ep['double'] = "False"
                        ep['path'] = path
                        shows['episodes'].append(ep)
                else:
                    if id != "0":
                        shows['imdbnumber'] = id
                    if title:
                        shows['title'] = title
                        if firstPart != lastPart:
                            for eps in firstPart, lastPart:
                                ep = {'episode': int(eps), 'season': season, 'date': watchedDate}
                                ep['playcount'] = watched
                                ep['double'] = "True"
                                ep['path'] = path
                                shows['episodes'].append(ep)
                        else:
                            ep = {'episode': int(firstPart), 'season': season, 'date': watchedDate}
                            ep['playcount'] = watched
                            ep['double'] = "False"
                            ep['path'] = path
                            shows = shows['episodes'].append(ep)


def get_trakt_shows():
    pchtrakt.logger.info('[YAMJ] Getting TV shows from trakt')

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
        #url = '/show/episode/unseen/' + TraktAPI
        #response = trakt_api('post', url, trakt_show)
        #url = '/show/episode/unlibrary/' + TraktAPI
        #response = trakt_api('post', url, trakt_show)
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

def convert_YAMJ_show_to_trakt(show):
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
            if 'date' in episode:
                ep = {'episode': episode['episode'], 'season': episode['season'], 'last_played': episode['date']}
            else:
                ep = {'episode': episode['episode'], 'season': episode['season']}

            #if 'playcount' in episode:
            #     ep['plays'] = episode['playcount']

            trakt_show['episodes'].append(ep)

    return trakt_show

def YAMJ_shows_to_trakt():
    pchtrakt.logger.info('[YAMJ] Checking for YAMJ episodes that are not in trakt.tv collection')
    YAMJ_shows_to_trakt = []

    def clean_episodes(shows):
        if shows:
            for show in shows:
                episodes = []
                for episode in show['episodes']:
                    episodes.append({'season': episode['season'], 'episode': episode['episode']})
                show['episodes'] = episodes

        return shows

    if YAMJ_shows:
        if trakt_shows:

            t_shows = copy.deepcopy(trakt_shows)
            t_shows = clean_episodes(t_shows)
        x_shows = copy.deepcopy(YAMJ_shows.values())
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
                        YAMJ_shows_to_trakt.append(show)

                        trakt_show = convert_YAMJ_show_to_trakt(show)
                        for episode in trakt_show['episodes']:
                            episode['plays'] = 0

                        trakt_shows.append(trakt_show)

                    else:
                        t_index = imdb_ids[show['imdbnumber']]

                        YAMJ_show = {
                            'title': show['title'],
                            'imdbnumber': show['imdbnumber'],
                            'episodes': []
                        }

                        for episode in show['episodes']:
                            if episode not in t_shows[t_index]['episodes']:
                                YAMJ_show['episodes'].append(episode)

                                trakt_shows[t_index]['episodes'].append(episode)
                                trakt_shows[t_index]['episodes'][-1]['plays'] = 0

                        if YAMJ_show['episodes']:
                            YAMJ_shows_to_trakt.append(YAMJ_show)

                else:
                    if not show['imdbnumber'] in tvdb_ids.keys():
                        YAMJ_shows_to_trakt.append(show)

                        trakt_show = convert_YAMJ_show_to_trakt(show)
                        for episode in trakt_show['episodes']:
                            episode['plays'] = 0

                        trakt_shows.append(trakt_show)

                    else:
                        t_index = tvdb_ids[show['imdbnumber']]

                        YAMJ_show = {
                            'title': show['title'],
                            'imdbnumber': show['imdbnumber'],
                            'episodes': []
                        }

                        for episode in show['episodes']:
                            if episode not in t_shows[t_index]['episodes']:
                                YAMJ_show['episodes'].append(episode)

                                trakt_shows[t_index]['episodes'].append(episode)
                                trakt_shows[t_index]['episodes'][-1]['plays'] = 0

                        if YAMJ_show['episodes']:
                            YAMJ_shows_to_trakt.append(YAMJ_show)

        if YAMJ_shows_to_trakt:
            pchtrakt.logger.info('[YAMJ] %s TV shows have episodes missing from trakt.tv collection' % len(YAMJ_shows_to_trakt))

            for i in range(len(YAMJ_shows_to_trakt)):
                #convert YAMJ show into something trakt will understand
                YAMJ_shows_to_trakt[i] = convert_YAMJ_show_to_trakt(YAMJ_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = '/show/episode/library/' + TraktAPI

            for show in YAMJ_shows_to_trakt:
                try:
                    pchtrakt.logger.info('[YAMJ]     -->%s' % show['title'].encode('utf-8'))
                    trakt = trakt_api('POST', url, show)
                    pchtrakt.logger.info('[YAMJ]       %s' % trakt['message'])
                except Exception, e:
                    pchtrakt.logger.info('[YAMJ] Failed to add %s\'s new episodes to trakt.tv collection' % show['title'].encode('utf-8'))
                    pchtrakt.logger.info(e)

        else:
            pchtrakt.logger.info('[YAMJ] trakt.tv TV show collection is up to date')

def YAMJ_shows_watched_to_trakt():
    pchtrakt.logger.info('[YAMJ] Comparing YAMJ watched TV shows against trakt.tv')
    YAMJ_shows_to_trakt = []

    if YAMJ_shows and trakt_shows:

        tvdb_ids = {}
        imdb_ids = {}

        for i in range(len(trakt_shows)):
            if 'tvdb_id' in trakt_shows[i]:
                tvdb_ids[trakt_shows[i]['tvdb_id']] = i

            if 'imdb_id' in trakt_shows[i]:
                imdb_ids[trakt_shows[i]['imdb_id']] = i

        for show in YAMJ_shows.values():
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if show['imdbnumber'] in imdb_ids.keys():
                        trakt_show = trakt_shows[imdb_ids[show['imdbnumber']]]

                        trakt_show_watched = {
                            'title': show['title'],
                            'imdb_id': show['imdbnumber'],
                            'episodes': []
                        }

                        for YAMJ_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == YAMJ_ep['season']:
                                    if trakt_ep['episode'] == YAMJ_ep['episode']:
                                        if trakt_ep['plays'] == 0 and YAMJ_ep['playcount'] >= 1:

                                            trakt_show_watched['episodes'].append(
                                                {
                                                    'season': YAMJ_ep['season'],
                                                    'episode': YAMJ_ep['episode'],
                                                    'date': YAMJ_ep['date']
                                                }
                                            )

                        if trakt_show_watched['episodes']:
                            YAMJ_shows_to_trakt.append(trakt_show_watched)

                else:
                    if show['imdbnumber'] in tvdb_ids.keys():
                        trakt_show = trakt_shows[tvdb_ids[show['imdbnumber']]]

                        trakt_show_watched = {
                            'title': show['title'],
                            'tvdb_id': show['imdbnumber'],
                            'episodes': []
                        }

                        for YAMJ_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == YAMJ_ep['season']:
                                    if trakt_ep['episode'] == YAMJ_ep['episode']:
                                        if trakt_ep['plays'] == 0 and YAMJ_ep['playcount'] >= 1:

                                            trakt_show_watched['episodes'].append(
                                                {
                                                    'season': YAMJ_ep['season'],
                                                    'episode': YAMJ_ep['episode'],
                                                    'date': YAMJ_ep['date']
                                                }
                                            )

                        if trakt_show_watched['episodes']:
                            YAMJ_shows_to_trakt.append(trakt_show_watched)

        if YAMJ_shows_to_trakt:
            pchtrakt.logger.info('[YAMJ] %s TV shows have episodes that will be marked as watched in trakt.tv collection' % len(YAMJ_shows_to_trakt))

            for i in range(len(YAMJ_shows_to_trakt)):
                #convert YAMJ show into something trakt will understand
                YAMJ_shows_to_trakt[i] = convert_YAMJ_show_to_trakt(YAMJ_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = '/show/episode/seen/' + TraktAPI

            for show in YAMJ_shows_to_trakt:
                try:
                    pchtrakt.logger.info('[YAMJ]     -->%s' % show['title'].encode('utf-8'))
                    trakt = trakt_api('POST', url, show)
                    pchtrakt.logger.info('[YAMJ]       %s' % trakt['message'])
                except Exception, e:
                    pchtrakt.logger.info('[YAMJ] Failed to mark %s\'s episodes as watched in trakt.tv collection' % show['title'].encode('utf-8'))
                    pchtrakt.logger.info(e)

        else:
            pchtrakt.logger.info('[YAMJ] trakt.tv TV show watched status is up to date')

def trakt_shows_watched_to_YAMJ():
    pchtrakt.logger.info('[YAMJ] Comparing trakt.tv watched TV shows against YAMJ')
    trakt_shows_seen = []

    if YAMJ_shows and trakt_shows:

        tvdb_ids = {}
        imdb_ids = {}

        for i in range(len(trakt_shows)):
            if 'tvdb_id' in trakt_shows[i]:
                tvdb_ids[trakt_shows[i]['tvdb_id']] = i

            if 'imdb_id' in trakt_shows[i]:
                imdb_ids[trakt_shows[i]['imdb_id']] = i

        for show in YAMJ_shows.values():
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if show['imdbnumber'] in imdb_ids.keys():
                        trakt_show = trakt_shows[imdb_ids[show['imdbnumber']]]

                        YAMJ_show = {'title': show['title'], 'episodes': []}

                        for YAMJ_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == YAMJ_ep['season']:
                                    if trakt_ep['episode'] == YAMJ_ep['episode']:
                                        if trakt_ep['plays'] == 1 > YAMJ_ep['playcount']:

                                            YAMJ_show['episodes'].append(
                                                {
                                                    'path': YAMJ_ep['path']
                                                }
                                            )

                        if YAMJ_show['episodes']:
                            trakt_shows_seen.append(YAMJ_show)

                else:
                    if show['imdbnumber'] in tvdb_ids.keys():
                        trakt_show = trakt_shows[tvdb_ids[show['imdbnumber']]]

                        YAMJ_show = {'title': show['title'], 'episodes': []}

                        for YAMJ_ep in show['episodes']:
                            for trakt_ep in trakt_show['episodes']:
                                if trakt_ep['season'] == YAMJ_ep['season']:
                                    if trakt_ep['episode'] == YAMJ_ep['episode']:
                                        if trakt_ep['plays'] == 1 > YAMJ_ep['playcount']:

                                            YAMJ_show['episodes'].append(
                                                {
                                                    'path': YAMJ_ep['path']
                                                }
                                            )

                        if YAMJ_show['episodes']:
                            trakt_shows_seen.append(YAMJ_show)

        if trakt_shows_seen:
            pchtrakt.logger.info('[YAMJ] %s TV shows episodes watched status will be updated in YAMJ' % len(trakt_shows_seen))
            WatchedYAMJtv(trakt_shows_seen)
        else:
            pchtrakt.logger.info('[YAMJ] Watched TV shows on YAMJ are up to date')

def WatchedYAMJtv(episodes):
    pchtrakt.logger.info('[YAMJ] Start to create watched files')
    if YamjWatched == True:
        for x in episodes['episodes']:
            try:
                path = x['path'].split('/')[::-1][0].encode('utf-8', 'replace')
            except:
                path = x['path'].split('/')[::-1][0].encode('latin-1', 'replace')
            if YamJWatchedVithVideo:
                try:
                    path = x['path'].replace('file:///', '/').encode('utf-8', 'replace')
                except:
                    path = x['path'].replace('file:///', '/').encode('latin-1', 'replace')
                if (path.split(".")[-1] == "DVD"):#Remember that .DVD extension
                    path = path[:-4]
            else:
                if (path.split(".")[-1] == "DVD"):
                    path = path[:-4]
                path = '{0}{1}'.format(YamjWatchedPath, path)
            path = '{0}.watched'.format(path)
            if not isfile(path):
                try:
                    f = open(path, 'w')
                    f.close()
                    msg = ' [Pchtrakt] I have created the file {0}'.format(path)
                    pchtrakt.logger.info(msg)
                except IOError, e:
                    pchtrakt.logger.exception(e)

def WatchedYAMJmv(movies):
    pchtrakt.logger.info('[YAMJ] Start to create watched files')
    if YamjWatched == True:
        for x in movies:
            try:
                path = x['path'].split('/')[::-1][0].encode('utf-8', 'replace')
            except:
                path = x['path'].split('/')[::-1][0].encode('latin-1', 'replace')
            if YamJWatchedVithVideo:
                try:
                    path = x['path'].replace('file:///', '/').encode('utf-8', 'replace')
                except:
                    path = x['path'].replace('file:///', '/').encode('latin-1', 'replace')
                if (path.split(".")[-1] == "DVD"):#Remember that .DVD extension
                    path = path[:-4]
            else:
                if (path.split(".")[-1] == "DVD"):
                    path = path[:-4]
                path = '{0}{1}'.format(YamjWatchedPath, path)
            path = '{0}.watched'.format(path)
            if not isfile(path):
                try:
                    f = open(path, 'w')
                    f.close()
                    msg = ' [Pchtrakt] I have created the file {0}'.format(path)
                    pchtrakt.logger.info(msg)
                except IOError, e:
                    pchtrakt.logger.exception(e)


