# -*- coding: utf-8 -*-
# From https://github.com/Manromen/script.TraktUtilities

from pchtrakt.config import *
#if use_debug:
#    from time import time
from time import sleep, time
try:
    # Python 3.0 +
    from http.client import HTTPException, BadStatusLine
    from hashlib import sha1
except ImportError:
    # Python 2.7 and earlier
    from httplib import HTTPException, BadStatusLine
    from sha import new as sha1
import pchtrakt
import re
from urllib2 import Request, urlopen, HTTPError, URLError
from urllib import urlencode, quote_plus
import os
import base64, copy
#import sys
#import socket
#try:
#    import simplejson as json
#except ImportError:
#    import json

  
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth", "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

OversightFile = '/share/Apps/oversight/index.db'
#OversightFile = 'D:\index.db'
Oversight_movies = []
Oversight_movies_seen = []
Oversight_movies_unseen = []
trakt_movies = []
trakt_shows = []
username = TraktUsername
apikey = 'def6943c09e19dccb4df715bd4c9c6c74bc3b6d7'
pwdsha1 = sha1(TraktPwd).hexdigest()
headers = {"Accept": "*/*", "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",}

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
    
def scrobbleMissed():
    pchtrakt.logger.info('started TEST ' + pchtrakt.lastpath)
    #self.path = pchtrakt.lastpath
    ctime = time()
    pchtrakt.missed = {}
    #if pchtrakt.online:
    if os.path.isfile('missed.scrobbles'):
        with open('missed.scrobbles','r+') as f:
            pchtrakt.missed = json.load(f)
    pchtrakt.missed[pchtrakt.lastPath]={"Totaltime": int(pchtrakt.Ttime), "Totallength": int(ctime)}
    with open('missed.scrobbles','w') as f:
        json.dump(pchtrakt.missed, f, separators=(',',':'), indent=4)

def Debug(myMsg):#, force=use_debug):
    if use_debug:# or force):
        try:
            pchtrakt.logger.debug(myMsg)
        except UnicodeEncodeError:
            myMsg = myMsg.encode("utf-8", "replace")
            pchtrakt.logger.info(myMsg)

def checkSettings(daemon=False):
    if username != 'your_trakt_login':
        data = traktJsonRequest('POST', '/account/test/%%API_KEY%%')#data = traktJsonRequest('POST', '/account/test/%%API_KEY%%', silent=True)
        if data == None:  # Incorrect trakt login details
            return False
        #print('True')  
        return True

def xcp(s):
    # SQL string quote escaper
    return re.sub('''(['])''', r"''", str(s))

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
    os.system('wget "http://127.0.0.1:8883/oversight/oversight.cgi?action=watch&actionids=%s > /dev/null 2>&1' % url)
    #request = urllib2.Request("http://127.0.0.1:8883/oversight/oversight.cgi?action=watch&actionids="+data)
    #try:
    #    response = urllib2.urlopen(request).read()
    #except urllib2.URLError, e:
    #    quit(e.reason)
    data = ""

def getYamj3Connection(url, timeout = 60):
    # get a connection to YAMJ3
    data = None
    args = None
    req = Request(url, headers = headers)
    if use_debug:
        t1 = time()
    response = urlopen(req, timeout = timeout)
    #pchtrakt.online = 1
    #except URLError:# needs better except error
    #    pchtrakt.online = 0
    if use_debug:
        t2 = time()
        #Debug("[traktAPI] getTraktConnection(): response.read()")
    if pchtrakt.online == 1:
        if pchtrakt.StopTrying:
            if response.msg == "OK":
                data = '{"status": "success", "message": "set watched"}'
        else:
            data = response.read()
        if use_debug:
            #Debug("[traktAPI] Response Code: %i" % response.getcode())
            Debug("[traktAPI] Response Time: %0.2f ms" % ((t2 - t1) * 1000))
            #Debug("[traktAPI] Response Headers: %s" % str(response.info().dict))
    else:
        data = '{"status": "success", "message": "fake scrobble"}'
    return data

