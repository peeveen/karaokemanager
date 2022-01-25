from karaokemanager.display_functions import clear, pad_or_ellipsize, SCREEN_HEIGHT
from colorama import Fore, Style
from karaokemanager.music_file import MusicFile

# Song selector function. Shows the list of "songs" to the user and asks them to pick one,
# cancel, or enter more text to narrow the search.
def select_song(searchString, songs):
	return show_song_list(searchString, songs, True)

# Asks the user to choose a song from the displayed list, and awaits a valid
# response.
def get_song_choice(message, options, blank_allowed, selection_allowed):
	invalid_choice = True
	while invalid_choice:
		invalid_choice = False
		try:
			song_num = input(message)
		except EOFError:
			pass
		song_num = song_num.strip()
		if song_num.lower().startswith("x"):
			return None
		if song_num.isdigit() and selection_allowed:
			parsed_int = int(song_num)-1
			if parsed_int < 0 or parsed_int > len(options):
				invalid_choice = True
				print(
					f"{Fore.RED}{Style.BRIGHT}Invalid choice, try again.{Style.RESET_ALL}")
			else:
				return options[parsed_int]
		else:
			if len(song_num) == 0:
				if blank_allowed:
					return ""
				else:
					invalid_choice = True
					print(
						f"{Fore.RED}{Style.BRIGHT}Invalid choice, try again.{Style.RESET_ALL}")
			else:
				return song_num

# Displays the list of songs and optionally prompts for a response.
def show_song_list(search_string, files, selection_allowed):
	search_again = True
	if selection_allowed:
		optional_selection_text = ", song number to select,"
	else:
		optional_selection_text = ""
	while search_again:
		search_again = False
		options = [
			song_file for song_file in files if song_file.matches(search_string)]
		if len(options) == 1 and selection_allowed:
			return options[0]
		if len(options) == 0:
			print(f"{Fore.RED}{Style.BRIGHT}No results found for \"{search_string}\" ...{Style.RESET_ALL}")
			try:
				input("Press Enter to continue.")
			except EOFError:
				pass
			return None
		clear()
		shown_count = 0
		total_shown_count = 0
		start_count = 1
		for i, option in enumerate(options):
			index_string = f"{i+1}"
			padding = (3-len(index_string))*" "
			index_string = padding+index_string
			print(f"{Fore.YELLOW}{Style.BRIGHT}{index_string}{Style.RESET_ALL}: {option.get_option_text()}")
			shown_count += 1
			total_shown_count += 1
			if shown_count == SCREEN_HEIGHT-2 or i == len(options)-1:
				print(f"Showing results {Fore.WHITE}{Style.BRIGHT}{start_count}-{start_count+(shown_count-1)}{Style.RESET_ALL} of {Fore.WHITE}{Style.BRIGHT}{len(options)}{Style.RESET_ALL} for {Fore.YELLOW}{Style.BRIGHT}\"{search_string}\"{Style.RESET_ALL}.")
				if len(options) > total_shown_count:
					song_number = get_song_choice(f"Press Enter for more, x to cancel{optional_selection_text} or more text to refine the search criteria: ", options, True, selection_allowed)
					if song_number is None:
						return None
					elif song_number == "":
						start_count += shown_count
						shown_count = 0
						continue
					elif isinstance(song_number, MusicFile):
						return song_number
					else:
						search_string = search_string+" "+song_number
						search_again = True
						break
		if not search_again:
			if not selection_allowed:
				try:
					input("Press Enter to continue ...")
				except EOFError:
					pass
				return None
			song_number = get_song_choice("Enter song number, or X to cancel, or more text to add to the search criteria: ", options, False, selection_allowed)
			if song_number is None:
				return None
			elif isinstance(song_number, MusicFile):
				return song_number
			else:
				search_string = search_string+" "+song_number
				search_again = True