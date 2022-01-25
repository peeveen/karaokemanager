from time import sleep
from colorama import Fore, Style
import sys
from commands import CommandType, parse_command
from exemptions import Exemptions
from state import State
from library import Library
from karaoke_file import KaraokeFile
from singer_column import SingerColumn
from song_selector import select_song, show_song_list
from display_functions import clear, pad_or_ellipsize
from config import Config
from error import Error, Info

# Default YAML config filename
DEFAULT_CONFIG_FILENAME='.yaml'
# Version number
VERSION="1.1"

# Shows onscreen help when the user types "help"
def show_help():
	clear()
	show_header()
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
def cue_song(params, config, music_files, feedback):
	if not any(params):
		feedback.append(Error("Not enough arguments. Expected song search string."))
	else:
		song = select_song(params[0], music_files)
		if not song is None:
			feedback.append(Info(f"Added \"{song.title}\" by {song.artist} to the requests queue."))
			try:
				with open(config.paths.requests_filename, mode="a", encoding="utf-8") as f:
					f.write(song.path+"\n")
			except PermissionError:
				feedback.append(Error("Failed to write to requests file."))
			if len(params)>1:
				if params[1]=="a" or params[1]=="add":
					try:
						with open(config.paths.background_music_list_path, mode="a", encoding="utf-8") as f:
							f.write(f"{song.artist} - {song.title}\n")
					except PermissionError:
						feedback.append(Error("Failed to append to background music playlist file."))

# Prints the app header
def show_header(library):
	print(f'{Fore.GREEN}{Style.BRIGHT}Karaoke Manager v{VERSION}{Style.RESET_ALL} ({len(library.karaoke_files)}/{len(library.music_files)} karaoke/music files found)')

# Splits a collection into smaller collections of the given size
def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]

# Print the current list of singers. Groups them into columns.
def show_singers(state):
	columnSize = 10
	singersWithRequests = state.getSingersDisplayList()
	if not any(singersWithRequests):
		print("No singers.")
	else:
		columnsOfSingers = []
		dictionary = [{'chunk': chunk, 'index': i} for i, chunk in enumerate(chunks(singersWithRequests, columnSize))]
		columnsOfSingers = list(map(lambda item: SingerColumn((item['index']*columnSize)+1, item['chunk']), dictionary))
		for row in range(0, min(len(singersWithRequests), columnSize)):
			print(*map(lambda singerColumn: singerColumn.get_row_text(row), columnsOfSingers))

# Print the list of songs for the current singer, or whatever singer
# has been flagged as the current "active list" singer.
def show_songs(state):
	activeSinger = state.get_active_song_list_singer()
	if activeSinger is None:
		print(f"{Fore.MAGENTA}No current singer selected.{Style.RESET_ALL}")
	else:
		isSongListSingerNext = (activeSinger == state.next_singer())
		if isSongListSingerNext:
			nameColor = f"{Fore.WHITE}"
		else:
			nameColor = f"{Fore.MAGENTA}"
		print(f"{Fore.WHITE}Showing song list for {nameColor}{Style.BRIGHT}{activeSinger.name}{Style.RESET_ALL}:")
		for i, song in enumerate(activeSinger.songs):
			songIndex = f"{Fore.YELLOW}{Style.BRIGHT}{i+1}{Style.RESET_ALL}"
			if i < 9:
				songIndex = f" {songIndex}"
			if isinstance(song.file, KaraokeFile):
				print(f"{songIndex}: {song.file.get_song_list_text(song.key_change)}")
			else:
				print(f"{songIndex}: {song.file.get_song_list_text()}")

