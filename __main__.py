from os import path, walk, makedirs, remove
from textdistance import levenshtein
from collections import defaultdict
from time import sleep
from colorama import Fore, Style
import random
import importlib
import threading
import sys
from commands import CommandType, parse_command
from state import State
from exemptions import get_exemptions, is_exempt_from_lower_case_check, is_exempt_from_reversal_check, is_exempt_from_similarity_check, is_exempt_from_the_check
from karaoke_file import KaraokeFile
from music_file import MusicFile
from file_pattern import parseFilePattern
from singer_column import SingerColumn
from song_selector import select_song, show_song_list
from display_functions import clear, pad_or_ellipsize
import yaml

# Default YAML config filename
DEFAULT_CONFIG_FILENAME='.yaml'
# Filename of the background music list file (just artist & titles)
BACKGROUND_MUSIC_PLAYLIST_FILENAME = "BackgroundMusicPlaylist.txt"
# Name of file that we will write to when we find malformed filenames.
FILENAME_ERRORS_FILENAME = "BadFilenames.txt"
# Name of file that we will write to when we find BackgroundMusicPlaylist entries that do not correspond
# to a known music file.
MISSING_PLAYLIST_ENTRIES_FILENAME = "MissingPlaylistEntries.txt"
# Name of file that we will write to when we find possible duplicates of music files.
MUSIC_DUPLICATES_FILENAME = "MusicDuplicates.txt"
# Name of file that we will write to when we find possible duplicates of karaoke files.
KARAOKE_DUPLICATES_FILENAME = "KaraokeDuplicates.txt"
# Name of file that we will write to when we find karaoke files with artist and/or title problems.
KARAOKE_ERRORS_FILENAME = "KaraokeArtistAndTitlesProblems.txt"
# Name of file that we will write to when we find music files with artist and/or title problems.
MUSIC_ERRORS_FILENAME = "MusicArtistAndTitleProblems.txt"
# Name of file that we will write to with a list of files that we ignored
IGNORED_FILES_FILENAME = "IgnoredFiles.txt"

# The current state
state = None
# List of paths to karaoke files
karaoke_paths = []
# List of paths to music (MP3/M4A/whatever) files
music_paths = []
# Patterns for karaoke filenames
karaoke_patterns = []
# Patterns for music filenames
music_patterns = []
# Path to the folder where data files (music playlist, exemption lists, etc) are stored
data_path = None
# Path to the temp data folder. We will write "temporary" data here, like the persistent state, request queue, etc.
temp_data_path = None
# Path to the current music requests file
requests_filename = None
# Path to the background music list (list of paths of files that match the BackgroundMusicPlaylist entries)
background_music_filename = None
# Path of file to which we will periodically write a random karaoke artist & song title, for on-screen
# suggestions.
random_suggestions_filename = None
# Current background music playlist (strings from the BackgroundMusicPlaylist file)
background_music_playlist = set([])
# List of karaoke files (KaraokeFile objects)
karaoke_files = []
# List of music files (MusicFile objects)
music_files = []
# Dictionary of karaoke files. Key is artist, value is another dictionary of karaoke files
# where the key is the song title, and the value is a list of tracks from one or more vendors.
karaoke_dictionary = None
# Dictionary of music files. Key is artist, value is another dictionary of music files
# where the key is the song title, and the value is a list of tracks with that title.
music_dictionary = None
# Thread that will periodically choose a random karaoke file and write it to the suggestion file.
suggestor_thread = None
# Flag to stop the suggestion thread.
stop_suggestions = False
# List of errors from last command
errors = []
# List of informational messages from last command
messages = []

# Shows onscreen help when the user types "help"
def show_help():
	clear()
	show_header()
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
def cue_song(params, errors):
	global messages
	if not any(params):
		errors.append("Not enough arguments. Expected song search string.")
	else:
		song = select_song(params[0], music_files)
		if not song is None:
			messages.append(f"Added \"{song.title}\" by {song.artist} to the requests queue.")
			try:
				with open(requests_filename, mode="a", encoding="utf-8") as f:
					f.write(song.path+"\n")
			except PermissionError:
				errors.append("Failed to write to requests file.")
			if len(params)>1:
				if params[1]=="a" or params[1]=="add":
					try:
						with open(path.join(data_path,BACKGROUND_MUSIC_PLAYLIST_FILENAME), mode="a", encoding="utf-8") as f:
							f.write(f"{song.artist} - {song.title}\n")
					except PermissionError:
						errors.append("Failed to append to background music playlist file.")

