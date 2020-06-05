from os import environ, system, name, path, walk, startfile, getenv, makedirs, remove
from textdistance import levenshtein
from collections import defaultdict
from time import sleep
from colorama import Fore, Style
from enum import Enum, auto
from copy import deepcopy
import ctypes
import random
import threading
import sys
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MAPVK_VK_TO_VSC = 0

# msdn.microsoft.com/en-us/library/dd3757312
VK_TAB = 0x09
VK_MENU = 0x12
VK_CTRL = 0x11
VK_SHIFT = 0x10
VK_A = 0x41
VK_P = 0x50
VK_Q = 0x51
VK_R = 0x52
VK_Z = 0x5A
VK_UP = 0x26
VK_DOWN = 0x28

# C struct definitions

wintypes.ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
	_fields_ = (("dx",			wintypes.LONG),
				("dy",			wintypes.LONG),
				("mouseData",	wintypes.DWORD),
				("dwFlags",		wintypes.DWORD),
				("time",		wintypes.DWORD),
				("dwExtraInfo", wintypes.ULONG_PTR))


class KEYBDINPUT(ctypes.Structure):
	_fields_ = (("wVk",			wintypes.WORD),
				("wScan",		wintypes.WORD),
				("dwFlags",		wintypes.DWORD),
				("time",		wintypes.DWORD),
				("time",		wintypes.DWORD),
				("dwExtraInfo", wintypes.ULONG_PTR))

	def __init__(self, *args, **kwds):
		super(KEYBDINPUT, self).__init__(*args, **kwds)
		# some programs use the scan code even if KEYEVENTF_SCANCODE
		# isn't set in dwFflags, so attempt to map the correct code.
		if not self.dwFlags & KEYEVENTF_UNICODE:
			self.wScan = user32.MapVirtualKeyExW(self.wVk,
												 MAPVK_VK_TO_VSC, 0)


class HARDWAREINPUT(ctypes.Structure):
	_fields_ = (("uMsg",	wintypes.DWORD),
				("wParamL", wintypes.WORD),
				("wParamH", wintypes.WORD))


class INPUT(ctypes.Structure):
	class _INPUT(ctypes.Union):
		_fields_ = (("ki", KEYBDINPUT),
					("mi", MOUSEINPUT),
					("hi", HARDWAREINPUT))
	_anonymous_ = ("_input",)
	_fields_ = (("type",   wintypes.DWORD),
				("_input", _INPUT))


LPINPUT = ctypes.POINTER(INPUT)


def _check_count(result, func, args):
	if result == 0:
		raise ctypes.WinError(ctypes.get_last_error())
	return args


user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT,  # nInputs
							 LPINPUT,		# pInputs
							 ctypes.c_int)  # cbSize


def PressKey(hexKeyCode):
	x = INPUT(type=INPUT_KEYBOARD,
			  ki=KEYBDINPUT(wVk=hexKeyCode))
	user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def ReleaseKey(hexKeyCode):
	x = INPUT(type=INPUT_KEYBOARD,
			  ki=KEYBDINPUT(wVk=hexKeyCode,
							dwFlags=KEYEVENTF_KEYUP))
	user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def pitchDown():
	PressKey(VK_SHIFT)
	PressKey(VK_CTRL)
	PressKey(VK_A)
	ReleaseKey(VK_A)
	sleep(0.25)
	ReleaseKey(VK_SHIFT)
	ReleaseKey(VK_CTRL)


def pitchUp():
	PressKey(VK_SHIFT)
	PressKey(VK_CTRL)
	PressKey(VK_Q)
	ReleaseKey(VK_Q)
	sleep(0.25)
	ReleaseKey(VK_SHIFT)
	ReleaseKey(VK_CTRL)


def resetPitch():
	PressKey(VK_SHIFT)
	PressKey(VK_CTRL)
	PressKey(VK_Z)
	ReleaseKey(VK_Z)
	sleep(0.25)
	ReleaseKey(VK_SHIFT)
	ReleaseKey(VK_CTRL)


firstSong = True
karaokeFilesPaths = None
musicFilesPaths = None
dataFolder = getenv("APPDATA")+"\\FullHouse Entertainment\\KaraokeManager"
stateFilename = dataFolder+"\\KaraokeManager.state.txt"
backgroundMusicPlaylistFilename = "BackgroundMusicPlaylist.txt"
requestsFilename = dataFolder+"\\KaraokeManager.musicRequests.txt"
backgroundMusicFilename = dataFolder+"\\KaraokeManager.backgroundMusic.txt"
reversalExemptionsFilename = "ReversalExemptions.txt"
theExemptionsFilename = "TheExemptions.txt"
lowerCaseExemptionsFilename = "LowerCaseExemptions.txt"
similarityExemptionsFilename = "SimilarityExemptions.txt"
filenameErrorsFilename = "BadFilenames.txt"
missingPlaylistEntriesFilename = "MissingPlaylistEntries.txt"
musicDuplicatesFilename = "MusicDuplicates.txt"
karaokeDuplicatesFilename = "KaraokeDuplicates.txt"
karaokeErrorsFilename = "KaraokeArtistAndTitlesProblems.txt"
musicErrorsFilename = "MusicArtistAndTitleProblems.txt"
singersQueueFilename = dataFolder+"\\KaraokeManager.singers.txt"
randomSuggestionsFilename = dataFolder+"\\KaraokeManager.songSuggestion.txt"

SCREENHEIGHT = 30
state = None
filenameErrorCount = 0
similarityExemptions = []
lowerCaseExemptions = []
reversalExemptions = []
theExemptions=set([])
backgroundMusicPlaylist = set([])
karaokeFiles = []
musicFiles = []
errors = []
messages = []
karaokeDictionary = None
musicDictionary = None
suggestorThread = None
stopSuggestions = False
quit = False


class CommandType(Enum):
	ADD = auto()
	INSERT = auto()
	MOVE = auto()
	DELETE = auto()
	LIST = auto()
	PLAY = auto()
	SCAN = auto()
	ZAP = auto()
	HELP = auto()
	QUIT = auto()
	UNDO = auto()
	REDO = auto()
	SEARCH = auto()
	NAME = auto()
	KEY = auto()
	FILLER = auto()
	MUSICSEARCH = auto()
	CUE = auto()


