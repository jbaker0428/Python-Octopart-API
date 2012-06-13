"""
NOTE: Running this unit test generates 24 API requests.
"""

import os
import unittest
import urllib2
import json

# Add build directory to search path
if os.path.exists("build"):
	from distutils.util import get_platform
	import sys
	s = "build/lib.%s-%.3s" % (get_platform(), sys.version)
	s = os.path.join(os.getcwd(), s)
	sys.path.insert(0,s)

import octopart
from octopart import *
print octopart

def get(req_url):
	"""Return a JSON dictionary from a pre-formed request URL."""
	
	response = unicode(urllib2.urlopen(req_url).read())
	return json.loads(response)

api = Octopart(apikey='92bdca1b')
# Reference JSON objects
brand = OctopartBrand(459, "Digi-Key", "http://www.digikey.com")
categories_get_json = get('http://octopart.com/api/v2/categories/get?id=4174')
categories_get_multi_json = get('http://octopart.com/api/v2/categories/get_multi?ids=[4215,4174,4780]')
categories_search_json = get('http://octopart.com/api/v2/categories/search?q=resistor')
parts_get_json = get('http://octopart.com/api/v2/parts/get?uid=39619421')
parts_get_multi_json = get('http://octopart.com/api/v2/parts/get_multi?uids=[39619421,29035751,31119928]')
parts_search_json = get('http://octopart.com/api/v2/parts/search?q=resistor&limit=20')
parts_suggest_json = get('http://octopart.com/api/v2/parts/suggest?q=sn74f&limit=3')
parts_match_json = get('http://octopart.com/api/v2/parts/match?manufacturer_name=texas+instruments&mpn=SN74LS240N')
partattributes_get_json = get('http://octopart.com/api/v2/partattributes/get?fieldname=capacitance')
partattributes_get_multi_json = get('http://octopart.com/api/v2/partattributes/get_multi?fieldnames=["capacitance","resistance"]')
bom_match_json = get('http://octopart.com/api/v2/bom/match?lines=%5B%7B%22mpn%22%3A+%22SN74LS240N%22%7D%5D&pretty_print=true')

class ArgumentValidationTest(unittest.TestCase):
	
	def setUp(self):
		unittest.TestCase.setUp(self)
	
	def tearDown(self):
		unittest.TestCase.tearDown(self)

class DataEquivalenceTest(unittest.TestCase):
	
	def setUp(self):
		unittest.TestCase.setUp(self)
	
	def tearDown(self):
		unittest.TestCase.tearDown(self)

if __name__ == '__main__':
	unittest.main()	