from os.path import isfile, getsize
import ConfigParser
import logging
import logging.handlers
#import os
#nbr = 0
#idOK = 0

StopTrying = 0
stop = 0
lastPath = ''
currentTime = 0
watched = 0
DAEMON = 0
config_file = 'pchtrakt.ini'
debug = False
isTvShow = 0
isMovie = 0
allowedPauseTime = 15
config = ConfigParser.RawConfigParser()

def loadOldConfig():
    config.read(config_file)

def newConfig():
    if not isfile(config_file):
        config.add_section('PCHtrakt')
    if not config.has_option('PCHtrakt','pch_ip'):
        config.set('PCHtrakt', 'pch_ip', '127.0.0.1')
    if not config.has_option('PCHtrakt','autoupdate'):
        config.set('PCHtrakt', 'autoupdate', '-1')
    if not config.has_option('PCHtrakt','sleep_time'):
        config.set('PCHtrakt', 'sleep_time', '5')
    if not config.has_option('PCHtrakt','watched_percent'):
        config.set('PCHtrakt', 'watched_percent', '90')
    if not config.has_option('PCHtrakt','log_file'):
        config.set('PCHtrakt', 'log_file', 'pchtrakt.log')
    if not config.has_option('PCHtrakt','log_size'):
        config.set('PCHtrakt', 'log_size', '0')
    if not config.has_option('PCHtrakt','ignored_repertory'):
        config.set('PCHtrakt', 'ignored_repertory', '')
    if not config.has_option('PCHtrakt','ignored_keywords'):
        config.set('PCHtrakt', 'ignored_keywords', '')
    if not config.has_option('PCHtrakt','parse_nfo'):
        config.set('PCHtrakt', 'parse_nfo', 'False')
    if not config.has_option('PCHtrakt','use_debug'):
        config.set('PCHtrakt', 'use_debug', 'False')

    if not config.has_section('Trakt'):
        config.add_section('Trakt')
    if not config.has_option('Trakt','enable_movie_scrobbling'):
        config.set('Trakt', 'enable_movie_scrobbling', True)
    if not config.has_option('Trakt','enable_tvshow_scrobbling'):
        config.set('Trakt', 'enable_tvshow_scrobbling', True)
    if not config.has_option('Trakt','login'):
        config.set('Trakt', 'login', 'your_trakt_login')
    if not config.has_option('Trakt','password'):
        config.set('Trakt', 'password', 'your_password')
    if not config.has_option('Trakt','api_key'):
        config.set('Trakt', 'api_key', 'your_api_key')
    if not config.has_option('Trakt','refresh_time'):
        config.set('Trakt', 'refresh_time', '15')

    if not config.has_section('BetaSeries'):
        config.add_section('BetaSeries')
    if not config.has_option('BetaSeries','enable_tvshow_scrobbling'):
        config.set('BetaSeries', 'enable_tvshow_scrobbling', False)
    if not config.has_option('BetaSeries','login'):
        config.set('BetaSeries', 'login', 'your_login')
    if not config.has_option('BetaSeries','password'):
        config.set('BetaSeries', 'password', 'your_password')

    if not config.has_section('Last.fm'):
        config.add_section('Last.fm')
    if not config.has_option('Last.fm','enable_now_playing'):
        config.set('Last.fm', 'enable_now_playing', False)
    if not config.has_option('Last.fm','enable_scrobbling'):
        config.set('Last.fm', 'enable_scrobbling', False)
    if not config.has_option('Last.fm','login'):
        config.set('Last.fm', 'login', 'your_login')
    if not config.has_option('Last.fm','password'):
        config.set('Last.fm', 'password', 'your_password')

    if not config.has_section('YAMJ'):
        config.add_section('YAMJ')
    if not config.has_option('YAMJ','watched'):
        config.set('YAMJ', 'watched', False)
    if not config.has_option('YAMJ','watched_path'):
        config.set('YAMJ', 'watched_path', '')
    if not config.has_option('YAMJ','watched_with_video'):
        config.set('YAMJ', 'watched_with_video', True)
    if not config.has_option('YAMJ','ignored_category'):
        config.set('YAMJ', 'ignored_category', '')

    if not config.has_section('YAMJ2'):
        config.add_section('YAMJ2')
    if not config.has_option('YAMJ2','jukebox_path'):
        config.set('YAMJ2', 'jukebox_path', '')
    #if not config.has_option('YAMJ2','boot_time_sync'):
    #    config.set('YAMJ2', 'boot_time_sync', '-1')
    #if not config.has_option('YAMJ2','update_movie_collection'):
    #    config.set('YAMJ2', 'update_movie_collection', 'False')
    #if not config.has_option('YAMJ2','update_movie_watched'):
    #    config.set('YAMJ2', 'update_movie_watched', 'False')		
    #if not config.has_option('YAMJ2','update_show_collection'):
    #    config.set('YAMJ2', 'update_show_collection', 'False')	
    #if not config.has_option('YAMJ2','update_show_watched'):
    #    config.set('YAMJ2', 'update_show_watched', 'False')			
    #if not config.has_option('YAMJ2','mark_watched'):
    #    config.set('YAMJ2', 'mark_watched', 'False')

    if not config.has_section('YAMJ3'):
        config.add_section('YAMJ3')
    if not config.has_option('YAMJ3','API_url'):
        config.set('YAMJ3', 'API_url', '')
    if config.has_option('YAMJ3','API url'):
        config.remove_option('YAMJ3', 'API url')

    if not config.has_section('Oversight'):
        config.add_section('Oversight')
    if not config.has_option('Oversight','boot_time_sync'):
        config.set('Oversight', 'boot_time_sync', '-1')
    if not config.has_option('Oversight','update_movie_collection'):
        config.set('Oversight', 'update_movie_collection', 'False')
    if not config.has_option('Oversight','update_movie_watched'):
        config.set('Oversight', 'update_movie_watched', 'False')		
    if not config.has_option('Oversight','update_show_collection'):
        config.set('Oversight', 'update_show_collection', 'False')	
    if not config.has_option('Oversight','update_show_watched'):
        config.set('Oversight', 'update_show_watched', 'False')			
    if not config.has_option('Oversight','mark_watched'):
        config.set('Oversight', 'mark_watched', 'False')
    if config.has_option('Oversight','mark watched'):
        config.remove_option('Oversight', 'mark watched')

    if not config.has_section('XML/HTML Update'):
        config.add_section('XML/HTML Update')
    if not config.has_option('XML/HTML Update','rutabaga_mod_watched'):
        config.set('XML/HTML Update', 'rutabaga_mod_watched', 'False')
    if not config.has_option('XML/HTML Update','update_xml_watched'):
        config.set('XML/HTML Update', 'update_xml_watched', 'False')
    if not config.has_option('XML/HTML Update','tvxml_find'):
        config.set('XML/HTML Update', 'tvxml_find', 'Other_All,Other_HD,Other_New_,Other_New-TV,Other_Rating,Other_TV,Other_Unwatched,Other_Sets')
    if not config.has_option('XML/HTML Update','moviexml_find'):
        config.set('XML/HTML Update', 'moviexml_find', 'Other_All,Other_HD,Other_New_,Other_New-Movies,Other_Rating,Other_Movies,Other_Unwatched,Other_Sets')

    if not config.has_section('User Edits'):
        config.add_section('User Edits')
    if not config.has_option('User Edits','replace_with'):
        config.set('User Edits', 'replace_with', '')

    with open(config_file, 'w') as configfile:
        config.write(configfile)

if isfile(config_file):
    loadOldConfig()
newConfig()

# Roll over on application start if file size is over
logger = logging.getLogger('pchtrakt')
log_file = config.get('PCHtrakt', 'log_file')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s\r')
hdlr = logging.handlers.RotatingFileHandler(log_file,backupCount=3)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

if getsize(log_file) > float(config.get('PCHtrakt', 'log_size')):
	logger.handlers[0].doRollover()