# Processes the given command.
# Returns true if the command is to quit the app.
def process_command(command, state, config, library):
	if command.command_type == CommandType.HELP:
		show_help()
	elif command.command_type == CommandType.QUIT:
		return None
	elif command.command_type == CommandType.ADD:
		state = state.add(command.params, library.karaoke_files, feedback)
	elif command.command_type == CommandType.INSERT:
		state = state.insert(command.params, library.karaoke_files, feedback)
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
		library.build_song_lists(command.params, config, feedback)
	elif command.command_type == CommandType.ZAP:
		state = state.clear()
	elif command.command_type == CommandType.NAME:
		state = state.rename_singer(command.params, feedback)
	elif command.command_type == CommandType.PLAY:
		state = state.play(command.params, True, config.driver, feedback)
	elif command.command_type == CommandType.FILLER:
		state = state.play(command.params, False, feedback)
	elif command.command_type == CommandType.KEY:
		state = state.change_song_key(command.params, feedback)
	elif command.command_type == CommandType.CUE:
		cue_song(command.params, config, library.music_files, feedback)
	elif command.command_type == CommandType.SEARCH:
		show_song_list(command.params[0], library.karaoke_files, False)
	elif command.command_type == CommandType.MUSIC_SEARCH:
		show_song_list(command.params[0], library.music_files, False)
	return state

# Asks the user for a command, and parses it
def get_command(feedback):
	try:
		command = input(":")
	except EOFError:
		pass
	command = command.strip()
	if len(command) > 0:
		parsed_command, command_string = parse_command(command, feedback)
		if parsed_command is None:
			feedback.append(Error(f"Unknown command: \"{command_string}\""))
		return parsed_command
	return None

def show_library_report(library):
	if any(library.unparseable_filenames) or any(library.missing_bgm_playlist_entries) or any(library.karaoke_analysis_results) or any(library.music_analysis_results) or any(library.karaoke_duplicates) or any (library.music_duplicates):
		scanCompleteMessage=pad_or_ellipsize("Scan complete.", 119)
		print(f"{Fore.WHITE}{Style.BRIGHT}{scanCompleteMessage}")
		print(f"{Fore.RED}{Style.BRIGHT}Bad filenames:{Style.RESET_ALL} {len(library.unparseable_filenames)}")
		print(f"{Fore.GREEN}{Style.BRIGHT}Ignored files:{Style.RESET_ALL} {len(library.ignored_files)}")
		print(f"{Fore.YELLOW}{Style.BRIGHT}Artist/title problems:{Style.RESET_ALL} {len(library.karaoke_analysis_results)+len(library.music_analysis_results)}")
		print(f"{Fore.CYAN}{Style.BRIGHT}Duplicate files:{Style.RESET_ALL} {len(library.karaoke_duplicates)+len(library.music_duplicates)}")
		print(f"{Fore.MAGENTA}{Style.BRIGHT}Missing playlist entries:{Style.RESET_ALL} {len(library.missing_bgm_playlist_entries)}")
		try:
			input("Press Enter to continue ...")
		except EOFError:
			pass

# Shows any info/errors from the previous command
def show_feedback(feedback):
	for message in feedback:
		message.print()

# Main execution loop
clear()

configPath=DEFAULT_CONFIG_FILENAME
if len(sys.argv)>1:
	configPath=sys.argv[1]

try:
	config=Config(configPath)
except Exception as e:
	print(f"{Fore.RED}Error parsing the configuration file: {e}{Style.RESET_ALL}")
	exit(1)

try:
	exemptions=Exemptions(config)
except Exception as e:
	print(f"{Fore.RED}Error reading an exemptions file: {e}{Style.RESET_ALL}")
	exit(1)

feedback=[]
library = Library(config, exemptions, feedback)
show_library_report(library)
state = State(config, library, feedback)
while True:
	clear()
	state.save(feedback)
	show_header(library)
	print()
	show_singers(state)
	print()
	show_songs(state)
	print()
	show_feedback(feedback)
	feedback=[]
	print(
		f"Enter command, or type {Style.BRIGHT}help{Style.NORMAL} to see list of commands.")
	command = get_command(feedback)
	if not command is None:
		state=process_command(command, state, config, library)
		if state is None:
			break
clear()
library.stop_suggestion_thread()