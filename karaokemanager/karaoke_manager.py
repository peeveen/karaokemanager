from colorama import Fore, Style
from os import get_terminal_size
import sys
from karaokemanager.commands import CommandType, parse_command
from karaokemanager.exemptions import Exemptions
from karaokemanager.state import State
from karaokemanager.library import Library, LibraryAnalysisType
from karaokemanager.singer_column import SingerColumn
from karaokemanager.song_selector import select_song, show_song_list
from karaokemanager.display_functions import COLUMN_SEPARATOR, clear, pad_or_ellipsize
from karaokemanager.config import Config
from karaokemanager.error import Error, Info
from karaokemanager.suggestion_generator import SuggestionGenerator
from karaokemanager.song import Song

class KaraokeManager:
	# Default YAML config filename
	DEFAULT_CONFIG_FILENAME='.yaml'
	# Version number
	VERSION="1.0.7"
	# How many singers to show in each column?
	SINGERS_PER_COLUMN = 10
	# Minimum console width
	MIN_CONSOLE_WIDTH=120
	# Minimum console height
	MIN_CONSOLE_HEIGHT=30

	config=None
	console_size=None
	exemptions=None
	library=None

	def __init__(self):
		# Main execution loop
		console_size = get_terminal_size()
		if console_size.columns<KaraokeManager.MIN_CONSOLE_WIDTH:
			raise Exception(f"Karaoke Manager requires a console with a minimum of {KaraokeManager.MIN_CONSOLE_WIDTH} columns")
		if console_size.lines<KaraokeManager.MIN_CONSOLE_HEIGHT:
			raise Exception(f"Karaoke Manager requires a console with a minimum of {KaraokeManager.MIN_CONSOLE_HEIGHT} rows")
		self.console_size=console_size
		
		config_path=KaraokeManager.DEFAULT_CONFIG_FILENAME
		if len(sys.argv)>1:
			config_path=sys.argv[1]

		try:
			self.config=Config(config_path)
		except Exception as e:
			print(f"{Fore.RED}Error parsing the configuration file: {e}{Style.RESET_ALL}")
			exit(1)

		try:
			self.exemptions=Exemptions(self.config)
		except Exception as e:
			print(f"{Fore.RED}Error reading an exemptions file: {e}{Style.RESET_ALL}")
			exit(1)

		self.library = Library(self.exemptions)

	# Shows onscreen help when the user types "help"
	def show_help(self):
		clear()
		self.show_header()
		print(f"All command keywords can be shortened to the first letter.")
		print(f"IDs can be a number from the list, or a partial or complete name (case-insensitive).")
		print()
		print(f"{Fore.CYAN}{Style.BRIGHT}add,NewSingerName{Style.RESET_ALL} = add a new singer to the list")
		print(f"{Fore.CYAN}{Style.BRIGHT}insert,NewSingerName,next/SingerID{Style.RESET_ALL} = insert a new singer before an existing singer")
		print(f"{Fore.CYAN}{Style.BRIGHT}move,SingerID,next/end/SingerID{Style.RESET_ALL} = move a singer to another position in the list")
		print(f"{Fore.CYAN}{Style.BRIGHT}delete,SingerID{Style.RESET_ALL} = remove a singer from the list")
		print(f"{Fore.CYAN}{Style.BRIGHT}name,SingerID,NewName{Style.RESET_ALL} = rename a singer")
		print()
		print(f"{Fore.CYAN}{Style.BRIGHT}add,list/SingerID,SongTitle[,KeyChange]{Style.RESET_ALL} = add a song to a singer, or to current list")
		print(f"{Fore.CYAN}{Style.BRIGHT}insert,list/SingerID,next/SongID,SongTitle[,KeyChange]{Style.RESET_ALL} = insert a song into a list for a singer")
		print(f"{Fore.CYAN}{Style.BRIGHT}move,list/SingerID,SongID,next/end/SongID{Style.RESET_ALL} = move a song to another position in the list")
		print(f"{Fore.CYAN}{Style.BRIGHT}delete,list/SingerID,SongID{Style.RESET_ALL} = remove a song from a singer")
		print(f"{Fore.CYAN}{Style.BRIGHT}key,list/SingerID,SongID{Style.RESET_ALL} = set the key change on a song")
		print()
		print(f"{Fore.CYAN}{Style.BRIGHT}undo{Style.RESET_ALL} = undo previous command")
		print(f"{Fore.CYAN}{Style.BRIGHT}redo{Style.RESET_ALL} = undo previous undo")
		print()
		print(f"{Fore.CYAN}{Style.BRIGHT}list[,SingerID]{Style.RESET_ALL} = change active song list to show list of songs for specified singer (default is next singer)")
		print(f"{Fore.CYAN}{Style.BRIGHT}play[,SongID]{Style.RESET_ALL} = play song and cycle queue. Defaults to next song.")
		print(f"{Fore.CYAN}{Style.BRIGHT}filler[,SongID]{Style.RESET_ALL} = play song without cycling queue. Defaults to next song.")
		print(f"{Fore.CYAN}{Style.BRIGHT}?searchText{Style.RESET_ALL} = search karaoke tracks for given text")
		print(f"{Fore.CYAN}{Style.BRIGHT}??searchText{Style.RESET_ALL} = search music tracks for given text")
		print(f"{Fore.CYAN}{Style.BRIGHT}cue,SongTitle[,add]{Style.RESET_ALL} = cue up a background music track, optionally adding it to the playlist permanently.")
		print(f"{Fore.CYAN}{Style.BRIGHT}scan[,[quick]analyze]{Style.RESET_ALL} = rescan current folder for tracks, optionally analyzing for problems/duplicates.")
		print(f"{Fore.CYAN}{Style.BRIGHT}zap{Style.RESET_ALL} = clear everything and start from scratch")
		print(f"{Fore.CYAN}{Style.BRIGHT}help{Style.RESET_ALL} = show this screen")
		print(f"{Fore.CYAN}{Style.BRIGHT}quit{Style.RESET_ALL} = quit")
		try:
			input(f"{Fore.WHITE}{Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
		except EOFError:
			pass

	# Cues up a song
	def cue_song(self, params, feedback):
		if not any(params):
			feedback.append(Error("Not enough arguments. Expected song search string."))
		else:
			song = select_song(params[0], self.library.music_files, self.console_size)
			if not song is None:
				feedback.append(Info(f"Added \"{song.title}\" by {song.artist} to the requests queue."))
				try:
					with open(self.config.paths.requests, mode="a", encoding="utf-8") as f:
						f.write(song.path+"\n")
				except PermissionError:
					feedback.append(Error("Failed to write to requests file."))
				if len(params)>1:
					if params[1]=="a" or params[1]=="add":
						try:
							with open(self.config.paths.bgm_playlist, mode="a", encoding="utf-8") as f:
								f.write(f"{song.artist} - {song.title}\n")
						except PermissionError:
							feedback.append(Error("Failed to append to background music playlist file."))

	# Prints the app header
	def show_header(self):
		print(f'{Fore.GREEN}{Style.BRIGHT}Karaoke Manager v{self.VERSION}{Style.RESET_ALL} ({len(self.library.karaoke_files)}/{len(self.library.music_files)} karaoke/music files found)')

	# Print the current list of singers. Groups them into columns.
	def show_singers(self, state):
		singers_with_requests = state.getSingersDisplayList()
		if not any(singers_with_requests):
			print("No singers.")
		else:
			columns_of_singers = []
			dictionary = [{'chunk': chunk, 'index': i} for i, chunk in enumerate(chunks(singers_with_requests, KaraokeManager.SINGERS_PER_COLUMN))]
			columns_of_singers = list(map(lambda item: SingerColumn((item['index']*KaraokeManager.SINGERS_PER_COLUMN)+1, item['chunk']), dictionary))
			for row in range(0, min(len(singers_with_requests), KaraokeManager.SINGERS_PER_COLUMN)):
				print(*map(lambda singerColumn: singerColumn.get_row_text(row), columns_of_singers))

	# Print the list of songs for the current singer, or whatever singer
	# has been flagged as the current "active list" singer.
	def show_songs(self, state, feedback):
		SONG_LIST_INDEX_LENGTH=4 # Two digits, colon and space
		active_singer = state.get_active_song_list_singer()
		if active_singer is None:
			print(f"{Fore.MAGENTA}No current singer selected.{Style.RESET_ALL}")
		else:
			is_song_list_singer_next = (active_singer == state.next_singer())
			if is_song_list_singer_next:
				name_color = f"{Fore.WHITE}"
			else:
				name_color = f"{Fore.MAGENTA}"
			print(f"{Fore.WHITE}Showing song list for {name_color}{Style.BRIGHT}{active_singer.name}{Style.RESET_ALL}:")
			rows_used=min(len(state.singers),KaraokeManager.SINGERS_PER_COLUMN)
			rows_used+=3 # Blank rows (one above and below singers list, and one after this song list)
			rows_used+=2 # App header, and caption for this song list
			rows_used+=2 # Upcoming prompt, and line for user to type on
			rows_used+=len(feedback) # Any errors/messages we need to show the user
			rows_available=self.console_size.lines-rows_used
			songs_in_list=len(active_singer.songs)
			overflow=songs_in_list-rows_available
			if overflow>0:
				rows_available-=1 # Have to show one fewer than that, so that we can show "+n more"

			max_artist_length, max_title_length=active_singer.get_maximum_lengths(rows_available)
			# We need to leave room for the song index, plus any key change indicator (and a column separator before that)
			# The rest of the screen is available for song artist + title
			max_available_space=self.console_size.columns-(SONG_LIST_INDEX_LENGTH+len(COLUMN_SEPARATOR)+Song.KEY_CHANGE_INDICATOR_LENGTH)
			combined_length=max_artist_length+max_title_length+len(COLUMN_SEPARATOR)
			# If the longest artist + longest title bigger than the available space? Scale 'em down.
			if max_available_space<combined_length:
				reduction_factor=max_available_space/combined_length
				max_artist_length=int(max_artist_length*reduction_factor)
				max_title_length=int(max_title_length*reduction_factor)
			for i, song in enumerate(active_singer.songs[:rows_available]):
				song_index = f"{Fore.YELLOW}{Style.BRIGHT}{i+1}{Style.RESET_ALL}"
				if i < 9:
					song_index = f" {song_index}"
				print(f"{song_index}: {song.get_song_list_text(max_artist_length, max_title_length)}")
			if overflow>0:
				print(f"{Fore.GREEN}{Style.BRIGHT}... and {overflow} more.{Style.RESET_ALL}")

	def show_library_report(self):
		if any(self.library.unparseable_filenames) or any(self.library.missing_bgm_playlist_entries) or any(self.library.karaoke_analysis_results) or any(self.library.music_analysis_results) or any(self.library.karaoke_duplicates) or any (self.library.music_duplicates):
			scanCompleteMessage=pad_or_ellipsize("Scan complete.", self.console_size.columns)
			print(f"{Fore.WHITE}{Style.BRIGHT}{scanCompleteMessage}")
			print(f"{Fore.RED}{Style.BRIGHT}Bad filenames:{Style.RESET_ALL} {len(self.library.unparseable_filenames)}")
			print(f"{Fore.GREEN}{Style.BRIGHT}Ignored files:{Style.RESET_ALL} {len(self.library.ignored_files)}")
			print(f"{Fore.YELLOW}{Style.BRIGHT}Artist/title problems:{Style.RESET_ALL} {len(self.library.karaoke_analysis_results)+len(self.library.music_analysis_results)}")
			print(f"{Fore.CYAN}{Style.BRIGHT}Duplicate files:{Style.RESET_ALL} {len(self.library.karaoke_duplicates)+len(self.library.music_duplicates)}")
			print(f"{Fore.MAGENTA}{Style.BRIGHT}Missing playlist entries:{Style.RESET_ALL} {len(self.library.missing_bgm_playlist_entries)}")
			try:
				input("Press Enter to continue ...")
			except EOFError:
				pass

	def rebuild_library(self, analysis_type, feedback):
		self.library.build_song_lists(self.config, analysis_type, self.console_size, feedback)
		self.show_library_report()

	# Processes the given command.
	# Returns true if the command is to quit the app.
	def process_command(self, command, state, feedback):
		if command.command_type == CommandType.HELP:
			self.show_help()
		elif command.command_type == CommandType.QUIT:
			return None
		elif command.command_type == CommandType.ADD:
			state = state.add(command.params, self.library.karaoke_files, self.console_size, feedback)
		elif command.command_type == CommandType.INSERT:
			state = state.insert(command.params, self.library.karaoke_files, self.console_size, feedback)
		elif command.command_type == CommandType.MOVE:
			state = state.move(command.params, feedback)
		elif command.command_type == CommandType.DELETE:
			state = state.delete(command.params, feedback)
		elif command.command_type == CommandType.LIST:
			state = state.list(command.params, feedback)
		elif command.command_type == CommandType.UNDO:
			state = state.undo(feedback)
		elif command.command_type == CommandType.REDO:
			state = state.redo(feedback)
		elif command.command_type == CommandType.SCAN:
			self.rebuild_library(parse_library_analysis_type(command.params), feedback)
		elif command.command_type == CommandType.ZAP:
			state = state.clear()
		elif command.command_type == CommandType.NAME:
			state = state.rename_singer(command.params, feedback)
		elif command.command_type == CommandType.PLAY or command.command_type == CommandType.FILLER:
			state = state.play(command.params, command.command_type == CommandType.PLAY, self.config, feedback)
		elif command.command_type == CommandType.KEY:
			state = state.change_song_key(command.params, feedback)
		elif command.command_type == CommandType.CUE:
			self.cue_song(command.params, feedback)
		elif command.command_type == CommandType.SEARCH:
			show_song_list(command.params[0], self.library.karaoke_files, False, self.console_size)
		elif command.command_type == CommandType.MUSIC_SEARCH:
			show_song_list(command.params[0], self.library.music_files, False, self.console_size)
		return state

	# Asks the user for a command, and parses it
	def get_command(self, feedback):
		try:
			command = input(":")
		except EOFError:
			pass
		command = command.strip()
		if len(command) > 0:
			parsed_command, command_string = parse_command(command)
			if parsed_command is None:
				feedback.append(Error(f"Unknown command: \"{command_string}\""))
			return parsed_command
		return None

	# Shows any info/errors from the previous command
	def show_feedback(self, feedback):
		for message in feedback:
			message.print()

	def run(self):
		clear()
		feedback=[]
		suggestion_generator=SuggestionGenerator(self.config)
		self.rebuild_library(LibraryAnalysisType.NONE, feedback)
		suggestion_generator.start_suggestion_thread(self.library.karaoke_dictionary)
		state = State(self.config, self.library, feedback)
		while not state is None:
			clear()
			state.save(feedback)
			self.show_header()
			print()
			self.show_singers(state)
			print()
			self.show_songs(state, feedback)
			print()
			self.show_feedback(feedback)
			feedback=[]
			print(f"Enter command, or type {Style.BRIGHT}help{Style.NORMAL} to see list of commands.")
			command = self.get_command(feedback)
			if not command is None:
				state=self.process_command(command, state, feedback)
				if command.command_type==CommandType.SCAN:
					suggestion_generator.start_suggestion_thread(self.library.karaoke_dictionary)
		clear()
		suggestion_generator.stop_suggestion_thread()

# Splits a collection into smaller collections of the given size
def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]

def parse_library_analysis_type(params):
	if any(params):
		if params[0] == "quickanalyze" or params[0] == "q":
			return LibraryAnalysisType.QUICK
		if params[0] == "analyze" or params[0] == "a":
			return LibraryAnalysisType.FULL
	return LibraryAnalysisType.NONE