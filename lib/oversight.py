#!/usr/bin/env python

###################### SETTINGS ######################
OversightFile = '/share/Apps/oversight/index.db'
#OversightFile = 'X:\Apps\oversight\index.db'
trakt_username = 'USERNAME'
trakt_password = 'PASSWORD'
trakt_apikey = 'API-KEY'
#################### END SETTINGS ####################

try:
    import json
except ImportError:
    import simplejson as json
import urllib2, base64, hashlib, copy, re
import fileinput
import sys
import csv
import codecs
import os
Oversight_movies = []
Oversight_movies_seen = []
Oversight_movies_unseen = []
trakt_movies = []
Oversight_shows = {}
trakt_shows = []


def trakt_api(url, params={}):
    username = trakt_username
    password = hashlib.sha1(trakt_password).hexdigest()

    params = json.JSONEncoder().encode(params)
    request = urllib2.Request(url, params)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)

    response = urllib2.urlopen(request).read()
    response = json.JSONDecoder().decode(response)

    return response

def get_Oversight_movies():
    print '\nGetting movies from Oversight'
    #movies = Oversight.VideoLibrary.GetMovies(properties=['title', 'imdbnumber', 'year', 'playcount'])['movies']
    f=open(OversightFile, 'r')
    #'\t_F\t/share/Storage/NAS/Men In Black II (2002) -1080p.BluRay.x264 [SET Men in black -2].mp4\t_rt\t88\t_r\t5.9\t_v\tc0=h264,f0=24,h0=1080,w0=1920\t_IT\t717ac9d\t_id\t51\t_DT\t713dd5f\t_FT\t713dd5f\t_A\t382,411,407,347\t_C\tM\t_G\ta|c|s\t_R\tGB:PG\t_T\tMen in Black II\t_U\t imdb:tt0120912 themoviedb:608\t_V\tBluRay\t_W\t412,518\t_Y\t66\t_a\tthemoviedb:086055\t_d\t538\t_m\t194\t\n'    #tthemoviedb:086055\t_d
    for movie in f:
        if "_C	M" in movie:
            if "\t_T\t" in movie:
                #title = movie[movie.find("\t_T\t")+len("\t_T\t"):movie.find("\t_U")+len("\t_U")].strip("\t_U")
                title = re.search("_T\t(.*?)\t", movie).group(1)
            if "\t_Y\t" in movie:
                #year = movie[movie.find("\t_Y\t")+len("\t_Y\t"):movie.find("\t_d")+len("\t_d")].strip("\t_d")
                    try:
                        year = re.search("_Y\t(.*?)\t", movie).group(1)
                        #return exec("sed -r 's/(.*)(\t"fieldId"\t[^\t]*)(.*)/\\2\\1\\3/' "qa(file_in)" | sort > "qa(file_out)) == 0;
                        #year = re.sub(r'_Y\t(.*)/\\2\\1\\3', r'\1', movie)
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

            if '\t_U\t imdb:' in movie:
                Oversight_movie['imdbnumber'] = re.search("(tt\d{7})", movie).group(1)
                #trakt_movie['imdb_id'] = "tt" + movie[movie.find("\t_U\t imdb:")+len("\t_U\t imdb:"):movie.find(" themoviedb:")+len(" themoviedb:")].strip(" themoviedb:")
            else:
                Oversight_movie['imdbnumber'] = "0"
            if "themoviedb:" in movie:
                Oversight_movie['tmdb_id'] = re.search("themoviedb:(.*?)\t", movie).group(1)
                #trakt_movie['tmdb_id'] = movie[movie.find("\t_a\tthemoviedb:")+len("\t_a\tthemoviedb:"):movie.find("\t_d\t")+len("\t_d\t")].strip("\t_d\t")

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
                #mySubString=myString[myString.find(startString)+len(startString):myString.find(endString)+len(endString)]
    f.close()

