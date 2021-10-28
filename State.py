from os import path, startfile
from copy import deepcopy
from Singer import Singer
from SongSelector import selectSong
from WindowsInput import PressKey, ReleaseKey, KeyCodes
from Song import Song
from time import sleep

# Filename to persist the state to.
# Gets written after every command, in case the app crashes.
stateFilename = "KaraokeManager.state.txt"
# Filename to persist the list of singers to.
# Gets written after every command, in the case the app crashes.
# Gets read by the Winamp SingersQueue plugin to show the current queue onscreen.
singersQueueFilename = "KaraokeManager.singers.txt"

# Current state of the app.
class State:
	singers = None
	firstSong = True
	activeSongListSingerName = None
	nextState = None
	prevState = None
	statePath = None
	queuePath = None	

	def __init__(self, dataFolder, karaokeFiles):
		self.statePath = dataFolder+"\\"+stateFilename
		self.queuePath = dataFolder+"\\"+singersQueueFilename
		self.load(karaokeFiles)

	# Load the last saved state.
	def load(self, karaokeFiles):
		self.singers = []
		if path.isfile(self.statePath):
			with open(self.statePath, mode="r", encoding="utf-8") as f:
				lines = f.readlines()
				currentSinger = None
				for line in lines:
					if line.startswith("\t"):
						if not currentSinger is None:
							lineBits = line.strip().split("|")
							karaokeFile = getKaraokeFileFromPath(lineBits[0], karaokeFiles)
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
			with open(self.statePath, mode="w", encoding="utf-8") as f:
				for singer in self.singers:
					singer.writeToStateFile(f)
		except PermissionError:
			errors.append("Failed to write state file.")
		try:
			with open(self.queuePath, mode="w", encoding="utf-8") as f:
				for singer in self.singers:
					singer.writeToQueueFile(f)
		except PermissionError:
			errors.append("Failed to write singer names file.")

	def getSingersDisplayList(self):
		singersCopy = self.singers.copy()
		return singersCopy

	# Make a deep copy of the current state, ready for alteration.
	# We create a chain of previous/next states for undo/redo.
	def mutate(self):
		newState = deepcopy(self)
		self.nextState = newState
		newState.prevState = self
		return newState

	def getSingerIndexFromID(self, id, endAllowed, reqAllowed, errors):
		if id.isdigit():
			singerIndex = int(id)
			if singerIndex <= 0 or singerIndex > len(self.singers):
				errors.append(f"Singer index out of bounds: it must be between 1 and {len(self.singers)}")
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
		for i, singer in enumerate(self.singers):
			if singer.name.lower() == id:
				return i
		matches = []
		for i, singer in enumerate(self.singers):
			if id in singer.name.lower():
				matches.append(i)
		if len(matches) == 0:
			errors.append(f"No match found for given singer ID \"{id}\"")
			return None
		if len(matches) > 1:
			errors.append(f"Multiple matches found for given singer ID \"{id}\"")
			return None
		return matches[0]

	def getSingerFromID(self, id, endAllowed, reqAllowed, errors):
		singerIndex = self.getSingerIndexFromID(id, endAllowed, reqAllowed, errors)
		if singerIndex is None:
			return None
		return self.singers[singerIndex]

	def addNewSinger(self, singerName, index, errors):
		sameNameSingers = [
			singer for singer in self.singers if singer.name.lower() == singerName.lower()]
		if len(sameNameSingers) > 0:
			errors.append(f"Singer with name \"{singerName}\" already exists.")
		else:
			newState = self.mutate()			
			newState.singers.insert(index, Singer(singerName))
			return newState
		return self

	def deleteSinger(self, singerID, errors):
		matchedSingerIndex = self.getSingerIndexFromID(singerID, False, False, errors)
		if not matchedSingerIndex is None:
			newState = self.mutate()
			del newState.singers[matchedSingerIndex]
			return newState
		return self

	def deleteSongFromSinger(self, singerID, songID, errors):
		matchedSingerIndex = self.getSingerIndexFromID(singerID, False, False, errors)
		if not matchedSingerIndex is None:
			matchedSinger = self.singers[matchedSingerIndex]
			matchedSongIndex = matchedSinger.getSongIndexFromID(songID, False, errors)
			if not matchedSongIndex is None:
				newState = self.mutate()
				del newState.singers[matchedSingerIndex].songs[matchedSongIndex]
				return newState
		return self

	def insertNewSinger(self, singerName, singerID, errors):
		matchedSingerIndex = self.getSingerIndexFromID(singerID, True, False, errors)
		if not matchedSingerIndex is None:
			return self.addNewSinger(singerName, matchedSingerIndex, errors)
		return self

	def moveSinger(self, singerToMoveID, singerID, errors):
		matchedSingerToMoveIndex = self.getSingerIndexFromID(singerToMoveID, False, False, errors)
		if not matchedSingerToMoveIndex is None:
			matchedSingerIndex = self.getSingerIndexFromID(singerID, True, False, errors)
			if not matchedSingerIndex is None:
				newState = self.mutate()
				singerToMove = newState.singers[matchedSingerToMoveIndex]
				del newState.singers[matchedSingerToMoveIndex]
				newState.singers.insert(matchedSingerIndex, singerToMove)
				return newState
		return self

	def addSongForSinger(self, singerID, songTitle, keyChange, index, karaokeFiles, errors):
		keychangeval = getKeyChangeValue(keyChange, errors)
		if keychangeval != -99:
			matchedSinger = self.getSingerFromID(singerID, False, True, errors)
			if not matchedSinger is None:
				karaokeSong = selectSong(songTitle, karaokeFiles)
				if not karaokeSong is None:
					if index == -1:
						index = len(matchedSinger.songs)
					newState = self.mutate()
					matchedSinger = newState.getSingerFromID(singerID, False, True, errors)
					matchedSinger.insertSong(index, Song(karaokeSong, keyChange))
					return newState
		return self

	def insertSongForSinger(self, singerID, songID, songTitle, keyChange, karaokeFiles, errors):
		matchedSinger = self.getSingerFromID(singerID, False, True, errors)
		if not matchedSinger is None:
			matchedSongIndex = matchedSinger.getSongIndexFromID(songID, True, errors)
			if not matchedSongIndex is None:
				return self.addSongForSinger(singerID, songTitle, keyChange, matchedSongIndex, karaokeFiles, errors)
		return self

	def moveSong(self, singerID, songToMoveID, songToMoveBeforeID, errors):
		matchedSinger = self.getSingerFromID(singerID, False, True, errors)
		if not matchedSinger is None:
			matchedSongToMoveIndex = matchedSinger.getSongIndexFromID(songToMoveID, False, errors)
			if not matchedSongToMoveIndex is None:
				matchedSongToMoveBeforeIndex = matchedSinger.getSongIndexFromID(songToMoveBeforeID, True, errors)
				if not matchedSongToMoveBeforeIndex is None:
					newState = self.mutate()
					matchedSinger = newState.getSingerFromID(singerID, False, True, errors)
					matchedSinger.moveSong(songToMoveID, songToMoveBeforeID, errors)
					return newState
		return self

	def add(self, params, karaokeFiles, errors):
		paramCount = len(params)
		if paramCount == 0:
			errors.append("Not enough arguments. Expected name of new singer, or existing singer name/index.")
		elif paramCount == 1:
			return self.addNewSinger(params[0], len(self.singers), errors)
		else:
			keyChange = None
			if paramCount > 2:
				keyChange = params[2]
			return self.addSongForSinger(params[0], params[1], keyChange, -1, karaokeFiles, errors)
		return self

	def insert(self, params, karaokeFiles, errors):
		paramCount = len(params)
		if paramCount < 2:
			errors.append("Not enough arguments. Expected name of new singer, or existing singer name/index.")
		elif paramCount == 2:
			return self.insertNewSinger(params[0], params[1], errors)
		elif paramCount > 2:
			keyChange = None
			if paramCount > 3:
				keyChange = params[3]
			return self.insertSongForSinger(params[0], params[1], params[2], keyChange, karaokeFiles, errors)
		return self

	def move(self, params, errors):
		paramCount = len(params)
		if paramCount < 2:
			errors.append("Not enough arguments. Expected ID of singer.")
		elif paramCount == 2:
			# Move a singer in the list
			return self.moveSinger(params[0], params[1], errors)
		elif paramCount > 2:
			# Move a song in a singer's list
			return self.moveSong(params[0], params[1], params[2], errors)
		return self

	def delete(self, params, errors):
		paramCount = len(params)
		if paramCount < 1:
			errors.append("Not enough arguments. Expected ID of singer.")
		elif paramCount == 1:
			# Delete a singer
			return self.deleteSinger(params[0], errors)
		elif paramCount > 1:
			# Delete a song from a singer
			return self.deleteSongFromSinger(params[0], params[1], errors)
		return self

	def undo(self):
		if self.prevState is None:
			errors.append("No undo history available.")
		else:
			return self.prevState

	def redo(self):
		if self.nextState is None:
			errors.append("No redo history available.")
		else:
			return self.nextState

	def renameSinger(self, params, errors):
		if len(params) < 2:
			errors.append("Not enough arguments. Expected singer ID and new name.")
		else:
			singer = self.getSingerFromID(params[0], False, False, errors)
			newName = params[1]
			if not singer is None:
				for singer in self.singers:
					if singer.name.lower() == newName:
						errors.append(f"Name \"{newName}\" already exists.")
						return
				newState = self.mutate()
				singer = newState.getSingerFromID(params[0], False, False, errors)
				singer.name = newName
				return newState
		return self

	def clear(self):
		newState = self.mutate()
		newState.singers = []
		newState.activeSongListSingerName = None
		return newState

	def nextSinger(self):
		for singer in self.singers:
			if len(singer.songs) > 0:
				return singer
		return None

	def setSongListToNextSinger(self):
		self.activeSongListSingerName = None

	def setSongListToSinger(self, singer):
		self.activeSongListSingerName = singer.name

	def list(self, params, errors):
		if len(params) == 0:
			nextState = self.mutate()
			nextState.setSongListToNextSinger()
			return nextState
		else:
			singer = self.getSingerFromID(params[0], False, True, errors)
			if not singer is None:
				nextState = self.mutate()
				nextState.setSongListToSinger(singer)
				return nextState

	def getActiveSongListSinger(self):
		if self.activeSongListSingerName is None:
			return self.nextSinger()
		activeSinger = [
			singer for singer in self.singers if singer.name == self.activeSongListSingerName]
		if len(activeSinger) == 0:
			self.activeSongListSingerName = None
			return self.nextSinger()
		return activeSinger[0]

	def changeSongKey(self, params, errors):
		if len(params) < 3:
			errors.append("Not enough arguments. Expected singer ID, song ID, and new key change value.")
		else:
			singer = self.getSingerFromID(params[0], False, False, errors)
			if not singer is None:
				songIndex = singer.getSongIndexFromID(params[1], False, errors)
				if not songIndex is None:
					keyChangeStr = params[2]
					if keyChangeStr == "0":
						keyChangeStr = None
					keyChangeValue = getKeyChangeValue(keyChangeStr, errors)
					if keyChangeValue != -99:
						newState = self.mutate()
						singer = newState.getSingerFromID(params[0], False, False, errors)
						if not singer is None:
							songIndex = singer.getSongIndexFromID(params[1], False, errors)
							if not songIndex is None:
								singer.songs[songIndex].keyChange = keyChangeStr
								return newState
		return self

	def play(self, params, cycleQueue, errors):
		if len(params) > 0:
			song = params[0]
		else:
			song = "next"
		if not self.nextSinger() is None:
			newState = self.mutate()
			nextSinger = newState.nextSinger()
			songToPlayIndex = nextSinger.getSongIndexFromID(song, False, errors)
			if not songToPlayIndex is None:
				song = nextSinger.songs[songToPlayIndex]
				fileToStart = nextSinger.songs[songToPlayIndex].file.path
				if cycleQueue:
					newState.singers.remove(nextSinger)
					newState.singers.append(nextSinger)
				del nextSinger.songs[songToPlayIndex]
				if newState.firstSong:
					startfile(fileToStart)
					sleep(5)
					newState.firstSong = False
				applyKeyChange(song.keyChange, errors)
				startfile(fileToStart)
				return newState
		else:
			errors.append("There are no singers with songs available.")
		return self