class ReversalExemption:
	artist1 = None
	artist2 = None

	def __init__(self, artist1, artist2):
		self.artist1 = artist1
		self.artist2 = artist2

	def matches(self, artist1, artist2):
		return (self.artist1 == artist1 and self.artist2 == artist2) or (self.artist1 == artist2 and self.artist2 == artist1)


class SimilarityExemption:
	title1 = None
	title2 = None

	def __init__(self, title1, title2):
		self.title1 = title1
		self.title2 = title2

	def matches(self, title1, title2):
		return (self.title1 == title1 and self.title2 == title2) or (self.title1 == title2 and self.title2 == title1)


class CommandDefinition:
	commandType = None
	commandString = None

	def __init__(self, commandType, commandString):
		self.commandType = commandType
		self.commandString = commandString


commands = [
	CommandDefinition(CommandType.ADD, "add"),
	CommandDefinition(CommandType.INSERT, "insert"),
	CommandDefinition(CommandType.MOVE, "move"),
	CommandDefinition(CommandType.DELETE, "delete"),
	CommandDefinition(CommandType.LIST, "list"),
	CommandDefinition(CommandType.PLAY, "play"),
	CommandDefinition(CommandType.SCAN, "scan"),
	CommandDefinition(CommandType.ZAP, "zap"),
	CommandDefinition(CommandType.HELP, "help"),
	CommandDefinition(CommandType.UNDO, "undo"),
	CommandDefinition(CommandType.REDO, "redo"),
	CommandDefinition(CommandType.QUIT, "quit"),
	CommandDefinition(CommandType.KEY, "key"),
	CommandDefinition(CommandType.NAME, "name"),
	CommandDefinition(CommandType.FILLER, "filler"),
	CommandDefinition(CommandType.CUE, "cue"),
	CommandDefinition(CommandType.SEARCH, "?"),
	CommandDefinition(CommandType.MUSICSEARCH, "??")
]


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


class MusicFile:
	path = None
	title = None
	artist = None
	lowerTitle = None
	lowerArtist = None
	searchString = None

	def __init__(self, path, artist, title):
		self.path = path
		self.title = title
		self.artist = artist
		self.lowerTitle = title.lower()
		self.lowerArtist = artist.lower()
		self.searchString = (title+" "+artist).lower()

	def matches(self, searchString):
		bits = searchString.strip().split()
		matchCount = 0
		for bit in bits:
			if bit.lower() in self.searchString:
				matchCount = matchCount+1
		return matchCount == len(bits)

	def getText(self):
		artistText = padOrEllipsize(self.artist+" ", 30, ".")
		titleText = padOrEllipsize(self.title, 60, " ")
		return f"{Fore.CYAN}{Style.BRIGHT}"+artistText+f"{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}"+titleText+f"{Style.RESET_ALL}"

	def getOptionText(self):
		return self.getText()

	def getSongListText(self):
		return self.getText()


class KaraokeFile(MusicFile):
	company = None

	def __init__(self, path, artist, title, company):
		MusicFile.__init__(self, path, artist, title)
		self.company = company

	def getOptionText(self):
		result = MusicFile.getOptionText(self)
		companyText = padOrEllipsize(self.company, 20, " ")
		return result+f"{Style.BRIGHT}{Fore.YELLOW}"+companyText+f"{Style.RESET_ALL}"

	def getSongListText(self, keyChange):
		txt = MusicFile.getSongListText(self)
		if keyChange is None:
			keyChange = ""
		else:
			keyChange = "("+keyChange+")"
		return txt+f" {Fore.MAGENTA}{Style.BRIGHT}"+keyChange+f"{Style.RESET_ALL}"


class Command:
	commandType = None
	params = []

	def __init__(self, commandType, params):
		self.commandType = commandType
		self.params = params


class SongList:
	name = ''
	songs = []

	def __init__(self, name):
		self.name = name
		self.songs = []

	def writeToStateFile(self, file):
		file.writelines(self.name+"\n")
		for song in self.songs:
			song.writeToStateFile(file)

	def writeToQueueFile(self, file):
		if len(self.songs) == 0:
			indent = "\t"
		else:
			indent = ""
		file.writelines(indent+self.name+"\n")

	def getSongIndexFromID(self, id, endAllowed):
		if id.isdigit():
			songIndex = int(id)
			if songIndex <= 0 or songIndex > len(self.songs):
				errors.append(
					"Song index out of bounds: it must be between 1 and "+str(len(self.songs)))
				return None
			return songIndex-1
		id = id.lower()
		if len(self.songs) > 0:
			if id == "next" or id == "n":
				return 0
			if endAllowed:
				if id == "end" or id == "e":
					return len(self.songs)+1
		matches = []
		for i, song in enumerate(self.songs):
			if id in song.file.title.lower() or id in song.file.artist.lower():
				matches.append(i)
		if len(matches) == 0:
			errors.append("No match found for given song ID \""+id+"\"")
			return None
		if len(matches) > 1:
			errors.append(
				"Multiple matches found for given song ID \""+id+"\"")
			return None
		return matches[0]

	def moveSong(self, songToMoveID, songToMoveBeforeID):
		matchedSongToMoveIndex = self.getSongIndexFromID(songToMoveID, False)
		if not matchedSongToMoveIndex is None:
			matchedSongToMoveBeforeIndex = self.getSongIndexFromID(
				songToMoveBeforeID, True)
			if not matchedSongToMoveBeforeIndex is None:
				songToMove = self.songs[matchedSongToMoveIndex]
				del self.songs[matchedSongToMoveIndex]
				self.insertSong(matchedSongToMoveBeforeIndex, songToMove)

	def insertSong(self, position, song):
		self.songs.insert(position, song)


