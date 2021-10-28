from SongList import SongList

# Class describing a singer, and their current list of selected songs.
class Singer(SongList):
	def __init__(self, name):
		SongList.__init__(self, name)

	def writeToStateFile(self, file):
		SongList.writeToStateFile(self, file)

	def writeToQueueFile(self, file):
		SongList.writeToQueueFile(self, file)

	def getSongIndexFromID(self, id, endAllowed, errors):
		return SongList.getSongIndexFromID(self, id, endAllowed, errors)

	def moveSong(self, songToMoveID, songToMoveBeforeID, errors):
		return SongList.moveSong(self, songToMoveID, songToMoveBeforeID, errors)

	def insertSong(self, position, song):
		SongList.insertSong(self, position, song)

