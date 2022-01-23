from os import path

# List of reversal exemptions. If we find a music file by "Chas & Dave", and one by "Dave & Chas",
# this will be flagged as a problem unless there is a line in the ReversalExemptions file
# declaring this reversal to be exempt from challenge. Each line in this file should be two
# string separated by a tab, for example "Chas\tDave".
reversalExemptionsFilename = "ReversalExemptions.txt"
# List of "the" exemptions. Usually, if we find a music file by an artist/group that also exists
# prefixed by "The" (e.g. one file by "Rolling Stones" and one by "The Rolling Stones") then this
# will be flagged as a problem, unless an exemption is listed in this file. Either of the two
# values can be used.
theExemptionsFilename = "TheExemptions.txt"
# Normally, we want artist names and song titles to be capitalised. However, some annoyances
# exist (e.g. "k.d. lang"). List them in this file to make them exempt from challenge.
lowerCaseExemptionsFilename = "LowerCaseExemptions.txt"
# If we find two artist names or song titles that look INCREDIBLY similar, we flag them as
# potential duplicates with an unintentional typo. However, sometimes this yields false positives.
# List them in this file to get rid of them, with both values separated by a tab.
similarityExemptionsFilename = "SimilarityExemptions.txt"

# Contents of the similarity exemptions file (a list of TwoPartExemption objects)
similarityExemptions = []
# Contents of the lower case exemptions file (a list of strings)
lowerCaseExemptions = []
# Contents of the reversal exemptions file (a list of TwoPartExemption objects)
reversalExemptions = []
# Contents of the "the" exemptions file (a list of strings)
theExemptions=set([])

class TwoPartExemption:
	part1 = None
	part2 = None

	def __init__(self, part1, part2):
		self.part1 = part1
		self.part2 = part2

	def matches(self, part1, part2):
		return (self.part1 == part1 and self.part2 == part2) or (self.part1 == part2 and self.part2 == part1)

def parseTwoPartExemption(line, errors, creatorFunc, exemptionType):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return creatorFunc(bits[0], bits[1])
		else:
			errors.append(f"Could not parse {exemptionType} exemption: {line}")
			return None

def createTwoPartExemption(part1,part2):
	return TwoPartExemption(part1,part2)

def parseReversalExemption(line, errors):
	return parseTwoPartExemption(line,errors, createTwoPartExemption, "reversal")

def parseSimilarityExemption(line, errors):
	return parseTwoPartExemption(line,errors, createTwoPartExemption, "similarity")

def parseSimpleExemption(line,errors):
	return line.strip()

def readLinesFromDataTextFile(dataFilesPath,filename):
	fullPath=path.join(dataFilesPath,filename)
	if path.isfile(fullPath):
		with open(fullPath, mode="r", encoding="utf-8") as f:
			return f.readlines()

def getItemsFromDataTextFile(dataFilesPath,filename,parserFunction,errors):
	lines=readLinesFromDataTextFile(dataFilesPath,filename)
	items=list(map(lambda line: parserFunction(line,errors),lines))
	items=list(filter(lambda item: not item is None, items))
	return items

def getReversalExemptions(dataFilesPath, errors):
	global reversalExemptions
	reversalExemptions=getItemsFromDataTextFile(dataFilesPath,reversalExemptionsFilename,parseReversalExemption,errors)

def getTheExemptions(dataFilesPath):
	global theExemptions
	theExemptionsList=getItemsFromDataTextFile(dataFilesPath,reversalExemptionsFilename,parseSimpleExemption,None)
	theExemptions = set(theExemptionsList)

def getSimilarityExemptions(dataFilesPath, errors):
	global similarityExemptions
	similarityExemptions=getItemsFromDataTextFile(dataFilesPath,reversalExemptionsFilename,parseSimilarityExemption,errors)

def getLowerCaseExemptions(dataFilesPath):
	global lowerCaseExemptions
	lowerCaseExemptions=getItemsFromDataTextFile(dataFilesPath,reversalExemptionsFilename,parseSimpleExemption,None)

def isExemptFromReversalCheck(artist1, artist2):
	for reversalExemption in reversalExemptions:
		if reversalExemption.matches(artist1, artist2):
			return True
	return False

def isExemptFromLowerCaseCheck(artist1):
	for lowerCaseExemption in lowerCaseExemptions:
		if lowerCaseExemption in artist1:
			return True
	return False

def isExemptFromSimilarityCheck(title1, title2):
	for similarityExemption in similarityExemptions:
		if similarityExemption.matches(title1, title2):
			return True
	return False

def isExemptFromTheCheck(artist1):
	return artist1 in theExemptions

def getExemptions(dataFilesPath, errors):
	getLowerCaseExemptions(dataFilesPath)
	getReversalExemptions(dataFilesPath, errors)
	getTheExemptions(dataFilesPath)
	getSimilarityExemptions(dataFilesPath, errors)