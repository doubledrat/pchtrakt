# -*- coding: utf-8 -*-

from pchtrakt.config import *
from lib.trakt import TraktAPI
import re
import os
import copy


class OversightSyncMain:
    def __init__(self):
        self.OversightFile = '/share/Apps/oversight/index.db'
        #self.OversightFile = 'D:\index.db'
        self.Oversight_movies = []
        self.Oversight_movies_seen = []
        self.Oversight_movies_unseen = []
        self.trakt_movies = []
        self.trakt_shows = []

    def OversightSync(self):
        if SyncCheck >= 0:
            if Oversightumc or Oversightumw:
                get_Oversight_movies(self)
                get_trakt_movies(self)
                if Oversightumc:
                    Oversight_movies_to_trakt(self)
                if Oversightumw:
                    Oversight_movies_watched_to_trakt(self)
                    trakt_movies_watched_to_Oversight(self)
            if Oversightusc or Oversightusw:
                self.Oversight_shows = {}
                get_Oversight_shows(self)
                get_trakt_shows(self)
                if Oversightusc:
                    Oversight_shows_to_trakt(self)
                if Oversightusw:
                    Oversight_shows_watched_to_trakt(self)
                    trakt_shows_watched_to_Oversight(self)
        #clear globals
        del self

def get_Oversight_movies(self):
    pchtrakt.logger.info(' [Oversight] Getting movies from Oversight')
    f=open(self.OversightFile, 'r')
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
            
            self.Oversight_movies.append(Oversight_movie)

            if "\t_w\t1\t" in movie:
                self.Oversight_movies_seen.append(Oversight_movie)
            else:
                self.Oversight_movies_unseen.append(Oversight_movie)
    f.close()

def get_trakt_movies(self):
    pchtrakt.logger.info(' [Oversight] Getting movies from trakt.tv')

    # Collection
    url = 'sync/collection/movies'
    trakt_api = TraktAPI()
    movies = trakt_api.traktRequest(url)
    
    for movie in movies:
        trakt_movie = {
            'title': movie['movie']['title'],
            'year': movie['movie']['year'],
        }

        if 'imdb' in movie['movie']['ids']:
            trakt_movie['imdb_id'] = movie['movie']['ids']['imdb']
        if 'tmdb' in movie['movie']['ids']:
            trakt_movie['tmdb_id'] = movie['movie']['ids']['tmdb']
        #trakt_movie['id'] = ""

        self.trakt_movies.append(trakt_movie)

    #Clean from collection, keep commented
    #url = 'https://api.trakt.tv/movie/unlibrary/' + TraktAPI
    #params = {'movies': self.trakt_movies}
    #response = trakt_api(url, params)
    # Seen
    url = 'sync/watched/movies'
    seen_movies = trakt_api.traktRequest(url)
    
    # Add playcounts to trakt collection
    for seen in seen_movies:
        if 'imdb' in seen['movie']['ids']:
            for movie in self.trakt_movies:
                if 'imdb_id' in movie:
                    if seen['movie']['ids']['imdb'] == movie['imdb_id']:
                        movie['plays'] = seen['plays']
        elif 'tmdb' in seen['movie']['ids']:
            for movie in self.trakt_movies:
                if 'tmdb_id' in movie:
                    if seen['movie']['ids']['tmdb'] == movie['tmdb_id']:
                        movie['plays'] = seen['plays']

        elif 'title' in seen['movie']:
            for movie in self.trakt_movies:
                if 'title' in movie:
                    if seen['movie']['title'] == movie['title']:
                        movie['plays'] = seen['plays']

    for movie in self.trakt_movies:
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

