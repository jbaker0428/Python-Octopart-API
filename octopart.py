
''' 
A simple Python client frontend to the Octopart public REST API.

@author: Joe Baker <jbaker@alum.wpi.edu>

@license: 
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
''' 

__version__ = "0.1"
__author__ = "Joe Baker <jbaker@alum.wpi.edu>"
__contributors__ = []

import urllib2
import json
from types import *
import dateutil.parser
import datetime

class OctopartException(Exception):
	errors = {0: 'Required argument missing from method call.', \
			  1: 'Passed an invalid argument for this method.', \
			  2: 'Malformed argument.', \
			  3: 'An argument was passed more than once.', \
			  4: 'Numeric argument value out of valid range.', \
			  5: 'String argument outside of allowed length.', \
			  6: 'Value of (start+limit) in a bom/match line argument exceeds 100.', \
			  7: 'Unexpected HTTP Error 404', \
			  8: 'Unexpected HTTP Error 503'}
	
	def __init__(self, source, args, required_args, arg_types, arg_ranges, error_number):
		self.source = source
		self.arguments = args
		self.required_args = required_args
		self.arg_types = arg_types
		self.arg_ranges = arg_ranges
		self.error = error_number
		
	def __str__(self):
		args = '\nPassed arguments: ' + str(self.arguments)
		rargs = '\nRequired arguments: ' + str(self.required_args)
		argt = '\nArgument types: ' + str(self.arg_types)
		argr = '\nArgument ranges: ' + str(self.arg_ranges)
		string = OctopartException.errors[self.error] + ' Source: ' + self.source + args + rargs + argt + argr
		return string

class OctopartBrand:
	@staticmethod
	def new_from_dict(brand_dict):
		new = OctopartBrand(brand_dict['id'], brand_dict['displayname'], brand_dict['homepage'])
		return new
	
	def __init__(self, id, dispname, homepage):
		self.id = id
		self.displayname = dispname
		self.homepage_url = homepage

class OctopartCategory:
	@staticmethod
	def new_from_dict(category_dict):
		new = OctopartCategory(category_dict['id'], category_dict['parent_id'], category_dict['nodename'], \
							category_dict['images'], category_dict['children_ids'], category_dict['ancestor_ids'], \
							category_dict['ancestors'], category_dict['num_parts'])
		return new
	
	def __init__(self, id, parent_id, nodename, images, children_ids, ancestor_ids, ancestors, num_parts):
		self.id = id
		self.parent_id = parent_id
		self.nodename = nodename
		self.images = images	# List of dicts of URLs
		self.children_ids = children_ids	# List of child node ids
		self.ancestor_ids = ancestor_ids	# Sorted list of ancestor node ids (immediate parent first)
		self.ancestors = ancestors	# Sorted list of category objects
		self.num_parts = num_parts

class OctopartPart:
	def __init__(self, part_dict):
		# If class data is in dictionary format, convert everything to class instances 
		# Otherwise, assume it is already in class format and do nothing
		
		if type(part_dict['manufacturer']) is DictType:
			part_dict['manufacturer'] = OctopartBrand.new_from_dict(part_dict['manufacturer'])
		for offer in part_dict['offers']:
			if type(offer['supplier']) is DictType:
				offer['supplier'] = OctopartBrand.new_from_dict(offer['supplier'])
			# Convert ISO 8601 datetime strings to datetime objects
			if 'update_ts' in offer:
				offer['update_ts'] = dateutil.parser.parse(offer['update_ts']) 
			
		for spec in part_dict['specs']:
			if type(spec['attribute']) is DictType:
				spec['attribute'] = OctopartPartAttribute.new_from_dict(spec['attribute'])
		
		self.uid = part_dict['uid']
		self.mpn = part_dict['mpn']
		self.manufacturer = part_dict['manufacturer']
		self.detail_url = part_dict['detail_url']
		self.avg_price = part_dict['avg_price']
		self.avg_avail = part_dict['avg_avail']
		self.market_status = part_dict['market_status']
		self.num_suppliers = part_dict['num_suppliers']
		self.num_authsuppliers = part_dict['num_authsuppliers']
		self.short_description = part_dict['short_description']
		self.category_ids = part_dict['category_ids']
		self.images = part_dict['images']
		self.datasheets = part_dict['datasheets']
		self.descriptions = part_dict['descriptions']
		self.hyperlinks = part_dict['hyperlinks']
		self.offers = part_dict['offers']
		self.specs = part_dict['specs']

class OctopartPartAttribute:
	TYPE_TEXT = 'text'
	TYPE_NUMBER = 'number'
	
	@staticmethod
	def new_from_dict(attribute_dict):
		new = OctopartPartAttribute(attribute_dict['fieldname'], attribute_dict['displayname'], attribute_dict['type'], attribute_dict['metadata'])
		return new
	
	def __init__(self, fieldname, displayname, type, metadata):
		self.fieldname = fieldanme
		self.displayname = displayname
		self.type = type
		self.metadata = metadata