# Sends the Pacemaker hotkey to knock the pitch down one semitone.
def pitchDown():
	PressKey(KeyCodes.VK_SHIFT)
	PressKey(KeyCodes.VK_CTRL)
	PressKey(KeyCodes.VK_A)
	ReleaseKey(KeyCodes.VK_A)
	sleep(0.25)
	ReleaseKey(KeyCodes.VK_SHIFT)
	ReleaseKey(KeyCodes.VK_CTRL)

# Sends the Pacemaker hotkey to raise the pitch up one semitone.
def pitchUp():
	PressKey(KeyCodes.VK_SHIFT)
	PressKey(KeyCodes.VK_CTRL)
	PressKey(KeyCodes.VK_Q)
	ReleaseKey(KeyCodes.VK_Q)
	sleep(0.25)
	ReleaseKey(KeyCodes.VK_SHIFT)
	ReleaseKey(KeyCodes.VK_CTRL)

# Sends the Pacemaker hotkey to reset the pitch change to zero.
def resetPitch():
	PressKey(KeyCodes.VK_SHIFT)
	PressKey(KeyCodes.VK_CTRL)
	PressKey(KeyCodes.VK_Z)
	ReleaseKey(KeyCodes.VK_Z)
	sleep(0.25)
	ReleaseKey(KeyCodes.VK_SHIFT)
	ReleaseKey(KeyCodes.VK_CTRL)

# Sends the correct sequence of hotkeys to set the key change to
# whatever the user requested for a particular song.
def applyKeyChange(keyChange, errors):
	resetPitch()
	keyChangeVal = getKeyChangeValue(keyChange, errors)
	if not keyChangeVal is None and keyChangeVal != -99:
		while keyChangeVal != 0:
			if keyChangeVal < 0:
				pitchDown()
				keyChangeVal += 1
			else:
				pitchUp()
				keyChangeVal -= 1

# Given a path, get the karaoke file that matches it.
# Used when restoring state on startup to check that a cued-up song still
# exists.				
def getKaraokeFileFromPath(path, karaokeFiles):
	path = path.lower()
	matches = [
		karaokeFile for karaokeFile in karaokeFiles if karaokeFile.path.lower() == path]
	if len(matches) == 1:
		return matches[0]
	return None

# Parses a keychange string.
def getKeyChangeValue(keyChange, errors):
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
		errors.append("Invalid key change, should in format \"+N\" or \"-N\", where N is a value between 1 and 5.")
		return -99
	return None