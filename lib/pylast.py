# -*- coding: utf-8 -*-
#
# pylast - A Python interface to Last.fm (and other API compatible social networks)
#
# Copyright 2008-2010 Amr Hassan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# http://code.google.com/p/pylast/
    
__version__ = '0.5'
__author__ = 'Amr Hassan'
__copyright__ = "Copyright (C) 2008-2010  Amr Hassan"
__license__ = "apache2"
__email__ = 'amr.hassan@gmail.com'

import hashlib
from xml.dom import minidom
import xml.dom
#import time
#import shelve
#import tempfile
#import sys
#import collections
import warnings

def _deprecation_warning(message):
    warnings.warn(message, DeprecationWarning)

from httplib import HTTPConnection
import htmlentitydefs 
from urllib import splithost as url_split_host
from urllib import quote_plus as url_quote_plus


STATUS_INVALID_SERVICE = 2
STATUS_INVALID_METHOD = 3
STATUS_AUTH_FAILED = 4
STATUS_INVALID_FORMAT = 5
STATUS_INVALID_PARAMS = 6
STATUS_INVALID_RESOURCE = 7
STATUS_TOKEN_ERROR = 8
STATUS_INVALID_SK = 9
STATUS_INVALID_API_KEY = 10
STATUS_OFFLINE = 11
STATUS_SUBSCRIBERS_ONLY = 12
STATUS_INVALID_SIGNATURE = 13
STATUS_TOKEN_UNAUTHORIZED = 14
STATUS_TOKEN_EXPIRED = 15

EVENT_ATTENDING = '0'
EVENT_MAYBE_ATTENDING = '1'
EVENT_NOT_ATTENDING = '2'

PERIOD_OVERALL = 'overall'
PERIOD_7DAYS = "7day"
PERIOD_3MONTHS = '3month'
PERIOD_6MONTHS = '6month'
PERIOD_12MONTHS = '12month'

DOMAIN_ENGLISH = 0
DOMAIN_GERMAN = 1
DOMAIN_SPANISH = 2
DOMAIN_FRENCH = 3
DOMAIN_ITALIAN = 4
DOMAIN_POLISH = 5
DOMAIN_PORTUGUESE = 6
DOMAIN_SWEDISH = 7
DOMAIN_TURKISH = 8
DOMAIN_RUSSIAN = 9
DOMAIN_JAPANESE = 10
DOMAIN_CHINESE = 11

COVER_SMALL = 0
COVER_MEDIUM = 1
COVER_LARGE = 2
COVER_EXTRA_LARGE = 3
COVER_MEGA = 4

IMAGES_ORDER_POPULARITY = "popularity"
IMAGES_ORDER_DATE = "dateadded"


USER_MALE = 'Male'
USER_FEMALE = 'Female'

SCROBBLE_SOURCE_USER = "P"
SCROBBLE_SOURCE_NON_PERSONALIZED_BROADCAST = "R"
SCROBBLE_SOURCE_PERSONALIZED_BROADCAST = "E"
SCROBBLE_SOURCE_LASTFM = "L"
SCROBBLE_SOURCE_UNKNOWN = "U"

SCROBBLE_MODE_PLAYED = ""
SCROBBLE_MODE_LOVED = "L"
SCROBBLE_MODE_BANNED = "B"
SCROBBLE_MODE_SKIPPED = "S"

