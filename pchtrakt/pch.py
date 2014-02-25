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
        oPchStatus = PchStatus()
        try:
            oXml = ElementTree.fromstring(response)
            if (oXml.tag == "theDavidBox") and (oXml.find("response/mediatype")!= None): # theDavidBox should be the root
                if oXml.find("returnValue").text == '0' and oXml.find("response/fullPath").text != "/cdrom"  and int(oXml.find("response/totalTime").text) > 90:#Added total time check to avoid scrobble while playing adverts/trailers
                    #Debug('[Pchtrakt] %s' % response)
                    oPchStatus.totalTime = int(oXml.find("response/totalTime").text)
                    oPchStatus.status = oXml.find("response/currentStatus").text
                    oPchStatus.fullPath = oXml.find("response/fullPath").text
                    oPchStatus.currentTime = int(oXml.find("response/currentTime").text)
                    lowerpath = oXml.find("response/fullPath").text.split('/')[::-1][0].lower()
                    if oXml.find("response/totalchapter")!= None:
                        oPchStatus.currentChapter = int(oXml.find("response/currentchapter").text)
                        oPchStatus.totalChapter = int(oXml.find("response/totalchapter").text)
                        self.mediaType = oXml.find("response/mediatype").text
                        if (oPchStatus.fullPath == "/iso"):#Change path if iso file
                            oPchStatus.fullPath = realpath(str(glob.glob("/isolink/*.iso")).strip('[\'\']'))
                            #oPchStatus.fullPath = unicode(newpath)[2:-2]#oPchStatus.fullPath = toUnicode(newpath)[2:-2]
                        if(self.mediaType == "BluRay"): # Blu-ray Disc are not handle like .mkv or .avi files
                            oPchStatus.fileName = oPchStatus.fullPath.split('/')[::-1][1]# add a / on last position when ISO
                            if oPchStatus.totalTime!=0:
                                oPchStatus.percent = int(math.ceil(float(oPchStatus.currentChapter) / float(oPchStatus.totalChapter) * 100.0)) # approximation because chapters are differents
                        elif (self.mediaType == "DVD") and (oPchStatus.fullPath.split(".")[-1] == "iso"):
                            oPchStatus.fileName = oPchStatus.fullPath.split('/')[::-1][0]
                            if oPchStatus.totalTime!=0:
                                oPchStatus.percent = int(math.ceil(float(oPchStatus.currentTime) / float(oPchStatus.totalTime) * 100.0))
                            if oPchStatus.totalChapter!=0:
                                oPchStatus.percent = int(math.ceil(float(oPchStatus.currentChapter) / float(oPchStatus.totalChapter) * 100.0)) # approximation because chapters are differents
                        elif (self.mediaType == "DVD") and (oPchStatus.fullPath.split(".")[-1] != "iso"):
                            if oPchStatus.fullPath[-1:] == "/":
                                oPchStatus.fullPath = oPchStatus.fullPath[:-1]+".DVD"#Add .DVD extension for later use or will just make .watched file
                                oPchStatus.fileName = oPchStatus.fullPath.split('/')[::-1][0]
                            elif oPchStatus.fullPath[-1:] != "/":
                                if lowerpath == "video_ts":
                                    oPchStatus.fullPath = oPchStatus.fullPath[:-9] + ".DVD"
                                else:
                                    oPchStatus.fullPath = oPchStatus.fullPath + ".DVD"#Add .DVD extension for later use or will just make .watched file
                                oPchStatus.fileName = oPchStatus.fullPath.split('/')[::-1][0]
                            if oPchStatus.totalTime!=0:
                                oPchStatus.percent = int(math.ceil(float(oPchStatus.currentTime) / float(oPchStatus.totalTime) * 100.0))
                        else:
                            oPchStatus.fileName = oPchStatus.fullPath.split('/')[::-1][0]
                            if oPchStatus.totalTime!=0:
                                oPchStatus.percent = int(math.ceil(float(oPchStatus.currentTime) / float(oPchStatus.totalTime) * 100.0))
            else:
                oPchStatus.status = EnumStatus.UNKNOWN
        except ElementTree.ParseError, e:
            oPchStatus.error = e
            oPchStatus.status = EnumStatus.UNKNOWN
        #if pchtrakt.lastPath != '':
        #    Debug('[Pchtrakt] full path: ' + oPchStatus.fullPath)
        return oPchStatus

    def getStatus(self,ip,timeout=10.0):
        oPchStatus = PchStatus()
        try:
            oResponse = urlopen("http://" + ip + ":8008/playback?arg0=get_current_vod_info",None,timeout)
            oPchStatus = self.parseResponse(oResponse.readlines()[0])
        except HTTPError, e:
            oPchStatus.error = e
            oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        except URLError, e:
            oPchStatus.error = e
            oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        return oPchStatus

class PchMusicRequestor:
    def parseResponse(self, response):
        oPchStatus = PchStatus()
        try:
            oXml = ElementTree.fromstring(response)
            if oXml.tag == "theDavidBox": # theDavidBox should be the root
                if oXml.find("returnValue").text == '0' and oXml.find("response/fullPath").text != "/cdrom"  and int(oXml.find("response/totalTime").text) > 30:#Added total time check to avoid scrobble while playing adverts/trailers
                    if oXml.find("response/mediatype")!= None:
                        oPchStatus.artist = oXml.find("response/artist").text
                        oPchStatus.title = oXml.find("response/title").text
                        oPchStatus.album = oXml.find("response/album").text
                        oPchStatus.totalTime = int(oXml.find("response/totalTime").text)
                        oPchStatus.status = oXml.find("response/currentStatus").text
                        oPchStatus.fullPath = oXml.find("response/fullPath").text
                        oPchStatus.currentTime = int(oXml.find("response/currentTime").text)
                        lowerpath = oXml.find("response/fullPath").text.split('/')[::-1][0].lower()
                        if oPchStatus.totalTime!=0:
                            oPchStatus.percent = int(math.ceil(float(oPchStatus.currentTime) / float(oPchStatus.totalTime) * 100.0))
                    else:
                        oPchStatus.status=EnumStatus.NOPLAY
            else:
                oPchStatus.status = EnumStatus.UNKNOWN
        except ElementTree.ParseError, e:
            oPchStatus.error = e
            oPchStatus.status = EnumStatus.UNKNOWN
        #if oPchStatus.artist == '':
        #    EnumStatus.NOPLAY
        return oPchStatus

    def getStatus(self,ip,timeout=10.0):
        oPchStatus = PchStatus()
        try:
            oResponse = urlopen("http://" + ip + ":8008/playback?arg0=get_current_aod_info",None,timeout)
            oPchStatus = self.parseResponse(oResponse.readlines()[0])
        except HTTPError, e:
            oPchStatus.error = e
            oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        except URLError, e:
            oPchStatus.error = e
            oPchStatus.status = EnumStatus.UNKNOWN
            #Debug("Fail to contact server : " + unicode(e.reason))
        return oPchStatus