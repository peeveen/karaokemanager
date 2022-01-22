import os
import re
from collections import defaultdict

class FilePattern:
	regExp=None
	validExtensions=[]
	groups=[]
	def __init__(self, validExtensions, regExp, groups):
		self.validExtensions=list(map(lambda ext: ext.lower(),validExtensions))
		self.regExp=re.compile(regExp)
		self.groups=groups

	def extensionMatches(self, ext):
		return ext.lower() in self.validExtensions
	
	def parseFilename(self, filename):
		groupMap=defaultdict()
		match=self.regExp.match(filename)
		if not match is None:
			for i,groupName in enumerate(self.groups):
				if (not groupName is None) and groupName!="":
					matchedString=match.group(i+1)
					if (not matchedString is None) and matchedString!="":
						groupMap[groupName]=matchedString
		return groupMap

def parseFilePattern(patternConfig):
	regExp=patternConfig["regExp"]
	groupNames=patternConfig["groupNames"]
	validExtensions=patternConfig["extensions"]
	if(regExp is None or regExp==""):
		raise Exception("No regExp defined for pattern.")
	if(groupNames is None or len(groupNames)==0):
		raise Exception("No groupNames defined for pattern.")
	if(validExtensions is None or len(validExtensions)==0):
		raise Exception("No extensions defined for pattern.")
	return FilePattern(validExtensions,regExp,groupNames)