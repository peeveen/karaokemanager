from os import name, system

SCREENHEIGHT = 30

def padOrEllipsize(str, length, padStr):
	if len(str) > length:
		str = str.strip()
		if len(str) > length:
			str = str[0:length-3].strip()+"..."
	return str+((length-len(str))*padStr)

def clear():
	# for windows
	if name == 'nt':
		_ = system('cls')
	# for mac and linux(here, os.name is 'posix')
	else:
		_ = system('clear')