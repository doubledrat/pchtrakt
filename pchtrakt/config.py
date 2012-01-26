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
config = ConfigParser.RawConfigParser()

config.read('pchtrakt.ini')
ipPch = config.get('PCHtrakt', 'pch_ip') 
username = config.get('PCHtrakt', 'trakt_login') 
pwd = config.get('PCHtrakt', 'trakt_pwd') 
sleepTime = 5 #sec
refreshTime = 15 #min

pathYAMJ='' #not used yet
debug = 'true'
