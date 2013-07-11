PchTrakt
=====

*PchTrakt is currently in beta release. There may be severe bugs in it and at any given time it may not work at all.*

PchTrakt is a software you can install on your popcorn-hour or a linux server. It scrobbles what you are playing on your popcorn-hour to [trakt.tv][trakt].


Features:

* Tv shows scrobbling
* Multi-episode scrobbling
* Movies scrobbling
* Add TvShows to Trakt.tv's library

PchTrakt makes use of the following projects:

* [tvdb_api][tvdb_api]
* [TraktUtilities][TraktUtilities]

## Bug

If you find a bug please report it or it'll never get fixed.


[trakt]: http://www.trakt.tv
[tvdb_api]: http://github.com/dbr/tvdb_api
[TraktUtilities]: https://github.com/Manromen/script.TraktUtilities



----------------------------------
feature's added with jhmiller mod:
---------------------------------- 


download : https://github.com/cptjhmiller/pchtrakt/zipball/dvp
 
installation : 
- unzip the package downloaded directly on the pch to overwrite already installed files 
- restart the pchtrakt program with CSI application. This will make the updated pchtrakt.ini
- edit and mod the pchtrakt.ini according with the feature and the file you want to update, using a compatible editor - ex: notepad++, save your change before leaving
- delete the pchtrakt.log file 
- restart the pchtrakt program with CSI application. his is so your new settings (pchtrakt.ini) will be used.
 
feature and parameter:
- Watched could now be trapped on the fly and could update yamj xml file used by eversion flash skin
 
parameter added to pchtrakt.ini
- in the [PCHtrakt] section 
add watched_percent = XX 
xx is the percentage shown of the movie, where you consider that this movie should be marked as watched 
by default it's 90 - that would say , if a movie has be watched more than 90% this movie will be marked as watched 
xx should be a numeric value >o and <100
 
remarks : When you play a file pchtrakt needs to be sure it didn't start after the watched pointer(90% in your case), so if you began to play begin just at 90% 
or if the movie is stopped to coth from 90% (30 seconds), the pchtrakt program could misfunctionned or partiallly update all the files. 
Watched file created and xml files not updated. 
If so delete the watched file that was made and re-play the video file starting before the 90% scheduled, wait a little before moving to 90%+, 
let run the movie some time after the jump - 2-3 minutes it should then behave as normal and show in the logs what xml files it has changed.
 

- in the [yamj] section: 

add update_xml_watched = path the jukebox where the xlm files are stored 
like /opt/sybhttpd/localhost.drives/NETWORK_SHARE/READYNAS/Jukebox/ or /opt/sybhttpd/localhost.drives/SATA_DISK/Yamj/Jukebox/
tvxml_find = all the index files which needed to be updated according with your TV show settings 
value could be : Other_All,Other_HD,Other_New,Other_Rating,Other_TV,Other_Unwatched,Other_Sets
 
moviexml_find = all the index files which needed to be updated according with your TV show settings 
value could be : Other_All,Other_HD,Other_New,Other_Rating,Other_Movies,Other_Unwatched,Other_Set?s
 
If you encounter problem you could report : http://www.networkedmediatank.com/showthread.php?tid=58356