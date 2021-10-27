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


