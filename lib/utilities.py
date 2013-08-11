# -*- coding: utf-8 -*-
# From https://github.com/Manromen/script.TraktUtilities

from pchtrakt.config import *
if use_debug:
    from time import time
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

username = TraktUsername
apikey = 'def6943c09e19dccb4df715bd4c9c6c74bc3b6d7'
pwdsha1 = sha1(TraktPwd).hexdigest()
headers = {"Accept": "*/*", "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",}

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
        print('True')  
        return True

# SQL string quote escaper
def xcp(s):
    return re.sub('''(['])''', r"''", str(s))

# get a connection to trakt
def getYamj3Connection(url, timeout = 60):
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
            Debug("[traktAPI] Response Code: %i" % response.getcode())
            Debug("[traktAPI] Response Time: %0.2f ms" % ((t2 - t1) * 1000))
            Debug("[traktAPI] Response Headers: %s" % str(response.info().dict))
    else:
        data = '{"status": "success", "message": "fake scrobble"}'
    return data

# get a connection to trakt
def getTraktConnection(url, args, timeout = 60):
    data = None
    #Debug("[traktAPI] urllib2.Request(%s)" % url)
    if args == None:
        req = Request(url, headers = headers)
        #req.add_header('Accept', '*/*')
    else:
        req = Request(url, args, headers = headers)
        #Debug('[traktAPI] getTraktConnection(): urllib2.urlopen()' + urlopen(req).read())
        #req.add_header('Accept', '*/*')
        #Debug('[traktAPI] getTraktConnection(): urllib2.urlopen()' + urlopen(req).read())
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
            data = response.read()
            if use_debug:
                Debug("[traktAPI] Response Code: %i" % response.getcode())
                Debug("[traktAPI] Response Time: %0.2f ms" % ((t2 - t1) * 1000))
                Debug("[traktAPI] Response Headers: %s" % str(response.info().dict))
        else:
            data = '{"status": "success", "message": "fake scrobble"}'
    return data

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
def traktJsonRequest(method, url, args = {}, passVersions=False):
    raw = None
    data = None
    jdata = {}
    url = 'https://api.trakt.tv' + url
    #retries = 3
    #if args is None:
    #    args = {}

    #if not (method == 'POST' or method == 'GET'):
    #    Debug("[traktAPI] traktJsonRequest(): Unknown method '%s'." % method)
    #    return None

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
            jdata = urlencode(args)
        # convert to json data/or maybe urlencode?
        else:
            jdata = json.dumps(args)#jdata = urlencode(args)#was jdata = json.dumps(args)

    #Debug("[traktAPI] Starting lookup.")
    
    # start retry loop (do we need retries?) remove breaks and use ?
    Debug("[traktAPI] Request URL '%s'" % (url))
    url = url.replace("%%API_KEY%%", apikey)
    url = url.replace("%%USERNAME%%", username)
    raw = getTraktConnection(url, jdata)
    if not raw:
        Debug("[traktAPI] JSON Response empty")
        return None
    data = json.loads(raw)
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
    responce = traktJsonRequest('POST', '/show/episode/seen/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'episodes':[{'episode': episode, 'season': season, 'last_played': SeenTime}]})
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
    responce = traktJsonRequest('POST', '/movie/seen/%%API_KEY%%', {'movies': [{'imdb_id': imdb_id, 'title': title, 'year': year, 'plays': '1', 'last_played': SeenTime}]})#, passVersions=True
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
    responce = traktJsonRequest('POST', '/movie/watching/%%API_KEY%%', {'imdb_id': imdb_id, 'title': title, 'year': year, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingMovieOnTrakt()'")
    return responce

# tell trakt that the user is watching an episode
def watchingEpisodeOnTrakt(tvdb_id, title, year, season, episode, duration, percent):
    responce = traktJsonRequest('POST', '/show/watching/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has stopped watching a movie
def cancelWatchingMovieOnTrakt():
    responce = traktJsonRequest('POST', '/movie/cancelwatching/%%API_KEY%%')
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingMovieOnTrakt()'")
    return responce

# tell trakt that the user has stopped an episode
def cancelWatchingEpisodeOnTrakt():
    responce = traktJsonRequest('POST', '/show/cancelwatching/%%API_KEY%%')
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has finished watching an movie
def scrobbleMovieOnTrakt(imdb_id, title, year, duration, percent):
    responce = traktJsonRequest('POST', '/movie/scrobble/%%API_KEY%%', {'imdb_id': imdb_id, 'title': title, 'year': year, 'duration': duration, 'progress': percent}, passVersions=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'scrobbleMovieOnTrakt()'")
    return responce

# tell trakt that the user has finished watching an episode
def scrobbleEpisodeOnTrakt(tvdb_id, title, year, season, episode, duration, percent):
    responce = traktJsonRequest('POST', '/show/scrobble/%%API_KEY%%', {'tvdb_id': tvdb_id, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progress': percent}, passVersions=True)
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

