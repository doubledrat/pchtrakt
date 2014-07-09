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

from xml.etree import ElementTree
from string import split
from urllib2 import Request, urlopen, URLError, HTTPError
from lib.utilities import Debug
from os.path import realpath
import math
import glob
import pchtrakt
#import repr

class EnumStatus:
    NOPLAY='noplay'
    PLAY='play'
    PAUSE='pause'
    LOAD='buffering'
    STOP='stop'
    UNKNOWN='unknown'

class PchStatus:
    def __init__(self):
        self.status=EnumStatus.NOPLAY
        self.fullPath = ""
        self.lastPath = ""
        self.fileName = ""
        self.currentTime = 0
        self.totalTime = 0
        self.percent = 0
        self.mediaType = ""
        self.currentChapter = 0 # For Blu-ray Disc only
        self.totalChapter = 0 # For Blu-ray Disc only
        self.artist = ""
        self.title = ""
        self.album = ""
        self.error = None

class PchRequestor:
    def parseResponse(self, response):
        self.oPchStatus = PchStatus()
        try:
            oXml = ElementTree.fromstring(response)
            if oXml.tag == "theDavidBox": # theDavidBox should be the root
                if oXml.find("returnValue").text == '0' and oXml.find("response/fullPath").text != "/cdrom"  and int(oXml.find("response/totalTime").text) > 90:#Added total time check to avoid scrobble while playing adverts/trailers
                    self.oPchStatus.totalTime = int(oXml.find("response/totalTime").text)
                    self.oPchStatus.status = oXml.find("response/currentStatus").text
                    self.oPchStatus.fullPath = oXml.find("response/fullPath").text
                    self.oPchStatus.currentTime = int(oXml.find("response/currentTime").text)
                    lowerpath = oXml.find("response/fullPath").text.split('/')[::-1][0].lower()
                    if oXml.find("response/totalchapter")!= None:
                        self.oPchStatus.currentChapter = int(oXml.find("response/currentchapter").text)
                        self.oPchStatus.totalChapter = int(oXml.find("response/totalchapter").text)
                    if oXml.find("response/mediatype")!= None:
                        self.mediaType = oXml.find("response/mediatype").text
                        if (self.oPchStatus.fullPath == "/iso"):#Change path if iso file
                            self.oPchStatus.fullPath = realpath(str(glob.glob("/isolink/*.[Ii][Ss][Oo]")).strip('[\'\']'))
                        if(self.mediaType == "BluRay"): # Blu-ray Disc are not handle like .mkv or .avi files
                            self.oPchStatus.fileName = self.oPchStatus.fullPath.split('/')[::-1][1]# add a / on last position when ISO
                            if oPchStatus.totalTime!=0:
                                self.oPchStatus.percent = int(math.ceil(float(self.oPchStatus.currentChapter) / float(self.oPchStatus.totalChapter) * 100.0)) # approximation because chapters are differents
                        elif (self.mediaType == "DVD") and (self.oPchStatus.fullPath.split(".")[-1].lower() == "iso"):
                            self.oPchStatus.fileName = self.oPchStatus.fullPath.split('/')[::-1][0]
                            if self.oPchStatus.totalTime!=0:
                                self.oPchStatus.percent = int(math.ceil(float(self.oPchStatus.currentTime) / float(self.oPchStatus.totalTime) * 100.0))
                            if self.oPchStatus.totalChapter!=0:
                                self.oPchStatus.percent = int(math.ceil(float(self.oPchStatus.currentChapter) / float(self.oPchStatus.totalChapter) * 100.0)) # approximation because chapters are differents
                        elif (self.mediaType == "DVD") and (self.oPchStatus.fullPath.split(".")[-1].lower() != "iso"):
                            if self.oPchStatus.fullPath[-1:] == "/":
                                self.oPchStatus.fullPath = self.oPchStatus.fullPath[:-1]+".DVD"#Add .DVD extension for later use or will just make .watched file
                                self.oPchStatus.fileName = self.oPchStatus.fullPath.split('/')[::-1][0]
                            elif self.oPchStatus.fullPath[-1:] != "/":
                                if lowerpath == "video_ts":
                                    self.oPchStatus.fullPath = self.oPchStatus.fullPath[:-9] + ".DVD"
                                else:
                                    self.oPchStatus.fullPath = self.oPchStatus.fullPath + ".DVD"#Add .DVD extension for later use or will just make .watched file
                                self.oPchStatus.fileName = self.oPchStatus.fullPath.split('/')[::-1][0]
                            if self.oPchStatus.totalTime!=0:
                                self.oPchStatus.percent = int(math.ceil(float(self.oPchStatus.currentTime) / float(self.oPchStatus.totalTime) * 100.0))
                        else:
                            self.oPchStatus.fileName = self.oPchStatus.fullPath.split('/')[::-1][0]
                            if self.oPchStatus.totalTime!=0:
                                self.oPchStatus.percent = int(math.ceil(float(self.oPchStatus.currentTime) / float(self.oPchStatus.totalTime) * 100.0))
                    else:
                        self.oPchStatus.status=EnumStatus.NOPLAY
            else:
                self.oPchStatus.status = EnumStatus.UNKNOWN
        except ElementTree.ParseError, e:
            self.oPchStatus.error = e
            self.oPchStatus.status = EnumStatus.UNKNOWN
        #if pchtrakt.lastPath != '':
        #    Debug('[Pchtrakt] full path: ' + oPchStatus.fullPath)
        return self.oPchStatus

    def getStatus(self,ip,timeout=10):
        self.oPchStatus = PchStatus()
        try:
            self.oResponse = urlopen("http://" + ip + ":8008/playback?arg0=get_current_vod_info", None, timeout)
            self.oPchStatus = self.parseResponse(self.oResponse.readlines()[0])
        except HTTPError, e:
            self.oPchStatus.error = e
            self.oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        except URLError, e:
            self.oPchStatus.error = e
            self.oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        except Exception as e:
            stopTrying()
            pchtrakt.logger.exception('This should never happend! Please contact me with the error if you read this')
            pchtrakt.logger.exception(pchtrakt.lastPath)
            pchtrakt.logger.exception(e.message)
            #pass
        return self.oPchStatus

