from time import sleep
import ctypes
from ctypes import wintypes
from enum import IntEnum

class Hotkey:
	def __init__(self, config, errors):
		modifiers=config.get("modifiers")
		if modifiers is None:
			raise Exception("No modifiers defined for hotkey")
		self.modifiers=set(map(lambda mod: parseModifier(mod), modifiers))
		key=config.get("key")
		self.key=getKeyCode(key)

	def press(self):
		for mod in self.modifiers:
			PressKey(mod)
		PressKey(self.key)
		ReleaseKey(self.key)
		sleep(0.25)
		for mod in self.modifiers:
			ReleaseKey(mod)

def PressKey(self, hexKeyCode):
	x = INPUT(type=INPUT_KEYBOARD,
				ki=KEYBDINPUT(wVk=hexKeyCode))
	user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def ReleaseKey(self, hexKeyCode):
	x = INPUT(type=INPUT_KEYBOARD,
				ki=KEYBDINPUT(wVk=hexKeyCode,
							dwFlags=KEYEVENTF_KEYUP))
	user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def getKeyCode(key):
	if key is None:
		raise Exception("No key defined for hotkey")
	if len(key)!=1:
		raise Exception("Key (for hotkey) should be exactly one character.")
	key=key.lower()
	if str.isdigit(key):
		return KeyCodes.VK_0+int(key)
	if str.isalpha(key):
		return KeyCodes.VK_A+(ord(key)-ord('a'))
	raise Exception("Hotkey should be a letter or a number.")

def parseModifier(modifier):
	if not modifier is None:
		modifier=modifier.lower()
		if(modifier=="shift"):
			return KeyCodes.VK_SHIFT
		if(modifier=="ctrl"):
			return KeyCodes.VK_CTRL
		if(modifier=="alt"):
			return KeyCodes.VK_MENU
		raise Exception("{modifier} is not a valid hotkey modifier (only 'ctrl', 'shift', or 'alt' allowed).")
	raise Exception("Null hotkey modifier found.")	

# Definitions needed to use the Win32 SendInput stuff.
# Copied from elsewhere.

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MAPVK_VK_TO_VSC = 0

# msdn.microsoft.com/en-us/library/dd3757312
class KeyCodes(IntEnum):
  VK_MENU = 0x12
  VK_CTRL = 0x11
  VK_SHIFT = 0x10
  VK_0 = 0x30
  VK_A = 0x41

# C struct definitions

wintypes.ULONG_PTR = wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
	_fields_ = (("dx", wintypes.LONG),
				("dy", wintypes.LONG),
				("mouseData", wintypes.DWORD),
				("dwFlags", wintypes.DWORD),
				("time", wintypes.DWORD),
				("dwExtraInfo", wintypes.ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
	_fields_ = (("wVk", wintypes.WORD),
				("wScan", wintypes.WORD),
				("dwFlags", wintypes.DWORD),
				("time", wintypes.DWORD),
				("time", wintypes.DWORD),
				("dwExtraInfo", wintypes.ULONG_PTR))

	def __init__(self, *args, **kwds):
		super(KEYBDINPUT, self).__init__(*args, **kwds)
		# some programs use the scan code even if KEYEVENTF_SCANCODE
		# isn't set in dwFflags, so attempt to map the correct code.
		if not self.dwFlags & KEYEVENTF_UNICODE:
			self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)

class HARDWAREINPUT(ctypes.Structure):
	_fields_ = (("uMsg", wintypes.DWORD),
				("wParamL", wintypes.WORD),
				("wParamH", wintypes.WORD))

class INPUT(ctypes.Structure):
	class _INPUT(ctypes.Union):
		_fields_ = (("ki", KEYBDINPUT),
					("mi", MOUSEINPUT),
					("hi", HARDWAREINPUT))
	_anonymous_ = ("_input",)
	_fields_ = (("type", wintypes.DWORD),
				("_input", _INPUT))

LPINPUT = ctypes.POINTER(INPUT)

def _check_count(result, func, args):
	if result == 0:
		raise ctypes.WinError(ctypes.get_last_error())
	return args

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
							 LPINPUT,       # pInputs
							 ctypes.c_int)  # cbSize