class Octopart:
	''' A simple client frontend to tho Octopart public REST API. 
	For detailed API documentation, refer to http://octopart.com/api/documentation'''
	api_url = 'http://octopart.com/api/v2/'
	
	@staticmethod
	def validate_args(args, required_args, arg_types, arg_ranges):
		''' Checks method arguments for syntax errors. 
		@param args: Dictionary of argumets to check
		@param required_args: frozen set of all argument names which must be present
		@param arg_types: Dictionary which contains the correct data type for each argument
		@param arg_ranges: Dictionary which contains range() calls for any numeric arguments with a limited range.
		Can also be used to constrain string argument length. For string arguments, contains a (min, max) pair.
		@raise OctopartException: If any syntax errors are found.'''
		valid_args = frozenset(arg_types.keys())
		args_set = set(args.keys())
		
		if required_args.issubset(args_set) is False:
			raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 0)
		if args_set.issubset(valid_args) is False:
			raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 1)
		for key in args_set:
			if arg_types[key] is StringType:
				if isinstance(args[key], basestring) is False:
					raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 2)
			else:
				if type(args[key]) is not arg_types[key]:
					raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 2)
			if key in arg_ranges.keys():
				if arg_types[key] is StringType:
					if len(args[key]) < arg_ranges[key][0] or len(args[key]) > arg_ranges[key][1]:
						raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 5)
				elif args[key] not in arg_ranges[key]:
					raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 4)
		if len(args_set) != len(args.keys()):
			raise OctopartException(Octopart.validate_args.__name__, args, required_args, arg_types, arg_ranges, 3)
	
	def __init__(self, apikey=None, callback=None, pretty_print=False):
		self.apikey = apikey
		self.callback = callback
		self.pretty_print = pretty_print
	
	def __get(self, method, args):
		''' Makes a GET request with the given method and arguments. 
		@param method: String containing the method path, such as "parts/search" 
		@param args: Dictionary of arguments to pass to the API method 
		@return: JSON response from server'''
		
		# Construct the request URL
		req_url = Octopart.api_url + method
		if self.apikey is not None:
			args['apikey'] = self.apikey
		if self.callback is not None:
			args['callback'] = self.callback
		if self.pretty_print is True:
			args['pretty_print'] = self.pretty_print
		if len(args) > 0:
			arg_strings = []
			for arg, val in args.items():
				if type(val) is BooleanType:
					v = int(val)
				elif type(val) is ListType:
					v = json.dumps(val, separators=(',',':'))
				else:
					v = val
				arg_strings.append(arg + '=' + str(v))


			req_url = req_url + '?' + '&'.join(arg_strings)
		
		response = urllib2.urlopen(req_url).read() 
		json_obj = json.loads(response)
		return json_obj

	def categories_get(self, args):
		''' Fetch a category object by its id. 
		@return: An OctopartCategory object or None. '''
		method = 'categories/get'
		required_args = frozenset(('id',))
		arg_types = {'id': IntType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_get.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(self.categories_get.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		return OctopartCategory.new_from_dict(json_obj)
	
	def categories_get_multi(self, args):
		''' Fetch multiple category objects by their ids. 
		@return: A list of OctopartCategory objects. '''
		method = 'categories/get_multi'
		required_args = frozenset(('ids',))
		arg_types = {'ids': ListType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_get_muti.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.categories_get_multi.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.categories_get_multi.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		categories = []
		for category in json_obj:
			categories.append(OctopartCategory.new_from_dict(category))
		return categories
	
	def categories_search(self, args):
		''' Execute search over all result objects. 
		@return: A list of [OctopartCategory, highlight_text] pairs. '''
		method = 'categories/search'
		required_args = frozenset()
		arg_types = {'q': StringType, 'start' : IntType, 'limit' : IntType, 'ancestor_id' : IntType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_search.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.categories_get_search.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.categories_get_search.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		categories = []
		for result in json_obj['results']:
			new_category = OctopartCategory.new_from_dict(result['item'])
			categories.append([new_category, result['highlight']])
		return categories
	
	def parts_get(self, args):
		''' Fetch a part object by its id. 
		@return: An OctopartPart object. '''
		method = 'parts/get'
		required_args = frozenset(('uid',))
		arg_types = {'uid': IntType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.parts_get.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(self.parts_get.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		return OctopartPart(json_obj)
	
	def parts_get_multi(self, args):
		''' Fetch multiple part objects by their ids. 
		@return: A list of OctopartPart objects. '''
		method = 'parts/get_multi'
		required_args = frozenset(('uids',))
		arg_types = {'uids': StringType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.parts_get_multi.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.parts_get_multi.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.parts_get_multi.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		parts = []
		for part in json_obj:
			parts.append(OctopartPart(part))
		return parts
	
	def parts_search(self, args):
		''' Execute a search over all result objects. 
		@return: A tuple pair containing:
		-A list of [OctopartPart, highlight_text] pairs. 
		-A list of drilldown result dictionaries. 
		If {drilldown.include : True} is not passed in the args dictionary, 
		the drilldown list will be empty. '''
		method = 'parts/search'
		required_args = frozenset()
		arg_types = {'q': StringType, \
					'start' : IntType, \
					'limit' : IntType, \
					'filters' : ListType, \
					'rangedfilters' : ListType, \
					'sortby' : ListType, \
					'drilldown.include' : BooleanType, \
					'drilldown.fieldname' : StringType, \
					'drilldown.facets.prefix' : StringType, \
					'drilldown.facets.start' : IntType, \
					'drilldown.facets.limit' : IntType, \
					'drilldown.facets.sortby' : StringType, \
					'drilldown.facets.include_hits' : BooleanType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {'start' : range(1001), \
					'limit' : range(0, 101), \
					'drilldown.facets.start' : range(1001), \
					'drilldown.facets.limit' : range(101)}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.parts_search.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.parts_search.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.parts_search.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		parts = []
		drilldown = []
		for result in json_obj['results']:
			new_part = OctopartPart(result['item'])
			parts.append([new_part, result['highlight']])
		if 'drilldown.include' in args and args['drilldown.include'] is True:
			for drill in json_obj['drilldown']:
				drill['attribute'] = OctopartPartAttribute.new_from_dict(drill['attribute'])
				drilldown.append(drill)
		return (parts, drilldown)
	
	def parts_suggest(self, args):
		''' Suggest a part search query string. 
		Optimized for speed (useful for auto-complete features).
		@return: A list of OctopartPart objects. '''
		method = 'parts/suggest'
		required_args = frozenset(('q',))
		arg_types = {'q': StringType, 'limit' : IntType}
		arg_ranges = {'q': (2, float("inf")), 'limit' : range(0, 11)}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.parts_suggest.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.parts_suggest.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.parts_suggest.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		parts = []
		for part in json_obj['results']:
			parts.append(OctopartPart(part))
		return parts
	
	def parts_match(self, args):
		''' Match (manufacturer name, mpn) to part uid. 
		@return: a list of (part uid, manufacturer displayname, mpn) tuples. '''
		method = 'parts/match'
		required_args = frozenset(('manufacturer_name', 'mpn'))
		arg_types = {'manufacturer_name': StringType, 'mpn' : StringType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.parts_match.__name__, args, required_args, arg_types, arg_ranges, e.error)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.parts_match.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.parts_match.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		return json_obj
	
	def partattributes_get(self, args):
		''' Fetch a partattribute object by its fieldname. 
		@return: An OctopartPartAttribute object. '''
		method = 'partattributes/get'
		required_args = frozenset(('fieldname',))
		arg_types = {'fieldname': StringType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.partattributes_get.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(self.partattributes_get.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		return OctopartPartAttribute.new_from_dict(json_obj)
	
	def partattributes_get_multi(self, args):
		''' Fetch multiple partattributes objects by their fieldnames. 
		@return: A list of OctopartPartAttribute objects. '''
		method = 'partattributes/get_multi'
		required_args = frozenset(('ids',))
		arg_types = {'ids': ListType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.partattributes_get_multi.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.partattributes_get_multi.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.partattributes_get_multi.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		attributes = []
		for attribute in json_obj:
			attributes.append(OctopartPartAttribute.new_from_dict(attribute))
		return attributes
	
	def bom_match(self, args):
		''' Match a list of part numbers to Octopart part objects. 
		@return: A list of 3-item dicts containing a list of OctopartParts, 
		a reference string, and a status string. '''
		method = 'bom/match'
		required_args = frozenset(('lines',))
		arg_types = {'lines': ListType, \
					'optimize.return_stubs' : BooleanType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		
		# DictType arguments need to be validated just like the normal args dict
		lines_required_args = frozenset(('reference',))
		lines_arg_types = {'q': StringType, \
					'mpn' : StringType, \
					'manufacturer' : StringType, \
					'sku' : StringType, \
					'supplier' : StringType, \
					'mpn_or_sku' : StringType, \
					'start' : IntType, \
					'limit' : IntType, \
					'reference' : StringType}
		lines_arg_ranges = {'limit' : range(21)}
		for line in args['lines']:
			try:
				Octopart.validate_args(line, lines_required_args, lines_arg_types, lines_arg_ranges)
			except OctopartException as e:
				raise OctopartException(self.bom_match.__name__, line, lines_required_args, lines_arg_types, lines_arg_ranges, e.error)
			# Method-specific check not covered by validate_args:
			if (line['start'] + line['match']) > 100:
				raise OctopartException(self.bom_match.__name__, line, lines_required_args, lines_arg_types, lines_arg_ranges, 6)
		
		# Now check the primary args dict as normal
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.bom_match.__name__, args, required_args, arg_types, arg_ranges, e.error)
		
		
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(self.bom_match.__name__, args, required_args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(self.bom_match.__name__, args, required_args, arg_types, arg_ranges, 8)
			else:
				raise e
		results = []
		for result in json_obj['results']:
			items = []
			for item in result['items']:
				items.append(OctopartPart(part))
			results.append({'items' : items, 'reference' : result['reference'], 'status' : result['status']})
		
		return results
