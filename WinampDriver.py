from os import startfile, path
from Driver import Driver
from win32ui import FindWindowEx
from time import sleep
import threading

WM_APP = 0x8000
PM_SET_PITCH = WM_APP+7

class WinampDriver(Driver):
	pitchUpHotkey = None
	pitchDownHotkey = None
	pitchResetHotkey = None

	def __init__(self, config, errors):
		exePath=config.get("exe")
		if not exePath is None:
			if path.exists(exePath):
				startfile(exePath)
			else:
				errors.append("The configured Winamp exe path ({exePath}) does not exist.")

	def playKaraokeFile(self,karaokeFile, keyChange, errors):
		startfile(karaokeFile)
		pacemakerWindow=FindWindowEx(None, None, None, "PaceMaker Plug-in")
		if pacemakerWindow is None:
			errors.append("Could not find PaceMaker window.")
		else:
			# Run a thread. We can't just set it once, cos the timing between
			# Pacemaker resetting itself when a new file starts, and us sending
			# this message to set a value, is too tight. We will set it once
			# every second for the next five seconds.
			keyChangeThread = threading.Thread(
				target=applyKeyChange, args=(keyChange,5,))
			keyChangeThread.daemon = True
			keyChangeThread.start()

# Sends the PM_SET_PITCH message to the PaceMaker window (if available) to set
# the correct key change to whatever the user requested for a particular song.
def applyKeyChange(keyChange,count):
	pacemakerWindow=FindWindowEx(None, None, None, "PaceMaker Plug-in")
	if not pacemakerWindow is None:
		for _ in range(count):
			pacemakerWindow.SendMessage(PM_SET_PITCH,0,keyChange*1000)
			sleep(1)
