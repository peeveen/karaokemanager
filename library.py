from collections import defaultdict
from colorama import Fore, Style
from textdistance import levenshtein
from os import path, walk
from time import sleep
from display_functions import pad_or_ellipsize
from karaoke_file import KaraokeFile
from music_file import MusicFile
from error import Error
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
	def build_song_lists(self, config, analysis_type, feedback):
		bgm_playlist=self.get_background_music_playlist(config)

		def create_karaoke_file(path, groupMap):
			vendor=groupMap["vendor"]
			if vendor is None:
				vendor="UNKNOWN"
			return KaraokeFile(path,groupMap["artist"],groupMap["title"],vendor)

		def create_music_file(path, groupMap):
			return MusicFile(path,groupMap["artist"],groupMap["title"])

		def parse_filename(filePath, filename, patterns, fileBuilder):
			nameWithoutExtension, extension = path.splitext(filename)
			extension=extension.strip('.')
			validPatterns=list(filter(lambda pattern: pattern.extension_matches(extension), patterns))
			if any(validPatterns):
				for pattern in validPatterns:
					groupMap = pattern.parse_filename(nameWithoutExtension)
					if any(groupMap):
						file=fileBuilder(filePath, groupMap)
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
			musicFile = parse_filename(full_path, file, config.music_patterns, create_music_file)
			if not musicFile is None:
				fileWithoutExtension = file[0:-4]
				if fileWithoutExtension in self.bgm_playlist:
					self.bgm_manifest.append(full_path)
					bgm_playlist.remove(fileWithoutExtension)
				self.music_files.append(musicFile)

		# Scans the files in one or more folders.
		def scan_files(filePaths,scanFileFunction):
			for filePath in filePaths:
				for root, _, files in walk(filePath):
					print(pad_or_ellipsize(f"Scanning {root}", 119), end="\r")
					for file in files:
						scanFileFunction(root,file)

		# Writes a list of strings to a text file.
		def write_text_file(itemList,path,errors):
			try:
				with open(path, mode="w", encoding="utf-8") as f:
					for item in itemList:
						f.writelines(f"{item}\n")
			except PermissionError:
				errors.append(Error(f"Failed to write to '{path}'."))

		self.backgroundMusic=[]
		self.ignoredFiles=[]
		self.karaoke_files=[]
		self.music_files=[]
		scan_files(config.paths.karaoke,scan_karaoke_file)
		scan_files(config.paths.music,scan_music_file)
		# Whatever's left in the background music playlist will be missing files.
		self.missing_bgm_playlist_entries=bgm_playlist

		self.build_dictionaries()
		self.start_suggestion_thread(config)

		self.music_duplicates=[]
		self.karaoke_duplicates=[]
		self.karaoke_analysis_results=[]
		self.music_analysis_results=[]
		if analysis_type != LibraryAnalysisType.NONE:
			print(pad_or_ellipsize(f"Analyzing karaoke files...", 119))
			self.karaoke_duplicates, self.karaoke_analysis_results=self.analyze_file_set(self.karaoke_files,self.karaoke_dictionary, analysis_type)
			print(pad_or_ellipsize(f"Analyzing music files...", 119))
			self.music_duplicates, self.music_analysis_results=self.analyze_file_set(self.music_files,self.music_dictionary, analysis_type)

		write_text_file(self.unparseable_filenames,config.paths.filename_errors,feedback)
		write_text_file(self.ignored_files,config.paths.ignored_files,feedback)
		write_text_file(bgm_playlist,config.paths.missing_playlist_entries,feedback)
		write_text_file(self.bgm_manifest,config.paths.bgm_manifest,feedback)
		write_text_file(self.karaoke_duplicates,config.paths.karaoke_duplicates,feedback)
		write_text_file(self.music_duplicates,config.paths.music_duplicates,feedback)
		write_text_file(self.karaoke_analysis_results,config.paths.karaoke_analysis_results,feedback)
		write_text_file(self.music_analysis_results,config.paths.music_analysis_results,feedback)

		# Helper function for dictionary sorting.
		def getMusicFileKey(file):
			return file.artist
		self.music_files.sort(key=getMusicFileKey)
		self.karaoke_files.sort(key=getMusicFileKey)

	# Scans a list of files for potential duplicates, bad filenames, etc.
	def analyze_file_set(self,files,dictionary,analysis_type):
		analysis_results=[]
		duplicates=[]
		# Checks two strings for similarity.
		def similarity(s1, s2):
			longerLength = max(len(s1),len(s2))
			if longerLength == 0:
				return 1.0
			return (longerLength - levenshtein(s1, s2)) / longerLength

		artists = set([])
		artistList = []
		artistLowerList = []

		lastPercent = -1
		counter = 0
		songProgressCount = len(dictionary)
		for artist, songDict in dictionary.items():
			counter += 1
			percent = round((counter/songProgressCount)*100.0)
			if percent > lastPercent:
				print(pad_or_ellipsize(f"Looking for duplicates: {percent}% done", 119), end="\r")
				lastPercent = percent
			for songCollection in songDict.values():
				if len(songCollection)>1:
					duplicates.extend(map(lambda song: f"{song.artist} - {song.title}", songCollection[1:]))
		for song in files:
			if not song.artist in artists:
				artists.add(song.artist)
				artistList.append(song.artist)
				artistLowerList.append(song.lower_artist)
		for artist in artists:
			firstletter = artist[0]
			if firstletter.isalpha() and firstletter.islower():
				if not self.exemptions.is_exempt_from_lower_case_check(artist):
					error = f"Artist \"{artist}\" is not capitalised."
					analysis_results.append(error)
			if artist.startswith("The "):
				if artist[4:] in artists and not self.exemptions.is_exempt_from_the_check(artist):
					error = f"Artist \"{artist}\" has a non-The variant."
					analysis_results.append(error)
		artistCount = len(artistList)
		songCount = len(files)
		songProgressCount = round((songCount*songCount)/2)
		artistProgressCount = round((artistCount*artistCount)/2)
		counter = 0
		lastPercent = -1
		for i in range(0, artistCount):
			artist = artistList[i]
			artistLower = artistLowerList[i]
			ampersandFirstIndex = artist.find(" & ")
			ampersandLastIndex = artist.rfind(" & ")
			if ampersandFirstIndex != -1 and ampersandLastIndex == ampersandFirstIndex:
				bit1 = artist[0:ampersandFirstIndex]
				bit2 = artist[ampersandFirstIndex+3:]
				if bit2 != bit1:
					if not self.exemptions.is_exempt_from_reversal_check(bit1, bit2):
						reverseCheck = bit2+" & "+bit1
						if reverseCheck in artists:
							error = f"Artist \"{artist}\" also appears as \"{reverseCheck}\"."
							analysis_results.append(error)
			for j in range(i+1, artistCount):
				counter += 1
				percent = round((counter/artistProgressCount)*100.0)
				if percent > lastPercent:
					print(pad_or_ellipsize(f"Analyzing artists: {percent}% done", 119), end="\r")
					lastPercent = percent
				compareArtist = artistList[j]
				compareArtistLower = artistLowerList[j]
				if artistLower == compareArtistLower and artist != compareArtist:
					error = f"Artist \"{artist}\" has a case variation: \"{compareArtist}\"."
					analysis_results.append(error)
		songProgressCount = round((songCount*songCount)/2)
		counter = 0
		lastPercent = -1
		for i in range(0, songCount):
			songFile = files[i]
			songTitle = songFile.title
			songTitleLower = songFile.lower_title
			firstletter = songTitle[0]
			if firstletter.isalpha() and firstletter.islower():
				if not self.exemptions.is_exempt_from_lower_case_check(songTitle):
					error = f"Title \"{songTitle}\" is not capitalised."
					analysis_results.append(error)
			for j in range(i+1, songCount):
				counter += 1
				percent = round((counter/songProgressCount)*100.0)
				if percent > lastPercent:
					print(pad_or_ellipsize(f"Analyzing song titles (simple analysis): {percent}% done", 119), end="\r")
					lastPercent = percent
				compareTitle = files[j].title
				compareTitleLower = files[j].lower_title
				if songTitle != compareTitle:
					if songTitleLower == compareTitleLower:
						error = f"Title \"{songTitle}\" has a case variation: \"{compareTitle}\"."
						analysis_results.append(error)
		lastPercent = -1
		counter = 0
		songProgressCount = len(dictionary)
		if analysis_type==LibraryAnalysisType.Full:
			for artist, songDict in dictionary.items():
				counter += 1
				percent = round((counter/songProgressCount)*100.0)
				if percent > lastPercent:
					print(pad_or_ellipsize(f"Analyzing song titles (complex analysis): {percent}% done"), end="\r")
					lastPercent = percent
				keys = list(songDict.keys())
				for i in range(0, len(keys)):
					for j in range(i+1, len(keys)):
						if not self.exemptions.is_exempt_from_similarity_check(keys[i], keys[j]):
							similarityCalc = similarity(keys[i], keys[j])
							if similarityCalc < 1.0 and similarityCalc > 0.9:
								error = f"Title \"{keys[i]}\" looks very similar to \"{keys[j]}\"."
								analysis_results.append(error)
		return duplicates, analysis_results