class _Network(object):
    def __init__(self, name, homepage, ws_server, api_key, api_secret, session_key, submission_server, username, password_hash):
        
        self.name = name
        self.homepage = homepage    
        self.ws_server = ws_server
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_key = session_key
        self.submission_server = submission_server
        self.username = username
        self.password_hash = password_hash
        #self.domain_names = domain_names
        #self.urls = urls
        
        #self.cache_backend = None
        #self.proxy_enabled = False
        #self.proxy = None
        #self.last_call_time = 0
        
        #generate a session_key if necessary
        if (self.api_key and self.api_secret) and not self.session_key and (self.username and self.password_hash):
            sk_gen = SessionKeyGenerator(self)
            self.session_key = sk_gen.get_session_key(self.username, self.password_hash)
    
    def _get_ws_auth(self):
        return (self.api_key, self.api_secret, self.session_key)

    def update_now_playing(self, artist, title, album = None, album_artist = None, 
            duration = None, track_number = None, mbid = None, context = None):
        
        params = {"track": title, "artist": artist}
        
        if duration: params["duration"] = duration
        
        _Request(self, "track.updateNowPlaying", params).execute()
    
    def scrobble(self, artist, title, timestamp, album = None, album_artist = None, track_number = None, 
        duration = None, stream_id = None, context = None, mbid = None):
        
        return self.scrobble_many(({"artist": artist, "title": title, "timestamp": timestamp, "album": album, "album_artist": album_artist,
            "track_number": track_number, "duration": duration, "stream_id": stream_id, "context": context, "mbid": mbid},))
        
    def scrobble_many(self, tracks):
        tracks_to_scrobble = tracks[:50]
        if len(tracks) > 50:
            remaining_tracks = tracks[50:]
        else:
            remaining_tracks = None
        
        params = {}
        for i in range(len(tracks_to_scrobble)):
            
            params["artist[%d]" % i] = tracks_to_scrobble[i]["artist"]
            params["track[%d]" % i] = tracks_to_scrobble[i]["title"]
            
            additional_args = ("timestamp", "album", "album_artist", "context", "stream_id", "track_number", "mbid", "duration")
            args_map_to = {"album_artist": "albumArtist", "track_number": "trackNumber", "stream_id": "streamID"}  # so friggin lazy
            
            for arg in additional_args:
                
                if arg in tracks_to_scrobble[i] and tracks_to_scrobble[i][arg]:
                    if arg in args_map_to:
                        maps_to = args_map_to[arg]
                    else:
                        maps_to = arg
                    
                    params["%s[%d]" %(maps_to, i)] = tracks_to_scrobble[i][arg]
        
        
        _Request(self, "track.scrobble", params).execute()
        
        if remaining_tracks:
            self.scrobble_many(remaining_tracks)
    
class LastFMNetwork(_Network):
    
    def __init__(self, api_key="", api_secret="", session_key="", username="", password_hash=""):
        _Network.__init__(self,
            name = "Last.fm",
                    homepage = "http://last.fm",
                    ws_server = ("ws.audioscrobbler.com", "/2.0/"),
                    api_key = api_key,
                    api_secret = api_secret,
                    session_key = session_key,
                    submission_server = "http://post.audioscrobbler.com:80/",
                    username = username,
                    password_hash = password_hash,
                )
    
class _Request(object):
    def __init__(self, network, method_name, params = {}):
        
        self.network = network
        self.params = {}
        
        for key in params:
            self.params[key] = _unicode(params[key])
        
        (self.api_key, self.api_secret, self.session_key) = network._get_ws_auth()
        
        self.params["api_key"] = self.api_key
        self.params["method"] = method_name
        
        if self.session_key:
            self.params["sk"] = self.session_key
            self.sign_it()
    
    def sign_it(self):
        if not "api_sig" in self.params.keys():
            self.params['api_sig'] = self._get_signature()
    
    def _get_signature(self):
        keys = list(self.params.keys())
        
        keys.sort()
        
        string = ""
        
        for name in keys:
            string += name
            string += self.params[name]
        
        string += self.api_secret
        
        return md5(string)
    
    def _download_response(self):
        """Returns a response body string from the server."""
        
        # Delay the call if necessary
        #self.network._delay_call()    # enable it if you want.
        
        data = []
        for name in self.params.keys():
            data.append('='.join((name, url_quote_plus(_string(self.params[name])))))
        data = '&'.join(data)
        
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'Accept-Charset': 'utf-8',
            'User-Agent': "pylast" + '/' + __version__
            }        
        
        (HOST_NAME, HOST_SUBDIR) = self.network.ws_server
        
        conn = HTTPConnection(host=HOST_NAME)
            
        try:
            conn.request(method='POST', url=HOST_SUBDIR, body=data, headers=headers)
        except Exception as e:
            raise NetworkError(self.network, e)
        
        try:
            response_text = _unicode(conn.getresponse().read())
        except Exception as e:
            raise MalformedResponseError(self.network, e)
        
        self._check_response_for_errors(response_text)
        return response_text
        
    def execute(self, cacheable = False):
        response = self._download_response()
        
        return minidom.parseString(_string(response))
    
    def _check_response_for_errors(self, response):
        try:
            doc = minidom.parseString(_string(response))
        except Exception as e:
            raise MalformedResponseError(self.network, e)
            
        e = doc.getElementsByTagName('lfm')[0]
        
        if e.getAttribute('status') != "ok":
            e = doc.getElementsByTagName('error')[0]
            status = e.getAttribute('code')
            details = e.firstChild.data.strip()
            raise WSError(self.network, status, details)