def getTraktConnection(url, args, timeout = 60):
    # get a connection to trakt
    if pchtrakt.online == 1:
        data = None
        #Debug("[traktAPI] urllib2.Request(%s)" % url)
        if args == None:
            req = Request(url, headers = headers)
            #req.add_header('Accept', '*/*')
        else:
            args = json.JSONEncoder().encode(args)
            req = Request(url, args)#, headers = headers)
            #Debug('[traktAPI] getTraktConnection(): urllib2.urlopen()' + urlopen(req).read())
            #req.add_header('Accept', '*/*')
            #Debug('[traktAPI] getTraktConnection(): urllib2.urlopen()' + urlopen(req).read())
            base64string = base64.encodestring('%s:%s' % (username, pwdsha1)).replace('\n', '')
            req.add_header("Authorization", "Basic %s" % base64string)
            if use_debug:
                t1 = time()
            response = urlopen(req).read()
            #pchtrakt.online = 1
            #except URLError:# needs better except error
            #    pchtrakt.online = 0
            if use_debug:
                t2 = time()
            #Debug("[traktAPI] getTraktConnection(): response.read()")
            data = json.JSONDecoder().decode(response)
            if use_debug:
                #Debug("[traktAPI] Response Code: %i" % response.getcode())
                Debug("[traktAPI] Response Time: %0.2f ms" % ((t2 - t1) * 1000))
                #Debug("[traktAPI] Response Headers: %s" % str(response.info().dict))
    else:
        data = '{"status": "success", "message": "fake scrobble"}'
    return data

def traktJsonRequest(method, url, args = {}, passVersions=False):
# make a JSON api request to trakt
# method: http method (GET or POST)
# req: REST request (ie '/user/library/movies/all.json/%%API_KEY%%/%%USERNAME%%')
# args: arguments to be passed by POST JSON (only applicable to POST requests), default:{}
# returnStatus: when unset or set to false the function returns None upon error and shows a notification,
# 	when set to true the function returns the status and errors in ['error'] as given to it and doesn't show the notification,
# 	use to customise error notifications
# silent: default is True, when true it disable any error notifications (but not debug messages)
# passVersions: default is False, when true it passes extra version information to trakt to help debug problems
# hideResponse: used to not output the json response to the log
    raw = None
    data = None
    jdata = {}
    url = 'https://api.trakt.tv' + url
    if method == 'POST':
        # debug log before username and sha1hash are injected
        Debug("[traktAPI] Request data: '%s'" % str(json.dumps(args)))

        # inject username/pass into json data
        args['username'] = username
        args['password'] = pwdsha1

        if passVersions:
            # check if plugin version needs to be passed
            args['plugin_version'] = PchTraktVersion[-4:]#0  # __settings__.getAddonInfo("version")
            args['media_center'] = 'Popcorn Hour ' + pchtrakt.chip# Todo get pch version
            args['media_center_version'] = 0
            args['media_center_date'] = '10/01/2012' 
            #jdata = urlencode(args)
        # convert to json data/or maybe urlencode?
        #else:
        #    jdata = json.dumps(args)#jdata = urlencode(args)#was jdata = json.dumps(args)

    #Debug("[traktAPI] Starting lookup.")
    
    # start retry loop (do we need retries?) remove breaks and use ?
    Debug("[traktAPI] Request URL '%s'" % (url))
    url = url.replace("%%API_KEY%%", apikey)
    url = url.replace("%%USERNAME%%", username)
    data = getTraktConnection(url, args)
    if not data:
        Debug("[traktAPI] JSON Response empty")
        return None
    #data = raw
    Debug("[traktAPI] JSON response: '%s'" % (str(data)))
        
    # check for the status variable in JSON data
    #if 'status' in data:
    #    if data['status'] == 'success':
    #        break
    #    elif returnOnFailure and data['status'] == 'failure':
    #        Debug("[traktAPI] traktJsonRequest(): Return on error set, breaking retry.")
    #        return None
    #    else:
    #        Debug("[traktAPI] traktJsonRequest(): (%i) JSON Error '%s' -> '%s'" % (i, data['status'], data['error']))

    # check to see if we have data
    #if not data is None:
    #    Debug("[traktAPI] traktJsonRequest(): Have JSON data, breaking retry.")
    #    break


    # handle scenario where all retries fail
    if data is None:
        Debug("[traktAPI] JSON Request failed, data is empty.")
        return None
    
    if 'status' in data:
        if data['status'] == 'failure':
            Debug("[traktAPI] Error: " + str(data['error']))
            if data['error'] == 'episode not found':
                raise NotFoundError()
            if data['error'] == 'failed authentication':
                raise AuthenticationTraktError()
            if data['error'] == 'shows per hour limit reached':
                #scrobbleMissed()
                data = {'status': 'success', 'message': 'shows per hour limit reached - added item to off-line list'}
                return data#raise MaxScrobbleError()
            if data['error'] == 'movies per hour limit reached':
                #scrobbleMissed()
                data = {'status': 'success', 'message': 'movies per hour limit reached - added item to off-line list'}
                return data
            #raise MaxScrobbleError()
            #if returnStatus:#do something with this?#Error: scrobbled White House Down (2013) already
            #    return data;
            return None
    return data