class Singer(SongList):
	def __init__(self, name):
		SongList.__init__(self, name)

	def writeToStateFile(self, file):
		SongList.writeToStateFile(self, file)

	def writeToQueueFile(self, file):
		SongList.writeToQueueFile(self, file)

	def getSongIndexFromID(self, id, endAllowed):
		return SongList.getSongIndexFromID(self, id, endAllowed)

	def moveSong(self, songToMoveID, songToMoveBeforeID):
		return SongList.moveSong(self, songToMoveID, songToMoveBeforeID)

	def insertSong(self, position, song):
		SongList.insertSong(self, position, song)


class State:
	singers = None
	activeSongListSingerName = None
	nextState = None
	prevState = None

	def __init__(self):
		self.load()

	def load(self):
		self.singers = []
		if path.isfile(stateFilename):
			with open(stateFilename, mode="r", encoding="utf-8") as f:
				lines = f.readlines()
				currentSinger = None
				for line in lines:
					if line.startswith("\t"):
						if not currentSinger is None:
							lineBits = line.strip().split("|")
							karaokeFile = getKaraokeFileFromPath(lineBits[0])
							keyChange = lineBits[1].strip()
							if len(keyChange) == 0:
								keyChange = None
							if not karaokeFile is None:
								currentSinger.songs.append(
									Song(karaokeFile, keyChange))
					else:
						if not currentSinger is None:
							self.singers.append(currentSinger)
						if len(line) > 0:
							currentSinger = Singer(line.strip())
				if not currentSinger is None:
					self.singers.append(currentSinger)

	def save(self):
		try:
			with open(stateFilename, mode="w", encoding="utf-8") as f:
				for singer in self.singers:
					singer.writeToStateFile(f)
		except PermissionError:
			errors.append("Failed to write state file.")
		try:
			with open(singersQueueFilename, mode="w", encoding="utf-8") as f:
				for singer in self.singers:
					singer.writeToQueueFile(f)
		except PermissionError:
			errors.append("Failed to write singer names file.")

	def getSingersDisplayList(self):
		singersCopy = self.singers.copy()
		return singersCopy

	def mutate(self):
		global state
		newState = deepcopy(self)
		self.nextState = newState
		newState.prevState = self
		state = newState
		return newState

	def getSingerIndexFromID(self, id, endAllowed, reqAllowed):
		if id.isdigit():
			singerIndex = int(id)
			if singerIndex <= 0 or singerIndex > len(self.singers):
				errors.append(
					"Singer index out of bounds: it must be between 1 and "+str(len(self.singers)))
				return None
			return singerIndex-1
		id = id.lower()
		if len(self.singers) > 0:
			if id == "next" or id == "n":
				return 0
			if id == "end" or id == "e":
				return len(self.singers)
		if id == "list" or id == "l":
			if not self.activeSongListSingerName is None:
				id = self.activeSongListSingerName.lower()
			else:
				nextSinger = self.nextSinger()
				if not nextSinger is None:
					id = nextSinger.name.lower()
				else:
					errors.append("There is no active song list to add to.")
					return None
		for i, singer in enumerate(state.singers):
			if singer.name.lower() == id:
				return i
		matches = []
		for i, singer in enumerate(state.singers):
			if id in singer.name.lower():
				matches.append(i)
		if len(matches) == 0:
			errors.append("No match found for given singer ID \""+id+"\"")
			return None
		if len(matches) > 1:
			errors.append(
				"Multiple matches found for given singer ID \""+id+"\"")
			return None
		return matches[0]

	def getSingerFromID(self, id, endAllowed, reqAllowed):
		singerIndex = self.getSingerIndexFromID(id, endAllowed, reqAllowed)
		if singerIndex is None:
			return None
		return self.singers[singerIndex]

	def addNewSinger(self, singerName, index):
		sameNameSingers = [
			singer for singer in self.singers if singer.name.lower() == singerName.lower()]
		if len(sameNameSingers) > 0:
			errors.append("Singer with name \"" +
						  singerName+"\" already exists.")
		else:
			newState = self.mutate()
			newState.singers.insert(index, Singer(singerName))

	def deleteSinger(self, singerID):
		matchedSingerIndex = self.getSingerIndexFromID(singerID, False, False)
		if not matchedSingerIndex is None:
			newState = self.mutate()
			del newState.singers[matchedSingerIndex]

	def deleteSongFromSinger(self, singerID, songID):
		matchedSingerIndex = self.getSingerIndexFromID(singerID, False, False)
		if not matchedSingerIndex is None:
			matchedSinger = state.singers[matchedSingerIndex]
			matchedSongIndex = matchedSinger.getSongIndexFromID(songID, False)
			if not matchedSongIndex is None:
				newState = self.mutate()
				del newState.singers[matchedSingerIndex].songs[matchedSongIndex]

	def insertNewSinger(self, singerName, singerID):
		matchedSingerIndex = self.getSingerIndexFromID(singerID, True, False)
		if not matchedSingerIndex is None:
			self.addNewSinger(singerName, matchedSingerIndex)

	def moveSinger(self, singerToMoveID, singerID):
		matchedSingerToMoveIndex = self.getSingerIndexFromID(
			singerToMoveID, False, False)
		if not matchedSingerToMoveIndex is None:
			matchedSingerIndex = self.getSingerIndexFromID(
				singerID, True, False)
			if not matchedSingerIndex is None:
				newState = self.mutate()
				singerToMove = newState.singers[matchedSingerToMoveIndex]
				del newState.singers[matchedSingerToMoveIndex]
				newState.singers.insert(matchedSingerIndex, singerToMove)

	def addSongForSinger(self, singerID, songTitle, keyChange, index):
		keychangeval = getKeyChangeValue(keyChange)
		if keychangeval != -99:
			matchedSinger = self.getSingerFromID(singerID, False, True)
			if not matchedSinger is None:
				karaokeSong = selectSong(songTitle, karaokeFiles)
				if not karaokeSong is None:
					if index == -1:
						index = len(matchedSinger.songs)
					newState = self.mutate()
					matchedSinger = newState.getSingerFromID(
						singerID, False, True)
					matchedSinger.insertSong(
						index, Song(karaokeSong, keyChange))

	def insertSongForSinger(self, singerID, songID, songTitle, keyChange):
		matchedSinger = self.getSingerFromID(singerID, False, True)
		if not matchedSinger is None:
			matchedSongIndex = matchedSinger.getSongIndexFromID(songID, True)
			if not matchedSongIndex is None:
				self.addSongForSinger(
					singerID, songTitle, keyChange, matchedSongIndex)

	def moveSong(self, singerID, songToMoveID, songToMoveBeforeID):
		matchedSinger = self.getSingerFromID(singerID, False, True)
		if not matchedSinger is None:
			matchedSongToMoveIndex = matchedSinger.getSongIndexFromID(
				songToMoveID, False)
			if not matchedSongToMoveIndex is None:
				matchedSongToMoveBeforeIndex = matchedSinger.getSongIndexFromID(
					songToMoveBeforeID, True)
				if not matchedSongToMoveBeforeIndex is None:
					newState = self.mutate()
					matchedSinger = newState.getSingerFromID(
						singerID, False, True)
					matchedSinger.moveSong(songToMoveID, songToMoveBeforeID)

	def add(self, params):
		paramCount = len(params)
		if paramCount == 0:
			errors.append(
				"Not enough arguments. Expected name of new singer, or existing singer name/index.")
		elif paramCount == 1:
			self.addNewSinger(params[0], len(self.singers))
		else:
			keyChange = None
			if paramCount > 2:
				keyChange = params[2]
			self.addSongForSinger(params[0], params[1], keyChange, -1)

	def insert(self, params):
		paramCount = len(params)
		if paramCount < 2:
			errors.append(
				"Not enough arguments. Expected name of new singer, or existing singer name/index.")
		elif paramCount == 2:
			self.insertNewSinger(params[0], params[1])
		elif paramCount > 2:
			keyChange = None
			if paramCount > 3:
				keyChange = params[3]
			self.insertSongForSinger(
				params[0], params[1], params[2], keyChange)

	def move(self, params):
		paramCount = len(params)
		if paramCount < 2:
			errors.append("Not enough arguments. Expected ID of singer.")
		elif paramCount == 2:
			# Move a singer in the list
			self.moveSinger(params[0], params[1])
		elif paramCount > 2:
			# Move a song in a singer's list
			self.moveSong(params[0], params[1], params[2])

	def delete(self, params):
		paramCount = len(params)
		if paramCount < 1:
			errors.append("Not enough arguments. Expected ID of singer.")
		elif paramCount == 1:
			# Delete a singer
			self.deleteSinger(params[0])
		elif paramCount > 1:
			# Delete a song from a singer
			self.deleteSongFromSinger(params[0], params[1])

	def undo(self):
		global state
		if self.prevState is None:
			errors.append("No undo history available.")
		else:
			state = state.prevState

	def redo(self):
		global state
		if self.nextState is None:
			errors.append("No redo history available.")
		else:
			state = state.nextState

	def renameSinger(self, params):
		if len(params) < 2:
			errors.append(
				"Not enough arguments. Expected singer ID and new name.")
			return
		singer = self.getSingerFromID(params[0], False, False)
		newName = params[1]
		if not singer is None:
			for singer in self.singers:
				if singer.name.lower() == newName:
					errors.append("Name \""+newName+"\" already exists.")
					return
			newState = self.mutate()
			singer = newState.getSingerFromID(params[0], False, False)
			singer.name = newName

	def clear(self):
		newState = self.mutate()
		newState.singers = []
		newState.activeSongListSingerName = None

	def nextSinger(self):
		for singer in self.singers:
			if len(singer.songs) > 0:
				return singer
		return None

	def setSongListToNextSinger(self):
		self.activeSongListSingerName = None

	def setSongListToSinger(self, singer):
		self.activeSongListSingerName = singer.name

	def list(self, params):
		if len(params) == 0:
			nextState = state.mutate()
			nextState.setSongListToNextSinger()
		else:
			singer = self.getSingerFromID(params[0], False, True)
			if not singer is None:
				nextState = state.mutate()
				nextState.setSongListToSinger(singer)

	def getActiveSongListSinger(self):
		if self.activeSongListSingerName is None:
			return self.nextSinger()
		activeSinger = [
			singer for singer in self.singers if singer.name == self.activeSongListSingerName]
		if len(activeSinger) == 0:
			self.activeSongListSingerName = None
			return self.nextSinger()
		return activeSinger[0]

	def changeSongKey(self, params):
		if len(params) < 3:
			errors.append(
				"Not enough arguments. Expected singer ID, song ID, and new key change value.")
			return
		singer = self.getSingerFromID(params[0], False, False)
		if not singer is None:
			songIndex = singer.getSongIndexFromID(params[1], False)
			if not songIndex is None:
				keyChangeStr = params[2]
				if keyChangeStr == "0":
					keyChangeStr = None
				keyChangeValue = getKeyChangeValue(keyChangeStr)
				if keyChangeValue != -99:
					newState = self.mutate()
					singer = newState.getSingerFromID(params[0], False, False)
					if not singer is None:
						songIndex = singer.getSongIndexFromID(params[1], False)
						if not songIndex is None:
							singer.songs[songIndex].keyChange = keyChangeStr

	def play(self, params, cycleQueue):
		global firstSong
		if len(params) > 0:
			song = params[0]
		else:
			song = "next"
		if not self.nextSinger() is None:
			newState = self.mutate()
			nextSinger = newState.nextSinger()
			songToPlayIndex = nextSinger.getSongIndexFromID(song, False)
			if not songToPlayIndex is None:
				song = nextSinger.songs[songToPlayIndex]
				fileToStart = nextSinger.songs[songToPlayIndex].file.path
				if cycleQueue:
					newState.singers.remove(nextSinger)
					newState.singers.append(nextSinger)
				del nextSinger.songs[songToPlayIndex]
				if firstSong:
					startfile(fileToStart)
					sleep(5)
					firstSong = False
				applyKeyChange(song.keyChange)
				startfile(fileToStart)
		else:
			errors.append("There are no singers with songs available.")


