from os import startfile
from Driver import Driver
from time import sleep
from Hotkey import Hotkey

class WinampDriver(Driver):
	firstSong = True
	pitchUpHotkey = None
	pitchDownHotkey = None
	pitchResetHotkey = None

	def __init__(self, config, errors):
		hotkeysConfig=config.get("hotkeys")
		if hotkeysConfig is None:
			errors.append("No hotkeys defined for Winamp driver.")
		else:
			pitchUpConfig=hotkeysConfig.get("pitchUp")
			if pitchUpConfig is None:
				errors.append("No pitchUp hotkey defined for Winamp driver.")
			else:
				try:
					self.pitchUpHotkey=Hotkey(pitchUpConfig, errors)
				except Exception as e:
					errors.append(e)
			pitchDownConfig=hotkeysConfig.get("pitchDown")
			if pitchDownConfig is None:
				errors.append("No pitchReset hotkey defined for Winamp driver.")
			else:
				try:
					self.pitchDownHotkey=Hotkey(pitchDownConfig, errors)
				except Exception as e:
					errors.append(e)
			pitchResetConfig=hotkeysConfig.get("pitchReset")
			if pitchResetConfig is None:
				errors.append("No pitchReset hotkey defined for Winamp driver.")
			else:
				try:
					self.pitchResetHotkey=Hotkey(pitchResetConfig, errors)
				except Exception as e:
					errors.append(e)

	def playKaraokeFile(self,karaokeFile, keyChange, errors):
		if self.firstSong:
			startfile(karaokeFile)
			sleep(5)
			self.firstSong = False
		self.applyKeyChange(keyChange, errors)
		startfile(karaokeFile)

	# Sends the correct sequence of hotkeys to set the key change to
	# whatever the user requested for a particular song.
	def applyKeyChange(self, keyChange, errors):
		if not self.pitchResetHotkey is None:
			self.pitchResetHotkey.press()
		else:
			errors.append("Could not press pitch reset hotkey.")
		while keyChange != 0:
			if keyChange < 0:
				if not self.pitchDownHotkey is None:
					self.pitchDownHotkey.press()
				else:
					errors.append("Could not press pitch down hotkey.")
					return
				keyChange += 1
			else:
				if not self.pitchUpHotkey is None:
					self.pitchUpHotkey.press()
				else:
					errors.append("Could not press pitch up hotkey.")
					return
				keyChange -= 1