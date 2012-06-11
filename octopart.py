
""" 
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
"""

__version__ = "0.3.1"
__author__ = "Joe Baker <jbaker@alum.wpi.edu>"
__contributors__ = []

import urllib2
import json
from types import *
import datetime
import traceback

class OctopartException(Exception):
	
	"""Various errors that can be raised by the Octopart API."""
	
	__slots__ = ["arguments", "arg_types", "arg_ranges", "code"]
	errors = {0: 'Required argument missing from method call.', \
			  1: 'Passed an invalid argument for this method.', \
			  2: 'Argument type mismatch.', \
			  3: 'An argument was passed more than once.', \
			  4: 'Numeric argument value out of valid range.', \
			  5: 'String argument outside of allowed length.', \
			  6: 'Value of (start+limit) in a bom/match line argument exceeds 100.', \
			  7: 'Unexpected HTTP Error 404.', \
			  8: 'Unexpected HTTP Error 503.', \
			  9: 'Argument is not a JSON-encoded list of pairs.', \
			  10: 'Invalid sort order. Valid sort order strings are "asc" and "desc".', \
			  11: 'List argument outside of allowed length.'}
	
	def __init__(self, args, arg_types, arg_ranges, error_code):
		self.arguments = args
		self.arg_types = arg_types
		self.arg_ranges = arg_ranges
		self.code = error_code
		
	def __str__(self):
		args = '\nPassed arguments: ' + str(self.arguments)
		argt = '\nArgument types: ' + str(self.arg_types)
		argr = '\nArgument ranges: ' + str(self.arg_ranges)
		string = OctopartException.errors[self.code] + args + argt + argr
		return string

class OctopartBrand(object):
	__slots__ = ["id", "displayname", "homepage_url"]
	
	@classmethod
	def new_from_dict(cls, brand_dict):
		new = cls(brand_dict['id'], brand_dict['displayname'], brand_dict['homepage_url'])
		return new
	
	def __init__(self, id, dispname, homepage):
		self.id = id
		self.displayname = dispname
		self.homepage_url = homepage

class OctopartCategory(object):
	@classmethod
	def new_from_dict(cls, category_dict):
		new = cls(category_dict['id'], category_dict['parent_id'], category_dict['nodename'], \
							category_dict['images'], category_dict['children_ids'], category_dict['ancestor_ids'], \
							category_dict.get('ancestors', []), category_dict['num_parts'])
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

class OctopartPart(object):
	
	@classmethod
	def new_from_dict(cls, part_dict):
		"""Constructor for use with JSON resource dictionaries."""
		
		uid = part_dict.pop('uid')
		mpn = part_dict.pop('mpn')
		manufacturer = part_dict.pop('manufacturer')
		detail_url = part_dict.pop('detail_url')
		return cls(uid, mpn, manufacturer, detail_url, **part_dict)
	
	def __init__(self, uid, mpn, manufacturer, detail_url, **kwargs):
		# If class data is in dictionary format, convert everything to class instances 
		# Otherwise, assume it is already in class format and do nothing
		if type(manufacturer) is DictType:
			manufacturer = OctopartBrand.new_from_dict(manufacturer)
		for offer in kwargs.get('offers', []):
			if type(offer['supplier']) is DictType:
				offer['supplier'] = OctopartBrand.new_from_dict(offer['supplier'])
			# Convert ISO 8601 datetime strings to datetime objects
			if 'update_ts' in offer:
				# Strip 'Z' UTC notation that can't be parsed
				if offer['update_ts'][-1] == 'Z':
					offer['update_ts'] = offer['update_ts'][0:-1]
				offer['update_ts'] = datetime.datetime.strptime(offer['update_ts'], '%Y-%m-%dT%H:%M:%S')
			
		for spec in kwargs.get('specs', []):
			if type(spec['attribute']) is DictType:
				spec['attribute'] = OctopartPartAttribute.new_from_dict(spec['attribute'])
		
		self.uid = uid
		self.mpn = mpn
		self.manufacturer = manufacturer
		self.detail_url = detail_url
		self.avg_price = kwargs.get('avg_price')
		self.avg_avail = kwargs.get('avg_avail')
		self.market_status = kwargs.get('market_status')
		self.num_suppliers = kwargs.get('num_suppliers')
		self.num_authsuppliers = kwargs.get('num_authsuppliers')
		self.short_description = kwargs.get('short_description', '')
		self.category_ids = kwargs.get('category_ids', [])
		self.images = kwargs.get('images', [])
		self.datasheets = kwargs.get('datasheets', [])
		self.descriptions = kwargs.get('descriptions', [])
		self.hyperlinks = kwargs.get('hyperlinks', {})
		self.offers = kwargs.get('offers', [])
		self.specs = kwargs.get('specs', [])

