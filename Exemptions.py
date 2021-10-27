from os import path

reversalExemptionsFilename = "ReversalExemptions.txt"
theExemptionsFilename = "TheExemptions.txt"
lowerCaseExemptionsFilename = "LowerCaseExemptions.txt"
similarityExemptionsFilename = "SimilarityExemptions.txt"

similarityExemptions = []
lowerCaseExemptions = []
reversalExemptions = []
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

def parseReversalExemption(line):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return ReversalExemption(bits[0], bits[1])
		else:
			errors.append("Could not parse reversal exemption: "+line)
			return None


def parseSimilarityExemption(line):
	line = line.strip()
	if len(line) > 0:
		bits = line.split("\t")
		if len(bits) == 2:
			return SimilarityExemption(bits[0], bits[1])
		else:
			errors.append("Could not parse similarity exemption: "+line)
			return None


def getReversalExemptions(dataFilesPath):
	global reversalExemptions
	reversalExemptions = []
	if path.isfile(dataFilesPath+"\\"+reversalExemptionsFilename):
		with open(dataFilesPath+"\\"+reversalExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				reversalExemption = parseReversalExemption(line)
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


def getSimilarityExemptions(dataFilesPath):
	global similarityExemptions
	similarityExemptions = []
	if path.isfile(dataFilesPath+"\\"+similarityExemptionsFilename):
		with open(dataFilesPath+"\\"+similarityExemptionsFilename, mode="r", encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				similarityExemption = parseSimilarityExemption(line)
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

def getExemptions(dataFilesPath):
	getLowerCaseExemptions(dataFilesPath)
	getReversalExemptions(dataFilesPath)
	getTheExemptions(dataFilesPath)
	getSimilarityExemptions(dataFilesPath)