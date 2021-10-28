from os import environ, path, walk, getenv, makedirs, remove
from textdistance import levenshtein
from collections import defaultdict
from time import sleep
from colorama import Fore, Style
import random
import threading
import sys
from Commands import commands, CommandType, Command, parseCommand
from State import State
from Exemptions import getExemptions, isExemptFromLowerCaseCheck, isExemptFromReversalCheck, isExemptFromSimilarityCheck, isExemptFromTheCheck
from KaraokeFile import KaraokeFile
from MusicFile import MusicFile
from Song import Song
from SingerColumn import SingerColumn
from SongSelector import selectSong
from DisplayFunctions import clear, padOrEllipsize, SCREENHEIGHT

# The current state
state = None
# List of paths to karaoke files
karaokeFilesPaths = None
# List of paths to music (MP3/M4A/whatever) files
musicFilesPaths = None
# Path to the folder where data files (music playlist, exemption lists, etc) are stored
dataFilesPath = None
# Path to the appdata folder. We will write "temporary" data here, like the persistent state, request queue, etc.
appDataFolder = getenv("APPDATA")+"\\FullHouse Entertainment\\KaraokeManager"
# Filename of the background music list file (just artist & titles)
backgroundMusicPlaylistFilename = "BackgroundMusicPlaylist.txt"
# Path to the current music requests file
requestsFilename = appDataFolder+"\\KaraokeManager.musicRequests.txt"
# Path to the background music list (list of paths of files that match the BackgroundMusicPlaylist entries)
backgroundMusicFilename = appDataFolder+"\\KaraokeManager.backgroundMusic.txt"
# Name of file that we will write to when we find malformed filenames.
filenameErrorsFilename = "BadFilenames.txt"
# Name of file that we will write to when we find BackgroundMusicPlaylist entries that do not correspond
# to a known music file.
missingPlaylistEntriesFilename = "MissingPlaylistEntries.txt"
# Name of file that we will write to when we find possible duplicates of music files.
musicDuplicatesFilename = "MusicDuplicates.txt"
# Name of file that we will write to when we find possible duplicates of karaoke files.
karaokeDuplicatesFilename = "KaraokeDuplicates.txt"
# Name of file that we will write to when we find karaoke files with artist and/or title problems.
karaokeErrorsFilename = "KaraokeArtistAndTitlesProblems.txt"
# Name of file that we will write to when we find music files with artist and/or title problems.
musicErrorsFilename = "MusicArtistAndTitleProblems.txt"
# Path of file to which we will periodically write a random karaoke artist & song title, for on-screen
# suggestions.
randomSuggestionsFilename = appDataFolder+"\\KaraokeManager.songSuggestion.txt"
# Current background music playlist (strings from the BackgroundMusicPlaylist file)
backgroundMusicPlaylist = set([])
# List of karaoke files (KaraokeFile objects)
karaokeFiles = []
# List of music files (MusicFile objects)
musicFiles = []
# Dictionary of karaoke files. Key is artist, value is another dictionary of karaoke files
# where the key is the song title, and the value is a list of tracks from one or more vendors.
karaokeDictionary = None
# Dictionary of music files. Key is artist, value is another dictionary of music files
# where the key is the song title, and the value is a list of tracks with that title.
musicDictionary = None
# Thread that will periodically choose a random karaoke file and write it to the suggestion file.
suggestorThread = None
# Flag to stop the suggestion thread.
stopSuggestions = False
# List of errors from last command
errors = []
# List of informational messages from last command
messages = []

