import threading
import random
from time import sleep

class SuggestionGenerator:
	# Thread that will periodically choose a random karaoke file and write it to the suggestion file.
	suggestor_thread = None
	# Flag to stop the suggestion thread.
	stop_suggestions = False
	# Output path
	path=None

	def __init__(self,config):
		self.path=config.paths.random_suggestion

	# Function to stop the suggestion thread.
	def stop_suggestion_thread(self):
		if not self.suggestor_thread is None:
			self.stop_suggestions = True
			self.suggestor_thread.join()
		self.stop_suggestions = False

	# Function to start the suggestion thread.
	def start_suggestion_thread(self, karaoke_dictionary):
		self.stop_suggestion_thread()
		suggestor_thread = threading.Thread(
			target=self.random_song_suggestion_generator_thread, args=[karaoke_dictionary,])
		suggestor_thread.daemon = True
		suggestor_thread.start()

	# Thread that periodically writes a random karaoke suggestion to a file.
	def random_song_suggestion_generator_thread(self,dictionary):
		random.seed()
		counter = 0
		while not self.stop_suggestions:
			if counter == 0:
				counter = 20
				if any(dictionary):
					artistKeys = list(dictionary.keys())
					randomArtistIndex = random.randrange(len(dictionary))
					artistString = artistKeys[randomArtistIndex]
					artistDict = dictionary[artistString]
					randomSongIndex = random.randrange(len(artistDict))
					songKeys = list(artistDict.keys())
					songString = songKeys[randomSongIndex]
					suggestionString = f"{artistString}\n{songString}\n"
					try:
						with open(self.path, mode="w", encoding="utf-8") as f:
							f.writelines(suggestionString)
					except PermissionError:
						pass
			else:
				counter -= 1
			sleep(0.5)

