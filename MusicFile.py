from DisplayFunctions import padOrEllipsize
from colorama import Fore, Style

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


