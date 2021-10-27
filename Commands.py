from enum import Enum, auto

class CommandType(Enum):
	ADD = auto()
	INSERT = auto()
	MOVE = auto()
	DELETE = auto()
	LIST = auto()
	PLAY = auto()
	SCAN = auto()
	ZAP = auto()
	HELP = auto()
	QUIT = auto()
	UNDO = auto()
	REDO = auto()
	SEARCH = auto()
	NAME = auto()
	KEY = auto()
	FILLER = auto()
	MUSICSEARCH = auto()
	CUE = auto()

class CommandDefinition:
	commandType = None
	commandString = None

	def __init__(self, commandType, commandString):
		self.commandType = commandType
		self.commandString = commandString


commands = [
	CommandDefinition(CommandType.ADD, "add"),
	CommandDefinition(CommandType.INSERT, "insert"),
	CommandDefinition(CommandType.MOVE, "move"),
	CommandDefinition(CommandType.DELETE, "delete"),
	CommandDefinition(CommandType.LIST, "list"),
	CommandDefinition(CommandType.PLAY, "play"),
	CommandDefinition(CommandType.SCAN, "scan"),
	CommandDefinition(CommandType.ZAP, "zap"),
	CommandDefinition(CommandType.HELP, "help"),
	CommandDefinition(CommandType.UNDO, "undo"),
	CommandDefinition(CommandType.REDO, "redo"),
	CommandDefinition(CommandType.QUIT, "quit"),
	CommandDefinition(CommandType.KEY, "key"),
	CommandDefinition(CommandType.NAME, "name"),
	CommandDefinition(CommandType.FILLER, "filler"),
	CommandDefinition(CommandType.CUE, "cue"),
	CommandDefinition(CommandType.SEARCH, "?"),
	CommandDefinition(CommandType.MUSICSEARCH, "??")
]

class Command:
	commandType = None
	params = []

	def __init__(self, commandType, params):
		self.commandType = commandType
		self.params = params

def parseCommandType(strCommand):
	strCommand = strCommand.lower()
	for command in commands:
		if strCommand == command.commandString or strCommand == command.commandString[0]:
			return command.commandType
	return None

def parseCommand(strCommand):
	# Special case = search
	if strCommand[0:2] == "??":
		return Command(CommandType.MUSICSEARCH, [strCommand[2:]])
	if strCommand[0] == "?":
		return Command(CommandType.SEARCH, [strCommand[1:]])
	commandBits = strCommand.split(',')
	for i, commandBit in enumerate(commandBits):
		commandBits[i] = commandBit.strip()
	commandType = parseCommandType(commandBits[0])
	if commandType is None:
		errors.append("Unknown command: \""+commandBits[0]+"\"")
		return None
	else:
		return Command(commandType, commandBits[1:])
