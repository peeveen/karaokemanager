from SongList import SongList

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

