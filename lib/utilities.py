# -*- coding: utf-8 -*-
# From https://github.com/Manromen/script.TraktUtilities

from pchtrakt.config import *
from time import sleep, time
from httplib import HTTPException, BadStatusLine
from sha import new as sha1

import urllib2 
from urllib2 import HTTPError 

from urllib import quote_plus, urlencode
import base64
import copy
import pchtrakt
import re
import os
import json
import xml.etree.cElementTree as etree

import ssl


#trakt_api=Trakt_API(TraktUsername,TraktPwd, token)
TEMP_ERRORS=[500, 502, 503, 504, 520, 521, 522, 524]

V2_API_KEY='a18b7486b102e402e5a627fa3b56b5d54697ec49c05ab9375c85891a48766030'
BASE_URL='https://api.trakt.tv'

#apikey='def6943c09e19dccb4df715bd4c9c6c74bc3b6d7'
pwdsha1=sha1(TraktPwd).hexdigest()
# headers = {'Accept-Encoding': 'gzip, deflate, compress', 'Accept': '*/*', 'User-Agent': 'CPython/2.7.6 Unknown/Unknown'}

  
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth", "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

def getIDFromNFO(type, file):
    if not isfile(file):
        pchtrakt.logger.info(" [Pchtrakt] Show dir doesn't exist, can't load NFO")
        raise exceptions.NoNFOException("The show dir doesn't exist, no NFO could be loaded")


    pchtrakt.logger.info(' [Pchtrakt] Loading info from NFO')
    id = ''
    try:
        
        if type == 'TV':
            xmlFileObj = open (file, 'r')
            showXML = etree.ElementTree(file=xmlFileObj)
            xmlFileObj.close()
            name = None
            for find in showXML.iter('id'):
                if find.attrib == {'moviedb': 'tvdb'}:
                    name = find.text
                    break
            if name != None:
                id = name
            elif showXML.findtext('id'):
                id = showXML.findtext('id')
            else:
                return ''
        if type != 'TV':
            xmlFileObj = open (file, 'r')
            txt = xmlFileObj.read()
            id = re.findall('(tt\d{4,7})', txt)[0]
            xmlFileObj.close()
        return id
    except Exception, e:
        Debug('[traktAPI] id:%s' % id)
        return id


def toUnicode(original, *args):
    try:
        if isinstance(original, unicode):
            return original
        else:
            try:
                return unicode(original, *args)
            except:
                try:
                    return ek(original, *args)
                except:
                    raise
    except:
        log.error('Unable to decode value "%s..." : %s ', (repr(original)[:20], traceback.format_exc()))
        ascii_text = str(original).encode('string_escape')
        return toUnicode(ascii_text)

def getExt(filename):
    return os.path.splitext(filename)[1][1:]

def getNfo(files):
    extensions = {
        'nfo': ['nfo', 'txt', 'tag']
    }
    return set(filter(lambda s: getExt(s.lower()) in extensions['nfo'], files))

def ss(original, *args):


    u_original = toUnicode(original, *args)
    try:
        return u_original.encode('UTF-8')
    except Exception, e:
        pchtrakt.logger.warning('[PchTrakt] Failed ss encoding char, force UTF8: %s', e)
        return u_original.encode('UTF-8')


def sp(path, *args):
    if not path or len(path) == 0:
        return path
    if os.path.sep == '/' and '\\' in path:
        path = '/' + path.replace(':', '').replace('\\', '/')
    path = os.path.normpath(ss(path, *args))
    if path != os.path.sep:
        path = path.rstrip(os.path.sep)
    if len(path) == 2 and path[1] == ':':
        path = path + os.path.sep
    path = re.sub('^//', '/', path)
    return path


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

def Debug(myMsg):
    if use_debug:
        try:
            pchtrakt.logger.debug(myMsg)
        except UnicodeEncodeError:
            myMsg = myMsg.encode("utf-8", "replace")
            pchtrakt.logger.info(myMsg)

def checkSettings(daemon=False):
    if TraktUsername != 'your_trakt_login':
        data = traktJsonRequest('POST', '/account/test/%%API_KEY%%')#data = traktJsonRequest('POST', '/account/test/%%API_KEY%%', silent=True)
        if data == None:  # Incorrect trakt login details
            return False
        #print('True')  
        return True

def xcp(s):
    # SQL string quote escaper
    return re.sub('''(['])''', r"''", str(s))

def getYamj3Connection(url, timeout = 60):
    # get a connection to YAMJ3
    data = None
    args = None
    req = Request(url, headers = headers)
    if use_debug:
        t1 = time()
    response = urlopen(req, timeout = timeout)
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


def login():
    if pchtrakt.token == '':
        Debug("[traktAPI] Getting auth token")
        url = '/auth/login' 
        if not TraktUsername or not TraktPwd:
            Debug("[traktAPI] Check username and password")
            return '' 
        data = {'login': TraktUsername, 'password': TraktPwd} 
        response = trakt_apiv2(url, data, cached=False)
        Debug("[traktAPI] Token recieved '%s'" % (response['token'])) 
        return response['token']
    else:
        return pchtrakt.token 