class SingerColumn:
	singers = []
	indexStart = 0
	columnWidth = 0

	def __init__(self, indexStart, columnSingers):
		self.indexStart = indexStart
		self.singers = columnSingers
		maxSingerLen = 8  # "nn: (n) "
		maxSongCount = max(len(singer.songs) for singer in columnSingers)
		maxNameLength = max(len(singer.name) for singer in columnSingers)
		maxSingerLen += maxNameLength
		if maxSongCount > 9:
			maxSingerLen += 1
		self.columnWidth = maxSingerLen

	def getRowText(self, row):
		if len(self.singers) > row:
			index = self.indexStart+row
			indexText = str(index)
			if index < 10:
				indexText = " "+indexText
			singer = self.singers[row]
			songCount = len(singer.songs)
			plainIndexText = indexText
			indexText = f"{Fore.YELLOW}{Style.BRIGHT}" + \
				indexText+f"{Style.RESET_ALL}"
			nameText = ''
			if songCount > 0:
				nameText += f"{Fore.WHITE}{Style.BRIGHT}"
			else:
				nameText += f"{Fore.MAGENTA}{Style.NORMAL}"
			plainNameText = singer.name
			nameText += singer.name
			rowText = indexText+": "+nameText + \
				"("+str(songCount)+")"+f"{Style.RESET_ALL}"
			plainRowText = plainIndexText+": " + \
				plainNameText+"("+str(songCount)+")"
			sizeDiff = self.columnWidth-len(plainRowText)
			padding = " "*sizeDiff
			return rowText+padding
		return ""


