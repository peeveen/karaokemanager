from colorama import Fore, Style

# Helper class representing an on-screen column of singers, in the singers
# display.
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
			indexText = f"{index}"
			if index < 10:
				indexText = f" {indexText}"
			singer = self.singers[row]
			songCount = len(singer.songs)
			plainIndexText = indexText
			indexText = f"{Fore.YELLOW}{Style.BRIGHT}{indexText}{Style.RESET_ALL}"
			nameText = ''
			if songCount > 0:
				nameText += f"{Fore.WHITE}{Style.BRIGHT}"
			else:
				nameText += f"{Fore.MAGENTA}{Style.NORMAL}"
			plainNameText = singer.name
			nameText += singer.name
			rowText = f"{indexText}: {nameText}({songCount}){Style.RESET_ALL}"
			plainRowText = f"{plainIndexText}: {plainNameText}({songCount})"
			sizeDiff = self.columnWidth-len(plainRowText)
			padding = " "*sizeDiff
			return rowText+padding
		return ""


