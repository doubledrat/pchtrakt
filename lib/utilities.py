# -*- coding: utf-8 -*-

from pchtrakt.config import *
from time import sleep, time
from lib.trakt import TraktAPI
from lib.trakt.exceptions import traktException
from urllib import quote_plus, urlencode
import pchtrakt
import re
import os
import json
import xml.etree.cElementTree as etree
import ssl

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

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
    ctime = time()
    pchtrakt.missed = {}
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
            pchtrakt.logger.debug(myMsg)

def checkSettings(daemon=False):
    data = getTokenviaPin()
    return data

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
                data = {'status': 'success', 'message': 'shows per hour limit reached - added item to off-line list'}
                return data
            if data['error'] == 'movies per hour limit reached':
                data = {'status': 'success', 'message': 'movies per hour limit reached - added item to off-line list'}
                return data
            return None
    return data

###############################
##### Scrobbling to trakt #####
###############################

# get token using pin
def getTokenviaPin():
    trakt_api = TraktAPI()
    responce = trakt_api.validateAccount()
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingMovieOnTrakt()'")
    return responce

# tell trakt that the user is watching a movie
def watchingMovieOnTrakt(imdb_id, percent):
    trakt_api = TraktAPI()
    responce = trakt_api.traktRequest('scrobble/start', {"movie": {"ids": {"imdb": imdb_id}}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingMovieOnTrakt()'")
    return responce

# tell trakt that the user is watching a episode
def watchingEpisodeOnTrakt(tvdb_id, season, episode, percent):
    trakt_api = TraktAPI()
    #responce = trakt_api.traktRequest('scrobble/start', {"show": {"title": title, "year": year}, "episode": {"season": season, "number": episode}, "ids": {"tvdb": tvdb_id,}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    responce = trakt_api.traktRequest('scrobble/start', {"show": {"ids": {"tvdb": tvdb_id}}, "episode": {"season": season, "number": episode }, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("[traktAPI] Error in request from 'watchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has stopped watching a movie
def cancelWatchingMovieOnTrakt(myMedia):
    trakt_api = TraktAPI()
    responce = trakt_api.traktRequest('scrobble/stop', {"movie": {"ids": {"imdb": myMedia.parsedInfoOld.id}}, "progress": myMedia.parsedInfoOld.percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingMovieOnTrakt()'")
    return responce

# tell trakt that the user has stopped a episode
def cancelWatchingEpisodeOnTrakt(myMedia):
    trakt_api = TraktAPI()
    #responce = trakt_api.traktRequest('scrobble/stop', {"show": {"title": myMedia.parsedInfoOld.name, "year": myMedia.parsedInfoOld.year}, "episode": {"season": myMedia.parsedInfoOld.season_number, "number": str(myMedia.parsedInfoOld.episode_numbers).replace('[','').replace(']','')}, "ids": {"tvdb": myMedia.parsedInfoOld.id,}, "progress": myMedia.parsedInfoOld.percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    responce = trakt_api.traktRequest('scrobble/stop', {"show": {"ids": {"tvdb": myMedia.parsedInfoOld.id}}, "episode": {"season": myMedia.parsedInfoOld.season_number, "number": str(myMedia.parsedInfoOld.episode_numbers).replace('[','').replace(']','')}, "progress": myMedia.parsedInfoOld.percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("[traktAPI] Error in request from 'cancelWatchingEpisodeOnTrakt()'")
    return responce

# tell trakt that the user has finished watching a movie
def scrobbleMovieOnTrakt(imdb_id, percent):
    trakt_api = TraktAPI()
    responce = trakt_api.traktRequest('scrobble/start', {"movie": {"ids": {"imdb": imdb_id}}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("[traktAPI] Error in request from 'scrobbleMovieOnTrakt()'")
    return responce

# tell trakt that the user has finished watching a episode
def scrobbleEpisodeOnTrakt(tvdb_id, season, episode, percent):
    trakt_api = TraktAPI()
    #responce = trakt_api.traktRequest('scrobble/start', {"show": {"title": title, "year": year}, "episode": {"season": season, "number": episode}, "ids": {"tvdb": tvdb_id}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    responce = trakt_api.traktRequest('scrobble/start', {"show": {"ids": {"tvdb": tvdb_id}}, "episode": {"season": season, "number": episode }, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("[traktAPI] Error in request from 'scrobbleEpisodeOnTrakt()'")
    return responce

# set episodes seen on trakt
def setEpisodesSeenOnTrakt(tvdb_id, title, year, season, episode, percent, SeenTime):
    trakt_api = TraktAPI()
    responce = trakt_api.traktRequest('scrobble/stop', {"show": {"title": title, "year": year}, "episode": {"season": season, "number": episode}, "ids": {"tvdb": tvdb_id}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("Error in request from 'setEpisodeSeenOnTrakt()'")
    return responce

# set movies seen on trakt
def setMoviesSeenOnTrakt(imdb_id, title, year, percent, SeenTime):
    trakt_api = TraktAPI()
    responce = trakt_api.traktRequest('scrobble/stop', {"movie": {"title": title, "year": year, "ids": {"imdb": imdb_id}}, "progress": percent, "app_version": "1.0", "app_date": "2014-09-22"}, method='POST')
    if responce == None:
        Debug("Error in request from 'setMoviesSeenOnTrakt()'")
    return responce


###############################
########## YAMJ3 API ##########
###############################

# get genres of file from YAMJ3 API
def getgenres(yamjname):
    responce = yamj3JsonRequest('api/genre?filename={0}'.format(quote_plus(yamjname)))
    if responce == None:
        Debug("[YAMJ3API] Error in request from 'scrobbleEpisodeOnTrakt()'")
    return responce

# get genres of file from YAMJ3 API
def watched(pchtrakt):
    yamjname = pchtrakt.lastName.encode('utf-8', 'replace')
    responce = yamj3JsonRequest('api/watched?filename={0}?watched={1}'.format(quote_plus(yamjname), str(pchtrakt.lastPercent)))
    if responce == None:
        Debug("[YAMJ3API] Error in request from 'scrobbleEpisodeOnTrakt()'")
    return responce