def get_trakt_movies():
    print '\nGetting movies from trakt.tv'

    # Collection
    url = 'http://api.trakt.tv/user/library/movies/collection.json/%s/%s' % (trakt_apikey, trakt_username)
    try:
        movies = trakt_api(url)
    except Exception as e:
        quit(e)

    for movie in movies:
        trakt_movie = {
            'title': movie['title'],
            'year': movie['year'],
        }

        if 'imdb_id' in movie:
            trakt_movie['imdb_id'] = movie['imdb_id']
        if 'tmdb_id' in movie:
            trakt_movie['tmdb_id'] = movie['tmdb_id']

        trakt_movies.append(trakt_movie)

    # Seen
    url = 'http://api.trakt.tv/user/library/movies/watched.json/%s/%s' % (trakt_apikey, trakt_username)
    try:
        seen_movies = trakt_api(url)
    except Exception as e:
        quit(e)

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
    print '\nChecking for Oversight movies that are not in trakt.tv collection'
    Oversight_movies_to_trakt = []

    if trakt_movies and Oversight_movies:
        imdb_ids = [x['imdb_id'] for x in trakt_movies if 'imdb_id' in x]
        tmdb_ids = [x['tmdb_id'] for x in trakt_movies if 'tmdb_id' in x]
        titles = [x['title'] for x in trakt_movies if 'title' in x]

        if Oversight_movies:
            for movie in Oversight_movies:
                if 'imdbnumber' in movie:
                    if movie['imdbnumber'].startswith('tt'):
                        if not movie['imdbnumber'] in imdb_ids:
                            Oversight_movies_to_trakt.append(movie)

                            trakt_movie = convert_Oversight_movie_to_trakt(movie)
                            trakt_movie['plays'] = 0
                            trakt_movies.append(trakt_movie)

                    else:
                        if not movie['tmdb_id'] in tmdb_ids:
                            Oversight_movies_to_trakt.append(movie)

                            trakt_movie = convert_Oversight_movie_to_trakt(movie)
                            trakt_movie['plays'] = 0
                            trakt_movies.append(trakt_movie)

                elif not movie['title'] in titles and not movie in Oversight_movies_to_trakt:
                    Oversight_movies_to_trakt.append(movie)

                    trakt_movie = convert_Oversight_movie_to_trakt(movie)
                    trakt_movie['plays'] = 0
                    trakt_movies.append(trakt_movie)

    if Oversight_movies_to_trakt:
        print '  %s movies will be added to trakt.tv collection' % len(Oversight_movies_to_trakt)

        for i in range(len(Oversight_movies_to_trakt)):
            #convert Oversight movie into something trakt will understand
            Oversight_movies_to_trakt[i] = convert_Oversight_movie_to_trakt(Oversight_movies_to_trakt[i])

        # Send request to add movies to trakt.tv
        url = 'http://api.trakt.tv/movie/library/' + trakt_apikey
        params = {'movies': Oversight_movies_to_trakt}

        try:
            print '    Adding movies to trakt.tv collection...'
            trakt_api(url, params)
            for movie in Oversight_movies_to_trakt:
                print '    --> ' + movie['title']#.encode('utf-8', 'replace')
        except Exception, e:
            print 'Failed to add movies to trakt.tv collection'
            print e
            
    else:
        print '  trakt.tv movie collection is up to date'

def Oversight_movies_watched_to_trakt():
    print '\nComparing Oversight watched movies against trakt.tv'
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
        print '  %s movies playcount will be updated on trakt.tv' % len(Oversight_movies_to_trakt)

        # Send request to update playcounts on trakt.tv
        url = 'http://api.trakt.tv/movie/seen/' + trakt_apikey
        params = {'movies': Oversight_movies_to_trakt}

        try:
            print '    Updating playcount for movies on trakt.tv...'
            trakt_api(url, params)
            for movie in Oversight_movies_to_trakt:
                print '    --> ' + movie['title'].encode('utf-8')

        except Exception, e:
            print 'Failed to update playcount for movies on trakt.tv'
            print e
    else:
        print '  trakt.tv movie playcount is up to date'

def trakt_movies_watched_to_Oversight():
    print '\nComparing trakt.tv watched movies against Oversight'

    trakt_movies_seen = []

    if trakt_movies and Oversight_movies_unseen:#Oversight_movies:
        for i in range(len(trakt_movies)):
            for movie in Oversight_movies_unseen:#Oversight_movies:
                if movie['playcount'] == 0 and trakt_movies[i]['plays'] != 0:

                    if 'imdb_id' in trakt_movies[i]:
                        if movie['imdbnumber'] == trakt_movies[i]['imdb_id']:
                            trakt_movies[i]['movieid'] = movie['imdbnumber']

                    elif 'tmdb_id' in trakt_movies[i]:
                        if movie['tmdb_id'] == trakt_movies[i]['tmdb_id']:
                            trakt_movies[i]['movieid'] = movie['tmdb_id']

                    elif movie['title'] == trakt_movies[i]['title']:
                        trakt_movies[i]['movieid'] = movie['title']

    # Remove movies without a movieid
    if trakt_movies:

        for movie in trakt_movies:
            if 'movieid' in movie:
                trakt_movies_seen.append(movie)

    if trakt_movies_seen:
        print '  %s movies playcount will be updated on Oversight' % len(trakt_movies_seen)
        addValue = "\t_w\t1\t"
        checkvalue = "\t_w\t0\t"
        myfile_list = open(OversightFile).readlines()
        newList = []
        for line in myfile_list:
            for movie in trakt_movies_seen:
                #searchValue = movie['movieid']#"\t/share/Storage/NAS/Videos/FILMS/Absence.(2013)/Absence.(2013).mkv\t"
                #print '    --> ' + movie['title'].encode('utf-8')
                #for line in fileinput.input("X:\Apps\oversight\index.db", inplace=1):
                if movie['movieid'] in line:
                    print '    --> ' + movie['title'].encode('utf-8')
                    if checkvalue in line:
                        line = line.replace(checkvalue, addValue)
                    elif not addValue in line:
                        line = line.replace('\n', addValue+'\n')
            newList.append(line)
        outref = open(OversightFile,'w')
        outref.writelines(newList)
        outref.close()
    else:
        print '  Watched movies on Oversight are up to date'

