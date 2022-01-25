from os import path

class Exemptions:
	# Contents of the similarity exemptions file (a list of TwoPartExemption objects)
	similarity_exemptions = []
	# Contents of the lower case exemptions file (a list of strings)
	lower_case_exemptions = []
	# Contents of the reversal exemptions file (a list of TwoPartExemption objects)
	reversal_exemptions = []
	# Contents of the "the" exemptions file (a list of strings)
	the_exemptions=set([])

	def __init__(self,config):
		self.reversal_exemptions=get_items_from_data_text_file(config.paths.reversal_exemptions,parse_reversal_exemption)
		self.the_exemptions=set(get_items_from_data_text_file(config.paths.the_exemptions,parse_simple_exemption))
		self.similarity_exemptions=get_items_from_data_text_file(config.paths.similarity_exemptions,parse_similarity_exemption)
		self.lower_case_exemptions=get_items_from_data_text_file(config.paths.lower_case_exemptions,parse_simple_exemption)

	def is_exempt_from_reversal_check(self,artist1, artist2):
		for reversalExemption in self.reversal_exemptions:
			if reversalExemption.matches(artist1, artist2):
				return True
		return False

	def is_exempt_from_lower_case_check(self,artist1):
		for lowerCaseExemption in self.lower_case_exemptions:
			if lowerCaseExemption in artist1:
				return True
		return False

	def is_exempt_from_similarity_check(self,title1, title2):
		for similarityExemption in self.similarity_exemptions:
			if similarityExemption.matches(title1, title2):
				return True
		return False

	def is_exempt_from_the_check(self,artist1):
		return artist1 in self.the_exemptions

class TwoPartExemption:
	part1 = None
	part2 = None

	def __init__(self, part1, part2):
		self.part1 = part1
		self.part2 = part2

	def matches(self, part1, part2):
		return (self.part1 == part1 and self.part2 == part2) or (self.part1 == part2 and self.part2 == part1)

def parse_two_part_exemption(line, creatorFunc, exemptionType):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return creatorFunc(bits[0], bits[1])
		else:
			raise Exception(f"Could not parse {exemptionType} exemption: {line}")

def create_two_part_exemption(part1,part2):
	return TwoPartExemption(part1,part2)

def parse_reversal_exemption(line):
	return parse_two_part_exemption(line, create_two_part_exemption, "reversal")

def parse_similarity_exemption(line):
	return parse_two_part_exemption(line, create_two_part_exemption, "similarity")

def parse_simple_exemption(line):
	return line.strip()

def read_lines_from_data_text_file(full_path):
	if path.isfile(full_path):
		with open(full_path, mode="r", encoding="utf-8") as f:
			return f.readlines()
	return []

def get_items_from_data_text_file(path,parserFunction):
	lines=read_lines_from_data_text_file(path)
	items=list(map(lambda line: parserFunction(line),lines))
	items=list(filter(lambda item: not item is None, items))
	return items