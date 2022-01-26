from karaokemanager.display_functions import pad_or_ellipsize, COLUMN_SEPARATOR
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
		self.search_string = f"{title} {artist}".lower()

	def matches(self, search_string):
		bits = search_string.strip().split()
		match_count = 0
		for bit in bits:
			if bit.lower() in self.search_string:
				match_count = match_count+1
		return match_count == len(bits)

	def get_text_with_specific_artist_and_title_lengths(self, max_artist_length, max_title_length):
		artist_text = pad_or_ellipsize(f"{self.artist} ", max_artist_length, ".")
		title_text = pad_or_ellipsize(self.title, max_title_length, " ")
		return f"{Fore.CYAN}{Style.BRIGHT}{artist_text}{Style.RESET_ALL}{COLUMN_SEPARATOR}{Fore.GREEN}{Style.BRIGHT}{title_text}{Style.RESET_ALL}"

	def get_text(self, max_length):
		max_length=max_length-len(COLUMN_SEPARATOR)
		max_artist_length=int(max_length/3)
		max_title_length=max_length-max_artist_length
		return self.get_text_with_specific_artist_and_title_lengths(max_artist_length,max_title_length)

	def get_option_text(self, max_length):
		return self.get_text(max_length)

	def get_song_list_text(self, max_artist_length, max_title_length):
		return self.get_text_with_specific_artist_and_title_lengths(max_artist_length, max_title_length)