# Prints the app header
def show_header():
	print(f'{Fore.GREEN}{Style.BRIGHT}Karaoke Manager v1.0{Style.RESET_ALL} ({len(karaoke_files)}/{len(music_files)} karaoke/music files found)')

# Splits a collection into smaller collections of the given size
def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]

# Print the current list of singers. Groups them into columns.
def show_singers():
	columnSize = 10
	singersWithRequests = state.getSingersDisplayList()
	if not any(singersWithRequests):
		print("No singers.")
	else:
		columnsOfSingers = []
		dictionary = [{'chunk': chunk, 'index': i} for i, chunk in enumerate(chunks(singersWithRequests, columnSize))]
		columnsOfSingers = list(map(lambda item: SingerColumn((item['index']*columnSize)+1, item['chunk']), dictionary))
		for row in range(0, min(len(singersWithRequests), columnSize)):
			print(*map(lambda singerColumn: singerColumn.get_row_text(row), columnsOfSingers))

# Print the list of songs for the current singer, or whatever singer
# has been flagged as the current "active list" singer.
def show_songs():
	activeSinger = state.get_active_song_list_singer()
	if activeSinger is None:
		print(f"{Fore.MAGENTA}No current singer selected.{Style.RESET_ALL}")
	else:
		isSongListSingerNext = (activeSinger == state.next_singer())
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
				print(f"{songIndex}: {song.file.get_song_list_text(song.key_change)}")
			else:
				print(f"{songIndex}: {song.file.get_song_list_text()}")

# Processes the given command.
# Returns true if the command is to quit the app.
def process_command(command, driver):
	global state
	global errors
	if command.command_type == CommandType.HELP:
		show_help()
	elif command.command_type == CommandType.QUIT:
		return True
	elif command.command_type == CommandType.ADD:
		state = state.add(command.params, karaoke_files, errors)
	elif command.command_type == CommandType.INSERT:
		state = state.insert(command.params, karaoke_files, errors)
	elif command.command_type == CommandType.MOVE:
		state = state.move(command.params, errors)
	elif command.command_type == CommandType.DELETE:
		state = state.delete(command.params, errors)
	elif command.command_type == CommandType.LIST:
		state = state.list(command.params, errors)
	elif command.command_type == CommandType.UNDO:
		state = state.undo(errors)
	elif command.command_type == CommandType.REDO:
		state = state.redo(errors)
	elif command.command_type == CommandType.SCAN:
		build_song_lists(command.params)
	elif command.command_type == CommandType.ZAP:
		state = state.clear()
	elif command.command_type == CommandType.NAME:
		state = state.rename_singer(command.params, errors)
	elif command.command_type == CommandType.PLAY:
		state = state.play(command.params, True, driver, errors)
	elif command.command_type == CommandType.FILLER:
		state = state.play(command.params, False, errors)
	elif command.command_type == CommandType.KEY:
		state = state.change_song_key(command.params, errors)
	elif command.command_type == CommandType.CUE:
		cue_song(command.params, errors)
	elif command.command_type == CommandType.SEARCH:
		show_song_list(command.params[0], karaoke_files, False)
	elif command.command_type == CommandType.MUSIC_SEARCH:
		show_song_list(command.params[0], music_files, False)
	return False

# Asks the user for a command, and parses it
def get_command():
	global errors
	try:
		command = input(":")
	except EOFError:
		pass
	command = command.strip()
	if len(command) > 0:
		parsedCommand = parse_command(command, errors)
		return parsedCommand
	return None

# Shows any errors from the previous command
def show_errors():
	global errors
	for error in errors:
		print(f'{Fore.RED}{Style.BRIGHT}{error}{Style.RESET_ALL}')
	errors = []

# Shows any messages from the previous command
def show_messages():
	global messages
	for message in messages:
		print(f'{Fore.YELLOW}{Style.BRIGHT}{message}{Style.RESET_ALL}')
	messages = []