class Song:
	file = None
	keyChange = None

	def __init__(self, file, keyChange):
		self.file = file
		self.keyChange = keyChange

	def writeToStateFile(self, file):
		anyKeyChange = ''
		if not self.keyChange is None:
			anyKeyChange = self.keyChange
		file.write("\t"+self.file.path+"|"+anyKeyChange+"\n")


def getKeyChangeValue(keyChange):
	if not keyChange is None:
		if len(keyChange) == 2:
			if keyChange[0] == '+' or keyChange[0] == '-':
				value = keyChange[1:2]
				if value.isdigit():
					intval = int(value)
					if intval < 6 and intval > 0:
						if keyChange[0] == '-':
							return -intval
						return intval
		errors.append(
			"Invalid key change, should in format \"+N\" or \"-N\", where N is a value between 1 and 5.")
		return -99
	return None


def applyKeyChange(keyChange):
	resetPitch()
	keyChangeVal = getKeyChangeValue(keyChange)
	if not keyChangeVal is None and keyChangeVal != -99:
		while keyChangeVal != 0:
			if keyChangeVal < 0:
				pitchDown()
				keyChangeVal += 1
			else:
				pitchUp()
				keyChangeVal -= 1


def getKaraokeFileFromPath(path):
	path = path.lower()
	matches = [
		karaokeFile for karaokeFile in karaokeFiles if karaokeFile.path.lower() == path]
	if len(matches) == 1:
		return matches[0]
	return None


def padOrEllipsize(str, length, padStr):
	if len(str) > length:
		str = str.strip()
		if len(str) > length:
			str = str[0:length-3].strip()+"..."
	return str+((length-len(str))*padStr)


def getSongChoice(message, options, blankAllowed, selectionAllowed):
	invalidChoice = True
	while invalidChoice:
		invalidChoice = False
		try:
			songNum = input(message)
		except EOFError:
			pass
		songNum = songNum.strip()
		if songNum.lower().startswith("x"):
			return None
		if songNum.isdigit() and selectionAllowed:
			parsedInt = int(songNum)-1
			if parsedInt < 0 or parsedInt > len(options):
				invalidChoice = True
				print(
					f"{Fore.RED}{Style.BRIGHT}Invalid choice, try again.{Style.RESET_ALL}")
			else:
				return options[parsedInt]
		else:
			if len(songNum) == 0:
				if blankAllowed:
					return ""
				else:
					invalidChoice = True
					print(
						f"{Fore.RED}{Style.BRIGHT}Invalid choice, try again.{Style.RESET_ALL}")
			else:
				return songNum


def selectSong(searchString, songs):
	return showSongList(searchString, songs, True)


def showSongList(searchString, files, selectionAllowed):
	searchAgain = True
	if selectionAllowed:
		optionalSelectionText = ", song number to select,"
	else:
		optionalSelectionText = ""
	while searchAgain:
		searchAgain = False
		options = [
			songFile for songFile in files if songFile.matches(searchString)]
		if len(options) == 1 and selectionAllowed:
			return options[0]
		if len(options) == 0:
			print(f"{Fore.RED}{Style.BRIGHT}No results found for \"" +
				  searchString+f"\" ...{Style.RESET_ALL}")
			try:
				input("Press Enter to continue.")
			except EOFError:
				pass
			return None
		clear()
		shownCount = 0
		totalShownCount = 0
		startCount = 1
		for i, option in enumerate(options):
			strIndex = str(i+1)
			padding = (3-len(strIndex))*" "
			strIndex = padding+strIndex
			print(f"{Fore.YELLOW}{Style.BRIGHT}"+strIndex +
				  f"{Style.RESET_ALL}: "+option.getOptionText())
			shownCount += 1
			totalShownCount += 1
			if shownCount == SCREENHEIGHT-2 or i == len(options)-1:
				print("Showing results "+f"{Fore.WHITE}{Style.BRIGHT}"+str(startCount)+"-"+str(startCount+(shownCount-1))+f"{Style.RESET_ALL}" +
					  f" of {Fore.WHITE}{Style.BRIGHT}"+str(len(options))+f"{Style.RESET_ALL} for {Fore.YELLOW}{Style.BRIGHT}\""+searchString+f"\"{Style.RESET_ALL}.")
				if len(options) > totalShownCount:
					songNum = getSongChoice("Press Enter for more, x to cancel"+optionalSelectionText +
											" or more text to refine the search criteria: ", options, True, selectionAllowed)
					if songNum is None:
						return None
					elif songNum == "":
						startCount += shownCount
						shownCount = 0
						continue
					elif isinstance(songNum, MusicFile):
						return songNum
					else:
						searchString = searchString+" "+songNum
						searchAgain = True
						break
		if not searchAgain:
			if not selectionAllowed:
				try:
					input("Press Enter to continue ...")
				except EOFError:
					pass
				return None
			songNum = getSongChoice(
				"Enter song number, or X to cancel, or more text to add to the search criteria: ", options, False, selectionAllowed)
			if songNum is None:
				return None
			elif isinstance(songNum, MusicFile):
				return songNum
			else:
				searchString = searchString+" "+songNum
				searchAgain = True


