from colorama import Fore, Style
from karaokemanager.display_functions import COLUMN_SEPARATOR

# Class representing a chosen song, with any requested key change
class Song:
	file = None
	key_change = None

	MAX_KEY_CHANGE=5 # To prevent things getting stupid

	KEY_CHANGE_INDICATOR_LENGTH=4 # Two parentheses, a sign, a digit

	def __init__(self, file, key_change):
		self.file = file
		self.key_change = key_change

	def write_to_state_file(self, file):
		sign=""
		if(self.key_change>0):
			sign="+"
		file.write(f"\t{self.file.path}|{sign}{self.key_change}\n")

	def get_song_list_text(self, max_artist_length, max_title_length):
		key_change_text=""
		if self.key_change!=0:
			sign=""
			if self.key_change>0:
				sign="+"
			key_change_text = f"{COLUMN_SEPARATOR}{Fore.MAGENTA}{Style.BRIGHT}({sign}{self.key_change}){Style.RESET_ALL}"
		song_text=self.file.get_song_list_text(max_artist_length, max_title_length)
		return f"{song_text}{key_change_text}"
