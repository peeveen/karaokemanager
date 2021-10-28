from DisplayFunctions import clear, padOrEllipsize, SCREENHEIGHT
from colorama import Fore, Style
from MusicFile import MusicFile

# Song selector function. Shows the list of "songs" to the user and asks them to pick one,
# cancel, or enter more text to narrow the search.
def selectSong(searchString, songs):
	return showSongList(searchString, songs, True)

# Asks the user to choose a song from the displayed list, and awaits a valid
# response.
def getSongChoice(message, options, blankAllowed, selectionAllowed):
	invalidChoice = True
	while invalidChoice:
		invalidChoice = False
		try:
			songNum = input(message)
		except EOFError:
			pass
		songNum = songNum.strip()
		if songNum.lower().startswith("x"):
			return None
		if songNum.isdigit() and selectionAllowed:
			parsedInt = int(songNum)-1
			if parsedInt < 0 or parsedInt > len(options):
				invalidChoice = True
				print(
					f"{Fore.RED}{Style.BRIGHT}Invalid choice, try again.{Style.RESET_ALL}")
			else:
				return options[parsedInt]
		else:
			if len(songNum) == 0:
				if blankAllowed:
					return ""
				else:
					invalidChoice = True
					print(
						f"{Fore.RED}{Style.BRIGHT}Invalid choice, try again.{Style.RESET_ALL}")
			else:
				return songNum

# Displays the list of songs and optionally prompts for a response.
def showSongList(searchString, files, selectionAllowed):
	searchAgain = True
	if selectionAllowed:
		optionalSelectionText = ", song number to select,"
	else:
		optionalSelectionText = ""
	while searchAgain:
		searchAgain = False
		options = [
			songFile for songFile in files if songFile.matches(searchString)]
		if len(options) == 1 and selectionAllowed:
			return options[0]
		if len(options) == 0:
			print(f"{Fore.RED}{Style.BRIGHT}No results found for \"{searchString}\" ...{Style.RESET_ALL}")
			try:
				input("Press Enter to continue.")
			except EOFError:
				pass
			return None
		clear()
		shownCount = 0
		totalShownCount = 0
		startCount = 1
		for i, option in enumerate(options):
			strIndex = f"{i+1}"
			padding = (3-len(strIndex))*" "
			strIndex = padding+strIndex
			print(f"{Fore.YELLOW}{Style.BRIGHT}{strIndex}{Style.RESET_ALL}: {option.getOptionText()}")
			shownCount += 1
			totalShownCount += 1
			if shownCount == SCREENHEIGHT-2 or i == len(options)-1:
				print(f"Showing results {Fore.WHITE}{Style.BRIGHT}{startCount}-{startCount+(shownCount-1)}{Style.RESET_ALL} of {Fore.WHITE}{Style.BRIGHT}{len(options)}{Style.RESET_ALL} for {Fore.YELLOW}{Style.BRIGHT}\"{searchString}\"{Style.RESET_ALL}.")
				if len(options) > totalShownCount:
					songNum = getSongChoice(f"Press Enter for more, x to cancel{optionalSelectionText} or more text to refine the search criteria: ", options, True, selectionAllowed)
					if songNum is None:
						return None
					elif songNum == "":
						startCount += shownCount
						shownCount = 0
						continue
					elif isinstance(songNum, MusicFile):
						return songNum
					else:
						searchString = searchString+" "+songNum
						searchAgain = True
						break
		if not searchAgain:
			if not selectionAllowed:
				try:
					input("Press Enter to continue ...")
				except EOFError:
					pass
				return None
			songNum = getSongChoice("Enter song number, or X to cancel, or more text to add to the search criteria: ", options, False, selectionAllowed)
			if songNum is None:
				return None
			elif isinstance(songNum, MusicFile):
				return songNum
			else:
				searchString = searchString+" "+songNum
				searchAgain = True