def get_Oversight_shows():
    print '\nGetting TV shows from Oversight'
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
                if imdb_id and imdb_id.startswith('tt'):
                    shows['imdbnumber'] = imdb_id
                elif thetvdb != "0":
                    shows['imdbnumber'] = thetvdb

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
    print '\nGetting TV shows from trakt'

    # Collection
    url = 'http://api.trakt.tv/user/library/shows/collection.json/%s/%s' % (trakt_apikey, trakt_username)
    try:
        collection_shows = trakt_api(url)
    except Exception as e:
        quit(e)

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


        trakt_shows.append(trakt_show)

    # Seen
    url = 'http://api.trakt.tv/user/library/shows/watched.json/%s/%s' % (trakt_apikey, trakt_username)
    try:
        seen_shows = trakt_api(url)
    except Exception as e:
        quit(e)

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
    print '\nChecking for Oversight episodes that are not in trakt.tv collection'
    Oversight_shows_to_trakt = []

    def clean_episodes(shows):
        if shows:
            for show in shows:
                episodes = []
                for episode in show['episodes']:
                    episodes.append({'season': episode['season'], 'episode': episode['episode']})
                show['episodes'] = episodes

        return shows

    if trakt_shows and Oversight_shows:

        t_shows = copy.deepcopy(trakt_shows)
        t_shows = clean_episodes(t_shows)
        x_shows = copy.deepcopy(Oversight_shows.values())
        x_shows = clean_episodes(x_shows)

        tvdb_ids = {}
        imdb_ids = {}

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
            print '  %s TV shows have episodes missing from trakt.tv collection' % len(Oversight_shows_to_trakt)

            for i in range(len(Oversight_shows_to_trakt)):
                #convert Oversight show into something trakt will understand
                Oversight_shows_to_trakt[i] = convert_Oversight_show_to_trakt(Oversight_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = 'http://api.trakt.tv/show/episode/library/' + trakt_apikey

            for show in Oversight_shows_to_trakt:
                try:
                    print '\n    --> ' + show['title'].encode('utf-8')
                    trakt = trakt_api(url, show)
                    print '      ' + trakt['message']
                except Exception, e:
                    print 'Failed to add %s\'s new episodes to trakt.tv collection' % show['title'].encode('utf-8')
                    print e

        else:
            print '  trakt.tv TV show collection is up to date'

def Oversight_shows_watched_to_trakt():
    print '\nComparing Oversight watched TV shows against trakt.tv'
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
            print '  %s TV shows have episodes that will be marked as watched in trakt.tv collection' % len(Oversight_shows_to_trakt)

            for i in range(len(Oversight_shows_to_trakt)):
                #convert Oversight show into something trakt will understand
                Oversight_shows_to_trakt[i] = convert_Oversight_show_to_trakt(Oversight_shows_to_trakt[i])

            # Send request to add TV shows to trakt.tv
            url = 'http://api.trakt.tv/show/episode/seen/' + trakt_apikey

            for show in Oversight_shows_to_trakt:
                try:
                    print '\n    --> ' + show['title'].encode('utf-8')
                    trakt = trakt_api(url, show)
                    print '      ' + trakt['message']
                except Exception, e:
                    print 'Failed to mark %s\'s episodes as watched in trakt.tv collection' % show['title'].encode('utf-8')
                    print e

        else:
            print '  trakt.tv TV show watched status is up to date'

def trakt_shows_watched_to_Oversight():
    print '\nComparing trakt.tv watched TV shows against Oversight'
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
            print '  %s TV shows episodes watched status will be updated in Oversight' % len(trakt_shows_seen)
            data = "*("
            with open(OversightFile, 'r') as infile:
                for show_dict in trakt_shows_seen:
                    print '    --> ' + show_dict["title"].encode('utf-8')
                    for episode in show_dict['episodes']:
                        print '      Season %i - Episode %i' % (episode['season'], episode['episode'])
                        m = episode['ids']#re.search("_id\t(.*?)\t", line).group(1)#title = re.search("_T\t(.*?)\t", movie).group(1)
                        
                        if data == "*(":
                            data = data + m
                        else:
                            data = data  + "|" + m
            WatchedOversight(data)
            data = ""
        else:
            print '  Watched TV shows on Oversight are up to date'

def WatchedOversight(data):
    print "sending to Oversight"
    url = data + '"'
    data = os.system('wget -O /dev/null "http://127.0.0.1:8883/oversight/oversight.cgi?action=watch&actionids=%s' % url)
    #request = urllib2.Request("http://127.0.0.1:8883/oversight/oversight.cgi?action=watch&actionids="+data)
    #try:
    #    response = urllib2.urlopen(request).read()
    #except urllib2.URLError, e:
    #    quit(e.reason)
    data = "*("	
	
if __name__ == '__main__':
    #get_Test()
    get_Oversight_movies()
    get_trakt_movies()
    Oversight_movies_to_trakt()
    Oversight_movies_watched_to_trakt()
    trakt_movies_watched_to_Oversight()
    get_Oversight_shows()
    get_trakt_shows()
    Oversight_shows_to_trakt()
    Oversight_shows_watched_to_trakt()
    trakt_shows_watched_to_Oversight()
    print '\n Sync complete.'