# Shows onscreen help when the user types "help"
def showHelp():
	clear()
	showHeader()
	print(f"All command keywords can be shortened to the first letter.")
	print(f"IDs can be a number from the list, or a partial or complete name (case-insensitive).")
	print()
	print(f"{Fore.CYAN}{Style.BRIGHT}add,NewSingerName{Style.RESET_ALL} = add a new singer to the list")
	print(f"{Fore.CYAN}{Style.BRIGHT}insert,NewSingerName,next/SingerID{Style.RESET_ALL} = insert a new singer before an existing singer")
	print(f"{Fore.CYAN}{Style.BRIGHT}move,SingerID,next/end/SingerID{Style.RESET_ALL} = move a singer to another position in the list")
	print(f"{Fore.CYAN}{Style.BRIGHT}delete,SingerID{Style.RESET_ALL} = remove a singer from the list")
	print(f"{Fore.CYAN}{Style.BRIGHT}name,SingerID,NewName{Style.RESET_ALL} = rename a singer")
	print()
	print(f"{Fore.CYAN}{Style.BRIGHT}add,list/SingerID,SongTitle[,KeyChange]{Style.RESET_ALL} = add a song to a singer, or to current list")
	print(f"{Fore.CYAN}{Style.BRIGHT}insert,list/SingerID,next/SongID,SongTitle[,KeyChange]{Style.RESET_ALL} = insert a song into a list for a singer")
	print(f"{Fore.CYAN}{Style.BRIGHT}move,list/SingerID,SongID,next/end/SongID{Style.RESET_ALL} = move a song to another position in the list")
	print(f"{Fore.CYAN}{Style.BRIGHT}delete,list/SingerID,SongID{Style.RESET_ALL} = remove a song from a singer")
	print(f"{Fore.CYAN}{Style.BRIGHT}key,list/SingerID,SongID{Style.RESET_ALL} = set the key change on a song")
	print()
	print(f"{Fore.CYAN}{Style.BRIGHT}undo{Style.RESET_ALL} = undo previous command")
	print(f"{Fore.CYAN}{Style.BRIGHT}redo{Style.RESET_ALL} = undo previous undo")
	print()
	print(f"{Fore.CYAN}{Style.BRIGHT}list[,SingerID]{Style.RESET_ALL} = change active song list to show list of songs for specified singer (default is next singer)")
	print(f"{Fore.CYAN}{Style.BRIGHT}play[,SongID]{Style.RESET_ALL} = play song and cycle queue. Defaults to next song.")
	print(f"{Fore.CYAN}{Style.BRIGHT}filler[,SongID]{Style.RESET_ALL} = play song without cycling queue. Defaults to next song.")
	print(f"{Fore.CYAN}{Style.BRIGHT}?searchText{Style.RESET_ALL} = search karaoke tracks for given text")
	print(f"{Fore.CYAN}{Style.BRIGHT}??searchText{Style.RESET_ALL} = search music tracks for given text")
	print(f"{Fore.CYAN}{Style.BRIGHT}cue,SongTitle[,add]{Style.RESET_ALL} = cue up a background music track, optionally adding it to the playlist permanently.")
	print(f"{Fore.CYAN}{Style.BRIGHT}scan[,[quick]analyze]{Style.RESET_ALL} = rescan current folder for tracks, optionally analyzing for problems/duplicates.")
	print(f"{Fore.CYAN}{Style.BRIGHT}zap{Style.RESET_ALL} = clear everything and start from scratch")
	print(f"{Fore.CYAN}{Style.BRIGHT}help{Style.RESET_ALL} = show this screen")
	print(f"{Fore.CYAN}{Style.BRIGHT}quit{Style.RESET_ALL} = quit")
	try:
		input(f"{Fore.WHITE}{Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
	except EOFError:
		pass

# Cues up a song
def cueSong(params, errors):
	global messages
	paramCount = len(params)
	if paramCount == 0:
		errors.append("Not enough arguments. Expected song search string.")
	else:
		song = selectSong(params[0], musicFiles)
		if not song is None:
			messages.append(f"Added \"{song.title}\" by {song.artist} to the requests queue.")
			try:
				with open(requestsFilename, mode="a", encoding="utf-8") as f:
					f.write(song.path+"\n")
			except PermissionError:
				errors.append("Failed to write to requests file.")
			if len(params)>1:
				if params[1]=="a" or params[1]=="add":
					try:
						with open(dataFilesPath+"\\"+backgroundMusicPlaylistFilename, mode="a", encoding="utf-8") as f:
							f.write(f"{song.artist} - {song.title}\n")
					except PermissionError:
						errors.append("Failed to append to background music playlist file.")

# Prints the app header
def showHeader():
	print(f'{Fore.GREEN}{Style.BRIGHT}Karaoke Manager v1.0{Style.RESET_ALL} ({len(karaokeFiles)}/{len(musicFiles)} karaoke/music files found)')

# Splits a collection into smaller collections of the given size
def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]

