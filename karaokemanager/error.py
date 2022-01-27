from enum import Enum, auto
from colorama import Fore, Style

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
			color=f'{Fore.YELLOW}'
		else:
			color=f'{Fore.RED}'
		print(f'{color}{Style.BRIGHT}{self.message}{Style.RESET_ALL}')

class Error(Message):
	def __init__(self,message):
		Message.__init__(self,message,Severity.ERROR)

class Info(Message):
	def __init__(self,message):
		Message.__init__(self,message,Severity.INFO)