def Oversight_movies_to_trakt(self):
    pchtrakt.logger.info(' [Oversight] Checking for Oversight movies that are not in trakt.tv collection')
    self.Oversight_movies_to_trakt = []

    if self.trakt_movies and self.Oversight_movies:
        imdb_ids = [x['imdb_id'] for x in self.trakt_movies if 'imdb_id' in x]
        tmdb_ids = [x['tmdb_id'] for x in self.trakt_movies if 'tmdb_id' in x]
        titles = [x['title'] for x in self.trakt_movies if 'title' in x]

    if self.Oversight_movies:
        for movie in self.Oversight_movies:
            if 'imdbnumber' in movie:
                if movie['imdbnumber'].startswith('tt'):
                    if self.trakt_movies:
                        if not movie['imdbnumber'] in imdb_ids:
                            self.Oversight_movies_to_trakt.append(movie)
                            #trakt_movie = convert_Oversight_movie_to_trakt(movie)
                            #trakt_movie['plays'] = 0
                            #self.trakt_movies.append(trakt_movie)
                    else:
                        self.Oversight_movies_to_trakt.append(movie)
                        #trakt_movie = convert_Oversight_movie_to_trakt(movie)
                        #trakt_movie['plays'] = 0
                        #self.trakt_movies.append(trakt_movie)
                else:
                    if self.trakt_movies:
                        if not movie['tmdb_id'] in tmdb_ids:
                            self.Oversight_movies_to_trakt.append(movie)
                            #trakt_movie = convert_Oversight_movie_to_trakt(movie)
                            #trakt_movie['plays'] = 0
                            #self.trakt_movies.append(trakt_movie)
                    else:
                        self.Oversight_movies_to_trakt.append(movie)
                        #trakt_movie = convert_Oversight_movie_to_trakt(movie)
                        #trakt_movie['plays'] = 0
                        #self.trakt_movies.append(trakt_movie)
            elif not movie['title'] in titles and not movie in self.Oversight_movies_to_trakt:
                self.Oversight_movies_to_trakt.append(movie)
                #trakt_movie = convert_Oversight_movie_to_trakt(movie)
                #trakt_movie['plays'] = 0
                #self.trakt_movies.append(trakt_movie)

    if self.Oversight_movies_to_trakt:
        pchtrakt.logger.info(' [Oversight] Checking for %s movies will be added to trakt.tv collection' % len(self.Oversight_movies_to_trakt))

        for i in range(len(self.Oversight_movies_to_trakt)):
            #convert Oversight movie into something trakt will understand
            self.Oversight_movies_to_trakt[i] = convert_Oversight_movie_to_trakt(self.Oversight_movies_to_trakt[i])

        # Send request to add movies to trakt.tv
        url = 'sync/collection'
        params = {'movies': self.Oversight_movies_to_trakt}
        trakt_api = TraktAPI()

        try:
            pchtrakt.logger.info(' [Oversight] Adding movies to trakt.tv collection...')
            response = trakt_api.traktRequest(url, params, method='POST')
            if response['added']['movies'] != 0:
                pchtrakt.logger.info(' [Oversight] Successfully added %s out of %s to your collection' % (response['added']['movies'], response['added']['movies'] + response['existing']['movies'] + len(response['not_found']['movies'])))
            if len(response['not_found']) != 0:
                pchtrakt.logger.info(' [Oversight] Failed to add the following %s titles to your collection' % len(response['not_found']['movies']))
                for failed in response['not_found']['movies']:
                    pchtrakt.logger.info(' [Oversight] Failed to add %s' % failed['title'].encode('utf-8', 'replace'))
        except Exception, e:
            pchtrakt.logger.info(' [Oversight] Failed to add movies to trakt.tv collection')
            pchtrakt.logger.info(e)
            
    else:
        pchtrakt.logger.info(' [Oversight] trakt.tv movie collection is up to date')

