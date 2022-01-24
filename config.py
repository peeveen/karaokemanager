import yaml
from os import path, makedirs, remove
import importlib
from file_pattern import FilePattern

class Config:
	karaoke_patterns=[]
	music_patterns=[]
	paths = None
	driver = None

	def __init__(self, config_path):
		if path.isfile(config_path):
			config = yaml.safe_load(open(config_path))
			if not config is None:
				self.paths=Paths(config)

				self.karaoke_patterns=get_patterns(config,"karaoke")
				if not any(self.karaoke_patterns):
					raise Exception("No karaoke file patterns defined.")
				self.music_patterns=get_patterns(config,"music")
				if any(self.paths.music) and not any(self.music_patterns):
					raise Exception("No music file patterns defined.")

				self.driver=create_driver(config)
				return
			raise Exception("Failed to parse YAML configuration.")
		raise Exception("{config_path} not found.")

def create_driver(config):
	driverConfig=config.get("driver")
	if driverConfig is None:
		raise Exception("No 'driver' section in configuration file.")
	else:
		driverClassString=get_config_string(driverConfig,"class",True)
		driverSpecificConfig=driverConfig.get(driverClassString)
		if driverSpecificConfig is None:
			raise Exception("No driver-specific config section found in configuration file.")
		else:
			components = driverClassString.split('.')
			if len(components)<3:
				raise Exception("Driver class string should be in the format 'packagename.modulename.classname'")
			else:
				upperBound=len(components)-1
				package=components[0]
				module=".".join(components[1:upperBound])
				className=components[upperBound]
				module = importlib.import_module(module, package)
				driverClass = getattr(module, className)
				return driverClass(driverSpecificConfig)

def get_config_string(config, name, required):
	if name in config:
		value=config.get(name)
		if isinstance(value, str):
			value=value.strip()
			if len(value)>0:
				return value
	if required:
		raise Exception("No string value found for '{name}' in YAML config file.")
	return None

def get_patterns(config,section):
	patterns=[]
	if section in config:
		section_config=config[section]
		if "patterns" in section_config:
			unparsed_patterns=section_config["patterns"]
			patterns=list(map(lambda unparsed_pattern: parse_file_pattern(unparsed_pattern), unparsed_patterns))
	return patterns

def get_paths(config,section,required):
	paths=[]
	if section in config:
		section_config=config[section]
		if "paths" in section_config:
			paths=section_config["paths"]
	if required and not any(paths):
		raise Exception("No paths defined in '{section}' section")
	return paths

def is_string_list(l):
	if isinstance(l,list):
		return all(map(lambda item: isinstance(item, str), l))
	return False
	
def parse_file_pattern(pattern_config):
	regular_expression=get_config_string(pattern_config,"regExp",True)
	group_names=pattern_config.get("groupNames")
	extensions=pattern_config.get("extensions")
	if group_names is None or not is_string_list(group_names):
		raise Exception("No groupNames defined for pattern.")
	if extensions is None or not is_string_list(extensions):
		raise Exception("No extensions defined for pattern.")
	return FilePattern(extensions,regular_expression,group_names)
	
