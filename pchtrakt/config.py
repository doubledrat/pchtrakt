# -*- coding: utf-8 -*-
# Authors: Jonathan Lauwers / Frederic Haumont
# URL: http://github.com/pchtrakt/pchtrakt
#
# This file is part of pchtrakt.
#
# pchtrakt is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pchtrakt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pchtrakt.  If not, see <http://www.gnu.org/licenses/>.
import ConfigParser
import pchtrakt
import json
from os.path import isfile
from commands import getoutput
import socket
pchtrakt.online = 1
pchtrakt.CreatedFile = 0
pchtrakt.Ttime = 0
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("gmail.com",80))
    myIp = s.getsockname()[0]
    s.close()
except socket.gaierror:
    myIp = '0.0.0.0'
    pchtrakt.online = 0

config = ConfigParser.RawConfigParser()

class cacheSerie: #Errkk... need to change this
    pass

cacheSerie.dictSerie = {}
if isfile('.git/ORIG_HEAD'):
    with open('.git/ORIG_HEAD', 'r') as f:
        PchTraktVersion = f.readline().split('\n', 1)[0]
elif isfile('.git/refs/heads/dvp'):
    with open('.git/refs/heads/dvp', 'r') as f:
        PchTraktVersion = f.readline().split('\n', 1)[0]
else:
    PchTraktVersion = '4'

 
if isfile('cache.json'):
    with open('cache.json','r+') as f:
        try:
            cacheSerie.dictSerie = json.load(f)
        except:
            pass
else:
    cacheSerie.dictSerie = {}

#PchTrakt
config.read(pchtrakt.config_file)
ipPch = config.get('PCHtrakt', 'pch_ip')
AutoUpdate = float(config.get('PCHtrakt', 'autoupdate'))
if AutoUpdate > 0:
    AutoUpdate = AutoUpdate*60*60
#uptime = float(config.get('PCHtrakt', 'update_check'))*60*60
sleepTime = float(config.get('PCHtrakt', 'sleep_time'))
watched_percent = float(config.get('PCHtrakt', 'watched_percent'))
if watched_percent > 100 or watched_percent < 0:
	watched_percent = 90
log_file = config.get('PCHtrakt','log_file')
log_size = float(config.get('PCHtrakt', 'log_size'))
ignored_repertory = [x.strip() for x in config.get('PCHtrakt', 'ignored_repertory').split(',')]
ignored_keywords = [x.strip() for x in config.get('PCHtrakt', 'ignored_keywords').split(',')]
OnPCH = (ipPch in ['127.0.0.1',myIp])
use_debug = config.getboolean('PCHtrakt', 'use_debug')

#Trakt
TraktUsername = config.get('Trakt', 'login')
TraktPwd = config.get('Trakt', 'password')
TraktAPI = config.get('Trakt','api_key')
TraktScrobbleTvShow = config.getboolean('Trakt', 'enable_tvshow_scrobbling')
TraktScrobbleMovie = config.getboolean('Trakt', 'enable_movie_scrobbling')
TraktRefreshTime = config.get('Trakt', 'refresh_time')
TraktMaxPauseTime = 60*15

# Betaseries
BetaSeriesUsername = config.get('BetaSeries', 'login')
BetaSeriesPwd = config.get('BetaSeries', 'password')
BetaSeriesScrobbleTvShow = config.getboolean('BetaSeries', 'enable_tvshow_scrobbling')

#YAMJ
YamjWatchedPath = config.get('YAMJ', 'watched_path')
if not YamjWatchedPath.endswith('/'):
    YamjWatchedPath += '/'
YamJWatchedVithVideo = config.getboolean('YAMJ', 'watched_with_video')
YamjWatched = config.getboolean('YAMJ', 'watched')
YamjIgnoredCategory = [x.strip().lower() for x in config.get('YAMJ', 'ignored_category').split(',')]

#YAMJ2
YamjPath = config.get('YAMJ2', 'jukebox_path')
if not YamjPath.endswith('/'):
    YamjPath += '/'

#YAMJ3
apiurl = config.get('YAMJ3', 'API_url')

#Oversight
markOversight = config.getboolean('Oversight', 'mark_watched')
SyncCheck = float(config.get('Oversight', 'boot_time_sync'))
if SyncCheck > 0:
    SyncCheck = SyncCheck*60*60
Oversightumc = config.getboolean('Oversight', 'update_movie_collection')
Oversightusc = config.getboolean('Oversight', 'update_show_collection')
Oversightumw = config.getboolean('Oversight', 'update_movie_watched')
Oversightusw = config.getboolean('Oversight', 'update_show_watched')

#Auto Watched
RutabagaModwatched = config.getboolean('XML/HTML Update', 'rutabaga_mod_watched')
updatexmlwatched = config.getboolean('XML/HTML Update', 'update_xml_watched')
tvxmlfind = [x.strip() for x in config.get('XML/HTML Update', 'tvxml_find').split(',')]
moviexmlfind = [x.strip() for x in config.get('XML/HTML Update', 'moviexml_find').split(',')]