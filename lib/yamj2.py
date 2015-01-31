# -*- coding: utf-8 -*-

import re
import os
import copy

from pchtrakt.config import *
from lib.utilities import Debug, trakt_apiv2
from xml.etree import ElementTree
from urllib import unquote_plus

from time import strftime



class YAMJSyncMain:
    

    def __init__(self):
        # Set variables
        self.name = YamjPath + 'CompleteMovies.xml'
        self.YAMJ_movies = []
        self.YAMJ_movies_seen = []
        self.YAMJ_movies_unseen = []
        self.trakt_movies = []
        self.trakt_shows = []

    def YAMJSync(self):
        if YAMJSyncCheck >= 0:
            Debug('[Pchtrakt] Reading ' + self.name)
            self.tree = ElementTree.parse(self.name)
            Debug('[Pchtrakt] Finished')
            if YAMJumc or YAMJumw:
                self.get_YAMJ_movies()
                self.get_trakt_movies()
                if YAMJumc:
                    self.YAMJ_movies_to_trakt()
                if YAMJumw:
                    self.get_trakt_movies() #Need to re-get trakt films in case they were updated above
                    self.YAMJ_movies_watched_to_trakt()
                    if markYAMJ:
                        self.trakt_movies_watched_to_YAMJ()
                self.YAMJ_movies = None
                self.YAMJ_movies_seen = None
                self.YAMJ_movies_unseen = None
                self.trakt_movies = None
    
            if YAMJusc or YAMJusw:
                self.YAMJ_shows = {}
                self.get_YAMJ_shows()
                self.get_trakt_shows()
                if YAMJusc:
                    self.YAMJ_shows_to_trakt()
                if YAMJusw:
                    self.get_trakt_shows() #Need to re-get trakt shows in case they were updated above
                    self.YAMJ_shows_watched_to_trakt()
                    if markYAMJ:
                        self.trakt_shows_watched_to_YAMJ()
        #clear globals
        del self

    
    def get_YAMJ_movies(self):
        pchtrakt.logger.info(' [YAMJ] Getting movies from YAMJ')
        for movie in self.tree.findall('movies'):
            if movie.get('isTV') == 'false':
                    
                # create movie item
                YAMJ_movie = {
                              'title': movie.find('originalTitle').text.encode('utf-8')
                              }
                try:
                    YAMJ_movie['imdbnumber'] = movie.find("id/[@movieDatabase='imdb']").text
                except Exception, e:
                    YAMJ_movie['imdbnumber'] = '0' 
                    pass
    
                year = movie.find('files/file/info').attrib['year']
                if year != "-1":
                    YAMJ_movie['year'] = year
                else:
                    YAMJ_movie['year'] = '1900'
    
                watched = movie.find('isWatched').text
                watchedDate = movie.find('files/file/watchedDateString').text
    
                YAMJ_movie['path'] = unquote_plus(movie.find('files/file/fileURL').text).decode('utf-8', 'replace')
            
                if watched == 'true':
                    if watchedDate == 'UNKNOWN' or watchedDate == '0':
                        watchedDate = strftime("%Y-%m-%d %H:%M:%S")
                    YAMJ_movie['playcount'] = 1
                    YAMJ_movie['date'] = watchedDate
                else:
                    YAMJ_movie['playcount'] = 0
                    YAMJ_movie['date'] = "0"
                self.YAMJ_movies.append(YAMJ_movie)

                if watched == 'true':
                    self.YAMJ_movies_seen.append(YAMJ_movie)
                else:
                    self.YAMJ_movies_unseen.append(YAMJ_movie)
        
    def get_trakt_movies(self):
        pchtrakt.logger.info(' [YAMJ] Getting movies from trakt.tv')
    
        # Collection
        url = '/sync/collection/movies'
        #url = '/users/%s/collection/movies' % (TraktUsername)
        movies = trakt_apiv2(url)
        
        for movie in movies:
            trakt_movie = {
                'title': movie['movie']['title'],
                'year': movie['movie']['year'],
            }

            if 'imdb' in movie['movie']['ids']:
                trakt_movie['imdb'] = movie['movie']['ids']['imdb']
            if 'tmdb' in movie['movie']['ids']:
                trakt_movie['tmdb'] = movie['movie']['ids']['tmdb']
            #trakt_movie['id'] = ""
    
            self.trakt_movies.append(trakt_movie)
    
        movies = ''
    
        #Clean from collection, keep commented
        #url = '/movie/unlibrary/' + TraktAPI
        #params = {'movies': trakt_movies}
        #response = trakt_api('POST', url, params)
        #url = '/movie/unseen/' + TraktAPI
        #response = trakt_api('POST', url, params)
    
        # Seen
        url = '/sync/watched/movies'
        #url = '/users/%s/watched/movies' % (TraktUsername)
        seen_movies = trakt_apiv2(url)
        
        # Add playcounts to trakt collection
        for seen in seen_movies:
            if 'imdb' in seen['movie']['ids']:
                for movie in self.trakt_movies:
                    if 'imdb' in movie:
                        if seen['movie']['ids']['imdb'] == movie['imdb']:
                            movie['plays'] = seen['plays']
            elif 'tmdb' in seen['movie']['ids']:
                for movie in self.trakt_movies:
                    if 'tmdb' in movie:
                        if seen['movie']['ids']['tmdb'] == movie['tmdb']:
                            movie['plays'] = seen['plays']
    
            elif 'title' in seen:
                for movie in self.trakt_movies:
                    if 'title' in movie:
                        if seen['title'] == movie['title']:
                            movie['plays'] = seen['plays']
    
        for movie in self.trakt_movies:
            if not 'plays' in movie:
                movie['plays'] = 0
    
        seen_movies = ''
        
    def convert_YAMJ_movie_to_trakt(self, movie, watched_at = False):
        ids = {}
        trakt_movie = {}
    
        if 'imdbnumber' in movie:
            if movie['imdbnumber'].startswith('tt'):
                ids['imdb'] = movie['imdbnumber']
            else:
                ids['tmdb'] = movie['imdbnumber']
    
        if watched_at:
            try:
                test = {"watched_at": movie['date'], "title": movie['title'], "year": movie['year'], "ids": ids}
            except:
                try:
                    test = {"watched_at": movie['date'], "title": movie['title'], "ids": ids}
                except:
                    test = {"title": movie['title'], "ids": ids}
        else:
            try:
                test = {"title": movie['title'], "year": movie['year'], "ids": ids}
            except:
                test = {"title": movie['title'], "ids": ids}
    
        trakt_movie = test
        return trakt_movie
        
    def YAMJ_movies_to_trakt(self):
        pchtrakt.logger.info(' [YAMJ] Checking for YAMJ movies that are not in trakt.tv collection')
        self.YAMJ_movies_to_trakt = []
    
        if self.trakt_movies and self.YAMJ_movies:
            imdb_ids = [x['imdb'] for x in self.trakt_movies if 'imdb' in x]
            tmdb_ids = [x['tmdb'] for x in self.trakt_movies if 'tmdb' in x]
            titles = [x['title'] for x in self.trakt_movies if 'title' in x]
    
        if self.YAMJ_movies:
            for movie in self.YAMJ_movies:
                if 'imdbnumber' in movie:
                    if movie['imdbnumber'].startswith('tt'):
                        if self.trakt_movies:
                            if self.search(imdb_ids, movie['imdbnumber']) == False:
                                self.YAMJ_movies_to_trakt.append(movie)
                                #trakt_movie = convert_YAMJ_movie_to_trakt(movie)# do we need these below?
                                #if not 'plays' in trakt_movie[0]:trakt_movie['movies']
                                #    trakt_movie[0]['plays'] = 0
                                #trakt_movies.append(trakt_movie)
                        else:
                            self.YAMJ_movies_to_trakt.append(movie)
                            #trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                            #if not 'plays' in trakt_movie[0]:
                            #    trakt_movie[0]['plays'] = 0
                            ##trakt_movies.append(trakt_movie)
                    else:
                        if self.trakt_movies:
                            if self.searchtv(tmdb_ids, movie['imdbnumber']) == False:#if not movie['imdbnumber'] in tmdb_ids:
                                self.YAMJ_movies_to_trakt.append(movie)
                                #trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                                #if not 'plays' in trakt_movie[0]:
                                #    trakt_movie[0]['plays'] = 0
                                #trakt_movies.append(trakt_movie)
                        else:
                            self.YAMJ_movies_to_trakt.append(movie)
                            #trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                            #if not 'plays' in trakt_movie[0]:
                            #    trakt_movie[0]['plays'] = 0
                            ##trakt_movies.append(trakt_movie)
                elif not movie['title'] in titles and not movie in self.YAMJ_movies_to_trakt:
                    self.YAMJ_movies_to_trakt.append(movie)
                    #trakt_movie = convert_YAMJ_movie_to_trakt(movie)
                    #if not 'plays' in trakt_movie[0]:
                    #    trakt_movie[0]['plays'] = 0
                    #trakt_movies.append(trakt_movie)

        if self.YAMJ_movies_to_trakt:
            pchtrakt.logger.info(' [YAMJ] Checking for %s movies will be added to trakt.tv collection' % len(self.YAMJ_movies_to_trakt))
            for i in range(len(self.YAMJ_movies_to_trakt)):
                #convert YAMJ movie into something trakt will understand
                self.YAMJ_movies_to_trakt[i] = self.convert_YAMJ_movie_to_trakt(self.YAMJ_movies_to_trakt[i])
    
            # Send request to add movies to trakt.tv
            url = '/sync/collection'
            params = {'movies': self.YAMJ_movies_to_trakt}

            try:
                pchtrakt.logger.info(' [YAMJ] Adding movies to trakt.tv collection...')
                response = trakt_apiv2(url, params, sync=True)
                if response['added']['movies'] != 0:
                    if len(response['not_found']['movies']) !=0:
                        pchtrakt.logger.info(' [YAMJ] Successfully added %s out of %s to your collection' % (response['added']['movies'], response['added']['movies'] + response['existing']['movies'] + len(response['not_found']['movies'])))
                        pchtrakt.logger.info(' [YAMJ] Failed to add the following %s titles to your collection' % len(response['not_found']['movies']))
                        for failed in response['not_found']['movies']:
                            pchtrakt.logger.info(' [YAMJ] Failed to add %s' % failed['movies'][0]['title'].encode('utf-8', 'replace'))
                    else:
                        pchtrakt.logger.info(' [YAMJ] Successfully added %s out of %s to your collection' % (response['added']['movies'], response['added']['movies'] + response['existing']['movies']))
                if response['existing']['movies'] != 0:
                    pchtrakt.logger.info(' [YAMJ] %s titles were found in your collection already' % response['existing']['movies'])
            except Exception, e:
                pchtrakt.logger.info(' [YAMJ] Failed to add movies to trakt.tv collection')
                pchtrakt.logger.info(e)
                
        else:
            pchtrakt.logger.info(' [YAMJ] trakt.tv movie collection is up to date')
        
    def YAMJ_movies_watched_to_trakt(self):
        pchtrakt.logger.info(' [YAMJ] Comparing YAMJ watched movies against trakt.tv')
        self.YAMJ_movies_to_trakt = []
    
        if self.trakt_movies and self.YAMJ_movies:
    
            for i in range(len(self.trakt_movies)):
                for movie in self.YAMJ_movies:
                    if movie['playcount'] != 0:
    
                        if 'imdb' in self.trakt_movies[i]:
                            if movie['imdbnumber'] == self.trakt_movies[i]['imdb']:
                                if self.trakt_movies[i]['plays'] < movie['playcount']:
                                    x_loop_must_break = False
                                    for x in self.YAMJ_movies_to_trakt:
                                        try:
                                            if movie['imdbnumber'] == x['movies'][0]['ids']['imdb']:
                                                x_loop_must_break = True
                                                break
                                        except:
                                            if movie['imdbnumber'] == x['ids']['imdb']:
                                                x_loop_must_break = True
                                                break
    
                                    if x_loop_must_break: break
                                    self.YAMJ_movies_to_trakt.append(self.convert_YAMJ_movie_to_trakt(movie, watched_at = True))
    
                        elif 'tmdb' in self.trakt_movies[i]:
                            if movie['imdbnumber'] == self.trakt_movies[i]['tmdb']:
                                if self.trakt_movies[i]['plays'] < movie['playcount']:
                                    self.YAMJ_movies_to_trakt.append(self.convert_YAMJ_movie_to_trakt(movie, watched_at = True))
    
                        elif movie['title'] == self.trakt_movies[i]['movies'][0]['title']:
                            if self.trakt_movies[i]['plays'] < movie['playcount']:
                                self.YAMJ_movies_to_trakt.append(self.convert_YAMJ_movie_to_trakt(movie, watched_at = True))
    
        if self.YAMJ_movies_to_trakt:
            pchtrakt.logger.info(' [YAMJ] %s movies playcount will be updated on trakt.tv' % len(self.YAMJ_movies_to_trakt))
            # Send request to update playcounts on trakt.tv
            url = '/sync/history'
            params = {'movies': self.YAMJ_movies_to_trakt}
            try:
                pchtrakt.logger.info(' [YAMJ] Updating watched status for movies on trakt.tv...')
                response = trakt_apiv2(url, params, sync=True)
                pchtrakt.logger.info(' [YAMJ]     Marked %s as watched out of %s movies' % (response['added']['movies'], len(self.YAMJ_movies_to_trakt)))
                if len(response['not_found']['movies']) != 0:
                    for skip in response['not_found']['movies']:
                        pchtrakt.logger.info(' [YAMJ]    could not add     -->%s' % skip['not_found']['movies'][0]['title'].encode('utf-8'))
            except Exception, e:
                pchtrakt.logger.info(' [YAMJ] Failed to update playcount for movies on trakt.tv')
                pchtrakt.logger.info(e)
        else:
            pchtrakt.logger.info(' [YAMJ] trakt.tv movie playcount is up to date')
        
    def trakt_movies_watched_to_YAMJ(self):
        pchtrakt.logger.info(' [YAMJ] Comparing trakt.tv watched movies against YAMJ')
        self.trakt_movies_seen = []
    
        if self.trakt_movies and self.YAMJ_movies_unseen:#YAMJ_movies:
            for i in range(len(self.trakt_movies)):
                for movie in self.YAMJ_movies_unseen:#YAMJ_movies:
                    if movie['playcount'] == 0 and self.trakt_movies[i]['plays'] != 0:
    
                        if 'imdb' in self.trakt_movies[i]:
                            if movie['imdbnumber'] == self.trakt_movies[i]['imdb']:
                                self.trakt_movies[i]['movieid'] = movie['imdbnumber']
                                self.trakt_movies[i]['path'] = movie['path']
    
                        elif 'tmdb' in self.trakt_movies[i]:
                            if movie['imdbnumber'] == self.trakt_movies[i]['tmdb']:
                                self.trakt_movies[i]['movieid'] = movie['tmdb']
                                self.trakt_movies[i]['path'] = movie['path']
    
                        elif movie['title'] == self.trakt_movies[i]['title']:
                            self.trakt_movies[i]['movieid'] = movie['title']
                            #trakt_movies[i]['id'] = movie['id']
                            self.trakt_movies[i]['path'] = movie['path']
    
        # Remove movies without a movieid
        if self.trakt_movies:
    
            for movie in self.trakt_movies:
                find = False
                if 'movieid' in movie:
                    for x in self.trakt_movies_seen:
                        if movie['title'] == x['title']:
                            find = True
                    if find:
                        break
                    self.trakt_movies_seen.append(movie)
    
        if self.trakt_movies_seen:
            pchtrakt.logger.info(' [YAMJ] %s movie watched files will be created' % len(self.trakt_movies_seen))
            self.WatchedYAMJ(self.trakt_movies_seen)
        else:
            pchtrakt.logger.info(' [YAMJ] No watched files ned to be created')
        self.trakt_movies_seen = []
        
    def get_YAMJ_shows(self):
        pchtrakt.logger.info(' [YAMJ] Getting TV shows from YAMJ2')
        for movie in self.tree.findall('movies'):
            try:
                if movie.get('isTV') == 'true':
                    title = movie.find('originalTitle').text.encode('utf-8')
                    if len(movie.findall('id')) >1:
                        ida = movie.findall('id')[0].text
                        idb = movie.findall('id')[1].text
                        if idb.startswith('tt'):
                            id = ida
                        else:
                            id = idb
                    else:
                        id = movie.find('id').text
                    zpath = "files/file"

                    for x in movie.findall(zpath):
                        watchedDate = x.find('watchedDateString').text
                        firstPart = x.get('firstPart')
                        lastPart = x.get('lastPart')
                        season = int(x.find('info').attrib['season'])
                        path = unquote_plus(x.find('fileURL').text).decode('utf-8', 'replace')
                        if x.find('watched').text == 'true':
                            watched = 1
                        else:
                            watched = 0
    
                        if title not in self.YAMJ_shows:
                            shows = self.YAMJ_shows[title] = {'episodes': []}  # new show dictionary
                        else:
                            shows = self.YAMJ_shows[title]
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
            except:
                continue

    def get_trakt_shows(self):
        pchtrakt.logger.info(' [YAMJ] Getting TV shows from trakt')

        # Collection
        #url = '/users/%s/collection/shows' % (TraktUsername)
        url = '/sync/collection/shows'
    
        collection_shows = trakt_apiv2(url)
        
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
            #url = '/show/episode/unseen/' + TraktAPI
            #response = trakt_api('post', url, trakt_show)
            #url = '/show/episode/unlibrary/' + TraktAPI
            #response = trakt_api('post', url, trakt_show)
            self.trakt_shows.append(trakt_show)
    
        collection_shows = ''
    
        # Seen
        url = '/sync/watched/shows'
        #url = '/users/%s/watched/shows' % (TraktUsername)
        seen_shows = trakt_apiv2(url)
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
        
    def convert_YAMJ_show_to_trakt(self, show):
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
        
    def YAMJ_shows_to_trakt(self):
        pchtrakt.logger.info(' [YAMJ] Checking for YAMJ episodes that are not in trakt.tv collection')
        self.YAMJ_shows_to_trakt = []
    
        def clean_episodes(shows):
            if shows:
                for show in shows:
                    episodes = []
                    for episode in show['episodes']:
                        episodes.append({'season': episode['season'], 'episode': episode['episode']})
                    show['episodes'] = episodes
    
            return shows

        if self.YAMJ_shows and self.trakt_shows:
    
            t_shows = copy.deepcopy(self.trakt_shows)
            t_shows = clean_episodes(t_shows)
            x_shows = copy.deepcopy(self.YAMJ_shows.values())
            x_shows = clean_episodes(x_shows)

            tvdb_ids = {}
            imdb_ids = {}
    
            for i in range(len(t_shows)):
                if 'tvdb' in t_shows[i]:
                    tvdb_ids[t_shows[i]['tvdb']] = i
                if 'imdb' in t_shows[i]:
                    imdb_ids[t_shows[i]['imdb']] = i
    
            for show in x_shows:
                if 'imdbnumber' in show:
                    if show['imdbnumber'].startswith('tt'):
                        if self.search(imdb_ids, show['imdbnumber']) == False:#if not show['imdbnumber'] in imdb_ids:
                            self.YAMJ_shows_to_trakt.append(show)
    
                            #trakt_show = convert_YAMJ_show_to_trakt(show)
                            for episode in trakt_show['episodes']:
                                episode['plays'] = 0
    
                            #trakt_shows.append(trakt_show)
    
                        else:
                            t_index = imdb_ids.get(int(show['imdbnumber']))
    
                            YAMJ_show = {
                                'title': show['title'],
                                'imdbnumber': show['imdbnumber'],
                                'episodes': []
                            }
    
                            for episode in show['episodes']:
                                if episode['episode'] == 0:
                                    continue
                                if episode not in t_shows[t_index]['episodes']:
                                    YAMJ_show['episodes'].append(episode)
    
                                    self.trakt_shows[t_index]['episodes'].append(episode)
                                    self.trakt_shows[t_index]['episodes'][-1]['plays'] = 0
    
                            if YAMJ_show['episodes']:
                                self.YAMJ_shows_to_trakt.append(YAMJ_show)
    
                    else:
                        if self.searchtv(tvdb_ids, show['imdbnumber']) == False:# if not show['imdbnumber'] in tvdb_ids:
                            self.YAMJ_shows_to_trakt.append(show)
    
                            #trakt_show = convert_YAMJ_show_to_trakt(show)
                            #for season in trakt_show['shows'][0]['seasons']:
                            #    for episode in season['episodes']:
                            #        episode['plays'] = 0
    
                            #trakt_shows.append(trakt_show)
    
                        else:
                            t_index = tvdb_ids.get(int(show['imdbnumber']))
                            #tvdb_ids.get(int(show['imdbnumber']))
    
                            YAMJ_show = {
                                'title': show['title'],
                                'imdbnumber': show['imdbnumber'],
                                'episodes': []
                            }
    
                            for episode in show['episodes']:
                                if episode['episode'] == 0:
                                    continue
                                if episode not in t_shows[t_index]['episodes']:
                                    YAMJ_show['episodes'].append(episode)
    
                                    self.trakt_shows[t_index]['episodes'].append(episode)
                                    self.trakt_shows[t_index]['episodes'][-1]['plays'] = 0
    
                            if YAMJ_show['episodes']:
                                self.YAMJ_shows_to_trakt.append(YAMJ_show)
    
            if self.YAMJ_shows_to_trakt:
                pchtrakt.logger.info(' [YAMJ] %s TV shows have episodes missing from trakt.tv collection' % len(self.YAMJ_shows_to_trakt))
    
                for i in range(len(self.YAMJ_shows_to_trakt)):
                    #convert YAMJ show into something trakt will understand
                    self.YAMJ_shows_to_trakt[i] = self.convert_YAMJ_show_to_trakt(self.YAMJ_shows_to_trakt[i])
    
                # Send request to add TV shows to trakt.tv
                url = '/sync/collection'
                #data = {'shows': [{'title': 'Mad Men', 'year': 2007, 'ids': {'trakt': 4, 'slug': 'mad-men', 'tvdb': 80337, 'imdb': 'tt0804503', 'tmdb': 1104, 'tvrage': 16356}, 'seasons': [{'number': 1, 'episodes': [{'number': 1},{'number': 2}]}]}]}
    
                for show in self.YAMJ_shows_to_trakt:
                    try:
                        #params = {'shows': [show]}
                        pchtrakt.logger.info(' [YAMJ]     -->%s' % show['shows'][0]['title'])
                        trakt = trakt_apiv2(url, show, sync=True)
                        if trakt['added']['episodes'] > 0:
                            pchtrakt.logger.info(' [YAMJ]       Added %s' % trakt['added']['episodes'])
                        if trakt['updated']['episodes'] > 0:
                            pchtrakt.logger.info(' [YAMJ]       Updated %s' % trakt['updated']['episodes'])
                        if trakt['existing']['episodes'] > 0:
                            pchtrakt.logger.info(' [YAMJ]       Modified %s' % trakt['existing']['episodes'])
                        #if trakt['not_found']['episodes']:
                    except Exception, e:
                        pchtrakt.logger.info(' [YAMJ] Failed to add %s\'s new episodes to trakt.tv collection' % show['title'])
                        pchtrakt.logger.info(e)
    
            else:
                pchtrakt.logger.info(' [YAMJ] trakt.tv TV show collection is up to date')
        
    def YAMJ_shows_watched_to_trakt(self):
        pchtrakt.logger.info(' [YAMJ] Comparing YAMJ watched TV shows against trakt.tv')
        self.YAMJ_shows_to_trakt = []
    
        if self.YAMJ_shows and self.trakt_shows:
    
            tvdb_ids = {}
            imdb_ids = {}
    
            for i in range(len(self.trakt_shows)):
                if 'tvdb' in self.trakt_shows[i]:
                    tvdb_ids[self.trakt_shows[i]['tvdb']] = i
    
                if 'imdb' in self.trakt_shows[i]:
                    imdb_ids[self.trakt_shows[i]['imdb']] = i
    
            for show in self.YAMJ_shows.values():
                if 'imdbnumber' in show:
                    if show['imdbnumber'].startswith('tt'):
                        if self.search(imdb_ids, show['imdbnumber']):#if show['imdbnumber'] in imdb_ids.keys():
                            trakt_show = self.trakt_shows[imdb_ids.get(int(show['imdbnumber']))]
    
                            trakt_show_watched = {
                                'title': show['title'],
                                'imdb': show['imdbnumber'],
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
                                self.YAMJ_shows_to_trakt.append(trakt_show_watched)
    
                    else:
                        if self.searchtv(tvdb_ids, show['imdbnumber']):#if show['imdbnumber'] in tvdb_ids.keys():
                            trakt_show = self.trakt_shows[tvdb_ids.get(int(show['imdbnumber']))]
    
                            trakt_show_watched = {
                                'title': show['title'],
                                'tvdb': show['imdbnumber'],
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
                                                        'watched_at': YAMJ_ep['date']
                                                    }
                                                )
    
                            if trakt_show_watched['episodes']:
                                self.YAMJ_shows_to_trakt.append(trakt_show_watched)
    
            if self.YAMJ_shows_to_trakt:
                pchtrakt.logger.info(' [YAMJ] %s TV shows have episodes that will be marked as watched in trakt.tv collection' % len(self.YAMJ_shows_to_trakt))
    
                for i in range(len(self.YAMJ_shows_to_trakt)):
                    #convert YAMJ show into something trakt will understand
                    self.YAMJ_shows_to_trakt[i] = self.convert_YAMJ_show_to_trakt(self.YAMJ_shows_to_trakt[i])
    
                # Send request to add TV shows to trakt.tv
                url = '/sync/history'
    
                for show in self.YAMJ_shows_to_trakt:
                    try:
                        pchtrakt.logger.info(' [YAMJ]     -->%s' % show['shows'][0]['title'])
                        trakt = trakt_apiv2(url, show, sync=True)
                        if trakt['added']['episodes'] != 0 and len(trakt['not_found']['episodes']) != 0:
                            pchtrakt.logger.info(' [YAMJ] Successfully marked  %s episodes watched out of %s' % (trakt['added']['episodes'], trakt['added']['episodes'] + trakt['not_found']['episodes']))
                        else:
                            pchtrakt.logger.info(' [YAMJ] Successfully marked  %s episodes watched out of %s' % (trakt['added']['episodes'], trakt['added']['episodes']))
                    except Exception, e:
                        pchtrakt.logger.info(' [YAMJ] Failed to mark %s\'s episodes as watched in trakt.tv collection' % show['shows'][0]['title'])
                        pchtrakt.logger.info(e)
    
            else:
                pchtrakt.logger.info(' [YAMJ] trakt.tv TV show watched status is up to date')
        
    def trakt_shows_watched_to_YAMJ(self):
        pchtrakt.logger.info(' [YAMJ] Comparing trakt.tv watched TV shows against YAMJ')
        self.trakt_shows_seen = []

        if self.YAMJ_shows and self.trakt_shows:
    
            tvdb_ids = {}
            imdb_ids = {}
    
            for i in range(len(self.trakt_shows)):
                if 'tvdb' in self.trakt_shows[i]:
                    tvdb_ids[self.trakt_shows[i]['tvdb']] = i
    
                if 'imdb' in self.trakt_shows[i]:
                    imdb_ids[self.trakt_shows[i]['imdb']] = i
    
            for show in self.YAMJ_shows.values():
                if 'imdbnumber' in show:
                    if show['imdbnumber'].startswith('tt'):
                        if self.search(imdb_ids.keys(), show['imdbnumber']):
                            trakt_show = self.trakt_shows[imdb_ids[int(show['imdbnumber'])]]
    
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
                                self.trakt_shows_seen.append(YAMJ_show)
    
                    else:
                        if self.search(tvdb_ids.keys(), int(show['imdbnumber'])):
                            trakt_show = self.trakt_shows[tvdb_ids[int(show['imdbnumber'])]]
    
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
                                self.trakt_shows_seen.append(YAMJ_show)
    
            if self.trakt_shows_seen:
                pchtrakt.logger.info(' [YAMJ] %s TV shows episodes watched status will be updated in YAMJ' % len(self.trakt_shows_seen))
                self.WatchedYAMJtv(self.trakt_shows_seen)
            else:
                pchtrakt.logger.info(' [YAMJ] Watched TV shows on YAMJ are up to date')
        
    def WatchedYAMJ(self, watched):
        pchtrakt.logger.info(' [YAMJ] Start to create watched files')
        if YamjWatched == True:
            for x in watched:
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
                        f = open(path, 'w+')
                        f.close()
                        msg = ' [Pchtrakt] I have created the file {0}'.format(path)
                        pchtrakt.logger.info(msg)
                    except BaseException as e:
                            pchtrakt.logger.info(u" [Pchtrakt] Error writing file: %s" % str(e))
                            continue
                Debug('[Pchtrakt] {0} already present'.format(path))
        
    def WatchedYAMJtv(self, watched):
            pchtrakt.logger.info(' [YAMJ] Start to create watched files')
            if YamjWatched == True:
                for x in watched:
                    for y in x['episodes']:
                        if YamJWatchedVithVideo:
                            try:
                                path = y['path'].replace('file:///', '/').encode('utf-8', 'replace')
                            except:
                                path = y['path'].replace('file:///', '/').encode('latin-1', 'replace')
                            if (path.split(".")[-1] == "DVD"):#Remember that .DVD extension
                                path = path[:-4]
                        else:
                            try:
                                path = y['path'].split('/')[::-1][0].encode('utf-8', 'replace')
                            except:
                                path = y['path'].split('/')[::-1][0].encode('latin-1', 'replace')
                            if (path.split(".")[-1] == "DVD"):
                                path = path[:-4]
                            path = '{0}{1}'.format(YamjWatchedPath, path)
                        path = '{0}.watched'.format(path)
                        if not isfile(path):
                            try:
                                f = open(path, 'w+')
                                f.close()
                                msg = ' [Pchtrakt] I have created the file {0}'.format(path)
                                pchtrakt.logger.info(msg)
                            except BaseException as e:
                                pchtrakt.logger.info(u" [Pchtrakt] Error writing file: %s" % str(e))
                                continue
                        Debug('[Pchtrakt] {0} already present'.format(path))