class PchMusicRequestor:
    def parseResponse(self, response):
        self.oPchStatus = PchStatus()
        try:
            oXml = ElementTree.fromstring(response)
            if oXml.tag == "theDavidBox": # theDavidBox should be the root
                if oXml.find("returnValue").text == '0' and oXml.find("response/fullPath").text != "/cdrom"  and int(oXml.find("response/totalTime").text) > 30:#Added total time check to avoid scrobble while playing adverts/trailers
                    if oXml.find("response/mediatype")!= None:
                        self.oPchStatus.artist = oXml.find("response/artist").text
                        self.oPchStatus.title = oXml.find("response/title").text
                        self.oPchStatus.album = oXml.find("response/album").text
                        self.oPchStatus.totalTime = int(oXml.find("response/totalTime").text)
                        self.oPchStatus.status = oXml.find("response/currentStatus").text
                        self.oPchStatus.fullPath = oXml.find("response/fullPath").text
                        self.oPchStatus.currentTime = int(oXml.find("response/currentTime").text)
                        lowerpath = oXml.find("response/fullPath").text.split('/')[::-1][0].lower()
                        if self.oPchStatus.totalTime!=0:
                            self.oPchStatus.percent = int(math.ceil(float(self.oPchStatus.currentTime) / float(self.oPchStatus.totalTime) * 100.0))
                    else:
                        self.oPchStatus.status=EnumStatus.NOPLAY
            else:
                self.oPchStatus.status = EnumStatus.UNKNOWN
        except ElementTree.ParseError, e:
            self.oPchStatus.error = e
            self.oPchStatus.status = EnumStatus.UNKNOWN
        #if self.oPchStatus.artist == '':
        #    EnumStatus.NOPLAY
        return self.oPchStatus

    def getStatus(self,ip,timeout=10.0):
        self.oPchStatus = PchStatus()
        try:
            self.oResponse = urlopen("http://" + ip + ":8008/playback?arg0=get_current_aod_info",None,timeout)
            self.oPchStatus = self.parseResponse(self.oResponse.readlines()[0])
        except HTTPError, e:
            self.oPchStatus.error = e
            self.oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        except URLError, e:
            self.oPchStatus.error = e
            self.oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        except Exception as e:
            stopTrying()
            #Debug(u'::: {0} :::'.format(pchtrakt.lastPath))
            #Debug(u'::: {0} :::'.format(e))
            pchtrakt.logger.exception('This should never happend! Please contact me with the error if you read this')
            pchtrakt.logger.exception(pchtrakt.lastPath)
            pchtrakt.logger.exception(e.message)
            startWait()
        return self.oPchStatus