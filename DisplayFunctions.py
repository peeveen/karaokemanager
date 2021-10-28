from os import name, system

# Maximum number of lines to use
SCREENHEIGHT = 30

# Pads the given string with spaces to make it reach the desired length.
# If it is already too long, it will be truncated and ellipsised.
def padOrEllipsize(str, length, padStr=" "):
	if len(str) > length:
		str = str.strip()
		if len(str) > length:
			str = f"{str[0:length-3].strip()}..."
	return str+((length-len(str))*padStr)

# Clear the screen. Have to use system commands for this.
def clear():
	# for windows
	if name == 'nt':
		_ = system('cls')
	# for mac and linux(here, os.name is 'posix')
	else:
		_ = system('clear')