# Print the current list of singers. Groups them into columns.
def showSingers():
	columnSize = 10
	singersWithRequests = state.getSingersDisplayList()
	if len(singersWithRequests) == 0:
		print("No singers.")
	else:
		columnsOfSingers = []
		dictionary = [{'chunk': chunk, 'index': i} for i, chunk in enumerate(chunks(singersWithRequests, columnSize))]
		columnsOfSingers = list(map(lambda item: SingerColumn((item['index']*columnSize)+1, item['chunk']), dictionary))
		for row in range(0, min(len(singersWithRequests), columnSize)):
			print(*map(lambda singerColumn: singerColumn.getRowText(row), columnsOfSingers))

# Print the list of songs for the current singer, or whatever singer
# has been flagged as the current "active list" singer.
def showSongs():
	activeSinger = state.getActiveSongListSinger()
	if activeSinger is None:
		print(f"{Fore.MAGENTA}No current singer selected.{Style.RESET_ALL}")
	else:
		isSongListSingerNext = (activeSinger == state.nextSinger())
		if isSongListSingerNext:
			nameColor = f"{Fore.WHITE}"
		else:
			nameColor = f"{Fore.MAGENTA}"
		print(f"{Fore.WHITE}Showing song list for {nameColor}{Style.BRIGHT}{activeSinger.name}{Style.RESET_ALL}:")
		for i, song in enumerate(activeSinger.songs):
			songIndex = f"{Fore.YELLOW}{Style.BRIGHT}{i+1}{Style.RESET_ALL}"
			if i < 9:
				songIndex = f" {songIndex}"
			if isinstance(song.file, KaraokeFile):
				print(f"{songIndex}: {song.file.getSongListText(song.keyChange)}")
			else:
				print(f"{songIndex}: {song.file.getSongListText()}")

# Processes the given command.
# Returns true if the command is to quit the app.
def processCommand(command):
	global state
	global errors
	if command.commandType == CommandType.HELP:
		showHelp()
	elif command.commandType == CommandType.QUIT:
		return True
	elif command.commandType == CommandType.ADD:
		state = state.add(command.params, karaokeFiles, errors)
	elif command.commandType == CommandType.INSERT:
		state = state.insert(command.params, karaokeFiles, errors)
	elif command.commandType == CommandType.MOVE:
		state = state.move(command.params, errors)
	elif command.commandType == CommandType.DELETE:
		state = state.delete(command.params, errors)
	elif command.commandType == CommandType.LIST:
		state = state.list(command.params, errors)
	elif command.commandType == CommandType.UNDO:
		state = state.undo()
	elif command.commandType == CommandType.REDO:
		state = state.redo()
	elif command.commandType == CommandType.SCAN:
		buildSongLists(command.params)
	elif command.commandType == CommandType.ZAP:
		state = state.clear()
	elif command.commandType == CommandType.NAME:
		state = state.renameSinger(command.params, errors)
	elif command.commandType == CommandType.PLAY:
		state = state.play(command.params, True, errors)
	elif command.commandType == CommandType.FILLER:
		state = state.play(command.params, False, errors)
	elif command.commandType == CommandType.KEY:
		state = state.changeSongKey(command.params, errors)
	elif command.commandType == CommandType.CUE:
		cueSong(command.params, errors)
	elif command.commandType == CommandType.SEARCH:
		showSongList(command.params[0], karaokeFiles, False)
	elif command.commandType == CommandType.MUSICSEARCH:
		showSongList(command.params[0], musicFiles, False)
	return False

# Asks the user for a command, and parses it
def getCommand():
	global errors
	try:
		command = input(":")
	except EOFError:
		pass
	command = command.strip()
	if len(command) > 0:
		parsedCommand = parseCommand(command, errors)
		return parsedCommand
	return None

# Shows any errors from the previous command
def showErrors():
	global errors
	for error in errors:
		print(f'{Fore.RED}{Style.BRIGHT}{error}{Style.RESET_ALL}')
	errors = []

