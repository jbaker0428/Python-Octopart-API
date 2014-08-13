"""
NOTE: Running this unit test generates 24 API requests.
"""

import os
import unittest
import urllib2
import json
import traceback

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

class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    @author: StackOverflow user hughdbrown
    @see: http://stackoverflow.com/questions/1165352/fast-comparison-between-two-python-dictionary/1165552#1165552
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

def get(req_url):
	"""Return a JSON dictionary from a pre-formed request URL."""
	
	response = unicode(urllib2.urlopen(req_url).read())
	return json.loads(response)

def json_eq(a, b):
	"""Asserts that two JSON objects are equal, ignoring dict keys named 'time'."""
	
	assert type(a) == type(b)
	if type(a) == dict:
		try:
			assert sorted(a.keys()) == sorted(b.keys())
		except AssertionError:
			traceback.print_exc()
			diff = DictDiffer(a, b)
			print 'Added keys:\n', diff.added()
			print 'Removed keys:\n', diff.removed()
			raise AssertionError(sorted(a.keys()), sorted(b.keys()))
		for key in sorted(a.keys()):
			if key != 'time':
				try:
					json_eq(a[key], b[key])
				except AssertionError:
					traceback.print_exc()
					diff = DictDiffer(a, b)
					dk = diff.changed()
					print 'Changed:'
					print 'key    a    b'
					for k in dk:
						print k, a[k], b[k]
					raise AssertionError(key, a[key], b[key])
			
	elif type(a) == list:
		try:
			assert len(a) == len(b)
		except AssertionError:
			traceback.print_exc()
			raise AssertionError(len(a), len(b))
		c = sorted(a)
		d = sorted(b)
		for i in range(len(a)):
			try:
				json_eq(c[i], d[i])
			except AssertionError:
				traceback.print_exc()
				raise AssertionError(i, c[i], d[i])
	else:
		try:
			assert a == b
		except AssertionError:
			traceback.print_exc()
			raise AssertionError(a, b)

api = Octopart(apikey='92bdca1b')
# Reference JSON objects with known-good URL
brand = OctopartBrand(459, "Digi-Key", "http://www.digikey.com")
categories_get_ref = get('http://octopart.com/api/v2/categories/get?id=4174&apikey=92bdca1b')
categories_get_multi_ref = get('http://octopart.com/api/v2/categories/get_multi?ids=[4215,4174,4780]&apikey=92bdca1b')
categories_search_ref = get('http://octopart.com/api/v2/categories/search?q=resistor&apikey=92bdca1b')
parts_get_ref = get('http://octopart.com/api/v2/parts/get?uid=39619421&apikey=92bdca1b')
parts_get_multi_ref = get('http://octopart.com/api/v2/parts/get_multi?uids=[39619421,29035751,31119928]&apikey=92bdca1b')
parts_search_ref = get('http://octopart.com/api/v2/parts/search?q=resistor&limit=10&apikey=92bdca1b')
parts_suggest_ref = get('http://octopart.com/api/v2/parts/suggest?q=sn74f&limit=3&apikey=92bdca1b')
parts_match_ref = get('http://octopart.com/api/v2/parts/match?manufacturer_name=texas+instruments&mpn=SN74LS240N&apikey=92bdca1b')
partattributes_get_ref = get('http://octopart.com/api/v2/partattributes/get?fieldname=capacitance&apikey=92bdca1b')
partattributes_get_multi_ref = get('http://octopart.com/api/v2/partattributes/get_multi?fieldnames=["capacitance","resistance"]&apikey=92bdca1b')
bom_match_ref = get('http://octopart.com/api/v2/bom/match?lines=[{%22mpn%22%3A+%22SN74LS240N%22%2C+%22manufacturer%22%3A+%22Texas+Instruments%22},' +
                    '{%22mpn%22%3A+%22RB-220-07A+R%22%2C+%22manufacturer%22%3A+%22C%26K%20Components%22}]&apikey=92bdca1b')

class ArgumentValidationTest(unittest.TestCase):
	
	def setUp(self):
		unittest.TestCase.setUp(self)
	
	def tearDown(self):
		unittest.TestCase.tearDown(self)

