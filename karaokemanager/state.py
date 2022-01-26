from os import path
from copy import deepcopy
from karaokemanager.singer import Singer
from karaokemanager.song_selector import select_song
from karaokemanager.song import Song
from karaokemanager.error import Error

# Current state of the app.
class State:
	singers = None
	active_song_list_singer_name = None
	next_state = None
	prev_state = None
	state_path = None
	queue_path = None	

	def __init__(self, config, library, errors):
		self.state_path = config.paths.state
		self.queue_path = config.paths.singers_queue
		self.load(library.karaoke_files, errors)

	# Load the last saved state.
	def load(self, karaokeFiles, errors):
		self.singers = []
		if path.isfile(self.state_path):
			with open(self.state_path, mode="r", encoding="utf-8") as f:
				lines = f.readlines()
				current_singer = None
				for line in lines:
					if line.startswith("\t"):
						if not current_singer is None:
							lineBits = line.strip().split("|")
							karaoke_file = get_karaoke_file_from_path(lineBits[0], karaokeFiles)
							key_change = get_key_change_value(lineBits[1].strip(), errors)
							if key_change!=-99:
								if not karaoke_file is None:
									current_singer.songs.append(Song(karaoke_file, key_change))
					else:
						if not current_singer is None:
							self.singers.append(current_singer)
						if len(line) > 0:
							current_singer = Singer(line.strip())
				if not current_singer is None:
					self.singers.append(current_singer)

	def save(self, errors):
		try:
			with open(self.state_path, mode="w", encoding="utf-8") as f:
				for singer in self.singers:
					singer.write_to_state_file(f)
		except PermissionError:
			errors.append(Error("Failed to write state file."))
		try:
			with open(self.queue_path, mode="w", encoding="utf-8") as f:
				for singer in self.singers:
					singer.write_to_queue_file(f)
		except PermissionError:
			errors.append(Error("Failed to write singer names file."))

	def getSingersDisplayList(self):
		singersCopy = self.singers.copy()
		return singersCopy

	# Make a deep copy of the current state, ready for alteration.
	# We create a chain of previous/next states for undo/redo.
	def mutate(self):
		new_state = deepcopy(self)
		self.next_state = new_state
		new_state.prev_state = self
		return new_state

	def get_singer_index_from_id(self, id, end_allowed, req_allowed, errors):
		if id.isdigit():
			singer_index = int(id)
			if singer_index <= 0 or singer_index > len(self.singers):
				errors.append(Error(f"Singer index out of bounds: it must be between 1 and {len(self.singers)}"))
				return None
			return singer_index-1
		id = id.lower()
		if len(self.singers) > 0:
			if id == "next" or id == "n":
				return 0
			if id == "end" or id == "e":
				return len(self.singers)
		if id == "list" or id == "l":
			if not self.active_song_list_singer_name is None:
				id = self.active_song_list_singer_name.lower()
			else:
				next_singer = self.next_singer()
				if not next_singer is None:
					id = next_singer.name.lower()
				else:
					errors.append(Error("There is no active song list to add to."))
					return None
		for i, singer in enumerate(self.singers):
			if singer.name.lower() == id:
				return i
		matches = []
		for i, singer in enumerate(self.singers):
			if id in singer.name.lower():
				matches.append(i)
		if len(matches) == 0:
			errors.append(Error(f"No match found for given singer ID \"{id}\""))
			return None
		if len(matches) > 1:
			errors.append(Error(f"Multiple matches found for given singer ID \"{id}\""))
			return None
		return matches[0]

	def get_singer_from_id(self, id, end_allowed, req_allowed, errors):
		singer_index = self.get_singer_index_from_id(id, end_allowed, req_allowed, errors)
		if singer_index is None:
			return None
		return self.singers[singer_index]

	def add_new_singer(self, singer_name, index, errors):
		same_name_singers = [
			singer for singer in self.singers if singer.name.lower() == singer_name.lower()]
		if len(same_name_singers) > 0:
			errors.append(Error(f"Singer with name \"{singer_name}\" already exists."))
		else:
			new_state = self.mutate()			
			new_state.singers.insert(index, Singer(singer_name))
			return new_state
		return self

	def delete_singer(self, singer_id, errors):
		matched_singer_index = self.get_singer_index_from_id(singer_id, False, False, errors)
		if not matched_singer_index is None:
			new_state = self.mutate()
			del new_state.singers[matched_singer_index]
			return new_state
		return self

	def delete_song_from_singer(self, singer_id, song_id, errors):
		matched_singer_index = self.get_singer_index_from_id(singer_id, False, False, errors)
		if not matched_singer_index is None:
			matched_singer = self.singers[matched_singer_index]
			matched_song_index = matched_singer.get_song_index_from_id(song_id, False, errors)
			if not matched_song_index is None:
				new_state = self.mutate()
				del new_state.singers[matched_singer_index].songs[matched_song_index]
				return new_state
		return self

	def insert_new_singer(self, singer_name, singer_id, errors):
		matched_singer_index = self.get_singer_index_from_id(singer_id, True, False, errors)
		if not matched_singer_index is None:
			return self.add_new_singer(singer_name, matched_singer_index, errors)
		return self

	def move_singer(self, singer_to_move_id, singer_id, errors):
		matched_singer_to_move_index = self.get_singer_index_from_id(singer_to_move_id, False, False, errors)
		if not matched_singer_to_move_index is None:
			matched_singer_index = self.get_singer_index_from_id(singer_id, True, False, errors)
			if not matched_singer_index is None:
				new_state = self.mutate()
				singer_to_move = new_state.singers[matched_singer_to_move_index]
				del new_state.singers[matched_singer_to_move_index]
				new_state.singers.insert(matched_singer_index, singer_to_move)
				return new_state
		return self

	def add_song_for_singer(self, singer_id, song_title, key_change, index, karaoke_files, console_size, errors):
		key_change_value = get_key_change_value(key_change, errors)
		if key_change_value != -99:
			matched_singer = self.get_singer_from_id(singer_id, False, True, errors)
			if not matched_singer is None:
				karaoke_song = select_song(song_title, karaoke_files, console_size)
				if not karaoke_song is None:
					if index == -1:
						index = len(matched_singer.songs)
					new_state = self.mutate()
					matched_singer = new_state.get_singer_from_id(singer_id, False, True, errors)
					matched_singer.insert_song(index, Song(karaoke_song, key_change_value))
					return new_state
		return self

	def insert_song_for_singer(self, singer_id, song_id, song_title, key_change, karaoke_files, console_size, errors):
		matched_singer = self.get_singer_from_id(singer_id, False, True, errors)
		if not matched_singer is None:
			matched_song_index = matched_singer.get_song_index_from_id(song_id, True, errors)
			if not matched_song_index is None:
				return self.add_song_for_singer(singer_id, song_title, key_change, matched_song_index, karaoke_files, console_size, errors)
		return self

	def move_song(self, singer_id, song_to_move_id, song_to_move_before_id, errors):
		matched_singer = self.get_singer_from_id(singer_id, False, True, errors)
		if not matched_singer is None:
			matched_song_to_move_index = matched_singer.get_song_index_from_id(song_to_move_id, False, errors)
			if not matched_song_to_move_index is None:
				matched_song_to_move_before_index = matched_singer.get_song_index_from_id(song_to_move_before_id, True, errors)
				if not matched_song_to_move_before_index is None:
					new_state = self.mutate()
					matched_singer = new_state.get_singer_from_id(singer_id, False, True, errors)
					matched_singer.move_song(song_to_move_id, song_to_move_before_id, errors)
					return new_state
		return self

	def add(self, params, karaoke_files, console_size, errors):
		param_count = len(params)
		if param_count == 0:
			errors.append(Error("Not enough arguments. Expected name of new singer, or existing singer name/index."))
		elif param_count == 1:
			return self.add_new_singer(params[0], len(self.singers), errors)
		else:
			key_change = None
			if param_count > 2:
				key_change = params[2]
			return self.add_song_for_singer(params[0], params[1], key_change, -1, karaoke_files, console_size, errors)
		return self

	def insert(self, params, karaoke_files, console_size, errors):
		param_count = len(params)
		if param_count < 2:
			errors.append(Error("Not enough arguments. Expected name of new singer, or existing singer name/index."))
		elif param_count == 2:
			return self.insert_new_singer(params[0], params[1], errors)
		elif param_count > 2:
			keyChange = None
			if param_count > 3:
				keyChange = params[3]
			return self.insert_song_for_singer(params[0], params[1], params[2], keyChange, karaoke_files, console_size, errors)
		return self

	def move(self, params, errors):
		param_count = len(params)
		if param_count < 2:
			errors.append(Error("Not enough arguments. Expected ID of singer."))
		elif param_count == 2:
			# Move a singer in the list
			return self.move_singer(params[0], params[1], errors)
		elif param_count > 2:
			# Move a song in a singer's list
			return self.move_song(params[0], params[1], params[2], errors)
		return self

	def delete(self, params, errors):
		param_count = len(params)
		if param_count < 1:
			errors.append(Error("Not enough arguments. Expected ID of singer."))
		elif param_count == 1:
			# Delete a singer
			return self.delete_singer(params[0], errors)
		elif param_count > 1:
			# Delete a song from a singer
			return self.delete_song_from_singer(params[0], params[1], errors)
		return self

	def undo(self, errors):
		if self.prev_state is None:
			errors.append(Error("No undo history available."))
		else:
			return self.prev_state

	def redo(self, errors):
		if self.next_state is None:
			errors.append(Error("No redo history available."))
		else:
			return self.next_state

	def rename_singer(self, params, errors):
		if len(params) < 2:
			errors.append(Error("Not enough arguments. Expected singer ID and new name."))
		else:
			singer = self.get_singer_from_id(params[0], False, False, errors)
			new_name = params[1]
			if not singer is None:
				for singer in self.singers:
					if singer.name.lower() == new_name:
						errors.append(Error(f"Name \"{new_name}\" already exists."))
						return
				new_state = self.mutate()
				singer = new_state.get_singer_from_id(params[0], False, False, errors)
				singer.name = new_name
				return new_state
		return self

	def clear(self):
		new_state = self.mutate()
		new_state.singers = []
		new_state.active_song_list_singer_name = None
		return new_state

	def next_singer(self):
		for singer in self.singers:
			if len(singer.songs) > 0:
				return singer
		return None

	def set_song_list_to_next_singer(self):
		self.active_song_list_singer_name = None

	def set_song_list_to_singer(self, singer):
		self.active_song_list_singer_name = singer.name

	def list(self, params, errors):
		if len(params) == 0:
			next_state = self.mutate()
			next_state.set_song_list_to_next_singer()
			return next_state
		else:
			singer = self.get_singer_from_id(params[0], False, True, errors)
			if not singer is None:
				next_state = self.mutate()
				next_state.set_song_list_to_singer(singer)
				return next_state

	def get_active_song_list_singer(self):
		if self.active_song_list_singer_name is None:
			return self.next_singer()
		active_singer = [
			singer for singer in self.singers if singer.name == self.active_song_list_singer_name]
		if len(active_singer) == 0:
			self.active_song_list_singer_name = None
			return self.next_singer()
		return active_singer[0]

	def change_song_key(self, params, errors):
		if len(params) < 3:
			errors.append(Error("Not enough arguments. Expected singer ID, song ID, and new key change value."))
		else:
			singer = self.get_singer_from_id(params[0], False, False, errors)
			if not singer is None:
				song_index = singer.get_song_index_from_id(params[1], False, errors)
				if not song_index is None:
					key_change_string = params[2]
					if key_change_string == "0":
						key_change_string = None
					key_change_value = get_key_change_value(key_change_string, errors)
					if key_change_value != -99:
						new_state = self.mutate()
						singer = new_state.get_singer_from_id(params[0], False, False, errors)
						if not singer is None:
							song_index = singer.get_song_index_from_id(params[1], False, errors)
							if not song_index is None:
								singer.songs[song_index].key_change = key_change_value
								return new_state
		return self

	def play(self, params, cycle_queue, driver, errors):
		if len(params) > 0:
			song = params[0]
		else:
			song = "next"
		if not self.next_singer() is None:
			new_state = self.mutate()
			next_singer = new_state.next_singer()
			song_to_play_index = next_singer.get_song_index_from_id(song, False, errors)
			if not song_to_play_index is None:
				song = next_singer.songs[song_to_play_index]
				file_to_start = next_singer.songs[song_to_play_index].file.path
				if cycle_queue:
					new_state.singers.remove(next_singer)
					new_state.singers.append(next_singer)
				del next_singer.songs[song_to_play_index]
				driver.play_karaoke_file(file_to_start, song.key_change, errors)
				return new_state
		else:
			errors.append(Error("There are no singers with songs available."))
		return self

# Given a path, get the karaoke file that matches it.
# Used when restoring state on startup to check that a cued-up song still
# exists.				
def get_karaoke_file_from_path(path, karaokeFiles):
	path = path.lower()
	matches = [
		karaokeFile for karaokeFile in karaokeFiles if karaokeFile.path.lower() == path]
	if len(matches) == 1:
		return matches[0]
	return None

# Parses a keychange string.
def get_key_change_value(key_change, errors):
	if not key_change is None and not key_change=="0":
		if len(key_change) == 2:
			if key_change[0] == '+' or key_change[0] == '-':
				value = key_change[1:2]
				if value.isdigit():
					int_value = int(value)
					if int_value <= Song.MAX_KEY_CHANGE and int_value > 0:
						if key_change[0] == '-':
							return -int_value
						return int_value
		errors.append(Error("Invalid key change, should in format \"+N\" or \"-N\", where N is a value between 1 and 5."))
		return -99
	return 0