def trakt_apiv2(url, data = None, params=None, auth=True, cache_limit=.25, cached=True, sync=False):
    json_data=json.dumps(data) if data else None
    headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': 2}
    url = '%s%s' % (BASE_URL, url) 
    if params: url = url + '?' + urlencode(params) 

    if data:
        if 'password' in data:
            data['password']="xXx"
    Debug("[traktAPI] Request URL %s, header: %s, data: %s" % (url, headers, data))
    login_retry=False
    while True:
            try:
                if url.endswith('login'):
                    if auth: headers.update({'trakt-user-login': TraktUsername})
                else:
                    if auth: headers.update({'trakt-user-login': TraktUsername, 'trakt-user-token': pchtrakt.token})
                request = urllib2.Request(url, data=json_data, headers=headers )
                result=urllib2.urlopen(request, timeout=60).read()
                break
            except urllib2.URLError as e:
                if isinstance(e, urllib2.HTTPError):
                    if e.code == 401:
                        #if login_retry or url.endswith('login'):
                            pchtrakt.token = login()
                            login_retry=True
                            continue
                    if e.code == 504:
                        if login_retry or url.endswith('login'):
                            raise
                        else:
                            pchtrakt.token = login()
                            login_retry=True

    response=json.loads(result)

    if 'status' in response and response['status']=='failure':
        if 'message' in response: raise TraktError(response['message'])
        if 'error' in response: raise TraktError(response['error'])
        else: raise TraktError()
    else:
        return response


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
    base64string = base64.encodestring('%s:%s' % (TraktUsername, pwdsha1)).replace('\n', '')
    request.add_header("Accept", "*/*")
    request.add_header("User-Agent", "CPython/2.7.5 Unknown/Unknown")
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
                retries += 1
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
                retries += 1
                if e.code == 401:  # authentication problem
                    #stopTrying()
                    #pchtrakt.logger.error('[traktAPI] Login or password incorrect')
                    response = {'status': 'success', 'message': 'PROBLEM', 'PROBLEM': 'Login or password incorrect'}
                    return response
                    pchtrakt.startWait('Login or password incorrect')
                elif e.code == 503:  # server busy problem
                    #stopTrying()
                    pchtrakt.logger.error('[traktAPI] trakt.tv server is busy, retrying in 60 seconds')
                    sleep(60)
                    continue
                elif e.code == 404:  # Not found on trakt.tv
                    if sync:
                        response = {'status': 'success', 'message': 'Item not found on trakt.tv'}
                        return response
                    else:
                        pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
                        startWait('Item not found on trakt.tv')
                elif e.code == 403:  # Forbidden on trakt.tv
                    #stopTrying()
                    pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
                    startWait('Item not found on trakt.tv')
                elif e.code == 502:  # Bad Gateway
                    #stopTrying()
                    pchtrakt.logger.warning('[traktAPI] Bad Gateway, retrying in 60 seconds')
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
            if response['error'][-7:] == 'already':
                #scrobblealready
                response = {'status': 'success', 'message': 'Item has just been scrobbled earlier'}
                return response
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
                #startWait(response['error'])
                response = {'status': 'success', 'message': 'PROBLEM', 'PROBLEM': 'episode must be > 0'}
                return response
                #exit
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
    responce = trakt_apiv2('/scrobble/start', {"movie": {"title": title, "year": year, "ids": {"imdb": imdb_id}}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, auth=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingMovieOnTrakt()'")
    return responce

# tell trakt that the user is watching an episode
def watchingEpisodeOnTrakt(tvdb_id, title, year, season, episode, duration, percent):
    responce = trakt_apiv2('/scrobble/start', {"show": {"title": title, "year": year}, "episode": {"season": season, "number": episode}, "ids": {"tvdb": tvdb_id,}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, auth=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has stopped watching a movie
def cancelWatchingMovieOnTrakt(myMedia):
    responce = trakt_apiv2('/scrobble/stop', {"movie": {"title": title, "year": year, "ids": {"imdb": imdb_id}}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, auth=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingMovieOnTrakt()'")
    return responcemy

# tell trakt that the user has stopped an episode
def cancelWatchingEpisodeOnTrakt(myMedia):
    responce = trakt_apiv2('/scrobble/stop', {"show": {"title": myMedia.parsedInfoOld.name, "year": myMedia.parsedInfoOld.year}, "episode": {"season": myMedia.parsedInfoOld.season_number, "number": str(myMedia.parsedInfoOld.episode_numbers).replace('[','').replace(']','')}, "ids": {"tvdb": myMedia.parsedInfoOld.id,}, "progress": myMedia.parsedInfoOld.percent, "app_version": "1.0", "app_date": "2014-09-22"}, auth=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has finished watching an movie
def scrobbleMovieOnTrakt(imdb_id, title, year, duration, percent):
    responce = trakt_apiv2('/scrobble/start', {"movie": {"title": title, "year": year, "ids": {"imdb": imdb_id}}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, auth=True)
    #Debug('[traktAPI] ' + str(responce))
    if responce == None:
        Debug("[traktAPI] Error in request from 'scrobbleMovieOnTrakt()'")
    return responce

# tell trakt that the user has finished watching an episode
def scrobbleEpisodeOnTrakt(tvdb_id, title, year, season, episode, duration, percent):
    responce = trakt_apiv2('/scrobble/start', {"show": {"title": title, "year": year}, "episode": {"season": season, "number": episode}, "ids": {"tvdb": tvdb_id,}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, auth=True)
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