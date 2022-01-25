from karaokemanager.display_functions import pad_or_ellipsize
from colorama import Fore, Style

# Class describing a music file
class MusicFile:
	path = None
	title = None
	artist = None
	lower_title = None
	lower_artist = None
	search_string = None

	def __init__(self, path, artist, title):
		self.path = path
		self.title = title
		self.artist = artist
		self.lower_title = title.lower()
		self.lower_artist = artist.lower()
		self.search_string = (title+" "+artist).lower()

	def matches(self, search_string):
		bits = search_string.strip().split()
		match_count = 0
		for bit in bits:
			if bit.lower() in self.search_string:
				match_count = match_count+1
		return match_count == len(bits)

	def get_text(self):
		artist_text = pad_or_ellipsize(f"{self.artist} ", 30, ".")
		title_text = pad_or_ellipsize(self.title, 60, " ")
		return f"{Fore.CYAN}{Style.BRIGHT}{artist_text}{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{title_text}{Style.RESET_ALL}"

	def get_option_text(self):
		return self.get_text()

	def get_song_list_text(self):
		return self.get_text()


