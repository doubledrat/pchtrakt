#!/usr/bin/env python
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

# pchtrakt - Connect your PCH 200 Series to trakt.tv :)
# pchtrakt uses some pyhton lib :
#    - tvdb_api (https://github.com/dbr/tvdb_api)
#    - nbrhttpconnection (another project)
#     - some classes from Sick Beard (http://sickbeard.com/)

import sys
import getopt
#import pchtrakt
#This needed?
#pchtrakt.SYS_ENCODING = None
#reload(sys)
#sys.setdefaultencoding("ANSI_X3.4-1968")
#pchtrakt.SYS_ENCODING = 'ANSI_X3.4-1968'
if not hasattr(sys, "setdefaultencoding"):
	reload(sys)

import os
import json
from pchtrakt.pch import *
from pchtrakt.scrobble import *
from pchtrakt.config import *
from pchtrakt.movieparser import MovieResultNotFound
from pchtrakt import mediaparser as mp
from time import sleep, time
from lib.tvdb_api import tvdb_api
from lib.tvdb_api import tvdb_exceptions
from lib.utilities import Debug, checkSettings, OversightSync
from xml.etree import ElementTree
#from urllib2 import URLError, HTTPError#Request, urlopen, URLError, HTTPError
#from datetime import date
#from subprocess import Popen, PIPE
#from lib import parser
#from lib import regexes
#from urllib import quote
#from lib.utilities import Debug
try:
    # Python 3.0 +
    from http.client import HTTPException, BadStatusLine
except ImportError:
    # Python 2.7 and earlier
    from httplib import HTTPException, BadStatusLine

class PchTraktException(Exception):
    pass

tvdb = tvdb_api.Tvdb()
pchtrakt.oPchRequestor = PchRequestor()
pchtrakt.mediaparser = mp.MediaParser()


class media():
    def __str__(self):
        if isinstance(self.parsedInfo, mp.MediaParserResultTVShow):
            msg = 'TV Show : {0} - Season:{1} - Episode:{2} ' \
                    '- {3}% - {4} - TvDB: {5}'.format(
                    self.parsedInfo.name,
                    self.parsedInfo.season_number,
                    self.parsedInfo.episode_numbers,
                    self.oStatus.percent,
                    self.oStatus.status,
                    self.parsedInfo.id)
        else:
            msg = 'Movie : {0} - Year : {1} - ' \
                    '{2}% - IMDB: {3}'.format(
                    self.parsedInfo.name,
                    self.parsedInfo.year,
                    self.oStatus.percent,
                    self.parsedInfo.id)
        return msg

myMedia = media()

def printHelp():
    print('Usage {0} <options>'.format('pythpn pchtrak.py'))
    print('Options:')
    print('    -h,--help    :    display this message')
    print('    -d,--daemon  :    launches pchtrakt in the background')

def getParams():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "dht:",
                                   ['daemon', 'help'])
    except getopt.GetoptError:
        print("Available options: -d, --daemon")
        sys.exit()

    for o, a in opts:
        # Run as a daemon
        if o in ('-d', '--daemon'):
            if sys.platform == 'win32':
                print('Daemonize not supported under Windows, ' \
                      'starting normally')
            else:
                pchtrakt.DAEMON = True
                #pchtrakt.debug = False

        if o in ('-h', '--help'):
            printHelp()
            sys.exit()

        if o in ('-t'):
            try:
                checkSettings()
            except AuthenticationTraktError:
                pass
            finally:
                sys.exit()

def checkUpdate(when):
    #pchtrakt.logger.info('update checker')
    hash = ""
    for row in os.popen('git ls-remote').read().split('\n'):
        if row.find('refs/heads/dvp') != -1:
            hash = row.split()[0]
            break
    if hash == PchTraktVersion or hash == "":
        if when == "first":
            pchtrakt.logger.info(' [Pchtrakt] Starting Pchtrakt version = ' + PchTraktVersion[-4:]  + ' Millers Mods (Running latest ' + pchtrakt.chip + ' version)')
    else:
        if AutoUpdate >= 0:
            if when == "first":
                pchtrakt.logger.info(' [Pchtrakt] Starting Pchtrakt version = ' + PchTraktVersion[-4:]  + ' Millers Mods (Running latest ' + pchtrakt.chip + ' version)')
                pchtrakt.logger.info(' [Pchtrakt] A new version is online. Starting update')
            else:
                pchtrakt.logger.info(' [Pchtrakt] Checking for new version.... ' + PchTraktVersion[-4:]  + ' Millers Mods (Running latest ' + pchtrakt.chip + ' version)')
                pchtrakt.logger.info(' [Pchtrakt] A new version is online. Starting update')
            os.system("./daemon.sh update")
        elif AutoUpdate < 0:
            if when == "first":
                pchtrakt.logger.info(' [Pchtrakt] Starting Pchtrakt version = ' + PchTraktVersion[-4:] + ' Millers Mods (' + pchtrakt.chip + ' version)')
                pchtrakt.logger.info(' [Pchtrakt] A new version is online. For manual install, download from https://github.com/cptjhmiller/pchtrakt/archive/dvp.zip')

