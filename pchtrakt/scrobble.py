from sys import version_info
from os.path import isfile
from os import listdir
from xml.etree import ElementTree
import fileinput
from lib import utilities
from lib.utilities import Debug
import pchtrakt, glob, os, re, urllib
from pchtrakt.exception import BetaSerieAuthenticationException
from pchtrakt import mediaparser as mp
from pchtrakt import betaseries as bs
from pchtrakt.config import *
from time import sleep
from pchtrakt.pch import EnumStatus
#from pchtrakt.pch import decode_string, utf8_encoded
class EnumScrobbleResult:
    KO = 0
    TRAKTOK = 1
    BETASERIESOK= 2

class OutToMainLoop(Exception):
    pass

def repl_func(m):
    return m.group(1) + m.group(2).upper()

def showStarted(myMedia):
    if TraktScrobbleTvShow:
        percent = myMedia.oStatus.percent * len(myMedia.parsedInfo.episode_numbers)  - (myMedia.idxEpisode * 100 )#fixed percent for multipleEpisode

        if percent < 0 : percent = 0
        
        if str(myMedia.parsedInfo.season_number) == "None":
            myMedia.parsedInfo.season_number = "1"
        response = utilities.watchingEpisodeOnTrakt(myMedia.parsedInfo.id,
                                                    myMedia.parsedInfo.name,
                                                    myMedia.parsedInfo.year,
                                                    str(myMedia.parsedInfo.season_number),
                                                    str(myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode]),
                                                    str(myMedia.oStatus.totalTime),
                                                    str(percent))
        #msg = u'[traktAPI] Sending play: {0} {1} {2} {3}' \
        #      ' {4} {5} {6}'.format(myMedia.parsedInfo.id,
        #                            myMedia.parsedInfo.name,
        #                            myMedia.parsedInfo.year,
        #                            str(myMedia.parsedInfo.season_number),
        #                            str(myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode]),
        #                            str(myMedia.oStatus.totalTime),
        #                            str(percent))
        #pchtrakt.logger.info(msg)
        if response != None:
            msg = ' [traktAPI] Tv Show is playing: %s - %s' %(response['status'],response['message'])

        else:
            msg = ' [traktAPI] No response from Trakt.tv'
        pchtrakt.logger.info(msg)

def movieStarted(myMedia):
    response = utilities.watchingMovieOnTrakt(myMedia.parsedInfo.id,
												myMedia.parsedInfo.name,
												myMedia.parsedInfo.year,
												str(myMedia.oStatus.totalTime),
												str(myMedia.oStatus.percent))
    if response != None:
        msg = ' [traktAPI] Movie is playing: %s - %s' %(response['status'],response['message'])
    else:
        msg = ' [traktAPI] No response from Trakt.tv'
    pchtrakt.logger.info(msg)


def showStopped():
    response = utilities.cancelWatchingEpisodeOnTrakt()
    if response != None:
        msg = ' [traktAPI] Tv Show has stopped: %s - %s' %(response['status'],response['message'])
    else:
        msg = ' [traktAPI] No response from Trakt.tv'
    pchtrakt.logger.info(msg)


def movieStopped():
    response = utilities.cancelWatchingMovieOnTrakt()
    if response != None:
        msg = ' [traktAPI] Movie has stopped: %s - %s' %(response['status'],response['message'])
    else:
        msg = ' [traktAPI] No response from Trakt.tv'
    pchtrakt.logger.info(msg)


def videoStopped():
    if pchtrakt.isTvShow and TraktScrobbleTvShow:
        showStopped()
    elif pchtrakt.isMovie and TraktScrobbleMovie:
        movieStopped()

	
def showStillRunning(myMedia):
    showStarted(myMedia)


def movieStillRunning(myMedia):
    movieStarted(myMedia)


