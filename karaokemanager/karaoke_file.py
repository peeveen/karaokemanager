from karaokemanager.music_file import MusicFile
from karaokemanager.display_functions import COLUMN_SEPARATOR, pad_or_ellipsize
from colorama import Fore, Style

# Class describing a karaoke file
class KaraokeFile(MusicFile):
	company = None

	def __init__(self, path, artist, title, company):
		MusicFile.__init__(self, path, artist, title)
		self.company = company

	def get_option_text(self, max_length):
		company_length=int(max_length/5)
		remaining_length=max_length-(company_length+len(COLUMN_SEPARATOR))
		company_text = pad_or_ellipsize(self.company, company_length, " ")
		song_text=MusicFile.get_option_text(self, remaining_length) # Company text, plus a space
		return f"{song_text}{COLUMN_SEPARATOR}{Style.BRIGHT}{Fore.YELLOW}{company_text}{Style.RESET_ALL}"
