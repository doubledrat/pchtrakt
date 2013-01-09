starts with 

elif pchtrakt.isTvShow:
					xmlpath = YamjPath + "Jukebox/Game.of.Thrones.S01E01.Winter.Is.Coming.xml"
					for name in glob.glob(xmlpath):
						print myMedia.parsedInfo.season_number, myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode]
						if myMedia.oStatus.fileName in open(name).read():
							tree = ElementTree.parse(name)
							for movie in tree.findall('./movie/files/file'):#         .=<details>     *=library
								if movie.get('firstPart') == str(myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode]):
									if movie.get('season') == str(myMedia.parsedInfo.season_number):
										movie.set('watched', 'true')
										bak_name = name[:-4]+'.bak'
										tree.write(bak_name)
										os.rename(bak_name, name)
										break
if myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode] =< 9:
	ep_no = str(%02d' % myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode])
elif myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode] => 10:
	ep_no = str(myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode])
	
	
a = re.split("(.*[Ss]\\d\\d[Ee]\\d\\d.)", test_name)#
a[2] = a[2][:-4].replace(".", " ")#
a[1] = a[1][:-3]#
	
	
 == str(	
	
	
	
	
	
	
	elif myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode] != 1:
	
		
		
fileinfo = 'Set_' + myMedia.parsedInfo.name + '_	
		
		xmlpath = YamjPath + "Jukebox/" + 

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		elif myMedia.parsedInfo.season_number => 10
	if myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode] == 1:
		xmlpath = YamjPath + "Jukebox/" + myMedia.oStatus.fileName[:-4] + ".xml"
	elif myMedia.parsedInfo.episode_numbers[myMedia.idxEpisode] != 1:
		xmlpath = YamjPath + "Jukebox/" + 
		
		
		
Set_show name_1.xml <10
Set_show name_2.xml >10

episode <> 1
path = "Set_" + myMedia.parsedInfo.name + 











					fileinfo = YamjPath + "Jukebox4/*.xml"
					txt = fileinfo
					Debug(txt)
					pchtrakt.logger.info(txt)
					for name in glob.glob(fileinfo):
						txt = name
						Debug(txt)
						pchtrakt.logger.info(txt)
						if myMedia.oStatus.fileName in open(name).read():
							tree = ElementTree.parse(name)

							for movie in tree.findall('*/movie/files/file'):
								txt = movie
								Debug(txt)
								pchtrakt.logger.info(txt)
								if movie.get('title') == ep_name:
									movie.set('watched', 'true')
									bak_name = name[:-4]+'.bak'
									tree.write(bak_name)
									os.rename(bak_name, name)
									break
					