def showIsEnding(myMedia):
    try:
        if BetaSeriesScrobbleTvShow:
            result = 0
            serieXml = bs.getSerieUrl(myMedia.parsedInfo.name)
            token = bs.getToken()
            isWatched = bs.isEpisodeWatched(serieXml,token,myMedia.parsedInfo.season_number
                                        ,myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode])
            Debug('(BetaSeries) Is episode watched: {0}'.format(isWatched))
            msg = '(BetaSeries) Video is '
            if not isWatched:
                result = bs.scrobbleEpisode(serieXml
                                                    ,token,
                                                    myMedia.parsedInfo.season_number,
                                                    myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode])
                bs.destroyToken(token)
                msg += 'ending: '
            else:
                msg += 'already watched: '
            if result or isWatched:
                myMedia.ScrobResult |=  EnumScrobbleResult.BETASERIESOK
                msg += u'{0} {1}x{2}'.format(myMedia.parsedInfo.name,
                                           myMedia.parsedInfo.season_number,
                                           myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode]
                                           )
                pchtrakt.logger.info(msg)

        else:
            myMedia.ScrobResult |= EnumScrobbleResult.BETASERIESOK
    except BetaSerieAuthenticationException as e:
        Debug(e)
    except Exception as e:
        Debug(e)
    if TraktScrobbleTvShow:
        Debug("[traktAPI] TV ENDIng")
        result = 0
        if str(myMedia.parsedInfo.season_number) == "None":
            myMedia.parsedInfo.season_number = "1"
        response = utilities.scrobbleEpisodeOnTrakt(myMedia.parsedInfo.id,
                                                    myMedia.parsedInfo.name,
                                                    myMedia.parsedInfo.year,
													str(myMedia.parsedInfo.season_number),
                                                    str(myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode]),
                                                    str(myMedia.oStatus.totalTime),
                                                    str(myMedia.oStatus.percent))
        if response:
            msg = ' [traktAPI] Tv Show is ending: %s - %s ' %(response['status'],response['message'])
            pchtrakt.logger.info(msg)
            result = 1

        if result == 1:
            myMedia.ScrobResult |= EnumScrobbleResult.TRAKTOK
    else:
        myMedia.ScrobResult |= EnumScrobbleResult.TRAKTOK
    return myMedia.ScrobResult == EnumScrobbleResult.TRAKTOK | EnumScrobbleResult.BETASERIESOK


def movieIsEnding(myMedia):
    Debug("Movie ENDIng")
    response = utilities.scrobbleMovieOnTrakt(myMedia.parsedInfo.id,
                                               myMedia.parsedInfo.name,
                                               myMedia.parsedInfo.year,
                                               str(myMedia.oStatus.totalTime),
                                               str(myMedia.oStatus.percent))
    if response != None:
        msg = ' [traktAPI] Movie is ending: %s - %s ' %(response['status'],response['message'])
        pchtrakt.logger.info(msg)
        return 1
    return 0


def videoStatusHandleMovie(myMedia):
    if pchtrakt.lastPath != myMedia.oStatus.fullPath:
        pchtrakt.watched = 0
        pchtrakt.lastPath = myMedia.oStatus.fullPath
        pchtrakt.lastName = myMedia.oStatus.fileName
        pchtrakt.currentTime = myMedia.oStatus.currentTime
        if pchtrakt.lastPath != '':
            if myMedia.oStatus.percent > watched_percent and pchtrakt.Check <= pchtrakt.PlayCount:
                pchtrakt.watched  = 1
                pchtrakt.logger.info(' [Pchtrakt] Started at more than '+ str(watched_percent) + '%! I''m not doing anything!')
            else:
                movieStarted(myMedia)
    if not pchtrakt.watched:
        if myMedia.oStatus.percent > watched_percent and pchtrakt.Check <= pchtrakt.PlayCount and not pchtrakt.BigJump:
            pchtrakt.watched = movieIsEnding(myMedia)
            if pchtrakt.watched:
			    pchtrakt.StopTrying = 0
			    while myMedia.oStatus.status == EnumStatus.PLAY:
			        sleep(sleepTime)
			        myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
			        pchtrakt.StopTrying = 1
			    UpdateXMLFiles(pchtrakt)
        elif myMedia.oStatus.currentTime > pchtrakt.currentTime + int(TraktRefreshTime)*60:
            pchtrakt.currentTime = myMedia.oStatus.currentTime
            movieStillRunning(myMedia)
    elif myMedia.oStatus.percent < 10 and myMedia.oStatus.status != EnumStatus.STOP:
        pchtrakt.logger.info(' [Pchtrakt] It seems you came back at the begining of the video... so I say to trakt it\'s playing')
        pchtrakt.watched = 0
        pchtrakt.PlayCount = 0
        pchtrakt.currentTime = myMedia.oStatus.currentTime
        movieStarted(myMedia)