class OctopartPartAttribute(object):
	TYPE_TEXT = 'text'
	TYPE_NUMBER = 'number'
	
	@classmethod
	def new_from_dict(cls, attribute_dict):
		new = cls(attribute_dict['fieldname'], attribute_dict['displayname'], attribute_dict['type'], attribute_dict.get('metadata', {}))
		return new
	
	def __init__(self, fieldname, displayname, attribute_type, metadata):
		self.fieldname = fieldname
		self.displayname = displayname
		self.type = attribute_type
		self.metadata = metadata

class Octopart(object):
	
	"""A simple client frontend to tho Octopart public REST API. 
	
	For detailed API documentation, refer to http://octopart.com/api/documentation.
	"""
	
	api_url = 'http://octopart.com/api/v2/'
	__slots__ = ["apikey", "callback", "pretty_print"]
	
	def __init__(self, apikey=None, callback=None, pretty_print=False):
		self.apikey = apikey
		self.callback = callback
		self.pretty_print = pretty_print
	
	def __validate_args(self, args, arg_types, arg_ranges):
		""" Checks method arguments for syntax errors.
		
		@param args: Dictionary of argumets to check
		@param arg_types: Dictionary which contains the correct data type for each argument.
		@param arg_ranges: Dictionary which contains range() calls for any numeric arguments with a limited range.
		Can also be used to constrain string argument length. For string arguments, contains a (min, max) pair.
		@raise OctopartException: If any syntax errors are found.
		"""
		
		valid_args = frozenset(arg_types.keys())
		args_set = set(args.keys())
		
		if args_set.issubset(valid_args) is False:
			raise OctopartException(args, arg_types, arg_ranges, 1)
		for key in args_set:
			if arg_types[key] is StringType:
				if isinstance(args[key], basestring) is False:
					raise OctopartException(args, arg_types, arg_ranges, 2)
			elif type(arg_types[key]) is TupleType:	# Tuple of types
				if type(args[key]) not in arg_types[key]:
					raise OctopartException(args, arg_types, arg_ranges, 2)
			else:
				if type(args[key]) is not arg_types[key]:
					raise OctopartException(args, arg_types, arg_ranges, 2)
			if key in arg_ranges.keys():
				if len(args[key]) < arg_ranges[key][0] or len(args[key]) > arg_ranges[key][1]:
					if arg_types[key] is StringType:
						raise OctopartException(args, arg_types, arg_ranges, 5)
					elif arg_types[key] is ListType:
						raise OctopartException(args, arg_types, arg_ranges, 11)
					elif arg_types[key] in (IntType, LongType, FloatType):
						raise OctopartException(args, arg_types, arg_ranges, 4)
		if len(args_set) != len(args.keys()):
			raise OctopartException(args, arg_types, arg_ranges, 3)
	
	def __get(self, method, args):
		"""Makes a GET request with the given API method and arguments.
		
		@param method: String containing the method path, such as "parts/search".
		@param args: Dictionary of arguments to pass to the API method.
		@return: JSON response from server.
		"""
		
		# Construct the request URL
		req_url = Octopart.api_url + method
		if self.apikey:
			args['apikey'] = self.apikey
		if self.callback:
			args['callback'] = self.callback
		if self.pretty_print:
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
		json_obj = json.loads(unicode(response))
		return json_obj
	
	def __translate_periods(self, args):
		"""Translates Python-friendly keyword arguments to valid Octopart API arguments.
		
		Several Octopart API arguments contain a period in their name.
		Unfortunately, trying to unpack a keyword argument in a Python function with 
		a period in the argument name will cause a syntax code: 
		'keyword can't be an expression'
		
		Therefore, the Python API methods expect an underscore in place of the
		periods in the argument names. This method replaces those underscores with
		periods for passing to the private class methods, which do not attempt
		to unpack the arguments dict.
		
		@param args: Unpackable keyword arguments dict from a public API call.
		@return Translated keyword arguments dict.
		"""
		
		translation = {'drilldown_include' : 'drilldown.include', \
					'drilldown_fieldname' : 'drilldown.fieldname', \
					'drilldown_facets_prefix' : 'drilldown.facets.prefix', \
					'drilldown_facets_start' : 'drilldown.facets.start', \
					'drilldown_facets_limit' : 'drilldown.facets.limit', \
					'drilldown_facets_sortby' : 'drilldown.facets.sortby', \
					'drilldown_facets_include_hits' : 'drilldown.facets.include_hits', \
					'optimize_return_stubs' : 'optimize.return_stubs', \
					'optimize_hide_datasheets' : 'optimize.hide_datasheets', \
					'optimize_hide_descriptions' : 'optimize.hide_descriptions', \
					'optimize_hide_images' : 'optimize.hide_images', \
					'optimize_hide_hide_offers' : 'optimize.hide_hide_offers', \
					'optimize_hide_hide_unauthorized_offers' : 'optimize.hide_hide_unauthorized_offers', \
					'optimize_hide_specs' : 'optimize.hide_specs'}
		
		for key in args:
			# Handle any list/dict arguments which may contain more arguments within 
			if type(args[key]) is DictType:
				args[key] = self.__translate_periods(args[key])
			elif type(args[key]) is ListType:
				for a in args[key]:
					if type(a) is DictType:
						a = self.__translate_periods(a)
						
			if key in translation:
				args[translation[key]] = args.pop(key)
			
		return args

	def categories_get(self, id):
		"""Fetch a category object by its id. 
		
		@return: An OctopartCategory object or None.
		"""
		
		method = 'categories/get'
		arg_types = {'id': (IntType, LongType)}
		arg_ranges = {}
		args = {'id' : id}
		
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return OctopartCategory.new_from_dict(json_obj)
		else:
			return None
	
	def categories_get_multi(self, ids):
		"""Fetch multiple category objects by their ids. 
		
		@return: A list of OctopartCategory objects.
		"""
		
		method = 'categories/get_multi'
		arg_types = {'ids': ListType}
		arg_ranges = {}
		args = {'ids' : ids}
		
		self.__validate_args(args, arg_types, arg_ranges)
		for id in args['ids']:
			if type(id) not in (IntType, LongType):
				raise OctopartException(args, arg_types, arg_ranges, 2)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		categories = []
		if json_obj:
			for category in json_obj:
				categories.append(OctopartCategory.new_from_dict(category))
		return categories
		
	
	def categories_search(self, **args):
		"""Execute search over all result objects. 
		
		@return: A list of [OctopartCategory, highlight_text] pairs.
		"""
		
		method = 'categories/search'
		arg_types = {'q': StringType, 'start' : IntType, 'limit' : IntType, 'ancestor_id' : IntType}
		arg_ranges = {}
		
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		categories = []
		if json_obj:
			for result in json_obj['results']:
				new_category = OctopartCategory.new_from_dict(result['item'])
				categories.append([new_category, result['highlight']])
		return categories
	
	def parts_get(self, uid, **kwargs):
		"""Fetch a part object by its id.
		
		@return: An OctopartPart object.
		"""
		
		method = 'parts/get'
		arg_types = {'uid': (IntType, LongType), \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		args = self.__translate_periods(kwargs)
		args['uid'] = uid
		
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return OctopartPart.new_from_dict(json_obj)
		else:
			return None
	
	def parts_get_multi(self, uids, **kwargs):
		"""Fetch multiple part objects by their ids.
		
		@return: A list of OctopartPart objects.
		"""
		
		method = 'parts/get_multi'
		arg_types = {'uids': ListType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {'uids': (0, 100)}
		args = self.__translate_periods(kwargs)
		args['uids'] = uids
		
		for id in args['uids']:
			if type(id) not in (IntType, LongType):
				raise OctopartException(args, arg_types, arg_ranges, 2)
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		parts = []
		if json_obj:
			for part in json_obj:
				parts.append(OctopartPart.new_from_dict(part))
		return parts
	
	def parts_search(self, **kwargs):
		"""Execute a search over all result objects.
		
		@return: A tuple pair containing:
			-A list of [OctopartPart, highlight_text] pairs. 
			-A list of drilldown result dictionaries. 
		If {drilldown.include : True} is not passed in the args dictionary, 
		the drilldown list will be empty.
		"""
		
		method = 'parts/search'
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
		arg_ranges = {'start' : (0, 1000), \
					'limit' : (0, 100), \
					'drilldown.facets.start' : (0, 1000), \
					'drilldown.facets.limit' : (0, 100)}
		
		args = self.__translate_periods(kwargs)
		# Method-specific checks not covered by validate_args:
		for filter in args.get('filters', []):
			if len(filter) != 2:
				raise OctopartException(args, arg_types, arg_ranges, 9)
			if isinstance(filter[0], basestring) is False:
				raise OctopartException(args, arg_types, arg_ranges, 2)
			if type(filter[1]) is not ListType:
				raise OctopartException(args, arg_types, arg_ranges, 2)
		
		for filter in args.get('rangedfilters', []):
			if len(filter) != 2:
				raise OctopartException(args, arg_types, arg_ranges, 9)
			if isinstance(filter[0], basestring) is False:
				raise OctopartException(args, arg_types, arg_ranges, 2)
			if type(filter[1]) is not ListType:
				raise OctopartException(args, arg_types, arg_ranges, 2)
			for r in filter[1]:
				if len(r) != 2:
					raise OctopartException(args, arg_types, arg_ranges, 9)
				for limit in r:
					if type(limit) not in (IntType, FloatType, NoneType, LongType):
						raise OctopartException(args, arg_types, arg_ranges, 2)
	
		for order in args.get('sortby', []):
			if len(order) != 2:
				raise OctopartException(args, arg_types, arg_ranges, 9)
			if isinstance(order[0], basestring) is False:
				raise OctopartException(args, arg_types, arg_ranges, 2)
			if isinstance(order[1], basestring) is False:
				raise OctopartException(args, arg_types, arg_ranges, 2)
			if order[1] not in ('asc', 'desc'):
				raise OctopartException(args, arg_types, arg_ranges, 10)
		
				
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		parts = []
		drilldown = []
		if json_obj:
			for result in json_obj['results']:
				new_part = OctopartPart.new_from_dict(result['item'])
				parts.append([new_part, result['highlight']])
			if args.get('drilldown.include'):
				for drill in json_obj['drilldown']:
					drill['attribute'] = OctopartPartAttribute.new_from_dict(drill['attribute'])
					drilldown.append(drill)
		return (parts, drilldown)
	
	def parts_suggest(self, q, **args):
		"""Suggest a part search query string.
		
		Optimized for speed (useful for auto-complete features).
		@return: A list of manufacturer part number strings.
		"""
		
		method = 'parts/suggest'
		arg_types = {'q': StringType, 'limit' : IntType}
		arg_ranges = {'q': (2, float("inf")), 'limit' : (0, 10)}
		
		args['q'] = q
		
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj['results']
		else:
			return None
	
	def parts_match(self, manufacturer_name, mpn):
		"""Match (manufacturer name, mpn) to part uid. 
		
		@return: a list of (part uid, manufacturer displayname, mpn) tuples.
		"""
		
		method = 'parts/match'
		arg_types = {'manufacturer_name': StringType, 'mpn' : StringType}
		arg_ranges = {}
		args = {'manufacturer_name': manufacturer_name, 'mpn' : mpn}
		
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj
		else:
			return None
	
	def partattributes_get(self, fieldname):
		"""Fetch a partattribute object by its fieldname.
		
		@return: An OctopartPartAttribute object.
		"""
		
		method = 'partattributes/get'
		arg_types = {'fieldname': StringType}
		arg_ranges = {}
		args = {'fieldname': fieldname}
		
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return OctopartPartAttribute.new_from_dict(json_obj)
		else:
			return None
	
	def partattributes_get_multi(self, fieldnames):
		"""Fetch multiple partattributes objects by their fieldnames.
		
		@return: A list of OctopartPartAttribute objects.
		"""
		
		method = 'partattributes/get_multi'
		arg_types = {'fieldnames': ListType}
		arg_ranges = {}
		args = {'fieldnames': fieldnames}
		
		for name in args['fieldnames']:
			if isinstance(name, basestring) is False:
				raise OctopartException(args, arg_types, arg_ranges, 2)
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		attributes = []
		if json_obj:
			for attribute in json_obj:
				attributes.append(OctopartPartAttribute.new_from_dict(attribute))
		return attributes
	
	def bom_match(self, lines, **kwargs):
		"""Match a list of part numbers to Octopart part objects.
		 
		@return: A list of 3-item dicts containing:
			-A list of OctopartParts.
			-A reference string.
			-A status string.
		"""
		
		method = 'bom/match'
		arg_types = {'lines': ListType, \
					'optimize.return_stubs' : BooleanType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		
		args = self.__translate_periods(kwargs)
		args['lines'] = lines
		
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
		for line in lines:
			self.__validate_args(line, lines_arg_types, lines_arg_ranges)
			# Method-specific checks not covered by validate_args:
			if lines_required_args.issubset(set(line.keys())) is False:
				raise OctopartException(line, lines_arg_types, lines_arg_ranges, 0)
			if (line.get('start', 0) + line.get('match', 0)) > 100:
				raise OctopartException(line, lines_arg_types, lines_arg_ranges, 6)

		# Now check the primary args dict as normal
		self.__validate_args(args, arg_types, arg_ranges)
		try:
			json_obj = self.__get(method, args)
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		results = []
		if json_obj:
			for result in json_obj['results']:
				items = []
				for item in result['items']:
					items.append(OctopartPart.new_from_dict(part))
				results.append({'items' : items, 'reference' : result.get('reference', ''), 'status' : result['status']})
		
		return results
