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