def videoStatusHandleTVSeries(myMedia):
    if len(myMedia.parsedInfo.episode_numbers)>1:
            doubleEpisode = 1
    else:
        doubleEpisode = 0
    if pchtrakt.lastPath != myMedia.oStatus.fullPath:
        pchtrakt.watched = 0
        pchtrakt.lastPath = myMedia.oStatus.fullPath
        pchtrakt.lastName = myMedia.oStatus.fileName
        pchtrakt.episode_numbers = myMedia.parsedInfo.episode_numbers 
        pchtrakt.season_number = myMedia.parsedInfo.season_number
        pchtrakt.currentTime = myMedia.oStatus.currentTime
        myMedia.idxEpisode = 0
        if pchtrakt.lastPath != '':
            if myMedia.oStatus.percent > watched_percent and pchtrakt.Check <= pchtrakt.PlayCount:
                pchtrakt.watched  = 1
                pchtrakt.logger.info(' [Pchtrakt] Started at more than '+ str(watched_percent) + '%! I''m not doing anything!')
            elif doubleEpisode:
                while myMedia.oStatus.percent > (myMedia.idxEpisode + 1) * watched_percent/len(myMedia.parsedInfo.episode_numbers):
                    myMedia.idxEpisode += 1
                showStarted(myMedia)
                pchtrakt.currentTime = myMedia.oStatus.currentTime
            else:
                showStarted(myMedia)
    if not pchtrakt.watched:
        if myMedia.oStatus.percent > watched_percent and pchtrakt.Check <= pchtrakt.PlayCount and not pchtrakt.BigJump:
            pchtrakt.watched = showIsEnding(myMedia)
            if pchtrakt.watched:
			    pchtrakt.StopTrying = 0
			    while myMedia.oStatus.status == EnumStatus.PLAY:
			        sleep(sleepTime)
			        myMedia.oStatus = pchtrakt.oPchRequestor.getStatus(ipPch, 10)
			        pchtrakt.StopTrying = 1
			    UpdateXMLFiles(pchtrakt)
        elif myMedia.oStatus.currentTime > pchtrakt.currentTime + int(TraktRefreshTime)*60:
            pchtrakt.currentTime = myMedia.oStatus.currentTime
            showStillRunning(myMedia)
        elif doubleEpisode and myMedia.oStatus.percent > (myMedia.idxEpisode+1) * watched_percent/len(myMedia.parsedInfo.episode_numbers) and myMedia.idxEpisode+1 < len(myMedia.parsedInfo.episode_numbers):
            showIsEnding(myMedia)
            myMedia.idxEpisode += 1
            showStarted(myMedia)
    elif myMedia.oStatus.percent < 10 and myMedia.oStatus.status != EnumStatus.STOP:
        pchtrakt.logger.info(' [Pchtrakt] It seems you came back at the begining of the video... so I say to trakt it\'s playing')
        pchtrakt.watched = 0
        pchtrakt.PlayCount = 0
        pchtrakt.currentTime = myMedia.oStatus.currentTime
        showStarted(myMedia)

