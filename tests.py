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
categories_get_json = get('http://octopart.com/api/v2/categories/get?id=4174&apikey=92bdca1b')
categories_get_multi_json = get('http://octopart.com/api/v2/categories/get_multi?ids=[4215,4174,4780]&apikey=92bdca1b')
categories_search_json = get('http://octopart.com/api/v2/categories/search?q=resistor&apikey=92bdca1b')
parts_get_json = get('http://octopart.com/api/v2/parts/get?uid=39619421&apikey=92bdca1b')
parts_get_multi_json = get('http://octopart.com/api/v2/parts/get_multi?uids=[39619421,29035751,31119928]&apikey=92bdca1b')
parts_search_json = get('http://octopart.com/api/v2/parts/search?q=resistor&limit=20&apikey=92bdca1b')
parts_suggest_json = get('http://octopart.com/api/v2/parts/suggest?q=sn74f&limit=3&apikey=92bdca1b')
parts_match_json = get('http://octopart.com/api/v2/parts/match?manufacturer_name=texas+instruments&mpn=SN74LS240N&apikey=92bdca1b')
partattributes_get_json = get('http://octopart.com/api/v2/partattributes/get?fieldname=capacitance&apikey=92bdca1b')
partattributes_get_multi_json = get('http://octopart.com/api/v2/partattributes/get_multi?fieldnames=["capacitance","resistance"]&apikey=92bdca1b')
bom_match_json = get('http://octopart.com/api/v2/bom/match?lines=%5B%7B%22mpn%22%3A+%22SN74LS240N%22%7D%5D&pretty_print=true&apikey=92bdca1b')

class ArgumentValidationTest(unittest.TestCase):
	
	def setUp(self):
		unittest.TestCase.setUp(self)
	
	def tearDown(self):
		unittest.TestCase.tearDown(self)

class DataEquivalenceTest(unittest.TestCase):
	
	def setUp(self):
		unittest.TestCase.setUp(self)
	
	def test_categories_get(self):
		category = api.categories_get(4174)
		assert isinstance(category, OctopartCategory)
		assert(category.equals_json(categories_get_json))
		print 'test_categories_get OK'
	
	def test_categories_get_multi(self):
		categories = api.categories_get_multi([4215,4174,4780])
		for category in categories:
			assert isinstance(category, OctopartCategory)
			truth = [category.equals_json(x) for x in categories_get_multi_json]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_categories_get_multi OK'
	
	def test_categories_search(self):
		categories = api.categories_search(q='resistor')
		for category in categories:
			assert isinstance(category[0], OctopartCategory)
			truth = [category[0].equals_json(x['item']) for x in categories_search_json['results']]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_categories_search OK'
	
	def test_parts_get(self):
		part = api.parts_get(39619421)
		assert isinstance(part, OctopartPart)
		assert(part.equals_json(parts_get_json))
		print 'test_parts_get OK'
	
	def test_parts_get_multi(self):
		parts = api.parts_get_multi([39619421,29035751,31119928])
		for part in parts:
			assert isinstance(part, OctopartPart)
			truth = [part.equals_json(p) for p in parts_get_multi_json]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_parts_get_multi OK'
	
	def test_parts_search(self):
		parts = api.parts_search(q='resistor', limit=20)
		for part in parts:
			assert isinstance(part[0], OctopartPart)
			truth = [part[0].equals_json(x['item']) for x in parts_search_json['results']]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_parts_search OK'
	
	def tearDown(self):
		unittest.TestCase.tearDown(self)

if __name__ == '__main__':
	unittest.main()

