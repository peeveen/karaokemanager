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

# Contents of the similarity exemptions file (a list of SimilarityExemption objects)
similarityExemptions = []
# Contents of the lower case exemptions file (a list of strings)
lowerCaseExemptions = []
# Contents of the reversal exemptions file (a list of ReversalExemption objects)
reversalExemptions = []
# Contents of the "the" exemptions file (a list of strings)
theExemptions=set([])

class ReversalExemption:
	artist1 = None
	artist2 = None

	def __init__(self, artist1, artist2):
		self.artist1 = artist1
		self.artist2 = artist2

	def matches(self, artist1, artist2):
		return (self.artist1 == artist1 and self.artist2 == artist2) or (self.artist1 == artist2 and self.artist2 == artist1)


class SimilarityExemption:
	title1 = None
	title2 = None

	def __init__(self, title1, title2):
		self.title1 = title1
		self.title2 = title2

	def matches(self, title1, title2):
		return (self.title1 == title1 and self.title2 == title2) or (self.title1 == title2 and self.title2 == title1)

def parseReversalExemption(line, errors):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return ReversalExemption(bits[0], bits[1])
		else:
			errors.append("Could not parse reversal exemption: "+line)
			return None


def parseSimilarityExemption(line, errors):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return SimilarityExemption(bits[0], bits[1])
		else:
			errors.append("Could not parse similarity exemption: "+line)
			return None


def getReversalExemptions(dataFilesPath, errors):
	global reversalExemptions
	reversalExemptions = []
	if path.isfile(dataFilesPath+"\\"+reversalExemptionsFilename):
		with open(dataFilesPath+"\\"+reversalExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				reversalExemption = parseReversalExemption(line, errors)
				if not reversalExemption is None:
					reversalExemptions.append(reversalExemption)

def getTheExemptions(dataFilesPath):
	global theExemptions
	theExemptions = set([])
	if path.isfile(dataFilesPath+"\\"+theExemptionsFilename):
		with open(dataFilesPath+"\\"+theExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				theExemption = line.strip()
				theExemptions.add(theExemption)


def getSimilarityExemptions(dataFilesPath, errors):
	global similarityExemptions
	similarityExemptions = []
	if path.isfile(dataFilesPath+"\\"+similarityExemptionsFilename):
		with open(dataFilesPath+"\\"+similarityExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				similarityExemption = parseSimilarityExemption(line, errors)
				if not similarityExemption is None:
					similarityExemptions.append(similarityExemption)


def getLowerCaseExemptions(dataFilesPath):
	global lowerCaseExemptions
	lowerCaseExemptions = []
	if path.isfile(dataFilesPath+"\\"+lowerCaseExemptionsFilename):
		with open(dataFilesPath+"\\"+lowerCaseExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				lowerCaseExemption = line.strip()
				lowerCaseExemptions.append(lowerCaseExemption)


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