def trakt_api(method, url, params={}, passVersions=False):
    url = 'https://api.trakt.tv' + url
    #url = 'http://httpstat.us/502' #use to test error codes
    Debug("[traktAPI] Request URL '%s'" % (url))
    url = url.replace("%%API_KEY%%", apikey)
    if passVersions:
        # check if plugin version needs to be passed
        params['plugin_version'] = PchTraktVersion[-4:]#0  # __settings__.getAddonInfo("version")
        params['media_center'] = 'Popcorn Hour ' + pchtrakt.chip
        params['media_center_version'] = 0
        params['media_center_date'] = '10/01/2012' 
    params = json.JSONEncoder().encode(params)
    request = Request(url, params)
    Debug("[traktAPI] Request URL '%s'" % (url+params))
    base64string = base64.encodestring('%s:%s' % (username, pwdsha1)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    retries = 0
    while True:
        try:
            response = urlopen(request).read()
        except BadStatusLine, e:
            if retries >= 10:
                pchtrakt.logger.warning('[traktAPI] BadStatusLine retries failed, switching to off-line mode.')
                pchtrakt.online = 0
                break
            else:
                msg = ('[BadStatusLine] ' \
				'{0} '.format(pchtrakt.lastPath))
                pchtrakt.logger.warning(msg)
                pchtrakt.logger.warning('[traktAPI] BadStatusLine')
                retries =+ 1
                sleep(60)
                continue
        except HTTPError as e:
            if retries >= 10:
                pchtrakt.logger.warning('[traktAPI] BadStatusLine retries failed, switching to off-line mode.')
                pchtrakt.online = 0
                break
            if hasattr(e, 'code'):  # error 401 or 503, possibly others
                # read the error document, strip newlines, this will make an html page 1 line
                error_data = e.read().replace("\n", "").replace("\r", "")
                retries =+ 1
                if e.code == 401:  # authentication problem
                    #stopTrying()
                    pchtrakt.logger.error('[traktAPI] Login or password incorrect')
                    sleep(60)
                    startWait()
                elif e.code == 503:  # server busy problem
                    #stopTrying()
                    pchtrakt.logger.error('[traktAPI] trakt.tv server is busy')
                    sleep(60)
                    continue
                elif e.code == 404:  # Not found on trakt.tv
                    #stopTrying()
                    pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
                    sleep(60)
                    startWait()
                elif e.code == 403:  # Forbidden on trakt.tv
                    #stopTrying()
                    pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
                    sleep(60)
                    startWait()
                elif e.code == 502:  # Bad Gateway
                    #stopTrying()
                    pchtrakt.logger.warning('[traktAPI] Bad Gateway')
                    sleep(60)
                    continue
                    #pass
        break

    if response is None:
        Debug("[traktAPI] JSON Request failed, data is empty.")
        return None

    if pchtrakt.online == 1:
        response = json.JSONDecoder().decode(response)
    else:
        response = '{"status": "success", "message": "Off-line scrobble"}'
    
    if 'status' in response:
        if response['status'] == 'failure':
            Debug("[traktAPI] Error: " + str(response['error']))
            if response['error'] == 'episode not found':
                raise NotFoundError()
            if response['error'] == 'failed authentication':
                raise AuthenticationTraktError()
            if response['error'] == 'shows per hour limit reached':
                #scrobbleMissed()
                response = {'status': 'success', 'message': 'shows per hour limit reached - added item to off-line list'}
                return data#raise MaxScrobbleError()
            if response['error'] == 'movies per hour limit reached':
                #scrobbleMissed()
                response = {'status': 'success', 'message': 'movies per hour limit reached - added item to off-line list'}
                return response
            if response['error'] == 'episode must be > 0':
                startWait(response['error'])
                #response = {'status': 'success', 'message': 'episode must be > 0'}
                exit
            return None
    return response

def yamj3JsonRequest(url):
    raw = None
    url = 'http://%s/yamj3/%s' % (apiurl, url)
    Debug("[YAMJ3API] Starting lookup.")
    Debug("[YAMJ3API] Request URL '%s'" % (url))
    raw = getYamj3Connection(url)
    if not raw:
        Debug("[YAMJ3API] JSON Response empty")
        return None
    data = json.loads(raw)
    Debug("[YAMJ3API] JSON response: '%s'" % (str(data)))
        
    if data is None:
        Debug("[YAMJ3API] JSON Request failed, data is empty.")
        return None
    
    if 'status' in data:
        if data['status'] == 'failure':
            Debug("[YAMJ3API] Error: " + str(data['error']))
            if data['error'] == 'episode not found':
                raise NotFoundError()
            if data['error'] == 'failed authentication':
                raise AuthenticationTraktError()
            if data['error'] == 'shows per hour limit reached':
                #scrobbleMissed()
                data = {'status': 'success', 'message': 'shows per hour limit reached - added item to off-line list'}
                return data#raise MaxScrobbleError()
            if data['error'] == 'movies per hour limit reached':
                #scrobbleMissed()
                data = {'status': 'success', 'message': 'movies per hour limit reached - added item to off-line list'}
                #{u'status': u'success', u'movie': {u'year': u'1998', u'tmdb_id': u'12229', u'imdb_id': u'tt0122515', u'title': u'The Acid House'}, u'twitter': False, u'tumblr': False, u'facebook': False, u'message': u'watching The Acid House (1998)'}
                return data
            #raise MaxScrobbleError()
            return None
    return data

def startWait(msg=''):
    if msg != '':
        pchtrakt.logger.info(' [Pchtrakt] waiting for file to stop as %s' % msg)
    else:
        pchtrakt.logger.info(' [Pchtrakt] waiting for file to stop as somthing is wrong with file name')
    waitforstop = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
    pchtrakt.StopTrying = 1#pchtrakt.StopTrying = 0
    while waitforstop.status != 'noplay':
        sleep(sleepTime)
        waitforstop = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
        #pchtrakt.StopTrying = 1
        if YamjWatched == True and not pchtrakt.watched and waitforstop.percent > watched_percent and pchtrakt.CreatedFile == 0:
            try:
                watchedFileCreation(myMedia)
            except BaseException as e:
                pchtrakt.logger.error(e)

# get movies from trakt server
def getMoviesFromTrakt(daemon=False):
    data = traktJsonRequest('POST', '/user/library/movies/all.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getMoviesFromTrakt()'")
    return data

# get movie that are listed as in the users collection from trakt server
def getMovieCollectionFromTrakt(daemon=False):
    data = traktJsonRequest('POST', '/user/library/movies/collection.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getMovieCollectionFromTrakt()'")
    return data

# get easy access to movie by imdb_id
def traktMovieListByImdbID(data):
    trakt_movies = {}

    for i in range(0, len(data)):
        if data[i]['imdb_id'] == "": continue
        trakt_movies[data[i]['imdb_id']] = data[i]
        
    return trakt_movies

# get easy access to tvshow by tvdb_id
def traktShowListByTvdbID(data):
    trakt_tvshows = {}

    for i in range(0, len(data)):
        trakt_tvshows[data[i]['tvdb_id']] = data[i]
        
    return trakt_tvshows

# get seen tvshows from trakt server
def getWatchedTVShowsFromTrakt(daemon=False):
    data = traktJsonRequest('POST', '/user/library/shows/watched.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getWatchedTVShowsFromTrakt()'")
    return data

# set episodes seen on trakt
def setEpisodesSeenOnTrakt(tvdb_id, title, year, season, episode, SeenTime):
    responce = trakt_api('POST', '/show/episode/seen/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'episodes':[{'episode': episode, 'season': season, 'last_played': SeenTime}]})
    if responce == None:
        Debug("Error in request from 'setEpisodeSeenOnTrakt()'")
    return responce

# set episodes in library on trakt
def setEpisodesInLibraryOnTrakt(tvdb_id, title, year, episodes):
    data = traktJsonRequest('POST', '/show/episode/library/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'episodes': episodes})
    if data == None:
        Debug("Error in request from 'setEpisodesInLibraryOnTrakt()'")
    return data    
    
# set episodes unseen on trakt
def setEpisodesUnseenOnTrakt(tvdb_id, title, year, episodes):
    data = traktJsonRequest('POST', '/show/episode/unseen/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'episodes': episodes})
    if data == None:
        Debug("Error in request from 'setEpisodesUnseenOnTrakt()'")
    return data

# set movies seen on trakt
#  - movies, required fields are 'plays', 'last_played' and 'title', 'year' or optionally 'imdb_id'
def setMoviesSeenOnTrakt(imdb_id, title, year, SeenTime):
    responce = trakt_api('POST', '/movie/seen/%%API_KEY%%', {'movies': [{'imdb_id': imdb_id, 'title': title, 'year': year, 'plays': '1', 'last_played': SeenTime}]})#, passVersions=True
    if responce == None:
        Debug("Error in request from 'setMoviesSeenOnTrakt()'")
    return responce

# set movies unseen on trakt
#  - movies, required fields are 'plays', 'last_played' and 'title', 'year' or optionally 'imdb_id'
def setMoviesUnseenOnTrakt(movies):
    data = traktJsonRequest('POST', '/movie/unseen/%%API_KEY%%', {'movies': movies})
    if data == None:
        Debug("Error in request from 'setMoviesUnseenOnTrakt()'")
    return data

# get tvshow collection from trakt server
def getTVShowCollectionFromTrakt(daemon=False):
    data = traktJsonRequest('POST', '/user/library/shows/collection.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getTVShowCollectionFromTrakt()'")
    return data
    
# returns list of movies from watchlist
def getWatchlistMoviesFromTrakt():
    data = traktJsonRequest('POST', '/user/watchlist/movies.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getWatchlistMoviesFromTrakt()'")
    return data

# returns list of tv shows from watchlist
def getWatchlistTVShowsFromTrakt():
    data = traktJsonRequest('POST', '/user/watchlist/shows.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getWatchlistTVShowsFromTrakt()'")
    return data

# add an array of movies to the watch-list
def addMoviesToWatchlist(data):
    movies = []
    for item in data:
        movie = {}
        if "imdb_id" in item:
            movie["imdb_id"] = item["imdb_id"]
        if "tmdb_id" in item:
            movie["tmdb_id"] = item["tmdb_id"]
        if "title" in item:
            movie["title"] = item["title"]
        if "year" in item:
            movie["year"] = item["year"]
        movies.append(movie)
    
    data = traktJsonRequest('POST', '/movie/watchlist/%%API_KEY%%', {"movies":movies})
    if data == None:
        Debug("Error in request from 'addMoviesToWatchlist()'")
    return data

# remove an array of movies from the watch-list
def removeMoviesFromWatchlist(data):
    movies = []
    for item in data:
        movie = {}
        if "imdb_id" in item:
            movie["imdb_id"] = item["imdb_id"]
        if "tmdb_id" in item:
            movie["tmdb_id"] = item["tmdb_id"]
        if "title" in item:
            movie["title"] = item["title"]
        if "year" in item:
            movie["year"] = item["year"]
        movies.append(movie)
    
    data = traktJsonRequest('POST', '/movie/unwatchlist/%%API_KEY%%', {"movies":movies})
    if data == None:
        Debug("Error in request from 'removeMoviesFromWatchlist()'")
    return data

# add an array of tv shows to the watch-list
def addTVShowsToWatchlist(data):
    shows = []
    for item in data:
        show = {}
        if "tvdb_id" in item:
            show["tvdb_id"] = item["tvdb_id"]
        if "imdb_id" in item:
            show["tmdb_id"] = item["imdb_id"]
        if "title" in item:
            show["title"] = item["title"]
        if "year" in item:
            show["year"] = item["year"]
        shows.append(show)
    
    data = traktJsonRequest('POST', '/show/watchlist/%%API_KEY%%', {"shows":shows})
    if data == None:
        Debug("Error in request from 'addMoviesToWatchlist()'")
    return data

# remove an array of tv shows from the watch-list
def removeTVShowsFromWatchlist(data):
    shows = []
    for item in data:
        show = {}
        if "tvdb_id" in item:
            show["tvdb_id"] = item["tvdb_id"]
        if "imdb_id" in item:
            show["imdb_id"] = item["imdb_id"]
        if "title" in item:
            show["title"] = item["title"]
        if "year" in item:
            show["year"] = item["year"]
        shows.append(show)
    
    data = traktJsonRequest('POST', '/show/unwatchlist/%%API_KEY%%', {"shows":shows})
    if data == None:
        Debug("Error in request from 'removeMoviesFromWatchlist()'")
    return data

# Set the rating for a movie on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateMovieOnTrakt(imdbid, title, year, rating):
    if not (rating in ("love", "hate", "unrate")):
        # add error message
        return
    
    Debug("Rating movie:" + rating)
    
    data = traktJsonRequest('POST', '/rate/movie/%%API_KEY%%', {'imdb_id': imdbid, 'title': title, 'year': year, 'rating': rating})
    if data == None:
        Debug("Error in request from 'rateMovieOnTrakt()'")
    
    # if (rating == "unrate"):
        # notification("Trakt Utilities", __language__(1166).encode( "utf-8", "ignore" )) # Rating removed successfully
    # else :
        # notification("Trakt Utilities", __language__(1167).encode( "utf-8", "ignore" )) # Rating submitted successfully
    
    return data

# Get the rating for a movie from trakt
def getMovieRatingFromTrakt(imdbid, title, year):
    if imdbid == "" or imdbid == None:
        return None  # would be nice to be smarter in this situation
    
    data = traktJsonRequest('POST', '/movie/summary.json/%%API_KEY%%/' + str(imdbid))
    if data == None:
        Debug("Error in request from 'getMovieRatingFromTrakt()'")
        return None
        
    if 'rating' in data:
        return data['rating']
        
    #print data
    Debug("Error in request from 'getMovieRatingFromTrakt()'")
    return None

# Set the rating for a tv episode on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateEpisodeOnTrakt(tvdbid, title, year, season, episode, rating):
    if not (rating in ("love", "hate", "unrate")):
        # add error message
        return
    
    Debug("Rating episode:" + rating)
    
    data = traktJsonRequest('POST', '/rate/episode/%%API_KEY%%', {'tvdb_id': tvdbid, 'title': title, 'year': year, 'season': season, 'episode': episode, 'rating': rating})
    if data == None:
        Debug("Error in request from 'rateEpisodeOnTrakt()'")
    
    # if (rating == "unrate"):
        # notification("Trakt Utilities", __language__(1166).encode( "utf-8", "ignore" )) # Rating removed successfully
    # else :
        # notification("Trakt Utilities", __language__(1167).encode( "utf-8", "ignore" )) # Rating submitted successfully
    
    return data
    
# Get the rating for a tv episode from trakt
def getEpisodeRatingFromTrakt(tvdbid, title, year, season, episode):
    if tvdbid == "" or tvdbid == None:
        return None  # would be nice to be smarter in this situation
    
    data = traktJsonRequest('POST', '/show/episode/summary.json/%%API_KEY%%/' + str(tvdbid) + "/" + season + "/" + episode)
    if data == None:
        Debug("Error in request from 'getEpisodeRatingFromTrakt()'")
        return None
        
    if 'rating' in data:
        return data['rating']
        
    #print data
    Debug("Error in request from 'getEpisodeRatingFromTrakt()'")
    return None

# Set the rating for a tv show on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateShowOnTrakt(tvdbid, title, year, rating):
    if not (rating in ("love", "hate", "unrate")):
        # add error message
        return
    
    Debug("Rating show:" + rating)
    
    data = traktJsonRequest('POST', '/rate/show/%%API_KEY%%', {'tvdb_id': tvdbid, 'title': title, 'year': year, 'rating': rating})
    if data == None:
        Debug("Error in request from 'rateShowOnTrakt()'")
    
    # if (rating == "unrate"):
        # notification("Trakt Utilities", __language__(1166).encode( "utf-8", "ignore" )) # Rating removed successfully
    # else :
        # notification("Trakt Utilities", __language__(1167).encode( "utf-8", "ignore" )) # Rating submitted successfully
    
    return data

# Get the rating for a tv show from trakt
def getShowRatingFromTrakt(tvdbid, title, year):
    if tvdbid == "" or tvdbid == None:
        return None  # would be nice to be smarter in this situation
    
    data = traktJsonRequest('POST', '/show/summary.json/%%API_KEY%%/' + str(tvdbid))
    if data == None:
        Debug("Error in request from 'getShowRatingFromTrakt()'")
        return None
        
    if 'rating' in data:
        return data['rating']
        
    #print data
    Debug("Error in request from 'getShowRatingFromTrakt()'")
    return None

def getRecommendedMoviesFromTrakt():
    data = traktJsonRequest('POST', '/recommendations/movies/%%API_KEY%%')
    if data == None:
        Debug("Error in request from 'getRecommendedMoviesFromTrakt()'")
    return data

def getRecommendedTVShowsFromTrakt():
    data = traktJsonRequest('POST', '/recommendations/shows/%%API_KEY%%')
    if data == None:
        Debug("Error in request from 'getRecommendedTVShowsFromTrakt()'")
    return data

def getTrendingMoviesFromTrakt():
    data = traktJsonRequest('GET', '/movies/trending.json/%%API_KEY%%')
    if data == None:
        Debug("Error in request from 'getTrendingMoviesFromTrakt()'")
    return data

def getTrendingTVShowsFromTrakt():
    data = traktJsonRequest('GET', '/shows/trending.json/%%API_KEY%%')
    if data == None:
        Debug("Error in request from 'getTrendingTVShowsFromTrakt()'")
    return data

def getFriendsFromTrakt():
    data = traktJsonRequest('POST', '/user/friends.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getFriendsFromTrakt()'")
    return data

def getWatchingFromTraktForUser(name):
    data = traktJsonRequest('POST', '/user/watching.json/%%API_KEY%%/%%USERNAME%%')
    if data == None:
        Debug("Error in request from 'getWatchingFromTraktForUser()'")
    return data

###############################
##### Scrobbling to trakt #####
###############################

# tell trakt that the user is watching a movie
def watchingMovieOnTrakt(imdb_id, title, year, duration, percent):
    responce = trakt_api('POST', '/movie/watching/%%API_KEY%%', {'imdb_id': imdb_id, 'title': title, 'year': year, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingMovieOnTrakt()'")
    return responce

# tell trakt that the user is watching an episode
def watchingEpisodeOnTrakt(tvdb_id, title, year, season, episode, duration, percent):
    responce = trakt_api('POST', '/show/watching/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has stopped watching a movie
def cancelWatchingMovieOnTrakt():
    responce = trakt_api('POST', '/movie/cancelwatching/%%API_KEY%%')
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingMovieOnTrakt()'")
    return responce

# tell trakt that the user has stopped an episode
def cancelWatchingEpisodeOnTrakt():
    responce = trakt_api('POST', '/show/cancelwatching/%%API_KEY%%')
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has finished watching an movie
def scrobbleMovieOnTrakt(imdb_id, title, year, duration, percent):
    responce = trakt_api('POST', '/movie/scrobble/%%API_KEY%%', {'imdb_id': imdb_id, 'title': title, 'year': year, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'scrobbleMovieOnTrakt()'")
    return responce

# tell trakt that the user has finished watching an episode
def scrobbleEpisodeOnTrakt(tvdb_id, title, year, season, episode, duration, percent):
    responce = trakt_api('POST', '/show/scrobble/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'scrobbleEpisodeOnTrakt()'")
    return responce

###############################
########## YAMJ3 API ##########
###############################

# get genres of file from YAMJ3 API
def getgenres(yamjname):
    responce = yamj3JsonRequest('api/genre?filename={0}'.format(quote_plus(yamjname)))
    #Debug('[YAMJ3API] ' + str(responce))
    if responce == None:
        Debug("[YAMJ3API] Error in request from 'scrobbleEpisodeOnTrakt()'")
    return responce

# get genres of file from YAMJ3 API
def watched(pchtrakt):
    yamjname = pchtrakt.lastName.encode('utf-8', 'replace')
    responce = yamj3JsonRequest('api/watched?filename={0}?watched={1}'.format(quote_plus(yamjname), str(pchtrakt.lastPercent)))
    #Debug('[YAMJ3API] ' + str(responce))
    if responce == None:
        Debug("[YAMJ3API] Error in request from 'scrobbleEpisodeOnTrakt()'")
    return responce
            
"""
ToDo:


"""


"""
for later:
First call "Player.GetActivePlayers" to determine the currently active player (audio, video or picture).
If it is audio or video call Audio/VideoPlaylist.GetItems and read the "current" field to get the position of the
currently playling item in the playlist. The "items" field contains an array of all items in the playlist and "items[current]" is
the currently playing file. You can also tell jsonrpc which fields to return for every item in the playlist and therefore you'll have all the information you need.

"""