# Shows any messages from the previous command
def showMessages():
	global messages
	for message in messages:
		print(f'{Fore.YELLOW}{Style.BRIGHT}{message}{Style.RESET_ALL}')
	messages = []

# Parses the name of a karaoke file, returning a KaraokeFile object
def parseKaraokeFilename(path, filename):
	filename = filename[0:-4]
	bits = filename.split(" - ")
	if len(bits) == 3:
		return KaraokeFile(path, bits[0].strip(), bits[1].strip(), bits[2].strip())
	return None

# Parses the name of a music file, returning a MusicFile object
def parseMusicFilename(path, filename):
	filename = filename[0:-4]
	bits = filename.split(" - ")
	if len(bits) >= 2:
		title = " - ".join(bits[1:])
		return MusicFile(path, bits[0].strip(), title)
	return None

# Reads the background music playlist into memory
def getBackgroundMusicPlaylist():
	global backgroundMusicPlaylist
	backgroundMusicPlaylist = set([])
	backgroundMusicFilePath=f"{dataFilesPath}\\{backgroundMusicPlaylistFilename}"
	if path.isfile(backgroundMusicFilePath):
		with open(backgroundMusicFilePath, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				line = line.strip()
				if(len(line) > 0):
					backgroundMusicPlaylist.add(line.lower())

# Builds the dictionaries of karaoke and music tracks
def buildDictionaries():
	global musicDictionary
	global karaokeDictionary
	songCount = len(karaokeFiles)
	karaokeDictionary = defaultdict()
	for i in range(0, songCount):
		songFile = karaokeFiles[i]
		karaokeDictionary.setdefault(songFile.artist, defaultdict()).setdefault(
			songFile.title, []).append(songFile)
	songCount = len(musicFiles)
	musicDictionary = defaultdict()
	for i in range(0, songCount):
		songFile = musicFiles[i]
		musicDictionary.setdefault(songFile.artist, defaultdict()).setdefault(
			songFile.title, []).append(songFile)

# Scans a list of files for potential duplicates, bad filenames, etc.
def analyzeFileSet(files,dictionary,fullanalysis,songErrors,duplicates):
	global errors
	getExemptions(dataFilesPath, errors)
	artists = set([])
	artistList = []
	artistLowerList = []

	lastPercent = -1
	counter = 0
	songProgressCount = len(dictionary)
	for artist, songDict in dictionary.items():
		counter += 1
		percent = round((counter/songProgressCount)*100.0)
		if percent > lastPercent:
			print(padOrEllipsize(f"Looking for duplicates: {percent}% done", 119), end="\r")
			lastPercent = percent
		keys = list(songDict.keys())
		for i in range(0, len(keys)):
			songCollection=songDict[keys[i]]
			if(len(songCollection)>1):
				duplicates.extend(songCollection[1:])
	for song in files:
		if not song.artist in artists:
			artists.add(song.artist)
			artistList.append(song.artist)
			artistLowerList.append(song.lowerArtist)
	for artist in artists:
		firstletter = artist[0]
		if firstletter.isalpha() and firstletter.islower():
			if not isExemptFromLowerCaseCheck(artist):
				error = f"Artist \"{artist}\" is not capitalised."
				songErrors.append(error)
		if artist.startswith("The "):
			if artist[4:] in artists and not isExemptFromTheCheck(artist):
				error = f"Artist \"{artist}\" has a non-The variant."
				songErrors.append(error)
	artistCount = len(artistList)
	songCount = len(files)
	songProgressCount = round((songCount*songCount)/2)
	artistProgressCount = round((artistCount*artistCount)/2)
	counter = 0
	lastPercent = -1
	for i in range(0, artistCount):
		artist = artistList[i]
		artistLower = artistLowerList[i]
		ampersandFirstIndex = artist.find(" & ")
		ampersandLastIndex = artist.rfind(" & ")
		if ampersandFirstIndex != -1 and ampersandLastIndex == ampersandFirstIndex:
			bit1 = artist[0:ampersandFirstIndex]
			bit2 = artist[ampersandFirstIndex+3:]
			if bit2 != bit1:
				if not isExemptFromReversalCheck(bit1, bit2):
					reverseCheck = bit2+" & "+bit1
					if reverseCheck in artists:
						error = f"Artist \"{artist}\" also appears as \"{reverseCheck}\"."
						songErrors.append(error)
		for j in range(i+1, artistCount):
			counter += 1
			percent = round((counter/artistProgressCount)*100.0)
			if percent > lastPercent:
				print(padOrEllipsize(f"Analyzing artists: {percent}% done", 119), end="\r")
				lastPercent = percent
			compareArtist = artistList[j]
			compareArtistLower = artistLowerList[j]
			if artistLower == compareArtistLower and artist != compareArtist:
				error = f"Artist \"{artist}\" has a case variation: \"{compareArtist}\"."
				songErrors.append(error)
	songProgressCount = round((songCount*songCount)/2)
	counter = 0
	lastPercent = -1
	for i in range(0, songCount):
		songFile = files[i]
		songTitle = songFile.title
		songTitleLower = songFile.lowerTitle
		firstletter = songTitle[0]
		if firstletter.isalpha() and firstletter.islower():
			if not isExemptFromLowerCaseCheck(songTitle):
				error = f"Title \"{songTitle}\" is not capitalised."
				songErrors.append(error)
		for j in range(i+1, songCount):
			counter += 1
			percent = round((counter/songProgressCount)*100.0)
			if percent > lastPercent:
				print(padOrEllipsize(f"Analyzing song titles (simple analysis): {percent}% done", 119), end="\r")
				lastPercent = percent
			compareTitle = files[j].title
			compareTitleLower = files[j].lowerTitle
			if songTitle != compareTitle:
				if songTitleLower == compareTitleLower:
					error = f"Title \"{songTitle}\" has a case variation: \"{compareTitle}\"."
					songErrors.append(error)
	lastPercent = -1
	counter = 0
	songProgressCount = len(dictionary)
	if fullanalysis:
		for artist, songDict in dictionary.items():
			counter += 1
			percent = round((counter/songProgressCount)*100.0)
			if percent > lastPercent:
				print(padOrEllipsize(f"Analyzing song titles (complex analysis): {percent}% done"), end="\r")
				lastPercent = percent
			keys = list(songDict.keys())
			for i in range(0, len(keys)):
				for j in range(i+1, len(keys)):
					if not isExemptFromSimilarityCheck(keys[i], keys[j]):
						similarityCalc = similarity(keys[i], keys[j])
						if similarityCalc < 1.0 and similarityCalc > 0.9:
							error = f"Title \"{keys[i]}\" looks very similar to \"{keys[j]}\"."
							songErrors.append(error)

# Checks two strings for similarity.
def similarity(s1, s2):
	longer = s1
	shorter = s2
	if len(s1) < len(s2):
		longer = s2
		shorter = s1
	longerLength = len(longer)
	if longerLength == 0:
		return 1.0
	return (longerLength - levenshtein(longer, shorter)) / longerLength

# Thread that periodically writes a random karaoke suggestion to a file.
def randomSongSuggestionGeneratorThread():
	global errors
	global stopSuggestions
	random.seed()
	counter = 0
	while not stopSuggestions:
		if counter == 0:
			counter = 20
			if len(karaokeDictionary) > 0:
				artistKeys = list(karaokeDictionary.keys())
				randomArtistIndex = random.randrange(len(karaokeDictionary))
				artistString = artistKeys[randomArtistIndex]
				artistDict = karaokeDictionary[artistString]
				randomSongIndex = random.randrange(len(artistDict))
				songKeys = list(artistDict.keys())
				songString = songKeys[randomSongIndex]
				suggestionString = f"{artistString}\n{songString}\n"
				try:
					with open(randomSuggestionsFilename, mode="w", encoding="utf-8") as f:
						f.writelines(suggestionString)
				except PermissionError:
					errors.append("Failed to write suggestion file.")
		else:
			counter -= 1
		sleep(0.5)

# Function to stop the suggestion thread.
def stopSuggestionThread():
	global suggestorThread
	global stopSuggestions
	if not suggestorThread is None:
		stopSuggestions = True
		suggestorThread.join()
	stopSuggestions = False

# Function to start the suggestion thread.
def startSuggestionThread():
	global suggestorThread
	stopSuggestionThread()
	suggestorThread = threading.Thread(
		target=randomSongSuggestionGeneratorThread)
	suggestorThread.daemon = True
	suggestorThread.start()

# Analyse set of files for duplicates, filename errors, etc, and report results.
def analyzeFilesPerCategory(full,songErrors,duplicates,files,dictionary,dupFilename,errFilename,descr):
	global errors
	dups=[]
	errs=[]
	print(padOrEllipsize(f"Analyzing {descr} files...", 119))
	analyzeFileSet(files,dictionary,full,errs,dups)
	duplicates.extend(dups)
	songErrors.extend(errs)
	try:
		with open(f"{dataFilesPath}\\{dupFilename}", mode="w", encoding="utf-8") as f:
			for duplicate in dups:
				f.writelines(duplicate.artist+" - "+duplicate.title+"\n")
	except PermissionError:
		errors.append("Failed to write duplicates file.")
	try:
		with open(f"{dataFilesPath}\\{errFilename}", mode="w", encoding="utf-8") as f:
			for songError in errs:
				f.writelines(f"{songError}\n")
	except PermissionError:
		errors.append("Failed to write artist or title errors file.")

# Analyses both the karaoke and music file sets for errors.
def analyzeFiles(full,songErrors,duplicates):
	global musicDictionary
	global karaokeDictionary
	analyzeFilesPerCategory(full,songErrors,duplicates,musicFiles,musicDictionary,musicDuplicatesFilename,musicErrorsFilename,"music")
	analyzeFilesPerCategory(full,songErrors,duplicates,karaokeFiles,karaokeDictionary,karaokeDuplicatesFilename,karaokeErrorsFilename,"karaoke")

# Tries to parse a karaoke file, adding it to a collection if successful.
def scanKaraokeFile(root,file,fileCollection,secondaryFileCollection,filenameErrors):
	if file.lower().endswith(".kzp"):
		karaokeFile = parseKaraokeFilename(root+"\\"+file, file)
		if karaokeFile is None:
			filenameErrors.append(file)
		else:
			fileCollection.append(karaokeFile)

# Tries to parse a music file, adding it to a collection if successful.
def scanMusicFile(root,file,fileCollection,secondaryFileCollection,filenameErrors):
	fileLower = file.lower()
	if fileLower.endswith(".mp3") or fileLower.endswith(".m4a"):
		fileWithoutExtension = fileLower[0:-4]
		if fileWithoutExtension in backgroundMusicPlaylist:
			secondaryFileCollection.append(root+"\\"+file)
			backgroundMusicPlaylist.remove(fileWithoutExtension)
		musicFile = parseMusicFilename(root+"\\"+file, file)
		if musicFile is None:
			filenameErrors.append(file)
		else:
			fileCollection.append(musicFile)

# Scans the files in one or more folders.
def scanFiles(filePaths,scanFileFunction,secondaryFileCollection):
	scannedFiles=[]
	filenameErrors=[]
	for filePath in filePaths:
		for root, _, files in walk(filePath):
			print(padOrEllipsize(f"Scanning {root}", 119), end="\r")
			for file in files:
				scanFileFunction(root,file,scannedFiles,secondaryFileCollection,filenameErrors)
	return scannedFiles,filenameErrors

# Writes a list of strings to a text file.
def writeTextFile(itemList,path):
	global errors
	try:
		with open(path, mode="w", encoding="utf-8") as f:
			for item in itemList:
				f.writelines(f"{item}\n")
	except PermissionError:
		errors.append(f"Failed to write {path}.")

# Builds the karaoke and music lists by analysing folder contents.
def buildSongLists(params):
	global karaokeDictionary
	global musicDictionary
	global karaokeFiles
	global musicFiles
	global errors
	getBackgroundMusicPlaylist()
	backgroundMusic=[]
	karaokeFilenameErrors=[]
	musicFilenameErrors=[]
	karaokeFiles=[]
	musicFiles=[]
	quickanalyze = len(params) > 0 and (params[0] == "quickanalyze" or params[0] == "q")
	fullanalyze = len(params) > 0 and (params[0] == "analyze" or params[0] == "a")
	if not karaokeFilesPaths is None:
		karaokeFiles, karaokeFilenameErrors=scanFiles(karaokeFilesPaths,scanKaraokeFile,None)
	else:
		errors.append("KaraokeFilesPath was not specified.")
	if not musicFilesPaths is None:
		musicFiles, musicFilenameErrors=scanFiles(musicFilesPaths,scanMusicFile,backgroundMusic)
	else:
		errors.append("MusicFilesPath was not specified.")
	filenameErrors = karaokeFilenameErrors+musicFilenameErrors
	writeTextFile(filenameErrors,dataFilesPath+"\\"+filenameErrorsFilename)
	# Whatever's left in the background music playlist will be missing files.
	writeTextFile(backgroundMusicPlaylist,dataFilesPath+"\\"+missingPlaylistEntriesFilename)
	writeTextFile(backgroundMusic,backgroundMusicFilename)
	buildDictionaries()
	startSuggestionThread()
	anythingToReport = len(filenameErrors) > 0 or len(backgroundMusicPlaylist)>0
	duplicates=[]
	songErrors=[]
	if quickanalyze or fullanalyze:
		analyzeFiles(fullanalyze,songErrors,duplicates)
		anythingToReport = anythingToReport or len(songErrors)>0 or len(duplicates)>0
	if anythingToReport:
		scanCompleteMessage=padOrEllipsize("Scan complete.", 69)
		print(f"{Fore.WHITE}{Style.BRIGHT}{scanCompleteMessage}")
		print(f"{Fore.RED}{Style.BRIGHT}Bad filenames:{Style.RESET_ALL} {len(filenameErrors)}")
		print(f"{Fore.YELLOW}{Style.BRIGHT}Artist/title problems:{Style.RESET_ALL} {len(songErrors)}")
		print(f"{Fore.CYAN}{Style.BRIGHT}Duplicate files:{Style.RESET_ALL} {len(duplicates)}")
		print(f"{Fore.MAGENTA}{Style.BRIGHT}Missing playlist entries:{Style.RESET_ALL} {len(backgroundMusicPlaylist)}")
		try:
			input("Press Enter to continue ...")
		except EOFError:
			pass
	# Helper function for dictionary sorting.
	def getMusicFileKey(file):
		return file.artist
	musicFiles.sort(key=getMusicFileKey)
	karaokeFiles.sort(key=getMusicFileKey)

# Parses command line arguments
def getSettings():
	global musicFilesPaths
	global karaokeFilesPaths
	global dataFilesPath
	lines = sys.argv
	for line in lines:
		equalsIndex = line.find("=")
		if equalsIndex != -1:
			firstBit = line[0:equalsIndex].strip().lower()
			secondBit = line[equalsIndex+1:].strip()
			if firstBit == "karaokefilespath":
				karaokeFilesPaths = secondBit.strip().split(';')
			else:
				if firstBit == "musicfilespath":
					musicFilesPaths = secondBit.strip().split(';')
				else:
					if firstBit == "datafilespath":
						dataFilesPath = secondBit.strip()


# Main execution loop
getSettings()
clear()
if(len(dataFilesPath)==0):
	print("No data folder specified.")
else:
	if not path.isdir(dataFilesPath):
		makedirs(dataFilesPath)
	if not path.isdir(appDataFolder):
		makedirs(appDataFolder)
	if path.exists(requestsFilename):
		remove(requestsFilename)
	buildSongLists([])
	state = State(appDataFolder, karaokeFiles)
	while True:
		clear()
		state.save()
		showHeader()
		print()
		showSingers()
		print()
		showSongs()
		print()
		showMessages()
		showErrors()
		print(
			f"Enter command, or type {Style.BRIGHT}help{Style.NORMAL} to see list of commands.")
		command = getCommand()
		if not command is None:
			if(processCommand(command)):
				break
	clear()
	stopSuggestionThread()