class Paths:
	# Filename of the background music list file (just artist & titles)
	BACKGROUND_MUSIC_PLAYLIST_FILENAME = "BackgroundMusicPlaylist.txt"
	# Filename of the background music manifest (full paths, calculated from playlist)	
	BACKGROUND_MUSIC_MANIFEST_FILENAME = "KaraokeManager.backgroundMusic.txt"
	# Filename of the requests file that we can write to.
	MUSIC_REQUESTS_FILENAME="KaraokeManager.musicRequests.txt"
	# Name of file that we will write to when we find malformed filenames.
	FILENAME_ERRORS_FILENAME = "BadFilenames.txt"
	# Name of file that we will write to when we find BackgroundMusicPlaylist entries that do not correspond
	# to a known music file.
	MISSING_PLAYLIST_ENTRIES_FILENAME = "MissingPlaylistEntries.txt"
	# Name of file that we will write to when we find possible duplicates of music files.
	MUSIC_DUPLICATES_FILENAME = "MusicDuplicates.txt"
	# Name of file that we will write to when we find possible duplicates of karaoke files.
	KARAOKE_DUPLICATES_FILENAME = "KaraokeDuplicates.txt"
	# Name of file that we will write to when we find karaoke files with artist and/or title problems.
	KARAOKE_ERRORS_FILENAME = "KaraokeArtistAndTitlesProblems.txt"
	# Name of file that we will write to when we find music files with artist and/or title problems.
	MUSIC_ERRORS_FILENAME = "MusicArtistAndTitleProblems.txt"
	# Name of file that we will write to with a list of files that we ignored
	IGNORED_FILES_FILENAME = "IgnoredFiles.txt"
	# File that we write a random song suggestion to periodically.
	SONG_SUGGESTION_FILENAME="KaraokeManager.songSuggestion.txt"
	# Filename to persist the state to.
	# Gets written after every command, in case the app crashes.
	STATE_FILENAME = "KaraokeManager.state.txt"
	# Filename to persist the list of singers to.
	# Gets written after every command, in the case the app crashes.
	# Gets read by the Winamp SingersQueue plugin to show the current queue onscreen.
	SINGERS_QUEUE_FILENAME = "KaraokeManager.singers.txt"
	# List of reversal exemptions. If we find a music file by "Chas & Dave", and one by "Dave & Chas",
	# this will be flagged as a problem unless there is a line in the ReversalExemptions file
	# declaring this reversal to be exempt from challenge. Each line in this file should be two
	# string separated by a tab, for example "Chas\tDave".
	REVERSAL_EXEMPTIONS_FILENAME = "ReversalExemptions.txt"
	# List of "the" exemptions. Usually, if we find a music file by an artist/group that also exists
	# prefixed by "The" (e.g. one file by "Rolling Stones" and one by "The Rolling Stones") then this
	# will be flagged as a problem, unless an exemption is listed in this file. Either of the two
	# values can be used.
	THE_EXEMPTIONS_FILENAME = "TheExemptions.txt"
	# Normally, we want artist names and song titles to be capitalised. However, some annoyances
	# exist (e.g. "k.d. lang"). List them in this file to make them exempt from challenge.
	LOWER_CASE_EXEMPTIONS_FILENAME = "LowerCaseExemptions.txt"
	# If we find two artist names or song titles that look INCREDIBLY similar, we flag them as
	# potential duplicates with an unintentional typo. However, sometimes this yields false positives.
	# List them in this file to get rid of them, with both values separated by a tab.
	SIMILARITY_EXEMPTIONS_FILENAME = "SimilarityExemptions.txt"

	requests=None
	bgm_manifest=None
	bgm_playlist=None
	random_suggestion=None
	karaoke_duplicates=None
	music_duplicates=None
	filename_errors=None
	missing_playlist_entries=None
	karaoke_errors=None
	music_errors=None
	ignored_files=None
	reversal_exemptions=None
	the_exemptions=None
	lower_case_exemptions=None
	similarity_exemptions=None

	def __init__(self, config):
		data_path=get_config_string(config,'dataPath',True)
		temp_data_path=get_config_string(config,'tempDataPath',True)

		if not path.isdir(temp_data_path):
			makedirs(temp_data_path)
		if not path.isdir(data_path):
			makedirs(data_path)

		bgm_playlist_filename=self.BACKGROUND_MUSIC_PLAYLIST_FILENAME
		musicConfig=config.get("music")
		if not musicConfig is None:
			temp = get_config_string(musicConfig, "backgroundMusicPlaylistFilename", False)
			if not temp is None:
				bgm_playlist_filename=temp

		self.requests = path.join(temp_data_path, self.MUSIC_REQUESTS_FILENAME)
		self.bgm_playlist = path.join(data_path,bgm_playlist_filename)
		self.bgm_manifest = path.join(temp_data_path, self.BACKGROUND_MUSIC_MANIFEST_FILENAME)
		self.music_duplicates=path.join(data_path,self.MUSIC_DUPLICATES_FILENAME)
		self.karaoke_duplicates=path.join(data_path,self.KARAOKE_DUPLICATES_FILENAME)
		self.music_errors=path.join(data_path,self.MUSIC_ERRORS_FILENAME)
		self.karaoke_errors=path.join(data_path,self.KARAOKE_ERRORS_FILENAME)
		self.random_suggestion = path.join(temp_data_path, self.SONG_SUGGESTION_FILENAME)
		self.filename_errors=path.join(data_path,self.FILENAME_ERRORS_FILENAME)
		self.missing_playlist_entries=path.join(data_path,self.MISSING_PLAYLIST_ENTRIES_FILENAME)
		self.ignored_files=path.join(data_path,self.IGNORED_FILES_FILENAME)
		self.state=path.join(temp_data_path,self.STATE_FILENAME)
		self.singers_queue=path.join(temp_data_path,self.SINGERS_QUEUE_FILENAME)
		self.reversal_exemptions=path.join(data_path,self.REVERSAL_EXEMPTIONS_FILENAME)
		self.the_exemptions=path.join(data_path,self.THE_EXEMPTIONS_FILENAME)
		self.lower_case_exemptions=path.join(data_path,self.LOWER_CASE_EXEMPTIONS_FILENAME)
		self.similarity_exemptions=path.join(data_path,self.SIMILARITY_EXEMPTIONS_FILENAME)

		self.karaoke=get_paths(config, "karaoke", True)
		self.music=get_paths(config, "music", False)

		if path.exists(self.requests):
			remove(self.requests)