def daemonize():
    """
    Fork off as a daemon
    """

    # Make a non-session-leader child process
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError as e:
        raise RuntimeError("1st fork failed: %s [%d]" %
                   (e.strerror, e.errno))

    os.setsid()  # @UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError as e:
        raise RuntimeError("2st fork failed: %s [%d]" % (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

def doWork():
    myMedia.ScrobResult = 0
    #pchtrakt.StopTrying = 0
    myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
    #if pchtrakt.lastPath != myMedia.oStatus.fullPath:# and myMedia.oStatus.status == EnumStatus.PLAY:
    if pchtrakt.lastPath != myMedia.oStatus.fullPath and pchtrakt.StopTrying == 0:
        if isIgnored(myMedia) == True:
            while myMedia.oStatus.status == EnumStatus.PLAY:
                sleep(sleepTime)
                myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
                pchtrakt.StopTrying = 1
        myMedia.parsedInfo = None
        with open('cache.json','w') as f:
            json.dump(pchtrakt.dictSerie, f, separators=(',',':'), indent=4)
    #if pchtrakt.online and (myMedia.parsedInfo.id == '0' or myMedia.parsedInfo.year == '0'):
    #    myMedia.parsedInfo = None
    #    with open('cache.json','w') as f:
    #        json.dump(pchtrakt.dictSerie, f, separators=(',',':'), indent=4)
    if YamjWatched == True and not pchtrakt.watched and myMedia.oStatus.percent > watched_percent and pchtrakt.CreatedFile == 0:
        #try:
            watchedFileCreation(myMedia)
        #except BaseException as e:
            #Debug('::: {0} :::'.format(pchtrakt.lastPath))
            #Debug('::: {0} :::'.format(e))
            #pchtrakt.logger.error(e)
    if not pchtrakt.StopTrying:
        if myMedia.oStatus.status not in [EnumStatus.NOPLAY,
                                          EnumStatus.UNKNOWN,
                                          EnumStatus.PAUSE]:
            pchtrakt.allowedPauseTime = TraktMaxPauseTime
            if myMedia.oStatus.status != EnumStatus.LOAD:
                if myMedia.parsedInfo == None:# and pchtrakt.online:
                    #if pchtrakt.lastPath != '':
                    Debug('[Pchtrakt] full path: ' + myMedia.oStatus.fullPath)
                    msg = u' [Pchtrakt] File: {0}'.format(myMedia.oStatus.fileName)
                    pchtrakt.logger.info(msg)
                    myMedia.parsedInfo = pchtrakt.mediaparser.parse(
                                            myMedia.oStatus.fileName)
                    pchtrakt.Ttime = myMedia.oStatus.totalTime
                videoStatusHandle(myMedia)
                    #else:
                    #if pchtrakt.Ttime == 0:
        elif (myMedia.oStatus.status == EnumStatus.PAUSE
            and pchtrakt.allowedPauseTime > 0):
            pchtrakt.allowedPauseTime -= sleepTime
            #Debug(myMedia.__str__())
        else:
            if pchtrakt.lastPath != '':# and myMedia.oStatus.status == EnumStatus.NOPLAY:
                if myMedia.oStatus.status == EnumStatus.NOPLAY:#if pchtrakt.watched:# and myMedia.oStatus.status != EnumStatus.PAUSE:
                    pchtrakt.logger.info(' [Pchtrakt] video Stopped')
                    videoStopped()
                    #elif myMedia.oStatus.percent > watched_percent and (TraktScrobbleTvShow or TraktScrobbleMovie):
                    #    pchtrakt.logger.info(' [Pchtrakt] saving off-line scrobble')
                    #    scrobbleMissed() 
                if pchtrakt.allowedPauseTime <= 0 and not pchtrakt.watched:
                    pchtrakt.logger.info(' [Pchtrakt] It seems you paused ' \
                                         'the video for more than {0} minutes: ' \
                                         'I say to trakt you stopped watching ' \
                                         'your video'.format(TraktMaxPauseTime/60))
                    #pchtrakt.logger.info(' [Pchtrakt] video Stopped')
                    #videoStopped()
                pchtrakt.watched = 0
                pchtrakt.lastPath = ''
                pchtrakt.lastName = ''
                pchtrakt.isMovie = 0
                pchtrakt.isTvShow = 0
                pchtrakt.Check = 0
                pchtrakt.Ttime = 0
                pchtrakt.CreatedFile = 0

def stopTrying():
    try:
        pchtrakt.StopTrying = 1
        pchtrakt.lastPath = myMedia.oStatus.fullPath
        pchtrakt.lastName = myMedia.oStatus.fileName
        sleep(sleepTime)
    except Exception as e:
        pass

def startWait():
	pchtrakt.StopTrying = 1#pchtrakt.StopTrying = 0
	while myMedia.oStatus.status != EnumStatus.NOPLAY:
		sleep(sleepTime)
		myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
		#pchtrakt.StopTrying = 1
		if YamjWatched == True and not pchtrakt.watched and myMedia.oStatus.percent > watched_percent and pchtrakt.CreatedFile == 0:
			try:
				watchedFileCreation(myMedia)
			except BaseException as e:
				pchtrakt.logger.error(e)
	videoStopped()

def starttvdbWait():
    if pchtrakt.online:
        while urllib.urlopen("http://thetvdb.com").getcode() != 200:
            pchtrakt.StopTrying = 1#pchtrakt.StopTrying = 0
            while myMedia.oStatus.status != EnumStatus.NOPLAY:
                sleep(sleepTime)
                myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
                #pchtrakt.StopTrying = 1
                if YamjWatched == True and not pchtrakt.watched and myMedia.oStatus.percent > watched_percent and pchtrakt.CreatedFile == 0:
                    try:
                        watchedFileCreation(myMedia)
                    except BaseException as e:
                        pchtrakt.logger.error(e)
            #videoStopped()

if __name__ == '__main__':
    getParams()
    if pchtrakt.DAEMON:
        daemonize()
    if os.path.isfile('cache.json'):
        with open('cache.json','r+') as f:
            pchtrakt.dictSerie = json.load(f)
    else:
        pchtrakt.dictSerie = {}

    #Get model
    pchtrakt.chip = os.popen('gbus_read_uint32 0x0002fee8').read()[-5:-1]
    if pchtrakt.chip == "8911":
        pchtrakt.chip = "A400 series"
    elif pchtrakt.chip == "8647":
        pchtrakt.chip = "300 series"
    elif pchtrakt.chip == "8643":
        pchtrakt.chip = "200 series"
    elif pchtrakt.chip == "8635":
        pchtrakt.chip = "100 series"#do we want/need this?
    else:
        pchtrakt.chip = ""
    #Check version and update if needed
    #gitproc = Popen(['git', 'ls-remote'], stdout = PIPE)
    #(stdout, stderr) = gitproc.communicate()
    if pchtrakt.online:
        checkUpdate('first')
        OversightSync()
        if os.path.isfile('missed.scrobbles'):
            pchtrakt.logger.info(' [Pchtrakt] Found missed scrobbles, updating trakt.tv')
            with open('missed.scrobbles','r+') as f:
                pchtrakt.missed = json.load(f)
            new_list = {}
            for xname in pchtrakt.missed:
                pchtrakt.logger.info(u' [Pchtrakt] marking %s watched on trakt.tv' % xname.split('/')[::-1][0])
                myMedia.parsedInfo = pchtrakt.mediaparser.parse(xname.split('/')[::-1][0])
                myMedia.idxEpisode = 0
                myMedia.ScrobResult = 0
                myMedia.oStatus = PchStatus()
                myMedia.oStatus.totalTime = pchtrakt.missed[xname]['Totaltime']
                myMedia.oStatus.percent = 100
                if isinstance(myMedia.parsedInfo,mp.MediaParserResultTVShow):
                    pchtrakt.watched = showIsSeen(myMedia, pchtrakt.missed[xname]['Totallength'])
                elif isinstance(myMedia.parsedInfo,mp.MediaParserResultMovie):
                    pchtrakt.watched = movieIsSeen(myMedia, pchtrakt.missed[xname]['Totallength'])#movieIsEnding(myMedia)
                if not pchtrakt.watched:
                    pchtrakt.logger.info(u' [traktAPI]  %s was NOT marked as watched on trakt.tv' % xname.split('/')[::-1][0])
                    new_list[xname]={"Totaltime": int(pchtrakt.missed[xname]['Totaltime']), "Totallength": int(pchtrakt.missed[xname]['Totallength'])}
            if new_list != {}:
                with open('missed.scrobbles','w') as f:
                    json.dump(new_list, f, separators=(',',':'), indent=4)
            else:
                os.remove('missed.scrobbles')
    else:
        pchtrakt.logger.info(' [Pchtrakt] Pchtrakt START version = ' + PchTraktVersion[-4:] + ' Millers Mods (' + pchtrakt.chip + ' version)')
        pchtrakt.logger.info(' [Pchtrakt] No internet - can not check for updates')
        pchtrakt.logger.info(' [Pchtrakt] .watched files will be created but no xml updating or track.tv scrobbles will happen.')
        pchtrakt.logger.info(' [Pchtrakt] track.tv scrobbles will be saved and processed when next on-line.')
    pchtrakt.logger.info(' [Pchtrakt] Waiting for a file to start.....')
    pchtrakt.Started = time()
    pchtrakt.Started2 = pchtrakt.Started
    
#Main routine
while not pchtrakt.stop:
    try:
        doWork()
        sleep(sleepTime)
        if myMedia.oStatus.status == EnumStatus.NOPLAY:
            if float(time()) > float(pchtrakt.Started+AutoUpdate) and AutoUpdate > 0:
                checkUpdate('no')
                pchtrakt.Started = time()
            if float(time()) > float(pchtrakt.Started2+SyncCheck) and SyncCheck > 0:
                OversightSync()
                pchtrakt.Started2 = time()

    #Error routine
    except BadStatusLine, e:
        msg = ('[BadStatusLine] ' \
        '{0} '.format(pchtrakt.lastPath))
        pchtrakt.logger.warning(msg)
        sleep(15)
        os.system("./daemon.sh restart")
    except HTTPError as e:
        if hasattr(e, 'code'):  # error 401 or 503, possibly others
            # read the error document, strip newlines, this will make an html page 1 line
            error_data = e.read().replace("\n", "").replace("\r", "")
            if e.code == 401:  # authentication problem
                stopTrying()
                pchtrakt.logger.error('[traktAPI] Login or password incorrect')
                sleep(sleepTime)
                startWait()
            elif e.code == 503:  # server busy problem
                stopTrying()
                pchtrakt.logger.error('[traktAPI] trakt.tv server is busy')
                sleep(sleepTime)
                startWait()
            elif e.code == 404:  # Not found on trakt.tv
                stopTrying()
                pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
                sleep(sleepTime)
                startWait()
            elif e.code == 403:  # Forbidden on trakt.tv
                stopTrying()
                pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
                sleep(sleepTime)
                startWait()
            elif e.code == 502:  # Bad Gateway
                stopTrying()
                pchtrakt.logger.error('[traktAPI] Bad Gateway')
                sleep(sleepTime)
                startWait()
        stopTrying()
        msg = ('[The TvDB] Show not found ' \
        '{0} '.format(pchtrakt.lastPath))
        pchtrakt.logger.warning(msg)
        startWait()
    except tvdb_exceptions.tvdb_shownotfound as e:
        stopTrying()
        msg = ('[The TvDB] Show not found ' \
        '{0} '.format(pchtrakt.lastPath))
        pchtrakt.logger.warning(msg)
        startWait()
    except tvdb_exceptions.tvdb_error, e:
        stopTrying()
        pchtrakt.logger.error('[The TvDB] Site apears to be down:::')
        starttvdbWait()
    except MovieResultNotFound as e:
        stopTrying()
        msg = '[Pchtrakt] Unable to find match for file - {0}'.format(e.file_name)
        pchtrakt.logger.warning(msg)
        startWait()
    except PchTraktException as e:
        stopTrying()
        msg = '[Pchtrakt] PchTraktException - {0}'.format(e)
        pchtrakt.logger.error(msg)
        sleep(sleepTime)
    except BetaSerieAuthenticationException as e:
        pchtrakt.logger.error(e)
    except IOError, e:
         if hasattr(e, 'reason'):
             if e.reason == 'Unauthorized':
                stopTrying()
                pchtrakt.logger.error('[traktAPI] Login or password incorrect')
                #sleep(sleepTime)
                startWait()
             else:
                pchtrakt.logger.error('Reason: %s ' % (e.reason))
         elif hasattr(e, 'code'):
             pchtrakt.logger.error('Error code: %s' % (e.code))
    except ValueError as e:
        pchtrakt.logger.error('[traktAPI] Problem with trakt.tv site  - {0}'.format(e))
        #pchtrakt.stop = 1
        #videoStopped()
    except AttributeError as e:
        if pchtrakt.online:
            Debug('[Pchtrakt] ID not found will retry in 60 seconds  - {0}'.format(e))
            while not (hasattr(myMedia.parsedInfo, 'id')) and myMedia.oStatus.status == EnumStatus.PLAY:
                sleep(15)
                myMedia.parsedInfo = pchtrakt.mediaparser.parse(myMedia.oStatus.fileName)
                myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
                Debug('[Pchtrakt] ID not found will retry in 60 seconds')
            videoStatusHandleMovie(myMedia)
        #else:
        #    Debug('[Pchtrakt] not on-line bla bla bla')
    except Exception as e:
    #    if hasattr(e, 'code'):  # error 401 or 503, possibly others
    #        # read the error document, strip newlines, this will make an html page 1 line
    #        error_data = e.read().replace("\n", "").replace("\r", "")
    #        if e.code == 401:  # authentication problem
    #            stopTrying()
    #            pchtrakt.logger.error('[traktAPI] Login or password incorrect')
    #            sleep(sleepTime)
    #            startWait()
    #        elif e.code == 503:  # server busy problem
    #            stopTrying()
    #            pchtrakt.logger.error('[traktAPI] trakt.tv server is busy')
    #            sleep(sleepTime)
    #            startWait()
    #        elif e.code == 404:  # Not found on trakt.tv
    #            stopTrying()
    #            pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
    #            sleep(sleepTime)
    #            startWait()
    #        elif e.code == 403:  # Forbidden on trakt.tv
    #            stopTrying()
    #            pchtrakt.logger.error('[traktAPI] Item not found on trakt.tv')
    #            sleep(sleepTime)
    #            startWait()
    #        elif e.code == 502:  # Bad Gateway
    #            stopTrying()
    #            pchtrakt.logger.error('[traktAPI] Bad Gateway')
    #            sleep(sleepTime)
    #            startWait()
        if hasattr(e, 'message'):  # error 401 or 503, possibly others
            if e.message == "global name 'NotFoundError' is not defined":
                msg = '[traktAPI] Unable to find match for file - {0}'.format(pchtrakt.lastName)
                pchtrakt.logger.warning(msg)
                startWait()
                #pass
            #elif e.message == "global name 'MaxScrobbleError' is not defined":
            #    pchtrakt.logger.warning('[traktAPI] ScrobbleError to many scrobbles in an hour')
            #    startWait()
            #    #passMaxScrobbleError
            else:
                stopTrying()
                #Debug(u'::: {0} :::'.format(pchtrakt.lastPath))
                #Debug(u'::: {0} :::'.format(e))
                pchtrakt.logger.exception('This should never happend! Please contact me with the error if you read this')
                pchtrakt.logger.exception(pchtrakt.lastPath)
                pchtrakt.logger.exception(e.message)
                startWait()
        else:
            stopTrying()
            #Debug(u'::: {0} :::'.format(pchtrakt.lastPath))
            #Debug(u'::: {0} :::'.format(e))
            pchtrakt.logger.exception('This should never happend! Please contact me with the error if you read this')
            pchtrakt.logger.exception(pchtrakt.lastPath)
            pchtrakt.logger.exception(e)
            startWait()
            #pass
pchtrakt.logger.info(' [Pchtrakt]  STOP')
#fix Bad Gateway error, where it stays in loop