from enum import Enum, auto

# List of commands as enums
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
	MUSIC_SEARCH = auto()
	CUE = auto()

# Command definition class. A combination of the command enum
# and the string that is associated with the command.
class CommandDefinition:
	command_type = None
	command_string = None

	def __init__(self, command_type, command_string):
		self.command_type = command_type
		self.command_string = command_string

# List of command definitions
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
	CommandDefinition(CommandType.MUSIC_SEARCH, "??")
]

# Result of a parsed command
class Command:
	command_type = None
	# The series of additional parameters that were entered after the command string
	# e.g. "add,Steve,Don't Look Back In Anger" would have two params: "Steve", and
	# "Don't Look Back In Anger"
	params = []

	def __init__(self, command_type, params):
		self.command_type = command_type
		self.params = params

# Attempts to parse the command type by checking the command string that was entered.
def parse_command_type(command_string):
	command_string = command_string.lower()
	for command in commands:
		if command_string == command.command_string or command_string == command.command_string[0]:
			return command.command_type
	return None

# Parses the given command line into a Command object
def parse_command(command_string, errors):
	# Special case = search
	if command_string[0:2] == "??":
		return Command(CommandType.MUSIC_SEARCH, [command_string[2:]])
	if command_string[0] == "?":
		return Command(CommandType.SEARCH, [command_string[1:]])
	command_bits = command_string.split(',')
	for i, command_bit in enumerate(command_bits):
		command_bits[i] = command_bit.strip()
	command_type = parse_command_type(command_bits[0])
	if command_type is None:
		errors.append(f"Unknown command: \"{command_bits[0]}\"")
		return None
	else:
		return Command(command_type, command_bits[1:])