def clear():
	# for windows
	if name == 'nt':
		_ = system('cls')
	# for mac and linux(here, os.name is 'posix')
	else:
		_ = system('clear')


def cueSong(params):
	global messages
	paramCount = len(params)
	if paramCount == 0:
		errors.append("Not enough arguments. Expected song search string.")
	else:
		song = selectSong(params[0], musicFiles)
		if not song is None:
			messages.append("Added \""+song.title+"\" by " +
							song.artist+" to the requests queue.")
			try:
				with open(requestsFilename, mode="a", encoding="utf-8") as f:
					f.write(song.path+"\n")
			except PermissionError:
				errors.append("Failed to write to requests file.")
			if len(params)>1:
				if params[1]=="a" or params[1]=="add":
					try:
						with open(backgroundMusicPlaylistFilename, mode="a", encoding="utf-8") as f:
							f.write(song.artist+" - "+song.title+"\n")
					except PermissionError:
						errors.append("Failed to append to background music playlist file.")

def showHeader():
	print(f'{Fore.GREEN}{Style.BRIGHT}Karaoke Manager v1.0{Style.RESET_ALL} (' +
		  str(len(karaokeFiles))+"/"+str(len(musicFiles))+" karaoke/music files found)")


def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]


def showSingers():
	singersWithRequests = state.getSingersDisplayList()
	if len(singersWithRequests) == 0:
		print("No singers.")
	else:
		columnsOfSingers = []
		indexStart = 1
		for singersChunk in chunks(singersWithRequests, 10):
			columnsOfSingers.append(SingerColumn(indexStart, singersChunk))
			indexStart += 10
		for row in range(0, min(len(singersWithRequests), 10)):
			for singerColumn in columnsOfSingers:
				print(singerColumn.getRowText(row), end='')
			print()


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
		print(f"{Fore.WHITE}Showing song list for "+nameColor +
			  f"{Style.BRIGHT}"+activeSinger.name+f"{Style.RESET_ALL}:")
		for i, song in enumerate(activeSinger.songs):
			songIndex = f"{Fore.YELLOW}{Style.BRIGHT}" + \
				str(i+1)+f"{Style.RESET_ALL}"
			if i < 9:
				songIndex = " "+songIndex
			if isinstance(song.file, KaraokeFile):
				print(songIndex+f": "+song.file.getSongListText(song.keyChange))
			else:
				print(songIndex+f": "+song.file.getSongListText())


def isKeyword(str, keyword):
	return str == keyword or str == keyword[0]


def processCommand(command):
	global quit
	global errors
	if command.commandType == CommandType.HELP:
		showHelp()
	elif command.commandType == CommandType.QUIT:
		quit = True
	elif command.commandType == CommandType.ADD:
		state.add(command.params)
	elif command.commandType == CommandType.INSERT:
		state.insert(command.params)
	elif command.commandType == CommandType.MOVE:
		state.move(command.params)
	elif command.commandType == CommandType.DELETE:
		state.delete(command.params)
	elif command.commandType == CommandType.LIST:
		state.list(command.params)
	elif command.commandType == CommandType.UNDO:
		state.undo()
	elif command.commandType == CommandType.REDO:
		state.redo()
	elif command.commandType == CommandType.SCAN:
		buildSongList(command.params)
	elif command.commandType == CommandType.ZAP:
		state.clear()
	elif command.commandType == CommandType.NAME:
		state.renameSinger(command.params)
	elif command.commandType == CommandType.PLAY:
		state.play(command.params, True)
	elif command.commandType == CommandType.FILLER:
		state.play(command.params, False)
	elif command.commandType == CommandType.KEY:
		state.changeSongKey(command.params)
	elif command.commandType == CommandType.CUE:
		cueSong(command.params)
	elif command.commandType == CommandType.SEARCH:
		showSongList(command.params[0], karaokeFiles, False)
	elif command.commandType == CommandType.MUSICSEARCH:
		showSongList(command.params[0], musicFiles, False)


def parseCommandType(strCommand):
	strCommand = strCommand.lower()
	for command in commands:
		if strCommand == command.commandString or strCommand == command.commandString[0]:
			return command.commandType
	return None


def parseCommand(strCommand):
	# Special case = search
	if strCommand[0:2] == "??":
		return Command(CommandType.MUSICSEARCH, [strCommand[2:]])
	if strCommand[0] == "?":
		return Command(CommandType.SEARCH, [strCommand[1:]])
	commandBits = strCommand.split(',')
	for i, commandBit in enumerate(commandBits):
		commandBits[i] = commandBit.strip()
	commandType = parseCommandType(commandBits[0])
	if commandType is None:
		errors.append("Unknown command: \""+commandBits[0]+"\"")
		return None
	else:
		return Command(commandType, commandBits[1:])


def getCommand():
	try:
		command = input(":")
	except EOFError:
		pass
	command = command.strip()
	if len(command) > 0:
		parsedCommand = parseCommand(command)
		return parsedCommand
	return None


def showErrors():
	global errors
	for error in errors:
		print(f'{Fore.RED}{Style.BRIGHT}'+error+f'{Style.RESET_ALL}')
	errors = []


def showMessages():
	global messages
	for message in messages:
		print(f'{Fore.YELLOW}{Style.BRIGHT}'+message+f'{Style.RESET_ALL}')
	messages = []


def parseKaraokeFilename(path, filename):
	filename = filename[0:-4]
	bits = filename.split(" - ")
	if len(bits) == 3:
		return KaraokeFile(path, bits[0].strip(), bits[1].strip(), bits[2].strip())
	return None


