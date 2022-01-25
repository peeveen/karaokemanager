# Class representing a chosen song, with any requested key change
class Song:
	file = None
	key_change = None

	def __init__(self, file, key_change):
		self.file = file
		self.key_change = key_change

	def write_to_state_file(self, file):
		sign=""
		if(self.key_change>0):
			sign="+"
		file.write(f"\t{self.file.path}|{sign}{self.key_change}\n")
