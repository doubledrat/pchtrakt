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
#'(.cp.(?P<id>tt[0-9{7}]+).)'
from lib import regexes
from unicodedata import normalize
import re
import mediaparser

regexes_movies = [
                    ("imdb", "^(?P<movie_title>.+?)[. _-]+[\(\[]{0,1}(?P<year>[0-9]{4})[\)\]]{0,1}.*(?P<imdbid>tt\d{7}).*")
                    ,
                    ("movie_only", "^(?P<movie_title>.+?)[. _-]+(?P<imdbid>tt\d{7}).*")
                    ,
                    ("movie_year", "^(?P<movie_title>.+?)[. _-]+[\(\[]{0,1}(?P<year>[0-9]{4})[\)\]]{0,1}")
                    ,
                    ("movie_only", "^(?P<movie_title>.+$)")
                ]

# black words in file names
blackwords = [
              # video tags
              'DVDRip', 'HD-DVD', 'HDDVD', 'HDDVDRip', 'BluRay', 'Blu-ray', 'BDRip', 'BRRip',
              'HDRip', 'DVD', 'DVDivX', 'HDTV', 'DVB', 'DVBRip', 'PDTV', 'WEBRip', 'DVDSCR',
              'Screener', 'VHS', 'VIDEO_TS', 'DVDR',
              # language
              '720p', '720', '1080p', '1080',
              # video codec
              'XviD', 'DivX', 'x264', 'h264', 'Rv10',
              # file extentions - find a better way
              'mkv', 'mp4', 'avi', 'mpeg', 'mpg', 'm4v', 'mov',
              # audio codec
              'DTS-HD', 'AC3', 'DTS', 'He-AAC', 'AAC-He', 'AAC', '5.1',
              # ripper teams
              'ESiR', 'WAF', 'SEPTiC', '[XCT]', 'iNT', 'PUKKA', 'CHD', 'ViTE', 'TLF',
              'DEiTY', 'FLAiTE', 'MDX', 'GM4F', 'DVL', 'SVD', 'iLUMiNADOS',
              'UnSeeN', 'aXXo', 'KLAXXON', 'NoTV', 'ZeaL', 'LOL'
              ]
				
class MovieParser():
    def __init__(self):
        self.compiled_regexes = []
        self._compile_regexes()

    def _compile_regexes(self):
        for (cur_pattern_name, cur_pattern) in regexes_movies:
            try:
                cur_regex = re.compile(cur_pattern, re.VERBOSE | re.IGNORECASE)
            except re.error, errormsg:
                Debug(u"WARNING: Invalid movie_pattern, %s. %s" % (errormsg, cur_regex.pattern))
            else:
                self.compiled_regexes.append((cur_pattern_name, cur_regex))

    def parse(self,file_name):
        oResult = None
        fullpath = file_name
        file_name = self.clean_movie_name(file_name.split('/')[::-1][0])
        for (name,regex) in self.compiled_regexes:
            try:
                match = regex.match(file_name)
                if not match:
                    continue

                tmp_movie_title = ""
                tmp_year = None
                tmp_imdbid = None
                named_groups = match.groupdict().keys()

                if 'movie_title' in named_groups:
                    tmp_movie_title = match.group('movie_title')
                if 'year' in named_groups:
                    tmp_year = match.group('year')
                if 'imdbid' in named_groups:
                    tmp_imdbid = match.group('imdbid')

                #Debug(name + "=" + str(regex.search(file_name).groupdict()) + '       [' + file_name + ']')
                return mediaparser.MediaParserResultMovie(fullpath,file_name,tmp_movie_title,tmp_year,tmp_imdbid)
                break
            except:
                raise MovieResultNotFound(file_name)

    def clean_movie_name(self, movie_name):
        """Cleans up name by removing any . and _
        characters, along with any trailing hyphens.

        Is basically equivalent to replacing all _ and . with a
        space, but handles decimal numbers in string, for example:

        >>> cleanRegexedSeriesName("an_example_1.0_test")
        'an example 1.0 test'

        Stolen from dbr's tvnamer
        """
        reps = {'0000':'0,000'}
        for i, j in reps.iteritems():
            movie_name = movie_name.replace(i, j)

        # remove everything inside parenthesis
        #movie_name = re.sub('[([{].*?[)\]}]', '', movie_name)
        # replace dots, underscores and dashes with spaces
        try:
            movie_name = normalize('NFKD', movie_name).encode('ascii', 'ignore').replace(' ', '-').lower()
        except:
            pass
        movie_name = re.sub(r'[^a-zA-Z0-9]', ' ', movie_name)
        stitle = movie_name.split()
        movie_name = []
        # loop on name
        # keep only words which are not black words
        for word in stitle:
            is_not_a_blackword = True
            for blackword in blackwords:
                if word.lower() == blackword.lower():
                    is_not_a_blackword = False
                    break
            if is_not_a_blackword:
                movie_name.append(word)
            else:
                break
        #check for IMDB
        reg=re.compile('tt\d{7}')
        for word in stitle:
            if reg.match(word):
                movie_name.append(word)
        movie_name = ' '.join(movie_name)
        return movie_name.strip()

class MovieResultNotFound(Exception):
    def __init__(self, file_name):
        self.file_name = file_name