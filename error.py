from enum import Enum, auto

# List of commands as enums
class Severity(Enum):
	ERROR = auto()
	INFO = auto()

class Message:
	message=None
	severity=Severity.ERROR
	def __init__(self,message,severity):
		self.message=message
		self.severity=severity

	def print(self):
		if self.severity==Severity.INFO:
			print(f'{Fore.YELLOW}')
		else:
			print(f'{Fore.RED}')
		print(f'{Style.BRIGHT}{self.message}{Style.RESET_ALL}')

class Error(Message):
	def __init__(message):
		Message(message,Severity.ERROR)

class Info(Message):
	def __init__(message):
		Message(message,Severity.INFO)