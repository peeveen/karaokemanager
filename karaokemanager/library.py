from collections import defaultdict
from colorama import Fore, Style
from textdistance import levenshtein
from os import path, walk
from time import sleep
from karaokemanager.display_functions import pad_or_ellipsize
from karaokemanager.karaoke_file import KaraokeFile
from karaokemanager.music_file import MusicFile
from karaokemanager.error import Error
from enum import Enum, auto

# How deep should the library analysis be?
class LibraryAnalysisType(Enum):
	NONE = auto()
	QUICK = auto()
	FULL = auto()

class Library:
	# Current background music playlist (strings from the BackgroundMusicPlaylist file)
	background_music_playlist = set([])
	# List of karaoke files (KaraokeFile objects)
	karaoke_files = []
	# List of music files (MusicFile objects)
	music_files = []
	# Dictionary of karaoke files. Key is artist, value is another dictionary of karaoke files
	# where the key is the song title, and the value is a list of tracks from one or more vendors.
	karaoke_dictionary = defaultdict()
	# Dictionary of music files. Key is artist, value is another dictionary of music files
	# where the key is the song title, and the value is a list of tracks with that title.
	music_dictionary = defaultdict()
	# Files that were ignored
	ignored_files=[]
	# Full manifest of BGM paths
	bgm_manifest=[]
	# All our lovely exemption info
	exemptions=None
	# BGM playlist entries that did not match a music file.
	missing_bgm_playlist_entries=[]
	# Filenames that matched an extension of a pattern, but failed the regex.
	unparseable_filenames=[]
	# Duplicates found during a scan
	karaoke_duplicates=[]
	music_duplicates=[]
	# Analysis errors found during a quick or full analysis of the fileset
	karaoke_analysis_results=[]
	# Analysis errors found during a quick or full analysis of the fileset
	music_analysis_results=[]

	def __init__(self,exemptions):
		self.exemptions = exemptions

	# Reads the background music playlist into memory
	def get_background_music_playlist(self, config):
		playlist = set([])
		backgroundMusicFilePath=config.paths.bgm_playlist
		if path.isfile(backgroundMusicFilePath):
			with open(backgroundMusicFilePath, mode="r", encoding="utf-8") as f:
				lines = f.readlines()
				for line in lines:
					line = line.strip()
					if(len(line) > 0):
						playlist.add(line.lower())
		return playlist

	# Builds the dictionaries of karaoke and music tracks
	def build_dictionaries(self):
		self.karaoke_dictionary = defaultdict()
		for songFile in self.karaoke_files:
			self.karaoke_dictionary.setdefault(songFile.artist, defaultdict()).setdefault(
				songFile.title, []).append(songFile)
		self.music_dictionary = defaultdict()
		for songFile in self.music_files:
			self.music_dictionary.setdefault(songFile.artist, defaultdict()).setdefault(
				songFile.title, []).append(songFile)

	# Builds the karaoke and music lists by analysing folder contents.
	def build_song_lists(self, config, analysis_type, console_size, feedback):
		bgm_playlist=self.get_background_music_playlist(config)

		def create_karaoke_file(path, group_map):
			vendor=group_map["vendor"]
			if vendor is None:
				vendor="UNKNOWN"
			return KaraokeFile(path,group_map["artist"],group_map["title"],vendor)

		def create_music_file(path, group_map):
			return MusicFile(path,group_map["artist"],group_map["title"])

		def parse_filename(path, filename, patterns, file_builder):
			name_without_extension, extension = path.splitext(filename)
			extension=extension.strip('.')
			valid_patterns=list(filter(lambda pattern: pattern.extension_matches(extension), patterns))
			if any(valid_patterns):
				for pattern in valid_patterns:
					group_map = pattern.parse_filename(name_without_extension)
					if any(group_map):
						file=file_builder(path, group_map)
						if not file is None:
							return file
				self.unparseable_filenames.append(filename)
			else:
				self.ignored_files.append(filename)
			return None

		# Tries to parse a karaoke file, adding it to a collection if successful.
		def scan_karaoke_file(root, file):
			karaokeFile = parse_filename(path.join(root,file), file, config.karaoke_patterns, create_karaoke_file)
			if not karaokeFile is None:
				self.karaoke_files.append(karaokeFile)

		# Tries to parse a music file, adding it to a collection if successful.
		def scan_music_file(root, file):
			full_path = path.join(root,file)
			music_file = parse_filename(full_path, file, config.music_patterns, create_music_file)
			if not music_file is None:
				name_without_extension, _ = path.splitext(file)
				name_without_extension=name_without_extension.lower()
				if name_without_extension in bgm_playlist:
					self.bgm_manifest.append(full_path)
					bgm_playlist.remove(name_without_extension)
				self.music_files.append(music_file)

		# Scans the files in one or more folders.
		def scan_files(file_paths, scan_file_function):
			for filePath in file_paths:
				for root, _, files in walk(filePath):
					print(pad_or_ellipsize(f"Scanning {root}", console_size.columns), end="\r")
					for file in files:
						scan_file_function(root,file)

		# Writes a list of strings to a text file.
		def write_text_file(item_list,path,errors):
			try:
				with open(path, mode="w", encoding="utf-8") as f:
					for item in item_list:
						f.writelines(f"{item}\n")
			except PermissionError:
				errors.append(Error(f"Failed to write to '{path}'."))

		self.bgm_manifest=[]
		self.ignored_files=[]
		self.karaoke_files=[]
		self.music_files=[]
		self.unparseable_filenames=[]
		scan_files(config.paths.karaoke,scan_karaoke_file)
		scan_files(config.paths.music,scan_music_file)
		# Whatever's left in the background music playlist will be missing files.
		self.missing_bgm_playlist_entries=bgm_playlist

		self.build_dictionaries()

		self.music_duplicates=[]
		self.karaoke_duplicates=[]
		self.karaoke_analysis_results=[]
		self.music_analysis_results=[]
		if analysis_type != LibraryAnalysisType.NONE:
			print(pad_or_ellipsize(f"Analyzing karaoke files...", console_size.columns))
			self.karaoke_duplicates, self.karaoke_analysis_results=self.analyze_file_set(self.karaoke_files,self.karaoke_dictionary, analysis_type, console_size)
			print(pad_or_ellipsize(f"Analyzing music files...", console_size.columns))
			self.music_duplicates, self.music_analysis_results=self.analyze_file_set(self.music_files,self.music_dictionary, analysis_type, console_size)

		write_text_file(self.unparseable_filenames,config.paths.filename_errors,feedback)
		write_text_file(self.ignored_files,config.paths.ignored_files,feedback)
		write_text_file(bgm_playlist,config.paths.missing_playlist_entries,feedback)
		write_text_file(self.bgm_manifest,config.paths.bgm_manifest,feedback)
		write_text_file(self.karaoke_duplicates,config.paths.karaoke_duplicates,feedback)
		write_text_file(self.music_duplicates,config.paths.music_duplicates,feedback)
		write_text_file(self.karaoke_analysis_results,config.paths.karaoke_analysis_results,feedback)
		write_text_file(self.music_analysis_results,config.paths.music_analysis_results,feedback)

		# Helper function for dictionary sorting.
		def get_music_file_key(file):
			return file.artist
		self.music_files.sort(key=get_music_file_key)
		self.karaoke_files.sort(key=get_music_file_key)

	# Scans a list of files for potential duplicates, bad filenames, etc.
	def analyze_file_set(self,files,dictionary,analysis_type, console_size):
		analysis_results=[]
		duplicates=[]
		# Checks two strings for similarity.
		def similarity(s1, s2):
			longer_length = max(len(s1),len(s2))
			if longer_length == 0:
				return 1.0
			return (longer_length - levenshtein(s1, s2)) / longer_length

		artists = set([])
		artist_list = []
		artist_lower_list = []

		last_percent = -1
		counter = 0
		song_progress_count = len(dictionary)
		for artist, song_dict in dictionary.items():
			counter += 1
			percent = round((counter/song_progress_count)*100.0)
			if percent > last_percent:
				print(pad_or_ellipsize(f"Looking for duplicates: {percent}% done", console_size.columns), end="\r")
				last_percent = percent
			for song_collection in song_dict.values():
				if len(song_collection)>1:
					duplicates.extend(map(lambda song: f"{song.artist} - {song.title}", song_collection[1:]))
		for song in files:
			if not song.artist in artists:
				artists.add(song.artist)
				artist_list.append(song.artist)
				artist_lower_list.append(song.lower_artist)
		for artist in artists:
			first_letter = artist[0]
			if first_letter.isalpha() and first_letter.islower():
				if not self.exemptions.is_exempt_from_lower_case_check(artist):
					error = f"Artist \"{artist}\" is not capitalised."
					analysis_results.append(error)
			if artist.startswith("The "):
				if artist[4:] in artists and not self.exemptions.is_exempt_from_the_check(artist):
					error = f"Artist \"{artist}\" has a non-The variant."
					analysis_results.append(error)
		artist_count = len(artist_list)
		song_count = len(files)
		song_progress_count = round((song_count*song_count)/2)
		artist_progress_count = round((artist_count*artist_count)/2)
		counter = 0
		last_percent = -1
		for i in range(0, artist_count):
			artist = artist_list[i]
			artist_lower = artist_lower_list[i]
			ampersand_first_index = artist.find(" & ")
			ampersand_last_index = artist.rfind(" & ")
			if ampersand_first_index != -1 and ampersand_last_index == ampersand_first_index:
				bit1 = artist[0:ampersand_first_index]
				bit2 = artist[ampersand_first_index+3:]
				if bit2 != bit1:
					if not self.exemptions.is_exempt_from_reversal_check(bit1, bit2):
						reverse_check = bit2+" & "+bit1
						if reverse_check in artists:
							error = f"Artist \"{artist}\" also appears as \"{reverse_check}\"."
							analysis_results.append(error)
			for j in range(i+1, artist_count):
				counter += 1
				percent = round((counter/artist_progress_count)*100.0)
				if percent > last_percent:
					print(pad_or_ellipsize(f"Analyzing artists: {percent}% done", console_size.columns), end="\r")
					last_percent = percent
				compare_artist = artist_list[j]
				compare_artist_lower = artist_lower_list[j]
				if artist_lower == compare_artist_lower and artist != compare_artist:
					error = f"Artist \"{artist}\" has a case variation: \"{compare_artist}\"."
					analysis_results.append(error)
		song_progress_count = round((song_count*song_count)/2)
		counter = 0
		last_percent = -1
		for i in range(0, song_count):
			song_file = files[i]
			song_title = song_file.title
			song_title_lower = song_file.lower_title
			first_letter = song_title[0]
			if first_letter.isalpha() and first_letter.islower():
				if not self.exemptions.is_exempt_from_lower_case_check(song_title):
					error = f"Title \"{song_title}\" is not capitalised."
					analysis_results.append(error)
			for j in range(i+1, song_count):
				counter += 1
				percent = round((counter/song_progress_count)*100.0)
				if percent > last_percent:
					print(pad_or_ellipsize(f"Analyzing song titles (simple analysis): {percent}% done", console_size.columns), end="\r")
					last_percent = percent
				compare_title = files[j].title
				compare_title_lower = files[j].lower_title
				if song_title != compare_title:
					if song_title_lower == compare_title_lower:
						error = f"Title \"{song_title}\" has a case variation: \"{compare_title}\"."
						analysis_results.append(error)
		last_percent = -1
		counter = 0
		song_progress_count = len(dictionary)
		if LibraryAnalysisType.FULL == analysis_type:
			for artist, song_dict in dictionary.items():
				counter += 1
				percent = round((counter/song_progress_count)*100.0)
				if percent > last_percent:
					print(pad_or_ellipsize(f"Analyzing song titles (complex analysis): {percent}% done", console_size.columns), end="\r")
					last_percent = percent
				keys = list(song_dict.keys())
				for i in range(0, len(keys)):
					for j in range(i+1, len(keys)):
						if not self.exemptions.is_exempt_from_similarity_check(keys[i], keys[j]):
							similarity_calculation = similarity(keys[i], keys[j])
							if similarity_calculation < 1.0 and similarity_calculation > 0.9:
								error = f"Title \"{keys[i]}\" looks very similar to \"{keys[j]}\"."
								analysis_results.append(error)
		return duplicates, analysis_results