def Oversight_movies_watched_to_trakt(self):
    pchtrakt.logger.info(' [Oversight] Comparing Oversight watched movies against trakt.tv')
    self.Oversight_movies_to_trakt = []

    if self.trakt_movies and self.Oversight_movies:

        for i in range(len(self.trakt_movies)):
            for movie in self.Oversight_movies:
                if movie['playcount'] != 0:

                    if 'imdb_id' in self.trakt_movies[i]:
                        if movie['imdbnumber'] == self.trakt_movies[i]['imdb_id']:
                            if self.trakt_movies[i]['plays'] < movie['playcount']:
                                self.Oversight_movies_to_trakt.append(convert_Oversight_movie_to_trakt(movie))

                    elif 'tmdb_id' in self.trakt_movies[i]:
                        if movie['imdbnumber'] == self.trakt_movies[i]['tmdb_id']:
                            if self.trakt_movies[i]['plays'] < movie['playcount']:
                                self.Oversight_movies_to_trakt.append(convert_Oversight_movie_to_trakt(movie))

                    elif movie['title'] == self.trakt_movies[i]['title']:
                        if self.trakt_movies[i]['plays'] < movie['playcount']:
                            self.Oversight_movies_to_trakt.append(convert_Oversight_movie_to_trakt(movie))

    if self.Oversight_movies_to_trakt:
        pchtrakt.logger.info(' [Oversight] %s movies playcount will be updated on trakt.tv' % len(self.Oversight_movies_to_trakt))

        # Send request to update playcounts on trakt.tv
        url = 'sync/history'
        params = {'movies': self.Oversight_movies_to_trakt}
        trakt_api = TraktAPI()

        try:
            pchtrakt.logger.info(' [Oversight] Updating watched status for movies on trakt.tv...')
            response = trakt_api.traktRequest(url, params, method='POST')
            pchtrakt.logger.info(' [Oversight]     Marked %s as watched out of %s movies' % (response['added']['movies'], len(self.Oversight_movies_to_trakt)))
            if len(response['not_found']['movies']) != 0:
                for skip in response['not_found']['movies']:
                    pchtrakt.logger.info(' [Oversight]    could not add     -->%s' % skip['not_found']['movies'][0]['title'].encode('utf-8'))
        except Exception, e:
            pchtrakt.logger.info(' [Oversight] Failed to update playcount for movies on trakt.tv')
            pchtrakt.logger.info(e)
    else:
        pchtrakt.logger.info(' [Oversight] trakt.tv movie playcount is up to date')

def trakt_movies_watched_to_Oversight(self):
    pchtrakt.logger.info(' [Oversight] Comparing trakt.tv watched movies against Oversight')

    self.trakt_movies_seen = []

    if self.trakt_movies and self.Oversight_movies_unseen:
        for i in range(len(self.trakt_movies)):
            for movie in self.Oversight_movies_unseen:
                if movie['playcount'] == 0 and self.trakt_movies[i]['plays'] != 0:

                    if 'imdb_id' in self.trakt_movies[i]:
                        if movie['imdbnumber'] == self.trakt_movies[i]['imdb_id']:
                            self.trakt_movies[i]['movieid'] = movie['imdbnumber']
                            self.trakt_movies[i]['id'] = movie['id']

                    elif 'tmdb_id' in self.trakt_movies[i]:
                        if movie['tmdb_id'] == self.trakt_movies[i]['tmdb_id']:
                            self.trakt_movies[i]['movieid'] = movie['tmdb_id']
                            self.trakt_movies[i]['id'] = movie['id']

                    elif movie['title'] == self.trakt_movies[i]['title']:
                        self.trakt_movies[i]['movieid'] = movie['title']
                        self.trakt_movies[i]['id'] = movie['id']

    # Remove movies without a movieid
    if self.trakt_movies:

        for movie in self.trakt_movies:
            if 'movieid' in movie:
                self.trakt_movies_seen.append(movie)

    if self.trakt_movies_seen:
        data = "*("
        pchtrakt.logger.info(' [Oversight] %s movies playcount will be updated on Oversight' % len(self.trakt_movies_seen))
        #addValue = "\t_w\t1\t"
        #checkvalue = "\t_w\t0\t"
        #myfile_list = open(OversightFile).readlines()
        #newList = []
        for movie in self.trakt_movies_seen:
            if movie['id']:# in movie:
                pchtrakt.logger.info(' [Oversight]     -->%s' % movie['title'].encode('utf-8'))
                m = movie['id']
                if data == "*(":
                    data = data + m
                else:
                    data = data  + "|" + m
        WatchedOversight(data+")")
        data = ""
    else:
        pchtrakt.logger.info(' [Oversight] Watched movies on Oversight are up to date')

