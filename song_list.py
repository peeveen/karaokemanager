# Class representing the list of songs that a singer has chosen.
class SongList:
	name = ''
	songs = []

	def __init__(self, name):
		self.name = name
		self.songs = []

	def write_to_state_file(self, file):
		file.writelines(self.name+"\n")
		for song in self.songs:
			song.write_to_state_file(file)

	def write_to_queue_file(self, file):
		if len(self.songs) == 0:
			indent = "\t"
		else:
			indent = ""
		file.writelines(indent+self.name+"\n")

	def get_song_index_from_id(self, id, end_allowed, errors):
		if id.isdigit():
			song_index = int(id)
			if song_index <= 0 or song_index > len(self.songs):
				errors.append(f"Song index out of bounds: it must be between 1 and {len(self.songs)}")
				return None
			return song_index-1
		id = id.lower()
		if len(self.songs) > 0:
			if id == "next" or id == "n":
				return 0
			if end_allowed:
				if id == "end" or id == "e":
					return len(self.songs)+1
		matches = []
		for i, song in enumerate(self.songs):
			if id in song.file.title.lower() or id in song.file.artist.lower():
				matches.append(i)
		if len(matches) == 0:
			errors.append(f"No match found for given song ID \"{id}\"")
			return None
		if len(matches) > 1:
			errors.append(f"Multiple matches found for given song ID \"{id}\"")
			return None
		return matches[0]

	def move_song(self, song_to_move_id, song_to_move_before_id, errors):
		matched_song_to_move_index = self.get_song_index_from_id(song_to_move_id, False, errors)
		if not matched_song_to_move_index is None:
			matched_song_to_move_before_index = self.get_song_index_from_id(song_to_move_before_id, True, errors)
			if not matched_song_to_move_before_index is None:
				song_to_move = self.songs[matched_song_to_move_index]
				del self.songs[matched_song_to_move_index]
				self.insert_song(matched_song_to_move_before_index, song_to_move)

	def insert_song(self, position, song):
		self.songs.insert(position, song)


