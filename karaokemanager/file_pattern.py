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

	def extension_matches(self, ext):
		return ext.lower() in self.extensions
	
	def parse_filename(self, filename):
		group_map=defaultdict()
		match=self.regular_expression.match(filename)
		if not match is None:
			for i,group_name in enumerate(self.groups):
				if (not group_name is None) and group_name!="":
					matched_string=match.group(i+1)
					if (not matched_string is None) and matched_string!="":
						group_map[group_name]=matched_string
		return group_map