class DataEquivalenceTest(unittest.TestCase):
	
	def test_categories_get(self):
		json_obj, category = api.categories_get(4174)
		assert json_obj is not None
		assert json_obj == categories_get_ref
		assert isinstance(category, OctopartCategory)
		assert(category.equals_json(categories_get_ref))
		print 'test_categories_get OK'
	
	def test_categories_get_multi(self):
		json_obj, categories = api.categories_get_multi([4215,4174,4780])
		assert json_obj is not None
		assert json_obj == categories_get_multi_ref
		for category in categories:
			assert isinstance(category, OctopartCategory)
			truth = [category.equals_json(x) for x in categories_get_multi_ref]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_categories_get_multi OK'
	
	def test_categories_search(self):
		json_obj, categories = api.categories_search(q='resistor')
		assert json_obj is not None
		assert json_obj == categories_search_ref
		for category in categories:
			assert isinstance(category[0], OctopartCategory)
			truth = [category[0].equals_json(x['item']) for x in categories_search_ref['results']]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_categories_search OK'
	
	def test_parts_get(self):
		json_obj, part = api.parts_get(39619421)
		assert json_obj is not None
		assert json_obj == parts_get_ref
		assert isinstance(part, OctopartPart)
		assert(part.equals_json(parts_get_ref))
		print 'test_parts_get OK'
	
	def test_parts_get_multi(self):
		json_obj, parts = api.parts_get_multi([39619421,29035751,31119928])
		assert json_obj is not None
		assert json_obj == parts_get_multi_ref
		for part in parts:
			assert isinstance(part, OctopartPart)
			truth = [part.equals_json(p) for p in parts_get_multi_ref]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_parts_get_multi OK'
	
	def test_parts_search(self):
		json_obj, parts = api.parts_search(q='resistor', limit=10)
		assert json_obj is not None
		json_eq(json_obj, parts_search_ref)
		for part, highlight in parts:
			assert isinstance(part, OctopartPart)
			assert True in [highlight == r['highlight'] for r in parts_search_ref['results']]
			truth = [part.equals_json(r['item']) for r in parts_search_ref['results']]
			assert True in truth
			assert truth.count(True) == 1
		print 'test_parts_search OK'
	
	def test_parts_suggest(self):
		json_obj, results = api.parts_suggest(q='sn74f', limit=3)
		assert json_obj is not None
		json_eq(json_obj, parts_suggest_ref)
		assert json_obj['results'] == results
		print 'test_parts_suggest OK'
	
	def test_parts_match(self):
		json_obj = api.parts_match(manufacturer_name='texas instruments', mpn='SN74LS240N')
		assert json_obj is not None
		assert json_obj == parts_match_ref
	
	def test_partattributes_get(self):
		json_obj, attrib = api.partattributes_get('capacitance')
		assert json_obj is not None
		assert json_obj == partattributes_get_ref
		assert isinstance(attrib, OctopartPartAttribute)
		assert attrib.equals_json(json_obj)
		print 'test_partattributes_get OK'
	
	def test_partattributes_get_multi(self):
		json_obj, attribs = api.partattributes_get_multi(['capacitance', 'resistance'])
		assert json_obj is not None
		assert json_obj == partattributes_get_multi_ref
		for attrib in attribs:
			assert isinstance(attrib, OctopartPartAttribute)
			assert True in [attrib.equals_json(a) for a in json_obj]
		print 'test_partattributes_get_multi OK'
		
	def test_bom_match(self):
		json_obj, results = api.bom_match(lines=[
            {'mpn':'SN74LS240N', 'manufacturer':'Texas Instruments'},
            {'mpn':'RB-220-07A R','manufacturer':'C&K Components'}
            ])
		assert json_obj is not None
		json_eq(json_obj, bom_match_ref)
		
		for result in results:
			if result.get('hits') is not None:	# Not in API docs, but exists
				assert result['hits'] == len(result['items'])
			assert result['status'] == json_obj['results'][results.index(result)]['status']
			assert result['reference'] == json_obj['results'][results.index(result)]['reference']
			for part in result['items']:
				assert isinstance(part, OctopartPart)
				assert part.equals_json(json_obj['results'][results.index(result)]['items'][result['items'].index(part)])
		print 'test_bom_match OK'
	
if __name__ == '__main__':
	unittest.main()