class SessionKeyGenerator(object):
    def __init__(self, network):        
        self.network = network
        self.web_auth_tokens = {}
    
    def get_session_key(self, username, password_hash):
        params = {"username": username, "authToken": md5(username + password_hash)}
        request = _Request(self.network, "auth.getMobileSession", params)
        
        request.sign_it()
        
        doc = request.execute()
        
        return _extract(doc, "key")

#TopItem = collections.namedtuple("TopItem", ["item", "weight"])
#SimilarItem = collections.namedtuple("SimilarItem", ["item", "match"])
#LibraryItem = collections.namedtuple("LibraryItem", ["item", "playcount", "tagcount"])
#PlayedTrack = collections.namedtuple("PlayedTrack", ["track", "playback_date", "timestamp"])
#LovedTrack = collections.namedtuple("LovedTrack", ["track", "date", "timestamp"])
#ImageSizes = collections.namedtuple("ImageSizes", ["original", "large", "largesquare", "medium", "small", "extralarge"])
#Image = collections.namedtuple("Image", ["title", "url", "dateadded", "format", "owner", "sizes", "votes"])
#Shout = collections.namedtuple("Shout", ["body", "author", "date"])

def md5(text):
    h = hashlib.md5()
    h.update(_unicode(text).encode("utf-8"))
    
    return h.hexdigest()

def _unicode(text):
    if type(text) in (str,):
        return unicode(text, "utf-8")
    elif type(text) == unicode:
        return text
    else:
        return unicode(text)

def _string(text):
    if type(text) == str:
        return text
        
    if type(text) == int:
        return str(text)
        
    return text.encode("utf-8")

def _extract(node, name, index = 0):
    nodes = node.getElementsByTagName(name)
    
    if len(nodes):
        if nodes[index].firstChild:
            return _unescape_htmlentity(nodes[index].firstChild.data.strip())
    else:
        return None

def _unescape_htmlentity(string):
    
    #string = _unicode(string)  
    
    mapping = htmlentitydefs.name2codepoint
    for key in mapping:
        string = string.replace("&%s;" %key, unichr(mapping[key]))
    
    return string

def _string_output(funct):
    def r(*args):
        return _string(funct(*args))
        
    return r

class WSError(Exception):
    """Exception related to the Network web service"""
    
    def __init__(self, network, status, details):
        self.status = status
        self.details = details
        self.network = network

    @_string_output
    def __str__(self):
        return self.details
    
    def get_id(self):
        """Returns the exception ID, from one of the following:
            STATUS_INVALID_SERVICE = 2
            STATUS_INVALID_METHOD = 3
            STATUS_AUTH_FAILED = 4
            STATUS_INVALID_FORMAT = 5
            STATUS_INVALID_PARAMS = 6
            STATUS_INVALID_RESOURCE = 7
            STATUS_TOKEN_ERROR = 8
            STATUS_INVALID_SK = 9
            STATUS_INVALID_API_KEY = 10
            STATUS_OFFLINE = 11
            STATUS_SUBSCRIBERS_ONLY = 12
            STATUS_TOKEN_UNAUTHORIZED = 14
            STATUS_TOKEN_EXPIRED = 15
        """
        
        return self.status