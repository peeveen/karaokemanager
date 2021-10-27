from DisplayFunctions import clear, padOrEllipsize, SCREENHEIGHT
from colorama import Fore, Style
from MusicFile import MusicFile

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

def selectSong(searchString, songs):
	return showSongList(searchString, songs, True)

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
			print(f"{Fore.RED}{Style.BRIGHT}No results found for \"" +
				  searchString+f"\" ...{Style.RESET_ALL}")
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
			strIndex = str(i+1)
			padding = (3-len(strIndex))*" "
			strIndex = padding+strIndex
			print(f"{Fore.YELLOW}{Style.BRIGHT}"+strIndex +
				  f"{Style.RESET_ALL}: "+option.getOptionText())
			shownCount += 1
			totalShownCount += 1
			if shownCount == SCREENHEIGHT-2 or i == len(options)-1:
				print("Showing results "+f"{Fore.WHITE}{Style.BRIGHT}"+str(startCount)+"-"+str(startCount+(shownCount-1))+f"{Style.RESET_ALL}" +
					  f" of {Fore.WHITE}{Style.BRIGHT}"+str(len(options))+f"{Style.RESET_ALL} for {Fore.YELLOW}{Style.BRIGHT}\""+searchString+f"\"{Style.RESET_ALL}.")
				if len(options) > totalShownCount:
					songNum = getSongChoice("Press Enter for more, x to cancel"+optionalSelectionText +
											" or more text to refine the search criteria: ", options, True, selectionAllowed)
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
			songNum = getSongChoice(
				"Enter song number, or X to cancel, or more text to add to the search criteria: ", options, False, selectionAllowed)
			if songNum is None:
				return None
			elif isinstance(songNum, MusicFile):
				return songNum
			else:
				searchString = searchString+" "+songNum
				searchAgain = True