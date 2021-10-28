# Class representing a chosen song, with any requested key change
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
		file.write(f"\t{self.file.path}|{anyKeyChange}\n")
