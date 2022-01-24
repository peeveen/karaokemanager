from os import path

# List of reversal exemptions. If we find a music file by "Chas & Dave", and one by "Dave & Chas",
# this will be flagged as a problem unless there is a line in the ReversalExemptions file
# declaring this reversal to be exempt from challenge. Each line in this file should be two
# string separated by a tab, for example "Chas\tDave".
REVERSAL_EXEMPTIONS_FILENAME = "ReversalExemptions.txt"
# List of "the" exemptions. Usually, if we find a music file by an artist/group that also exists
# prefixed by "The" (e.g. one file by "Rolling Stones" and one by "The Rolling Stones") then this
# will be flagged as a problem, unless an exemption is listed in this file. Either of the two
# values can be used.
THE_EXEMPTIONS_FILENAME = "TheExemptions.txt"
# Normally, we want artist names and song titles to be capitalised. However, some annoyances
# exist (e.g. "k.d. lang"). List them in this file to make them exempt from challenge.
LOWER_CASE_EXEMPTIONS_FILENAME = "LowerCaseExemptions.txt"
# If we find two artist names or song titles that look INCREDIBLY similar, we flag them as
# potential duplicates with an unintentional typo. However, sometimes this yields false positives.
# List them in this file to get rid of them, with both values separated by a tab.
SIMILARITY_EXEMPTIONS_FILENAME = "SimilarityExemptions.txt"

# Contents of the similarity exemptions file (a list of TwoPartExemption objects)
similarity_exemptions = []
# Contents of the lower case exemptions file (a list of strings)
lower_case_exemptions = []
# Contents of the reversal exemptions file (a list of TwoPartExemption objects)
reversal_exemptions = []
# Contents of the "the" exemptions file (a list of strings)
the_exemptions=set([])

class TwoPartExemption:
	part1 = None
	part2 = None

	def __init__(self, part1, part2):
		self.part1 = part1
		self.part2 = part2

	def matches(self, part1, part2):
		return (self.part1 == part1 and self.part2 == part2) or (self.part1 == part2 and self.part2 == part1)

def parse_two_part_exemption(line, errors, creatorFunc, exemptionType):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return creatorFunc(bits[0], bits[1])
		else:
			errors.append(f"Could not parse {exemptionType} exemption: {line}")
			return None

def create_two_part_exemption(part1,part2):
	return TwoPartExemption(part1,part2)

def parse_reversal_exemption(line, errors):
	return parse_two_part_exemption(line,errors, create_two_part_exemption, "reversal")

def parse_similarity_exemption(line, errors):
	return parse_two_part_exemption(line,errors, create_two_part_exemption, "similarity")

def parse_simple_exemption(line,errors):
	return line.strip()

def read_lines_from_data_text_file(dataFilesPath,filename):
	fullPath=path.join(dataFilesPath,filename)
	if path.isfile(fullPath):
		with open(fullPath, mode="r", encoding="utf-8") as f:
			return f.readlines()
	return []

def get_items_from_data_text_file(dataFilesPath,filename,parserFunction,errors):
	lines=read_lines_from_data_text_file(dataFilesPath,filename)
	items=list(map(lambda line: parserFunction(line,errors),lines))
	items=list(filter(lambda item: not item is None, items))
	return items

def get_reversal_exemptions(dataFilesPath, errors):
	global reversal_exemptions
	reversal_exemptions=get_items_from_data_text_file(dataFilesPath,REVERSAL_EXEMPTIONS_FILENAME,parse_reversal_exemption,errors)

def get_the_exemptions(dataFilesPath):
	global the_exemptions
	theExemptionsList=get_items_from_data_text_file(dataFilesPath,REVERSAL_EXEMPTIONS_FILENAME,parse_simple_exemption,None)
	the_exemptions = set(theExemptionsList)

def get_similarity_exemptions(dataFilesPath, errors):
	global similarity_exemptions
	similarity_exemptions=get_items_from_data_text_file(dataFilesPath,REVERSAL_EXEMPTIONS_FILENAME,parse_similarity_exemption,errors)

def get_lower_case_exemptions(dataFilesPath):
	global lower_case_exemptions
	lower_case_exemptions=get_items_from_data_text_file(dataFilesPath,REVERSAL_EXEMPTIONS_FILENAME,parse_simple_exemption,None)

def is_exempt_from_reversal_check(artist1, artist2):
	for reversalExemption in reversal_exemptions:
		if reversalExemption.matches(artist1, artist2):
			return True
	return False

def is_exempt_from_lower_case_check(artist1):
	for lowerCaseExemption in lower_case_exemptions:
		if lowerCaseExemption in artist1:
			return True
	return False

def is_exempt_from_similarity_check(title1, title2):
	for similarityExemption in similarity_exemptions:
		if similarityExemption.matches(title1, title2):
			return True
	return False

def is_exempt_from_the_check(artist1):
	return artist1 in the_exemptions

def get_exemptions(dataFilesPath, errors):
	get_lower_case_exemptions(dataFilesPath)
	get_reversal_exemptions(dataFilesPath, errors)
	get_the_exemptions(dataFilesPath)
	get_similarity_exemptions(dataFilesPath, errors)