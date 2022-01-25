from karaokemanager.music_file import MusicFile
from karaokemanager.display_functions import pad_or_ellipsize
from colorama import Fore, Style

# Class describing a karaoke file
class KaraokeFile(MusicFile):
	company = None

	def __init__(self, path, artist, title, company):
		MusicFile.__init__(self, path, artist, title)
		self.company = company

	def get_option_text(self):
		result = MusicFile.get_option_text(self)
		company_text = pad_or_ellipsize(self.company, 20, " ")
		return result+f"{Style.BRIGHT}{Fore.YELLOW}{company_text}{Style.RESET_ALL}"

	def get_song_list_text(self, key_change):
		txt = MusicFile.get_song_list_text(self)
		if key_change is None or key_change==0:
			key_change = ""
		else:
			sign=""
			if key_change>0:
				sign="+"
			key_change = f"({sign}{key_change})"
		return f"{txt} {Fore.MAGENTA}{Style.BRIGHT}{key_change}{Style.RESET_ALL}"