def videoStatusHandle(myMedia):
    if isinstance(myMedia.parsedInfo,mp.MediaParserResultTVShow):
        if TraktScrobbleTvShow or BetaSeriesScrobbleTvShow:
            videoStatusHandleTVSeries(myMedia)
        pchtrakt.isTvShow = 1
        pchtrakt.episode_numbers = myMedia.parsedInfo.episode_numbers 
        pchtrakt.season_number = myMedia.parsedInfo.season_number
    elif isinstance(myMedia.parsedInfo,mp.MediaParserResultMovie):
        if TraktScrobbleMovie:
           videoStatusHandleMovie(myMedia)
        pchtrakt.isMovie = 1
    else:
        pchtrakt.StopTrying = 1
    pchtrakt.lastPath = myMedia.oStatus.fullPath
    pchtrakt.lastName = myMedia.oStatus.fileName
    if myMedia.oStatus.currentTime > pchtrakt.currentTimeB + int(sleepTime):
	    Z = int(myMedia.oStatus.currentTime - pchtrakt.currentTimeB)
	    Z = int(Z / float(int(sleepTime)))
	    #work out length of jump or not?
	    Debug('[Pchtrakt] FORWARDS' + str(Z) + ' - ' + str(pchtrakt.currentTimeB))
	    pchtrakt.currentTimeB = myMedia.oStatus.currentTime
	    pchtrakt.PlayCount += Z
	    if pchtrakt.BigJump:
	        pchtrakt.BigJump += Z
                if pchtrakt.BigJump >= int(pchtrakt.Check / 10):
				    pchtrakt.BigJump = 0
	    if Z >= int(pchtrakt.Check / 10):
	        pchtrakt.BigJump = 1
    elif myMedia.oStatus.currentTime < pchtrakt.currentTimeB:# + int(TraktRefreshTime):
	    Debug('[Pchtrakt] BACKWARDS' + str(myMedia.oStatus.currentTime) + ' - ' + str(pchtrakt.currentTimeB))
	    Z = int(pchtrakt.currentTimeB - myMedia.oStatus.currentTime)# + int(TraktRefreshTime))
	    Z = int(Z / float(int(sleepTime)) + 1)
	    if Z >= pchtrakt.PlayCount:
	        pchtrakt.PlayCount = 0
	        x = float(myMedia.oStatus.totalTime) - float(myMedia.oStatus.currentTime)
	        pchtrakt.Check = int(float(x / 100) * float(watched_percent) / float(int(sleepTime)))
	        pchtrakt.currentTimeB = myMedia.oStatus.currentTime
	    else:
	        pchtrakt.PlayCount -= Z
	    Debug('[Pchtrakt] BACKWARDS: ' + str(Z) + ' - ' + str(pchtrakt.currentTimeB))
	    pchtrakt.currentTimeB = myMedia.oStatus.currentTime
	    if pchtrakt.PlayCount != 0:
	        pchtrakt.PlayCount -= 1
	    if pchtrakt.BigJump and Z >= int(pchtrakt.Check / 9):
	        pchtrakt.BigJump = 0
    Debug('[Pchtrakt] ' + str(myMedia.oStatus.currentTime) + ' ' + str(pchtrakt.currentTimeB + int(sleepTime)))
    Debug('[Pchtrakt] ' + str(pchtrakt.Check) + ' <= ' + str(pchtrakt.PlayCount))#could add +1 here and below

def isIgnored(myMedia):
    ignored = False

    msg = u' [Pchtrakt] File: {0}'.format(myMedia.oStatus.fileName)
    pchtrakt.logger.info(msg)
    ignored = isKeywordIgnored(myMedia.oStatus.fileName)

    if not ignored and ignored_repertory[0] != '':
        for el in myMedia.oStatus.fullPath.split('/'):
            Debug("[Pchtrakt] Checking if " + el + " is an ignored folder")
            if el != '' and el in ignored_repertory:
                msg = ' [Pchtrakt] This video is in a ignored repertory: {0}'.format(el) + ' Waiting for next file to start.'
                pchtrakt.logger.info(msg)
                ignored = True
                break

    if not ignored and YamjIgnoredCategory[0] != '':
        if isinstance(myMedia.parsedInfo, mp.MediaParserResultTVShow):
            files = listdir(YamjPath)
            for file in files:
                if file.endswith('xml'):
                    file = unicode(file, errors='replace')
                    if file.find(myMedia.parsedInfo.name) >= 0:
                        oXml = ElementTree.parse(YamjPath + file)
                        ignored = isGenreIgnored(oXml.findall('.//genre'))
                        if ignored:
                            break
        else:
            file = unicode(myMedia.oStatus.fileName.rsplit('.',1)[0] + '.xml', errors='replace')
            oXml = ElementTree.parse(YamjPath + file)
            genres = oXml.findall('.//genre')

            ignored = isGenreIgnored(genres)
    return ignored

def isKeywordIgnored(title):
    if ignored_keywords[0] != '':
        for keyword in ignored_keywords:
            if keyword.lower() in title.lower():
                msg = u' [Pchtrakt] This file contains an ignored keyword. Waiting for next file to start.'
                pchtrakt.logger.info(msg)
                return True
    return False

def isGenreIgnored(genres):
    txt = ' [Pchtrakt] The ignored genres are :{0}'.format(YamjIgnoredCategory)
    pchtrakt.logger.info(txt)
    for genre in genres:
        genre = genre.text.strip().lower()
        txt = ' [Pchtrakt] This genre is {0}'.format(genre)
        txt += ' --- Should it be ignored? {0}'.format(genre in YamjIgnoredCategory)
        pchtrakt.logger.info(txt)
        if genre in YamjIgnoredCategory:
            txt = ' [Pchtrakt] This video is in the ignored genre {0}'.format(genre)
            pchtrakt.logger.info(txt)
            return True
    return False