def get_Oversight_shows(self):
    pchtrakt.logger.info(' [Oversight] Getting TV shows from Oversight')
    f=open(self.OversightFile, 'r')
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

            if title not in self.Oversight_shows:
                shows = self.Oversight_shows[title] = {'episodes': []}  # new show dictionary
            else:
                shows = self.Oversight_shows[title]
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

def get_trakt_shows(self):
    pchtrakt.logger.info(' [Oversight] Getting TV shows from trakt')

    # Collection
    url = 'sync/collection/shows'
    
    trakt_api = TraktAPI()
    collection_shows = trakt_api.traktRequest(url)
    
    for show in collection_shows:
        trakt_show = {
            'title': show['show']['title'],
            'episodes': []
        }

        if 'imdb' in show['show']['ids']:
            trakt_show['imdb'] = show['show']['ids']['imdb']
        if 'tvdb' in show['show']['ids']:
            trakt_show['tvdb'] = show['show']['ids']['tvdb']

        for season in show['seasons']:
            for episode in season['episodes']:
                ep = {'season': season['number'], 'episode': episode['number'], 'plays': 0}
                trakt_show['episodes'].append(ep)

        #Clean from collection, keep commented
        #url = 'https://api.trakt.tv/show/episode/unlibrary/' + TraktAPI
        #params = trakt_show
        #response = trakt_api(url, params)
        self.trakt_shows.append(trakt_show)

    collection_shows = None
    
    # Seen
    url = 'sync/watched/shows'
    seen_shows = trakt_api.traktRequest(url)
    show = ''
    
    for show in seen_shows:
        for season in show['seasons']:
            for episode in season['episodes']:
                for trakt_show in self.trakt_shows:
                    if ('imdb' in show['show']['ids'] and 'imdb' in trakt_show) and show['show']['ids']['imdb'] != None and show['show']['ids']['imdb'] == trakt_show['imdb']:
                        try:
                            #if len(show['show']['ids']['imdb']) > 0:
                                for trakt_episode in trakt_show['episodes']:
                                    if trakt_episode['season'] == season['number'] and trakt_episode['episode'] == episode['number']:
                                        trakt_episode['plays'] = 1
                        except Exception as e:
                            pass
    
                    elif ('tvdb' in show['show']['ids'] and 'tvdb' in trakt_show) and show['show']['ids']['tvdb'] != None and show['show']['ids']['tvdb'] == trakt_show['tvdb']:
                        try:
                            #if len(show['show']['ids']['tvdb']) > 0:
                                for trakt_episode in trakt_show['episodes']:
                                    if trakt_episode['season'] == season['number'] and trakt_episode['episode'] == episode['number']:
                                        trakt_episode['plays'] = 1
                        except Exception as e:
                            pass
    
                    else:
                        try:
                            if show['show']['title'] == trakt_show['title']:
                                for trakt_episode in trakt_show['episodes']:
                                    if trakt_episode['season'] == season['number'] and trakt_episode['episode'] == episode['number']:
                                        trakt_episode['plays'] = 1
                        except:
                            if show['show']['title'] == trakt_show['shows'][0]['title']:
                                for trakt_episode in trakt_show['episodes']:
                                    if trakt_episode['season'] == season['number'] and trakt_episode['episode'] == episode['number']:
                                        trakt_episode['plays'] = 1
    
    seen_shows = ''
    show = ''

