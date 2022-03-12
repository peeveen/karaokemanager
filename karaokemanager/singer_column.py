from colorama import Fore, Style

# Helper class representing an on-screen column of singers, in the singers
# display.
class SingerColumn:
	singers = []
	index_start = 0
	column_width = 0

	def __init__(self, index_start, column_singers):
		self.index_start = index_start
		self.singers = column_singers
		max_singer_len = 8  # "nn: (n) "
		max_song_count = max(len(singer.songs) for singer in column_singers)
		max_name_length = max(len(singer.name) for singer in column_singers)
		max_singer_len += max_name_length + (0 if max_song_count < 10 else 1)
		self.column_width = max_singer_len

	def get_row_text(self, row):
		if len(self.singers) > row:
			index = self.index_start+row
			plain_index_text = f"{index}" if index > 9 else f" {index}"
			singer = self.singers[row]
			song_count = len(singer.songs)
			index_text = f"{Fore.YELLOW}{Style.BRIGHT}{plain_index_text}{Style.RESET_ALL}"
			name_style = f"{Fore.WHITE}{Style.BRIGHT}" if song_count > 0 else f"{Fore.MAGENTA}{Style.NORMAL}"
			row_text = f"{index_text}: {name_style}{singer.name}{Fore.CYAN}({song_count}){Style.RESET_ALL}"
			plain_row_text = f"{plain_index_text}: {singer.name}({song_count})"
			size_diff = self.column_width-len(plain_row_text)
			padding = " "*size_diff
			return row_text+padding
		return ""