def parseMusicFilename(path, filename):
	filename = filename[0:-4]
	bits = filename.split(" - ")
	if len(bits) >= 2:
		title = " - ".join(bits[1:])
		return MusicFile(path, bits[0].strip(), title)
	return None


def parseReversalExemption(line):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return ReversalExemption(bits[0], bits[1])
		else:
			errors.append("Could not parse reversal exemption: "+line)
			return None


def parseSimilarityExemption(line):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return SimilarityExemption(bits[0], bits[1])
		else:
			errors.append("Could not parse similarity exemption: "+line)
			return None


def getReversalExemptions():
	global reversalExemptions
	reversalExemptions = []
	if path.isfile(reversalExemptionsFilename):
		with open(reversalExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				reversalExemption = parseReversalExemption(line)
				if not reversalExemption is None:
					reversalExemptions.append(reversalExemption)

def getTheExemptions():
	global theExemptions
	theExemptions = set([])
	if path.isfile(theExemptionsFilename):
		with open(theExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				theExemption = line.strip()
				theExemptions.add(theExemption)


def getBackgroundMusicPlaylist():
	global backgroundMusicPlaylist
	backgroundMusicPlaylist = set([])
	if path.isfile(backgroundMusicPlaylistFilename):
		with open(backgroundMusicPlaylistFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				line = line.strip()
				if(len(line) > 0):
					backgroundMusicPlaylist.add(line.lower())


def getSimilarityExemptions():
	global similarityExemptions
	similarityExemptions = []
	if path.isfile(similarityExemptionsFilename):
		with open(similarityExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				similarityExemption = parseSimilarityExemption(line)
				if not similarityExemption is None:
					similarityExemptions.append(similarityExemption)


def getLowerCaseExemptions():
	global lowerCaseExemptions
	lowerCaseExemptions = []
	if path.isfile(lowerCaseExemptionsFilename):
		with open(lowerCaseExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				lowerCaseExemption = line.strip()
				lowerCaseExemptions.append(lowerCaseExemption)


def isExemptFromReversalCheck(artist1, artist2):
	for reversalExemption in reversalExemptions:
		if reversalExemption.matches(artist1, artist2):
			return True
	return False


def isExemptFromLowerCaseCheck(artist1):
	for lowerCaseExemption in lowerCaseExemptions:
		if lowerCaseExemption in artist1:
			return True
	return False


def isExemptFromSimilarityCheck(title1, title2):
	for similarityExemption in similarityExemptions:
		if similarityExemption.matches(title1, title2):
			return True
	return False


def buildDictionary():
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


def analyzeFileSet(files,dictionary,fullanalysis,songErrors,duplicates):
	getLowerCaseExemptions()
	getReversalExemptions()
	getTheExemptions()
	getSimilarityExemptions()
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
			message = "Looking for duplicates: " + \
				str(percent)+"% done"
			padding = " "*(119-len(message))
			print(message+padding, end="\r")
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
				error = "Artist \""+artist+"\" is not capitalised."
				songErrors.append(error)
		if artist.startswith("The "):
			if artist[4:] in artists and not artist in theExemptions:
				error = "Artist \""+artist+"\" has a non-The variant."
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
						error = "Artist \""+artist+"\" also appears as \""+reverseCheck+"\"."
						songErrors.append(error)
		for j in range(i+1, artistCount):
			counter += 1
			percent = round((counter/artistProgressCount)*100.0)
			if percent > lastPercent:
				message = "Analyzing artists: "+str(percent)+"% done"
				padding = " "*(119-len(message))
				print(message+padding, end="\r")
				lastPercent = percent
			compareArtist = artistList[j]
			compareArtistLower = artistLowerList[j]
			if artistLower == compareArtistLower and artist != compareArtist:
				error = "Artist \""+artist+"\" has a case variation: \""+compareArtist+"\"."
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
				error = "Title \""+songTitle+"\" is not capitalised."
				songErrors.append(error)
		for j in range(i+1, songCount):
			counter += 1
			percent = round((counter/songProgressCount)*100.0)
			if percent > lastPercent:
				message = "Analyzing song titles (simple analysis): " + \
					str(percent)+"% done"
				padding = " "*(119-len(message))
				print(message+padding, end="\r")
				lastPercent = percent
			compareTitle = files[j].title
			compareTitleLower = files[j].lowerTitle
			if songTitle != compareTitle:
				if songTitleLower == compareTitleLower:
					error = "Title \""+songTitle+"\" has a case variation: \""+compareTitle+"\"."
					songErrors.append(error)
	lastPercent = -1
	counter = 0
	songProgressCount = len(dictionary)
	if fullanalysis:
		for artist, songDict in dictionary.items():
			counter += 1
			percent = round((counter/songProgressCount)*100.0)
			if percent > lastPercent:
				message = "Analyzing song titles (complex analysis): " + \
					str(percent)+"% done"
				padding = " "*(119-len(message))
				print(message+padding, end="\r")
				lastPercent = percent
			keys = list(songDict.keys())
			for i in range(0, len(keys)):
				for j in range(i+1, len(keys)):
					if not isExemptFromSimilarityCheck(keys[i], keys[j]):
						similarityCalc = similarity(keys[i], keys[j])
						if similarityCalc < 1.0 and similarityCalc > 0.9:
							error = "Title \"" + \
								keys[i]+"\" looks very similar to \"" + \
								keys[j]+"\"."
							songErrors.append(error)

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


def randomSongSuggestionGeneratorThread():
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
				suggestionString = artistString+"\n"+songString+"\n"
				try:
					with open(randomSuggestionsFilename, mode="w", encoding="utf-8") as f:
						f.writelines(suggestionString)
				except PermissionError:
					errors.append("Failed to write suggestion file.")
		else:
			counter -= 1
		sleep(0.5)


def stopSuggestionThread():
	global suggestorThread
	global stopSuggestions
	if not suggestorThread is None:
		stopSuggestions = True
		suggestorThread.join()
	stopSuggestions = False


def startSuggestionThread():
	global suggestorThread
	stopSuggestionThread()
	suggestorThread = threading.Thread(
		target=randomSongSuggestionGeneratorThread)
	suggestorThread.daemon = True
	suggestorThread.start()


def getMusicFileKey(file):
	return file.artist

def writeBackgroundMusicFile(paths):
	try:
		with open(backgroundMusicFilename, mode="w", encoding="utf-8") as f:
			f.writelines(paths,)
	except PermissionError:
		errors.append("Failed to write background music file.")

def analyzeFilesPerCategory(full,songErrors,duplicates,files,dictionary,dupFilename,errFilename,descr):
	dups=[]
	errs=[]
	message="Analyzing "+descr+" files..."
	padding = " "*(119-len(message))
	print(message+padding)
	analyzeFileSet(files,dictionary,full,errs,dups)
	duplicates.extend(dups)
	songErrors.extend(errs)
	try:
		with open(dupFilename, mode="w", encoding="utf-8") as f:
			for duplicate in dups:
				f.writelines(duplicate.artist+" - "+duplicate.title+"\n")
	except PermissionError:
		errors.append("Failed to write duplicates file.")
	try:
		with open(errFilename, mode="w", encoding="utf-8") as f:
			for songError in errs:
				f.writelines(songError+"\n")
	except PermissionError:
		errors.append("Failed to write artist or title errors file.")

def analyzeFiles(full,songErrors,duplicates):
	analyzeFilesPerCategory(full,songErrors,duplicates,musicFiles,musicDictionary,musicDuplicatesFilename,musicErrorsFilename,"music")
	analyzeFilesPerCategory(full,songErrors,duplicates,karaokeFiles,karaokeDictionary,karaokeDuplicatesFilename,karaokeErrorsFilename,"karaoke")

def buildSongList(params):
	global karaokeDictionary
	global musicDictionary
	global karaokeFiles
	global musicFiles
	global filenameErrorCount
	getBackgroundMusicPlaylist()
	backgroundMusic=[]
	filenameErrors = []
	quickanalyze = len(params) > 0 and (params[0] == "quickanalyze" or params[0] == "q")
	fullanalyze = len(params) > 0 and (params[0] == "analyze" or params[0] == "a")
	karaokeFiles = []
	if not karaokeFilesPaths is None:
		for karaokeFilesPath in karaokeFilesPaths:
			for root, _, files in walk(karaokeFilesPath):
				message = "Scanning "+root
				message = message[0:118]
				padding = " "*(119-len(message))
				print(message+padding, end="\r")
				for file in files:
					if file.lower().endswith(".zip"):
						karaokeFile = parseKaraokeFilename(root+"\\"+file, file)
						if karaokeFile is None:
							filenameErrors.append(file)
						else:
							karaokeFiles.append(karaokeFile)
	else:
		errors.append("KaraokeFilesPath was not specified.")
	musicFiles=[]
	if not musicFilesPaths is None:
		for musicFilesPath in musicFilesPaths:
			for root, _, files in walk(musicFilesPath):
				message = "Scanning "+root
				message = message[0:118]
				padding = " "*(119-len(message))
				print(message+padding, end="\r")
				for file in files:
					fileLower = file.lower()
					if fileLower.endswith(".mp3") or fileLower.endswith(".m4a"):
						fileWithoutExtension = fileLower[0:-4]
						if fileWithoutExtension in backgroundMusicPlaylist:
							backgroundMusic.append(root+"\\"+file+"\n")
							backgroundMusicPlaylist.remove(fileWithoutExtension)
						musicFile = parseMusicFilename(root+"\\"+file, file)
						if musicFile is None:
							filenameErrors.append(file)
						else:
							musicFiles.append(musicFile)
	else:
		errors.append("MusicFilesPath was not specified.")
	try:
		with open(filenameErrorsFilename, mode="w", encoding="utf-8") as f:
			for filenameError in filenameErrors:
				f.writelines(filenameError+"\n")
	except PermissionError:
		errors.append("Failed to write filename errors file.")
	try:
		with open(missingPlaylistEntriesFilename, mode="w", encoding="utf-8") as f:
			for backgroundMusicFile in backgroundMusicPlaylist:
				f.writelines(backgroundMusicFile+"\n")
	except PermissionError:
		errors.append("Failed to write missing playlist entries file.")
	buildDictionary()
	startSuggestionThread()
	anythingToReport = len(filenameErrors) > 0 or len(backgroundMusicPlaylist)>0
	duplicates=[]
	songErrors=[]
	if quickanalyze or fullanalyze:
		analyzeFiles(fullanalyze,songErrors,duplicates)
		anythingToReport = anythingToReport or len(songErrors)>0 or len(duplicates)>0
	if anythingToReport:
		print(f"{Fore.WHITE}{Style.BRIGHT}Scan complete.                                                       ")
		print(f"{Fore.RED}{Style.BRIGHT}Bad filenames:{Style.RESET_ALL} " + str(len(filenameErrors)))
		print(f"{Fore.YELLOW}{Style.BRIGHT}Artist/title problems:{Style.RESET_ALL} "+str(len(songErrors)))
		print(f"{Fore.CYAN}{Style.BRIGHT}Duplicate files:{Style.RESET_ALL} " + str(len(duplicates)))
		print(f"{Fore.MAGENTA}{Style.BRIGHT}Missing playlist entries:{Style.RESET_ALL} " + str(len(backgroundMusicPlaylist)))
		try:
			input("Press Enter to continue ...")
		except EOFError:
			pass
	musicFiles.sort(key=getMusicFileKey)
	karaokeFiles.sort(key=getMusicFileKey)
	writeBackgroundMusicFile(backgroundMusic)

def getSettings():
	global musicFilesPaths
	global karaokeFilesPaths
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


getSettings()
clear()
if not path.isdir(dataFolder):
	makedirs(dataFolder)
if path.exists(requestsFilename):
  remove(requestsFilename)
buildSongList([])
state = State()
while not quit:
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
		processCommand(command)
clear()
stopSuggestionThread()
