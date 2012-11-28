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

import unittest
from pchtrakt.pch import *
from pchtrakt.mediaparser import *
from urllib2 import URLError, HTTPError
from xml.etree import ElementTree 
from lib.tvdb_api import tvdb_api 
from lib import parser
from lib import regexes
import re, locale, sys
import ConfigParser
from os.path import isfile
from lib.transliteration import short_encode
reload(sys)
sys.setdefaultencoding("ANSI_X3.4-1968")

TVShows = [ 
            # Filename , Serie, #Season, #Episode(s) 
             #("Dexter - 6x09.mkv","Dexter",6,[9])
            #,("The.Colbert.Report.2012.11.15.Chris.Stringer.720p.HDTV.x264-LMAO.mkv","Terra Nova",1,[11,12])
            #,("Dexter - S06E09.mkv","Dexter",6,[9])
            #,("Terra Nova - S01E11-12 - Occupation & Resistance.mkv","Terra Nova",1,[11,12])
            #,("Dexter.6x09.mkv","Dexter",6,[9])
            #,("Terra.Nova.1x11x12.Occupation.&.Resistance.mkv","Terra Nova",1,[11,12])
            #,("Breaking.Bad.S02E03.Bit.by.a.Dead.Bee.mkv","Breaking Bad",2,[3])
            #,("Dexter.S06E09.mkv","Dexter",6,[9])
            #,("Terra.Nova.S01E11-12.Occupation.&.Resistance.mkv","Terra Nova",1,[11,12])
            #("The Big Bang Theory - S02E07 - The Panty Piñata Polarization.avi")
            #,("The.Colbert.Report.2012.11.15.Chris.Stringer.720p.HDTV.x264-LMAO.mkv")
            #,("The.Daily.Show.2012.11.15.Andrew.Napolitano.720p.HDTV.x264-LMAO.mkv")
        ]

Movies = [
            # Filename [I should inform the majors that theses files are some examples taken from the net ! ;-)]
             #("Watchmen - Die Wächter.avi") 
            ("L'age de glace La dérive des continents - Bluray - DTS-HD - X264 (2012) [SET L'age de glace-4].avi")
            #,("Indiana.Jones.and.the.Temple.of.Doom.[1984].HDTV.1080p.mkv")
            #,("Inglourious.Basterds.(2009).BDRip.1080p.mkv")        
            #,("James.Bond.04.Thunderball.1965.Bluray.1080p.DTSMA.x264.dxva-FraMeSToR.mkv")
            #,("James.Bond.08.Live.and.Let.Die.1973.Bluray.1080p.DTSMA.x264.dxva-FraMeSToR.mkv")
            #,("Underworld.Rise.Of.The.Lycans.(2008).BDRip.1080p.[SET Underworld].mkv")
            #,("unstoppable.2010.bluray.1080p.dts.x264-chd.mkv")
            #,("UP.(2009).BDRip.720p.mkv") # epic !
            #,("127.Hours.2010.1080p.BluRay.x264-SECTOR7.mkv")
            #,("13.Assassins.2010.LIMITED.1080p.BluRay.x264-WEST.mkv")
            #,("2012.(2009).BDRip.1080p.mkv")
            #,("300.(2006).BDRip.1080p.mkv")
            #,("Big.Fish.2003.1080p.BluRay.DTS.x264-DON")
            #,("inf-fast5-1080p[ID tt1596343].mkv") # Who are looking this shit ?
            ,("Le.Fabuleux.Destin.d'Amélie.Poulain.2001.1080p.BluRay.DTS.x264-CtrlHD.mkv")
            #,("avchd-paul.2011.extended.1080p.x264.mkv")
            #,("twiz-unknown-1080p.mkv")
	    #,("Hostel.Part.III.2011.Dvdrip.avi")
        ]                
                
