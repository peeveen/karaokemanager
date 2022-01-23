# Class representing a chosen song, with any requested key change
class Song:
	file = None
	keyChange = None

	def __init__(self, file, keyChange):
		self.file = file
		self.keyChange = keyChange

	def writeToStateFile(self, file):
		sign=""
		if(self.keyChange>0):
			sign="+"
		file.write(f"\t{self.file.path}|{sign}{self.keyChange}\n")