def watchedFileCreation(myMedia):
    Debug('[Pchtrakt] ' + str(pchtrakt.Check) + ' <= ' + str(pchtrakt.PlayCount))#could add +1 here and below
    if myMedia.oStatus.percent > watched_percent and pchtrakt.Check <= pchtrakt.PlayCount and not pchtrakt.BigJump:
        Debug('watchedFileCreation')
        try:
            path = myMedia.oStatus.fileName.encode('utf-8', 'replace')
        except:
            Debug('doing except for path')
            path = myMedia.oStatus.fileName.encode('latin-1', 'replace')
        if YamJWatchedVithVideo:
            try:
                path = myMedia.oStatus.fullPath.encode('utf-8', 'replace')
            except:
                path = myMedia.oStatus.fullPath.encode('latin-1', 'replace')
            #Remember that .DVD extension
            if (path.split(".")[-1] == "DVD"):
                path = path[:-4]
            if not OnPCH:
                path = path.replace('/opt/sybhttpd/localhost.drives/','')
                path = path.split('/', 2)[2]
                path = '{0}{1}'.format(YamjWatchedPath, path)
        else:
            if (path.split(".")[-1] == "DVD"):
                path = path[:-4]
            path = '{0}{1}'.format(YamjWatchedPath, path)
        path = '{0}.watched'.format(path)
        if not isfile(path):
            Debug('[Pchtrakt] Start to write file')
            f = open(path, 'w')
            f.close()
            msg = ' [Pchtrakt] I have created the file {0}'.format(path)
            pchtrakt.logger.info(msg)
            pchtrakt.CreatedFile = 1
        else:
            pchtrakt.CreatedFile = 2