def convert_Oversight_show_to_trakt(show):
    ids = {}

    trakt_show = {'shows': []}
    if 'title' in show:
        if 'imdbnumber' in show:
            if show['imdbnumber'].startswith('tt'):
                ids['imdb'] = show['imdbnumber']
            else:
                ids['tvdb'] = show['imdbnumber']
        if 'tvdb' in show:
            ids['tvdb'] = show['tvdb']
    
    if 'episodes' in show and show['episodes']:
        ep = {}
        for episode in show['episodes']:
            try:
                ep[episode["season"]].append(episode["episode"])
            except:
                ep[episode["season"]] = [episode["episode"]]
        ep1 = {"seasons":[]}
        y=0
        for i in ep:
            tmp = dict()
            tmp["number"] = i
            tmp["episodes"] = []
            for j in ep[i]:
                if 'watched_at' in show['episodes'][y]:
                    tmp["episodes"].append({"number":j, 'watched_at': show['episodes'][y]['watched_at']})
                else:
                    tmp["episodes"].append({"number":j})
                y=y+1
            ep1["seasons"].append(tmp)
            #y=y+1
    
        test = [{'title': show['title'], 'ids': ids, 'seasons': ep1['seasons']}]
        trakt_show['shows'] = test
        #trakt_show['shows'].append(test)
    
    return trakt_show

