import os
import re
from collections import defaultdict

class FilePattern:
	regular_expression=None
	extensions=[]
	groups=[]
	def __init__(self, extensions, regular_expression, groups):
		self.extensions=list(map(lambda ext: ext.lower(),extensions))
		self.regular_expression=re.compile(regular_expression)
		self.groups=groups

	def extensionMatches(self, ext):
		return ext.lower() in self.extensions
	
	def parseFilename(self, filename):
		group_map=defaultdict()
		match=self.regular_expression.match(filename)
		if not match is None:
			for i,group_name in enumerate(self.groups):
				if (not group_name is None) and group_name!="":
					matched_string=match.group(i+1)
					if (not matched_string is None) and matched_string!="":
						group_map[group_name]=matched_string
		return group_map

def parseFilePattern(pattern_config):
	regular_expression=pattern_config.get("regExp")
	group_names=pattern_config.get("groupNames")
	extensions=pattern_config.get("extensions")
	if(regular_expression is None or regular_expression==""):
		raise Exception("No regExp defined for pattern.")
	if(group_names is None or len(group_names)==0):
		raise Exception("No groupNames defined for pattern.")
	if(extensions is None or len(extensions)==0):
		raise Exception("No extensions defined for pattern.")
	return FilePattern(extensions,regular_expression,group_names)