def UpdateXMLFiles(pchtrakt):
    Debug('[Pchtrakt] ' + str(pchtrakt.CreatedFile))
    if pchtrakt.CreatedFile == 1 and not pchtrakt.BigJump:
        if  updatexmlwatched:
            matchthis = pchtrakt.lastName.encode('utf-8')
            matchthisfull = pchtrakt.lastPath.encode('utf-8')
            Debug('[Pchtrakt] Start xml update routine')
            lookfor = matchthis[:-4]
            lookforfull = matchthisfull[:-4]
            if pchtrakt.isMovie:
                msg = ' [Pchtrakt] Starting Normal Movie xml update in '+YamjPath
                pchtrakt.logger.info(msg)
                previous = None
                name = urllib.unquote_plus(YamjPath + lookfor + '.xml')
                Debug('[Pchtrakt] Looking at ' + name)
                tree = ElementTree.parse(name)
                try:
                    SET = urllib.unquote_plus(tree.find('movie/sets/set').attrib['index'])
                except AttributeError:
                    SET = '0'
                Debug('[Pchtrakt] 1 ' + name)
                for movie in tree.findall('movie'):
                    Debug('[Pchtrakt] 2 ' + name)
                    if movie.find('baseFilenameBase').text.encode('utf-8') == lookfor:#for  content in penContents:
                        Debug('[Pchtrakt] MATCH FOUND')
                        movie.find('watched').text = 'true'
                        for mfile in movie.findall('files/file'):
                            mfile.set('watched', 'true')
                            bak_name = name[:-4]+'.bak'
                            tree.write(bak_name, encoding='utf-8')
                            os.rename(bak_name, name)
                            txt = name.replace(YamjPath, '') + ' has been modified as watched for ' + matchthis
                            pchtrakt.logger.info(' [Pchtrakt] ' + txt)
                            break
                try:
                    if SET != "0":
                        moviexmlfind.insert(0,SET)
                        Debug('[Pchtrakt] Has Set_ file: ' + SET)
                    for xmlword in moviexmlfind:
                        fileinfo = YamjPath + xmlword + "*xml"
                        Debug('[Pchtrakt] ' + fileinfo)
                        for name in glob.glob(fileinfo):
                            Debug('[Pchtrakt] Looking for ' + lookfor + " in " + name)
                            if lookfor in open(name).read():#gets xml file name as name
                                Debug('[Pchtrakt] MATCH FOUND')
                                tree = ElementTree.parse(name)
                                for movie in tree.findall('movies/movie'):
                                    if movie.find('baseFilenameBase').text.encode('utf-8') == lookfor:
                                        if movie.attrib['isSet'] == "true" and SET != "0":
                                            Debug('[Pchtrakt] isset is true')
                                            raise OutToMainLoop()
                                        movie.find('watched').text = 'true'
                                        bak_name = name[:-4]+'.bak'
                                        tree.write(bak_name, encoding='utf-8')
                                        os.rename(bak_name, name)
                                        txt = name.replace(YamjPath, '') + ' has been modified as watched for ' + matchthis
                                        pchtrakt.logger.info(' [Pchtrakt] ' + txt)
                                        previous = xmlword
                                        break
                                break
                except OutToMainLoop:
                    pass
            elif pchtrakt.isTvShow:
                pchtrakt.logger.info(' [Pchtrakt] Starting Tv xml update in '+ YamjPath)
                epno = str(pchtrakt.episode_numbers).replace('[', '').replace(']', '')
                if version_info >= (2,7): #[@...=...] only available with python >= 2.7
                    xpath = "*/movie/files/file[@firstPart='{0}'][@season='{1}']".format(
                                                epno,str(pchtrakt.season_number))
                else:
                    xpath = "*/movie/files/file"
                a = re.split("([-|.]*[Ss]\\d\\d[Ee]\\d\\d.)", matchthis)
                if len(a) == 1:
                    a = re.split("(?P<season_num>\d+)[. _-]*", matchthis)
                ep_name = a[2][:-4].replace(".", " ").replace("- ", "")
                season_xml = re.sub("(^|\s)(\S)", repl_func, a[0][:2])
                tvxmlfind.extend(["Set_" + season_xml,season_xml])
                for xmlword in tvxmlfind:
                    fileinfo = YamjPath + xmlword + "*.xml"
                    for name in glob.glob(fileinfo):
                        Debug('[Pchtrakt] scanning ' + fileinfo)
                        if lookfor in open(name).read():
                            Debug("after name " + fileinfo)
                            tree = ElementTree.parse(name)
                            if xmlword == season_xml:
                                if version_info >= (2,7):
                                    zpath = "./movie/files/file[@firstPart='{0}'][@season='{1}']".format(
						                            epno,str(pchtrakt.season_number))
                                else:
                                    zpath = "./movie/files/file"
                            else:
                                zpath = xpath
                            Debug(zpath)
                            for movie in tree.findall(zpath):
                                Debug('[Pchtrakt] looking for file://' + matchthisfull)
                                Debug('[Pchtrakt] found this  ' + urllib.unquote_plus(movie.find('fileURL').text.encode('utf-8')))
                                if urllib.unquote_plus(movie.find('fileURL').text.encode('utf-8')) == 'file://' + matchthisfull:
                                    Debug('[Pchtrakt] MATCH FOUND')
                                    movie.set('watched', 'true')
                                    bak_name = name[:-4]+'.bak'
                                    tree.write(bak_name, encoding='utf-8')
                                    os.rename(bak_name, name)
                                    txt = name.replace(YamjPath, '') + ' has been modified as watched for ' + matchthis
                                    pchtrakt.logger.info(' [Pchtrakt] ' + txt)
                                    previous = xmlword
                                    break
                            break
            msg = ' [Pchtrakt] XML Update complete'
            pchtrakt.logger.info(msg)
        elif RutabagaModwatched:
            lookfor = matchthis[:-4]
            lookforfull = matchthisfull[:-4]
            msg = ' [Pchtrakt] Starting html update in '+YamjPath
            pchtrakt.logger.info(msg)
            if pchtrakt.isMovie:
                fileinfo = YamjPath + lookfor + ".html"
                content = open(fileinfo,'rb+').read()
                replacedText = content.replace('unwatched', 'watched') 
                if replacedText is not content:
                    open(fileinfo, 'w').write(replacedText)
                    txt = name.replace(YamjPath, '') + ' has been modified as watched for ' + matchthis
                    pchtrakt.logger.info(' [Pchtrakt] ' + txt)
                else:
                    txt = name.replace(YamjPath, '') + ' has NOT been modified as watched for ' + matchthis
                    pchtrakt.logger.info(' [Pchtrakt] ' + txt)
            #elif pchtrakt.isTvShow:
                #fileinfo = YamjPath + lookfor + ".html"
                #content = open(fileinfo,'rb+').read()
                #replacedText = content.replace('unwatched', 'watched') 
                #if replacedText is not content:
                    #open(fileinfo, 'w').write(replacedText)
                    #txt = name.replace(YamjPath, '') + ' has been modified as watched for ' + matchthis
                    #pchtrakt.logger.info(txt)
                #else:
                    #txt = name.replace(YamjPath, '') + ' has NOT been modified as watched for ' + matchthis
                    #pchtrakt.logger.info(txt)
    pchtrakt.PlayCount = 0