class TestPchRequestor(unittest.TestCase):

    def setUp(self):
        self.oPchRequestor = PchRequestor()
        self.fakeResponseOTHER = u"<html><body>Not the theDavidBox api ;-)</body></html>"
        self.fakeResponseNOPLAY = u"<theDavidBox><returnValue>1</returnValue></theDavidBox>"
        self.fakeResponseBUFFERING = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><bufferStatus>0</bufferStatus><currentStatus>buffering</currentStatus><currentTime>2341</currentTime><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</fullPath><lastPacketTime>0</lastPacketTime><mediatype>OTHERS</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</title><totalTime>5620</totalTime></response><returnValue>0</returnValue></theDavidBox>"
        self.fakeResponsePAUSE = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><bufferStatus>0</bufferStatus><currentStatus>pause</currentStatus><currentTime>2341</currentTime><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</fullPath><lastPacketTime>0</lastPacketTime><mediatype>OTHERS</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</title><totalTime>5620</totalTime></response><returnValue>0</returnValue></theDavidBox>"
        self.fakeResponsePLAYING = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><bufferStatus>0</bufferStatus><currentStatus>play</currentStatus><currentTime>2341</currentTime><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</fullPath><lastPacketTime>0</lastPacketTime><mediatype>OTHERS</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</title><totalTime>5620</totalTime></response><returnValue>0</returnValue></theDavidBox>"
        self.fakeResponsePLAYING_BD = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><currentStatus>play</currentStatus><currentTime>82</currentTime><currentchapter>135</currentchapter><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/SATA_DISK_B4/Video/Films/Home/</fullPath><lastPacketTime>0</lastPacketTime><mediatype>BD</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/SATA_DISK_B4/Video/Films/Home/</title><totalTime>99</totalTime><totalchapter>909</totalchapter></response><returnValue>0</returnValue></theDavidBox>"
            
    def test_getStatus(self):
        self.assertEqual(self.oPchRequestor.getStatus("1.1.1.1",0.1).status, EnumStatus.UNKNOWN, "Should be UNKNOWN (cannot connect to pch)")
        
    def test_getStatusRemote(self):
        oStatus = self.oPchRequestor.getStatus("83.134.24.223",0.1)
        if(oStatus.status != EnumStatus.UNKNOWN):
            print (u"Remote PCH is [" + oStatus.status + "]")
            print (u"    FileName=" + oStatus.fileName)
            print (u"    CurrentTime=" + str(oStatus.currentTime) + "s")
            print (u"    TotalTime=" + str(oStatus.totalTime) + "s")
            print (u"    PercentTime=" + str(oStatus.percent) + "%")

class TestMediaParser(unittest.TestCase):

    def setUp(self):
        self.mediaparser = MediaParser()

    def test_TVShows(self):
        for (fileName) in TVShows:#,season,episode_numbers) in TVShows:
            fileName = unescape(fileName).decode('Latin-1', 'replace')#.encode(pchtrakt.SYS_ENCODING, 'replace')
            self.assertEqual(isinstance(self.mediaparser.parse(fileName),MediaParserResultTVShow),True)
            #self.assertEqual(self.mediaparser.parse(fileName).name,serie_name)
            #self.assertEqual(self.mediaparser.parse(fileName).season_number,season)
            #self.assertEqual(self.mediaparser.parse(fileName).episode_numbers,episode_numbers)
            print ("Title=" + str(self.mediaparser.parse(fileName).name) + " Season=" + str(self.mediaparser.parse(fileName).season_number) + " Episode=" + str(self.mediaparser.parse(fileName).episode_numbers))
            path = '/share/Apps/pchtrakt/'
            path = path + '{0}.watched'.format(short_encode(fileName))
            if not isfile(path):
				f = open(path, 'w')
				f.close()
				print 'I have created the file {0}'.format(path)
			
    def test_Movies(self):
        for (fileName) in Movies:
            fileName1 = unescape(fileName).decode('Latin-1', 'replace')#.encode('ANSI_X3.4-1968', 'replace')
            print short_encode(fileName1)
            self.assertEqual(isinstance(self.mediaparser.parse(fileName1),MediaParserResultMovie),True)
            print ("Title=" + str(self.mediaparser.parse(fileName1).name) +" (" + str(self.mediaparser.parse(fileName1).year) + ") - IMDB=" + str(self.mediaparser.parse(fileName1).id))
            path = '/share/Apps/pchtrakt/'
            path = path + '{0}.watched'.format(fileName1.encode('UTF-8', 'replace'))
            if not isfile(path):
				f = open(path, 'w')
				f.close()
				print 'I have created the file {0}'.format(path)

if __name__ == '__main__':
	pchtrakt.SYS_ENCODING = None
	try:
		locale.setlocale(locale.LC_ALL, "")
		pchtrakt.SYS_ENCODING = locale.getpreferredencoding()
		print "system encoding is: " + pchtrakt.SYS_ENCODING
	except (locale.Error, IOError):
		pass
	unittest.main()