# Reads the background music playlist into memory
def get_background_music_playlist():
	global background_music_playlist
	background_music_playlist = set([])
	backgroundMusicFilePath=path.join(data_path,BACKGROUND_MUSIC_PLAYLIST_FILENAME)
	if path.isfile(backgroundMusicFilePath):
		with open(backgroundMusicFilePath, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				line = line.strip()
				if(len(line) > 0):
					background_music_playlist.add(line.lower())

# Builds the dictionaries of karaoke and music tracks
def build_dictionaries():
	global music_dictionary
	global karaoke_dictionary
	karaoke_dictionary = defaultdict()
	for songFile in karaoke_files:
		karaoke_dictionary.setdefault(songFile.artist, defaultdict()).setdefault(
			songFile.title, []).append(songFile)
	music_dictionary = defaultdict()
	for songFile in music_files:
		music_dictionary.setdefault(songFile.artist, defaultdict()).setdefault(
			songFile.title, []).append(songFile)

# Scans a list of files for potential duplicates, bad filenames, etc.
def analyze_file_set(files,dictionary,fullanalysis,songErrors,duplicates):
	global errors
	get_exemptions(data_path, errors)
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
			print(pad_or_ellipsize(f"Looking for duplicates: {percent}% done", 119), end="\r")
			lastPercent = percent
		for songCollection in songDict.values():
			if len(songCollection)>1:
				duplicates.extend(songCollection[1:])
	for song in files:
		if not song.artist in artists:
			artists.add(song.artist)
			artistList.append(song.artist)
			artistLowerList.append(song.lower_artist)
	for artist in artists:
		firstletter = artist[0]
		if firstletter.isalpha() and firstletter.islower():
			if not is_exempt_from_lower_case_check(artist):
				error = f"Artist \"{artist}\" is not capitalised."
				songErrors.append(error)
		if artist.startswith("The "):
			if artist[4:] in artists and not is_exempt_from_the_check(artist):
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
				if not is_exempt_from_reversal_check(bit1, bit2):
					reverseCheck = bit2+" & "+bit1
					if reverseCheck in artists:
						error = f"Artist \"{artist}\" also appears as \"{reverseCheck}\"."
						songErrors.append(error)
		for j in range(i+1, artistCount):
			counter += 1
			percent = round((counter/artistProgressCount)*100.0)
			if percent > lastPercent:
				print(pad_or_ellipsize(f"Analyzing artists: {percent}% done", 119), end="\r")
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
		songTitleLower = songFile.lower_title
		firstletter = songTitle[0]
		if firstletter.isalpha() and firstletter.islower():
			if not is_exempt_from_lower_case_check(songTitle):
				error = f"Title \"{songTitle}\" is not capitalised."
				songErrors.append(error)
		for j in range(i+1, songCount):
			counter += 1
			percent = round((counter/songProgressCount)*100.0)
			if percent > lastPercent:
				print(pad_or_ellipsize(f"Analyzing song titles (simple analysis): {percent}% done", 119), end="\r")
				lastPercent = percent
			compareTitle = files[j].title
			compareTitleLower = files[j].lower_title
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
				print(pad_or_ellipsize(f"Analyzing song titles (complex analysis): {percent}% done"), end="\r")
				lastPercent = percent
			keys = list(songDict.keys())
			for i in range(0, len(keys)):
				for j in range(i+1, len(keys)):
					if not is_exempt_from_similarity_check(keys[i], keys[j]):
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
def random_song_suggestion_generator_thread():
	global errors
	global stop_suggestions
	random.seed()
	counter = 0
	while not stop_suggestions:
		if counter == 0:
			counter = 20
			if any(karaoke_dictionary):
				artistKeys = list(karaoke_dictionary.keys())
				randomArtistIndex = random.randrange(len(karaoke_dictionary))
				artistString = artistKeys[randomArtistIndex]
				artistDict = karaoke_dictionary[artistString]
				randomSongIndex = random.randrange(len(artistDict))
				songKeys = list(artistDict.keys())
				songString = songKeys[randomSongIndex]
				suggestionString = f"{artistString}\n{songString}\n"
				try:
					with open(random_suggestions_filename, mode="w", encoding="utf-8") as f:
						f.writelines(suggestionString)
				except PermissionError:
					errors.append("Failed to write suggestion file.")
		else:
			counter -= 1
		sleep(0.5)

# Function to stop the suggestion thread.
def stop_suggestion_thread():
	global suggestor_thread
	global stop_suggestions
	if not suggestor_thread is None:
		stop_suggestions = True
		suggestor_thread.join()
	stop_suggestions = False

# Function to start the suggestion thread.
def start_suggestion_thread():
	global suggestor_thread
	stop_suggestion_thread()
	suggestor_thread = threading.Thread(
		target=random_song_suggestion_generator_thread)
	suggestor_thread.daemon = True
	suggestor_thread.start()

# Analyse set of files for duplicates, filename errors, etc, and report results.
def analyze_files_per_category(full,songErrors,duplicates,files,dictionary,dupFilename,errFilename,descr):
	global errors
	dups=[]
	errs=[]
	print(pad_or_ellipsize(f"Analyzing {descr} files...", 119))
	analyze_file_set(files,dictionary,full,errs,dups)
	duplicates.extend(dups)
	songErrors.extend(errs)
	try:
		with open(path.join(data_path,dupFilename), mode="w", encoding="utf-8") as f:
			for duplicate in dups:
				f.writelines(duplicate.artist+" - "+duplicate.title+"\n")
	except PermissionError:
		errors.append("Failed to write duplicates file.")
	try:
		with open(path.join(data_path,errFilename), mode="w", encoding="utf-8") as f:
			for songError in errs:
				f.writelines(f"{songError}\n")
	except PermissionError:
		errors.append("Failed to write artist or title errors file.")

# Analyses both the karaoke and music file sets for errors.
def analyze_files(full,songErrors,duplicates):
	global music_dictionary
	global karaoke_dictionary
	analyze_files_per_category(full,songErrors,duplicates,music_files,music_dictionary,MUSIC_DUPLICATES_FILENAME,MUSIC_ERRORS_FILENAME,"music")
	analyze_files_per_category(full,songErrors,duplicates,karaoke_files,karaoke_dictionary,KARAOKE_DUPLICATES_FILENAME,KARAOKE_ERRORS_FILENAME,"karaoke")

def create_karaoke_file(path, groupMap):
	vendor=groupMap["vendor"]
	if vendor is None:
		vendor="UNKNOWN"
	return KaraokeFile(path,groupMap["artist"],groupMap["title"],vendor)

def create_music_file(path, groupMap):
	return MusicFile(path,groupMap["artist"],groupMap["title"])

def parse_filename(filePath, filename, patterns, errors, ignored, fileBuilder):
	nameWithoutExtension, extension = path.splitext(filename)
	extension=extension.strip('.')
	validPatterns=list(filter(lambda pattern: pattern.extensionMatches(extension), patterns))
	if any(validPatterns):
		for pattern in validPatterns:
			groupMap = pattern.parseFilename(nameWithoutExtension)
			if any(groupMap):
				file=fileBuilder(filePath, groupMap)
				if not file is None:
					return file
		errors.append(filename)
	else:
		ignored.append(filename)
	return None

# Tries to parse a karaoke file, adding it to a collection if successful.
def scan_karaoke_file(root, file, fileCollection, secondaryFileCollection, filenameErrors, ignoredFiles):
	karaokeFile = parse_filename(path.join(root,file), file, karaoke_patterns, filenameErrors, ignoredFiles, create_karaoke_file)
	if not karaokeFile is None:
		fileCollection.append(karaokeFile)

# Tries to parse a music file, adding it to a collection if successful.
def scan_music_file(root, file, fileCollection, secondaryFileCollection, filenameErrors, ignoredFiles):
	musicFile = parse_filename(path.join(root,file), file, music_patterns, filenameErrors, ignoredFiles, create_music_file)
	if not musicFile is None:
		fileWithoutExtension = file[0:-4]
		if fileWithoutExtension in background_music_playlist:
			secondaryFileCollection.append(path.join(root,file))
			background_music_playlist.remove(fileWithoutExtension)
		fileCollection.append(musicFile)

# Scans the files in one or more folders.
def scan_files(filePaths,scanFileFunction,secondaryFileCollection):
	scannedFiles=[]
	filenameErrors=[]
	ignoredFiles=[]
	for filePath in filePaths:
		for root, _, files in walk(filePath):
			print(pad_or_ellipsize(f"Scanning {root}", 119), end="\r")
			for file in files:
				scanFileFunction(root,file,scannedFiles,secondaryFileCollection,filenameErrors,ignoredFiles)
	return scannedFiles,filenameErrors,ignoredFiles

# Writes a list of strings to a text file.
def write_text_file(itemList,path):
	global errors
	try:
		with open(path, mode="w", encoding="utf-8") as f:
			for item in itemList:
				f.writelines(f"{item}\n")
	except PermissionError:
		errors.append(f"Failed to write {path}.")

# Builds the karaoke and music lists by analysing folder contents.
def build_song_lists(params):
	global karaoke_dictionary
	global music_dictionary
	global karaoke_files
	global music_files
	global errors
	get_background_music_playlist()
	backgroundMusic=[]
	karaokeFilenameErrors=[]
	musicFilenameErrors=[]
	ignoredFiles=[]
	karaoke_files=[]
	music_files=[]
	quickanalyze = any(params) and (params[0] == "quickanalyze" or params[0] == "q")
	fullanalyze = any(params) and (params[0] == "analyze" or params[0] == "a")
	karaoke_files, karaokeFilenameErrors, ignoredKaraokeFiles=scan_files(karaoke_paths,scan_karaoke_file,None)
	music_files, musicFilenameErrors, ignoredMusicFiles=scan_files(music_paths,scan_music_file,backgroundMusic)
	filenameErrors = karaokeFilenameErrors+musicFilenameErrors
	ignoredFiles = ignoredKaraokeFiles+ignoredMusicFiles
	write_text_file(filenameErrors,path.join(data_path,FILENAME_ERRORS_FILENAME))
	write_text_file(ignoredFiles,path.join(data_path,IGNORED_FILES_FILENAME))
	# Whatever's left in the background music playlist will be missing files.
	write_text_file(background_music_playlist,path.join(data_path,MISSING_PLAYLIST_ENTRIES_FILENAME))
	write_text_file(backgroundMusic,background_music_filename)
	build_dictionaries()
	start_suggestion_thread()
	anythingToReport = any(filenameErrors) or any(background_music_playlist)
	duplicates=[]
	songErrors=[]
	if quickanalyze or fullanalyze:
		analyze_files(fullanalyze,songErrors,duplicates)
		anythingToReport = anythingToReport or any(songErrors) or any(duplicates)
	if anythingToReport:
		scanCompleteMessage=pad_or_ellipsize("Scan complete.", 119)
		print(f"{Fore.WHITE}{Style.BRIGHT}{scanCompleteMessage}")
		print(f"{Fore.RED}{Style.BRIGHT}Bad filenames:{Style.RESET_ALL} {len(filenameErrors)}")
		print(f"{Fore.GREEN}{Style.BRIGHT}Ignored files:{Style.RESET_ALL} {len(ignoredFiles)}")
		print(f"{Fore.YELLOW}{Style.BRIGHT}Artist/title problems:{Style.RESET_ALL} {len(songErrors)}")
		print(f"{Fore.CYAN}{Style.BRIGHT}Duplicate files:{Style.RESET_ALL} {len(duplicates)}")
		print(f"{Fore.MAGENTA}{Style.BRIGHT}Missing playlist entries:{Style.RESET_ALL} {len(background_music_playlist)}")
		try:
			input("Press Enter to continue ...")
		except EOFError:
			pass
	# Helper function for dictionary sorting.
	def getMusicFileKey(file):
		return file.artist
	music_files.sort(key=getMusicFileKey)
	karaoke_files.sort(key=getMusicFileKey)

def get_paths_and_patterns(config,section):
	paths=[]
	patterns=[]
	if section in config:
		sectionConfig=config[section]
		if "paths" in sectionConfig:
			paths=sectionConfig["paths"]
		if "patterns" in sectionConfig:
			unparsedPatterns=sectionConfig["patterns"]
			patterns=list(map(lambda unparsedPattern: parseFilePattern(unparsedPattern), unparsedPatterns))
	return paths,patterns

# Parses command line arguments
def get_settings(configPath):
	global music_paths
	global karaoke_paths
	global data_path
	global temp_data_path
	global karaoke_patterns
	global music_patterns
	global requests_filename
	global background_music_filename
	global random_suggestions_filename
	global BACKGROUND_MUSIC_PLAYLIST_FILENAME
	if path.isfile(configPath):
		config = yaml.safe_load(open(configPath))
		if not config is None:
			dataFilesPath=config.get('dataPath')
			tempDataFilesPath=config.get('tempDataPath')
			karaoke_paths,karaoke_patterns=get_paths_and_patterns(config,"karaoke")
			music_paths,music_patterns=get_paths_and_patterns(config,"music")
			musicConfig=config.get("music")
			if not musicConfig is None:
				bgmFilename=musicConfig.get("backgroundMusicPlaylistFilename")
				if not bgmFilename is None:
					BACKGROUND_MUSIC_PLAYLIST_FILENAME=bgmFilename
			if dataFilesPath is None or len(dataFilesPath.strip())==0:
				raise Exception("'dataPath' (from YAML) must not be an empty string.")
			if tempDataFilesPath is None or len(tempDataFilesPath.strip())==0:
				raise Exception("'tempDataPath' (from YAML) must not be an empty string.")
			data_path=dataFilesPath.strip()
			temp_data_path=tempDataFilesPath.strip()
			# Path to the current music requests file
			requests_filename = path.join(temp_data_path,"KaraokeManager.musicRequests.txt")
			# Path to the background music list (list of paths of files that match the BackgroundMusicPlaylist entries)
			background_music_filename = path.join(temp_data_path,"KaraokeManager.backgroundMusic.txt")
			# Path of file to which we will periodically write a random karaoke artist & song title, for on-screen
			# suggestions.
			random_suggestions_filename = path.join(temp_data_path,"KaraokeManager.songSuggestion.txt")
			return config
		raise Exception("Failed to parse YAML configuration.")
	raise Exception("{defaultConfigFilename} not found.")

def create_driver(config, errors):
	driverConfig=config.get("driver")
	if driverConfig is None:
		errors.append("No 'driver' section in configuration file.")
	else:
		driverClassString=driverConfig.get("class")
		if driverClassString is None or driverClassString=="":
			errors.append("No driver class specified in configuration file.")
		else:
			driverSpecificConfig=driverConfig.get(driverClassString)
			if driverSpecificConfig is None:
				errors.append("No driver-specific config section found in configuration file.")
			else:
				components = driverClassString.split('.')
				if len(components)<3:
					errors.append("Driver class string should be in the format 'packagename.modulename.classname'")
				else:
					upperBound=len(components)-1
					package=components[0]
					module=".".join(components[1:upperBound])
					className=components[upperBound]
					module = importlib.import_module(module, package)
					driverClass = getattr(module, className)
					return driverClass(driverSpecificConfig, errors)
	return None

# Main execution loop
clear()
configPath=DEFAULT_CONFIG_FILENAME
if len(sys.argv)>1:
	configPath=sys.argv[1]
try:
	config=get_settings(configPath)
except Exception as e:
	print(f"{Fore.RED}Error parsing the configuration file: {e}{Style.RESET_ALL}")
	exit(1)

if not path.isdir(temp_data_path):
	makedirs(temp_data_path)
if not path.isdir(data_path):
	makedirs(data_path)
if path.exists(requests_filename):
	remove(requests_filename)

driver=create_driver(config, errors)

build_song_lists([])
state = State(temp_data_path, karaoke_files, errors)
while True:
	clear()
	state.save(errors)
	show_header()
	print()
	show_singers()
	print()
	show_songs()
	print()
	show_messages()
	show_errors()
	print(
		f"Enter command, or type {Style.BRIGHT}help{Style.NORMAL} to see list of commands.")
	command = get_command()
	if not command is None:
		if(process_command(command, driver)):
			break
clear()
stop_suggestion_thread()