def Oversight_shows_to_trakt(self):
    pchtrakt.logger.info(' [Oversight] Checking for Oversight episodes that are not in trakt.tv collection')
    self.Oversight_shows_to_trakt = []

    def clean_episodes(shows):
        if shows:
            for show in shows:
                episodes = []
                for episode in show['episodes']:
                    episodes.append({'season': episode['season'], 'episode': episode['episode']})
                show['episodes'] = episodes

        return shows

    if self.Oversight_shows and self.trakt_shows:

        t_shows = copy.deepcopy(self.trakt_shows)
        t_shows = clean_episodes(t_shows)
        x_shows = copy.deepcopy(self.Oversight_shows.values())
        x_shows = clean_episodes(x_shows)

        tvdb_ids = {}
        imdb_ids = {}

        if self.trakt_shows:
            for i in range(len(t_shows)):
                if 'tvdb' in t_shows[i]:
                    tvdb_ids[t_shows[i]['tvdb']] = i

                if 'imdb' in t_shows[i]:
                    imdb_ids[t_shows[i]['imdb']] = i

        for show in x_shows:
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if search(self, imdb_ids, show['imdbnumber']) == False:
                        self.Oversight_shows_to_trakt.append(show)

                        #trakt_show = convert_Oversight_show_to_trakt(show)
                        #for episode in trakt_show['episodes']:
                        #    episode['plays'] = 0

                        #self.trakt_shows.append(trakt_show)

                    else:
                        t_index = imdb_ids.get(show['imdbnumber'])

                        Oversight_show = {
                            'title': show['title'],
                            'imdbnumber': show['imdbnumber'],
                            'episodes': []
                        }

                        for episode in show['episodes']:
                            if episode not in t_shows[t_index]['episodes']:
                                Oversight_show['episodes'].append(episode)

                                self.trakt_shows[t_index]['episodes'].append(episode)
                                self.trakt_shows[t_index]['episodes'][-1]['plays'] = 0

                        if Oversight_show['episodes']:
                            self.Oversight_shows_to_trakt.append(Oversight_show)

                else:
                    if searchtv(self, tvdb_ids, show['imdbnumber']) == False:
                        self.Oversight_shows_to_trakt.append(show)

                        #trakt_show = convert_Oversight_show_to_trakt(show)
                        #for episode in trakt_show['episodes']:
                        #    episode['plays'] = 0

                        #self.trakt_shows.append(trakt_show)

                    else:
                        t_index = tvdb_ids.get(int(show['imdbnumber']))

                        Oversight_show = {
                            'title': show['title'],
                            'imdbnumber': show['imdbnumber'],
                            'episodes': []
                        }

                        for episode in show['episodes']:
                            if episode['episode'] == 0:
                                continue
                            if episode not in t_shows[t_index]['episodes']:
                                Oversight_show['episodes'].append(episode)

                                self.trakt_shows[t_index]['episodes'].append(episode)
                                self.trakt_shows[t_index]['episodes'][-1]['plays'] = 0

                        if Oversight_show['episodes']:
                            self.Oversight_shows_to_trakt.append(Oversight_show)

        if self.Oversight_shows_to_trakt:
            pchtrakt.logger.info(' [Oversight] %s TV shows have episodes missing from trakt.tv collection' % len(self.Oversight_shows_to_trakt))

            for i in range(len(self.Oversight_shows_to_trakt)):
                #convert Oversight show into something trakt will understand
                self.Oversight_shows_to_trakt[i] = convert_Oversight_show_to_trakt(self.Oversight_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = 'sync/collection'
            trakt_api = TraktAPI()

            for show in self.Oversight_shows_to_trakt:
                try:
                    pchtrakt.logger.info(' [Oversight]     -->%s' % show['shows'][0]['title'].encode('utf-8'))
                    trakt = trakt_api.traktRequest(url, show, method='POST')
                    if trakt['added']['episodes'] > 0:
                        pchtrakt.logger.info(' [Oversight]       Added %s' % trakt['added']['episodes'])
                    if trakt['updated']['episodes'] > 0:
                        pchtrakt.logger.info(' [Oversight]       Updated %s' % trakt['updated']['episodes'])
                    if trakt['existing']['episodes'] > 0:
                        pchtrakt.logger.info(' [Oversight]       Modified %s' % trakt['existing']['episodes'])
                except Exception, e:
                    pchtrakt.logger.info(' [Oversight] Failed to add %s\'s new episodes to trakt.tv collection' % show['title'].encode('utf-8'))
                    pchtrakt.logger.info(e)

        else:
            pchtrakt.logger.info(' [Oversight] trakt.tv TV show collection is up to date')

def Oversight_shows_watched_to_trakt(self):
    pchtrakt.logger.info(' [Oversight] Comparing Oversight watched TV shows against trakt.tv')
    self.Oversight_shows_to_trakt = []

    if self.Oversight_shows and self.trakt_shows:

        tvdb_ids = {}
        imdb_ids = {}

        for i in range(len(self.trakt_shows)):
            if 'tvdb' in self.trakt_shows[i]:
                tvdb_ids[self.trakt_shows[i]['tvdb']] = i

            if 'imdb' in self.trakt_shows[i]:
                imdb_ids[self.trakt_shows[i]['imdb']] = i

        for show in self.Oversight_shows.values():
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if search(self, imdb_ids, show['imdbnumber']):
                        trakt_show = self.trakt_shows[imdb_ids.get(show['imdbnumber'])]

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
                            self.Oversight_shows_to_trakt.append(trakt_show_watched)

                else:
                    if searchtv(self, tvdb_ids, show['imdbnumber']):
                        trakt_show = self.trakt_shows[tvdb_ids.get(int(show['imdbnumber']))]

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
                            self.Oversight_shows_to_trakt.append(trakt_show_watched)

        if self.Oversight_shows_to_trakt:
            pchtrakt.logger.info(' [Oversight] %s TV shows have episodes that will be marked as watched in trakt.tv collection' % len(self.Oversight_shows_to_trakt))

            for i in range(len(self.Oversight_shows_to_trakt)):
                #convert Oversight show into something trakt will understand
                self.Oversight_shows_to_trakt[i] = convert_Oversight_show_to_trakt(self.Oversight_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = 'sync/history'
            trakt_api = TraktAPI()

            for show in self.Oversight_shows_to_trakt:
                try:
                    pchtrakt.logger.info(' [Oversight]     -->%s' % show['shows'][0]['title'].encode('utf-8'))
                    trakt = trakt_api.traktRequest(url, show, method='POST')
                    if trakt['added']['episodes'] != 0 and len(trakt['not_found']['episodes']) != 0:
                        pchtrakt.logger.info(' [Oversight] Successfully marked  %s episodes watched out of %s' % (trakt['added']['episodes'], trakt['added']['episodes'] + trakt['not_found']['episodes']))
                    else:
                        pchtrakt.logger.info(' [Oversight] Successfully marked  %s episodes watched out of %s' % (trakt['added']['episodes'], trakt['added']['episodes']))
                except Exception, e:
                    pchtrakt.logger.info(' [Oversight] Failed to mark %s\'s episodes as watched in trakt.tv collection' % show['shows'][0]['title'].encode('utf-8'))
                    pchtrakt.logger.info(e)

        else:
            pchtrakt.logger.info(' [Oversight] trakt.tv TV show watched status is up to date')

def trakt_shows_watched_to_Oversight(self):
    pchtrakt.logger.info(' [Oversight] Comparing trakt.tv watched TV shows against Oversight')
    self.trakt_shows_seen = []

    if self.Oversight_shows and self.trakt_shows:

        tvdb_ids = {}
        imdb_ids = {}

        for i in range(len(self.trakt_shows)):
            if 'tvdb' in self.trakt_shows[i]:
                tvdb_ids[self.trakt_shows[i]['tvdb']] = i

            if 'imdb' in self.trakt_shows[i]:
                imdb_ids[self.trakt_shows[i]['imdb']] = i

        for show in self.Oversight_shows.values():
            if 'imdbnumber' in show:
                if show['imdbnumber'].startswith('tt'):
                    if search(self, imdb_ids, show['imdbnumber']):
                        trakt_show = self.trakt_shows[imdb_ids[show['imdbnumber']]]

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
                            self.trakt_shows_seen.append(Oversight_show)

                else:
                    if searchtv(self, tvdb_ids, show['imdbnumber']):
                        trakt_show = self.trakt_shows[tvdb_ids[int(show['imdbnumber'])]]

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
                            self.trakt_shows_seen.append(Oversight_show)



        #http://192.168.123.154:8883/oversight/oversight.cgi?select=Mark&action=watch&actionids=*(90)
        if self.trakt_shows_seen:
            pchtrakt.logger.info(' [Oversight] %s TV shows episodes watched status will be updated in Oversight' % len(self.trakt_shows_seen))
            data = "*("
            #with open(self.OversightFile, 'r') as infile:
            for show_dict in self.trakt_shows_seen:
                pchtrakt.logger.info(' [Oversight]     -->%s' % show_dict["title"].encode('utf-8'))
                for episode in show_dict['episodes']:
                    pchtrakt.logger.info(' [Oversight]       Season %i - Episode %i' % (episode['season'], episode['episode']))
                    m = episode['ids']
                        
                    if data == "*(":
                        data = data + m
                    else:
                        data = data  + "|" + m
            WatchedOversight(data+")")
            data = ""
        else:
            pchtrakt.logger.info(' [Oversight] Watched TV shows on Oversight are up to date')

def WatchedOversight(data):
    pchtrakt.logger.info(' [Oversight] sending to Oversight')
    url = data + '"'
    #command = 'wget "http://%s:8883/oversight/oversight.cgi?action=watch&actionids=%s > /dev/null 2>&1' % (ipPch, url)
    os.system('wget "http://%s:8883/oversight/oversight.cgi?action=watch&actionids=%s > /dev/null 2>&1' % (ipPch, url))
    #request = urllib2.Request("http://127.0.0.1:8883/oversight/oversight.cgi?action=watch&actionids="+data)
    #try:
    #    response = urllib2.urlopen(request).read()
    #except urllib2.URLError, e:
    #    quit(e.reason)
    data = ""

def searchtv(self, values, searchFor):
    for k in values:
        if int(searchFor) == k:
            return True
    return False
        
def search(self, values, searchFor):
    for k in values:
        if searchFor == k:
            return True
    return False