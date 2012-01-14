# -*- coding: utf-8 -*-
# Authors: Jonathan Lauwers / Frederic Haumont
# URL: http://github.com/PCHtrakt/PCHtrakt
#
# This file is part of PCHtrakt.
#
# PCHtrakt is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PCHtrakt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PCHtrakt.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from pch import *
from mediaparser import *
from urllib2 import Request, urlopen, URLError, HTTPError
from xml.etree import ElementTree 
from lib import tvdb_api 
from lib import parser
from lib import regexes
import re

class TestPchRequestor(unittest.TestCase):

	def setUp(self):
		self.oPchRequestor = PchRequestor()
		self.fakeResponseOTHER = u"<html><body>Not the theDavidBox api ;-)</body></html>"
		self.fakeResponseNOPLAY = u"<theDavidBox><returnValue>1</returnValue></theDavidBox>"
		self.fakeResponseBUFFERING = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><bufferStatus>0</bufferStatus><currentStatus>buffering</currentStatus><currentTime>2341</currentTime><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</fullPath><lastPacketTime>0</lastPacketTime><mediatype>OTHERS</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</title><totalTime>5620</totalTime></response><returnValue>0</returnValue></theDavidBox>"
		self.fakeResponsePAUSE = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><bufferStatus>0</bufferStatus><currentStatus>pause</currentStatus><currentTime>2341</currentTime><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</fullPath><lastPacketTime>0</lastPacketTime><mediatype>OTHERS</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</title><totalTime>5620</totalTime></response><returnValue>0</returnValue></theDavidBox>"
		self.fakeResponsePLAYING = u"<theDavidBox><request><arg0>get_current_vod_info</arg0><module>playback</module></request><response><bufferStatus>0</bufferStatus><currentStatus>play</currentStatus><currentTime>2341</currentTime><downloadSpeed>0</downloadSpeed><fullPath>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</fullPath><lastPacketTime>0</lastPacketTime><mediatype>OTHERS</mediatype><seekEnable>true</seekEnable><title>/opt/sybhttpd/localhost.drives/NETWORK_SHARE/download/Home.(2009).1080p.mkv</title><totalTime>5620</totalTime></response><returnValue>0</returnValue></theDavidBox>"
			
	def test_parseResponse(self):
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponseOTHER).status, EnumStatus.UNKNOWN, "Should be UNKNOWN")
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponseNOPLAY).status, EnumStatus.NOPLAY, "Should be NOPLAY")
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponseBUFFERING).status, EnumStatus.LOAD, "Should be LOAD")			
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponsePAUSE).status, EnumStatus.PAUSE, "Should be PAUSE")	
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponsePLAYING).status, EnumStatus.PLAY,"Should be PLAY")
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponsePLAYING).status, EnumStatus.PLAY,"Should be PLAY")
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponsePLAYING).totalTime, 5620,"Should be 5620 seconds")
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponsePLAYING).currentTime, 2341,"Should be 2341 seconds")
		self.assertEqual(self.oPchRequestor.parseResponse(self.fakeResponsePLAYING).fileName, "Home.(2009).1080p.mkv","Should be [Home.(2009).1080p.mkv]")
					 						 					 
	def test_getStatus(self):
		self.assertEqual(self.oPchRequestor.getStatus("1.1.1.1",0.1).status, EnumStatus.UNKNOWN, "Should be UNKNOWN (cannot connect to pch)")

class TestMediaParser(unittest.TestCase):

	def setUp(self):
		self.mediaparser = MediaParser()
		self.TVShows = [ 
					("Dexter - 6x09.mkv","Dexter",6,[9]),
					("Terra Nova - 1x11x12 - Occupation & Resistance.mkv","Terra Nova",1,[11,12]),
					("Dexter - S06E09.mkv","Dexter",6,[9]),
					("Terra Nova - S01E11-12 - Occupation & Resistance.mkv","Terra Nova",1,[11,12]),
					("Dexter.6x09.mkv","Dexter",6,[9]),
					("Terra.Nova.1x11x12.Occupation.&.Resistance.mkv","Terra Nova",1,[11,12]),
					("Breaking.Bad.S02E03.Bit.by.a.Dead.Bee.mkv","Breaking Bad",2,[3]),
					("Dexter.S06E09.mkv","Dexter",6,[9]),
					("Terra.Nova.S01E11-12.Occupation.&.Resistance.mkv","Terra Nova",1,[11,12]),
					("Terra.Nova.S1E11-12.Occupation.&.Resistance.mkv","Terra Nova",1,[11,12]),
					("Dexter.S6E9.mkv","Dexter",6,[9])
				]
		self.Movies = [
				("Home.(2009).1080p","Home",2009),
				("Home (2009) 1080p","Home",2009),
				("Home_(2009)_1080p","Home",2009)	
				]

	def test_TVShows(self):
		for (fileName,SerieName,Season,Episode) in  self.TVShows:
			self.assertEqual(self.mediaparser.parse(fileName).series_name,SerieName)
			self.assertEqual(self.mediaparser.parse(fileName).season_number,Season)
			self.assertEqual(self.mediaparser.parse(fileName).episode_numbers,Episode)
			self.assertEqual(isinstance(self.mediaparser.parse(fileName),parser.ParseResult),True)
		
class TestTVShowParsing(unittest.TestCase):
		
	def test_parseTVShow(self):
		o = parser.NameParser()
		self.assertEqual(o.parse("Breaking Bad - 2x03 - Bit by a Dead Bee.mkv").series_name,"Breaking Bad")
		self.assertEqual(o.parse("Breaking Bad - 2x03 - Bit by a Dead Bee.mkv").episode_numbers[0], 3)
		self.assertEqual(o.parse("Breaking Bad - 2x03 - Bit by a Dead Bee.mkv").series_name,"Breaking Bad")
		self.assertEqual(o.parse("Terra Nova - 1x11x12 - Occupation & Resistance.mkv").episode_numbers,[11,12])

if __name__ == '__main__':
    unittest.main()
	
	
"""def test_tvdbapi(self):
		t = tvdb_api.Tvdb()
		count = 0
		while (count < 100):
			
			episode = t['Dexter'][6][9] # get season 1, episode 3 of show
			print episode['id'] # Print episode name
			print t['Dexter']['id'] # Print seadon name
			count = count + 1
"""	