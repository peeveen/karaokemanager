from song_list import SongList

# Class describing a singer, and their current list of selected songs.
class Singer(SongList):
	def __init__(self, name):
		SongList.__init__(self, name)

	def write_to_state_file(self, file):
		SongList.write_to_state_file(self, file)

	def write_to_queue_file(self, file):
		SongList.write_to_queue_file(self, file)

	def get_song_index_from_id(self, id, end_allowed, errors):
		return SongList.get_song_index_from_id(self, id, end_allowed, errors)

	def move_song(self, song_to_move_id, song_to_move_before_id, errors):
		return SongList.move_song(self, song_to_move_id, song_to_move_before_id, errors)

	def insert_song(self, position, song):
		SongList.insert_song(self, position, song)

