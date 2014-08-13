
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

__version__ = "0.5.5"
__author__ = "Joe Baker <jbaker@alum.wpi.edu>"
__contributors__ = []

import copy
import urllib2
import json
from types import *
import datetime

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
		args = ' '.join(('\nPassed arguments:', str(self.arguments)))
		argt = ' '.join(('\nArgument types:', str(self.arg_types)))
		argr = ' '.join(('\nArgument ranges:', str(self.arg_ranges)))
		string = OctopartException.errors[self.code] + args + argt + argr
		return string

class OctopartBrand(object):
	
	@classmethod
	def new_from_dict(cls, brand_dict):
		new = cls(brand_dict['id'], brand_dict['displayname'], brand_dict['homepage_url'])
		return new
	
	def __init__(self, id, dispname, homepage):
		self._id = id
		self.displayname = dispname
		self.homepage_url = homepage
	
	@property
	def id(self):
		return self._id
	
	def equals_json(self, resource):
		"""Checks the object for data equivalence to a JSON Brand resource."""
		
		if isinstance(resource, DictType) and resource.get('__class__') == 'Brand': 
			if self.id != resource.get('id'):
				return False
			if self.displayname != resource.get('displayname'):
				return False
			if self.homepage_url != resource.get('homepage_url'):
				return False
		else:
			return False
		return True
	
	def __eq__(self, b):
		if isinstance(b, OctopartBrand):
			try:
				if self.id != b.id:
					return False
				if self.displayname != b.displayname:
					return False
				if self.homepage_url != b.homepage_url:
					return False
			except AttributeError:
				return False
		else:
			return False
		return True
	
	def __ne__(self, b):
		return not self.__eq__(b)
	
	def __hash__(self):
		return (hash(self.__class__), hash(self.id))
	
	def __str__(self):
		return ''.join(('Brand ', str(self.id), ': ', self.displayname, ' (', self.homepage_url, ')'))

class OctopartCategory(object):
	
	@classmethod
	def new_from_dict(cls, category_dict):
		new_dict = copy.deepcopy(category_dict)
		new = cls(new_dict['id'], new_dict['parent_id'], new_dict['nodename'], \
							new_dict['images'], new_dict['children_ids'], new_dict['ancestor_ids'], \
							new_dict.get('ancestors', []), new_dict['num_parts'])
		return new
	
	def __init__(self, id, parent_id, nodename, images, children_ids, ancestor_ids, ancestors, num_parts):
		self._id = id
		self.parent_id = parent_id
		self.nodename = nodename
		self.images = images	# List of dicts of URLs
		self.children_ids = children_ids	# List of child node ids
		self.ancestor_ids = ancestor_ids	# Sorted list of ancestor node ids (immediate parent first)
		self.ancestors = ancestors	# Sorted list of category objects
		self.num_parts = num_parts
	
	@property
	def id(self):
		return self._id
	
	def equals_json(self, resource):
		"""Checks the object for data equivalence to a JSON Category resource."""
		
		if isinstance(resource, DictType) and resource.get('__class__') == 'Category': 
			if self.id != resource.get('id'):
				return False
			if self.parent_id != resource.get('parent_id'):
				return False
			if self.nodename != resource.get('nodename'):
				return False
			if sorted(self.images) != sorted(resource.get('images')):
				return False
			if sorted(self.children_ids) != sorted(resource.get('children_ids')):
				return False
			if sorted(self.ancestor_ids) != sorted(resource.get('ancestor_ids')):
				return False
			if set(self.ancestors) != set(resource.get('ancestors', [])):
				return False
			if self.num_parts != resource.get('num_parts'):
				return False
		else:
			return False
		return True
	
	def __eq__(self, c):
		if isinstance(c, OctopartCategory):
			try:
				if self.id != c.id:
					return False
				if self.parent_id != c.parent_id:
					return False
				if self.nodename != c.nodename:
					return False
				if sorted(self.images != c.images):
					return False
				if sorted(self.children_ids) != sorted(c.children_ids):
					return False
				if sorted(self.ancestor_ids) != sorted(c.ancestor_ids):
					return False
				if set(self.ancestors) != set(c.ancestors):
					return False
				if self.num_parts != c.num_parts:
					return False
			except AttributeError:
				return False
		else:
			return False
		return True
	
	def __ne__(self, c):
		return not self.__eq__(c)
	
	def __hash__(self):
		return (hash(self.__class__), hash(self.id))
	
	def __str__(self):
		return ''.join(('Category ', str(self.id), ': ', self.nodename))

class OctopartPart(object):
	
	@classmethod
	def new_from_dict(cls, part_dict):
		"""Constructor for use with JSON resource dictionaries."""
		
		copied_dict = part_dict.copy()
		uid = copied_dict.pop('uid')
		mpn = copied_dict.pop('mpn')
		manufacturer = copied_dict.pop('manufacturer')
		detail_url = copied_dict.pop('detail_url')
		return cls(uid, mpn, manufacturer, detail_url, **copied_dict)
	
	def __init__(self, uid, mpn, manufacturer, detail_url, **kwargs):
		# If class data is in dictionary format, convert everything to class instances 
		# Otherwise, assume it is already in class format and do nothing
		args = copy.deepcopy(kwargs)
		if type(manufacturer) is DictType:
			manufacturer = OctopartBrand.new_from_dict(copy.deepcopy(manufacturer))
		for offer in args.get('offers', []):
			if type(offer['supplier']) is DictType:
				offer['supplier'] = OctopartBrand.new_from_dict(offer['supplier'])
			# Convert ISO 8601 datetime strings to datetime objects
			if 'update_ts' in offer:
				# Strip 'Z' UTC notation that can't be parsed
				if offer['update_ts'][-1] == 'Z':
					offer['update_ts'] = offer['update_ts'][0:-1]
				offer['update_ts'] = datetime.datetime.strptime(offer['update_ts'], '%Y-%m-%dT%H:%M:%S')
			
		for spec in args.get('specs', []):
			if type(spec['attribute']) is DictType:
				spec['attribute'] = OctopartPartAttribute.new_from_dict(spec['attribute'])
		
		self._uid = uid
		self._mpn = mpn
		self.manufacturer = manufacturer
		self.detail_url = detail_url
		self.avg_price = args.get('avg_price')
		self.avg_avail = args.get('avg_avail')
		self.market_status = args.get('market_status')
		self.num_suppliers = args.get('num_suppliers')
		self.num_authsuppliers = args.get('num_authsuppliers')
		self.short_description = args.get('short_description', '')
		self.category_ids = args.get('category_ids', [])
		self.images = args.get('images', [])
		self.datasheets = args.get('datasheets', [])
		self.descriptions = args.get('descriptions', [])
		self.hyperlinks = args.get('hyperlinks', {})
		self.offers = args.get('offers', [])
		self.specs = args.get('specs', [])
	
	@property
	def uid(self):
		return self._uid
	
	@property
	def mpn(self):
		return self._mpn
	
	def get_authorized_offers(self):
		return [o for o in self.offers if o['is_authorized'] is True]
	
	def get_unauthorized_offers(self):
		return [o for o in self.offers if o['is_authorized'] is False]
	
	def equals_json(self, resource, hide_datasheets=False, hide_descriptions=False, hide_images=False, \
				hide_offers=False, hide_unauthorized_offers=False, hide_specs=False):
		"""Checks the object for data equivalence to a JSON Part resource."""
		
		def compare_offers(class_offer, json_offer):
			"""Compares two offers.
			
			@param class_offer: An offer from an OctopartPart instance.
			@param json_offer: An offer from a JSON Part resource.
			"""
			
			class_attribs = (class_offer['sku'], class_offer['avail'], class_offer['prices'], \
							class_offer['is_authorized'], class_offer.get('clickthrough_url'), \
							class_offer.get('buynow_url'), class_offer.get('sendrfq_url'))
			json_attribs = (json_offer['sku'], json_offer['avail'], json_offer['prices'], \
							json_offer['is_authorized'], json_offer.get('clickthrough_url'), \
							json_offer.get('buynow_url'), json_offer.get('sendrfq_url'))
			if class_attribs != json_attribs:
				return False
			if not class_offer['supplier'].equals_json(json_offer['supplier']):
				return False
			return True
		
		def compare_specs(class_spec, json_spec):
			"""Compares two specs.
			
			@param class_spec: A spec from an OctopartPart instance.
			@param json_spec: A spec from a JSON Part resource.
			"""
			
			if not class_spec['attribute'].equals_json(json_spec['attribute']):
				return False
			if sorted(class_spec['values']) != sorted(json_spec['values']):
				return False
			return True
		
		if isinstance(resource, DictType) and resource.get('__class__') == 'Part': 
			if self.uid != resource.get('uid'):
				return False
			if self.mpn != resource.get('mpn'):
				return False
			if not self.manufacturer.equals_json(resource.get('manufacturer')):
				return False
			if self.detail_url != resource.get('detail_url'):
				return False
			if self.avg_price != resource.get('avg_price'):
				return False
			if self.avg_avail != resource.get('avg_avail'):
				return False
			if self.market_status != resource.get('market_status'):
				return False
			if self.num_suppliers != resource.get('num_suppliers'):
				return False
			if self.num_authsuppliers != resource.get('num_authsuppliers'):
				return False
			if self.short_description != resource.get('short_description', ''):
				return False
			if sorted(self.category_ids) != sorted(resource.get('category_ids', [])):
				return False
			if hide_images is False and sorted(self.images) != sorted(resource.get('images', [])):
				return False
			if hide_datasheets is False and sorted(self.datasheets) != sorted(resource.get('datasheets', [])):
				return False
			if hide_descriptions is False and sorted(self.descriptions) != sorted(resource.get('descriptions', [])):
				return False
			if self.hyperlinks != resource.get('hyperlinks', {}):
				return False
			if hide_offers is False:
				checked_offers = []
				if hide_unauthorized_offers:
					checked_offers = sorted(self.get_unauthorized_offers())
				else:
					checked_offers = sorted(self.offers)
				for offer in checked_offers:
					truth = [compare_offers(offer, other) for other in sorted(resource.get('offers', []))]
					if True not in truth:
						return False
			if not hide_specs:
				for spec in sorted(self.specs):
					truth = [compare_specs(spec, other) for other in sorted(resource.get('specs', []))]
					if True not in truth:
						return False
		else:
			return False
		return True
	
	def __eq__(self, p):
		if isinstance(p, OctopartPart):
			try:
				if self.uid != p.uid:
					return False
				if self.mpn != p.mpn:
					return False
				if self.manufacturer != p.manufacturer:
					return False
				if self.detail_url != p.detail_url:
					return False
				if self.avg_price != p.avg_price:
					return False
				if self.avg_avail != p.avg_avail:
					return False
				if self.market_status != p.market_status:
					return False
				if self.num_suppliers != p.num_suppliers:
					return False
				if self.num_authsuppliers != p.num_authsuppliers:
					return False
				if self.short_description != p.short_description:
					return False
				if self.category_ids != p.category_ids:
					return False
				if self.images != p.images:
					return False
				if self.datasheets != p.datasheets:
					return False
				if self.descriptions != p.descriptions:
					return False
				if self.hyperlinks != p.hyperlinks:
					return False
				if self.offers != p.offers:
					return False
				if self.specs != p.specs:
					return False
			except AttributeError:
				return False
		else:
			return False
		return True
	
	def __ne__(self, p):
		return not self.__eq__(p)
	
	def __hash__(self):
		return (hash(self.__class__), hash(self.uid), hash(self.mpn))
	
	def __str__(self):
		return ''.join(('Part ', str(self.uid), ': ', str(self.manufacturer), ' ', self.mpn))

class OctopartPartAttribute(object):
	TYPE_TEXT = 'text'
	TYPE_NUMBER = 'number'
	
	@classmethod
	def new_from_dict(cls, attribute_dict):
		new = cls(attribute_dict['fieldname'], attribute_dict['displayname'], attribute_dict['type'], attribute_dict.get('metadata', {}))
		return new
	
	def __init__(self, fieldname, displayname, attribute_type, metadata):
		self._fieldname = fieldname
		self.displayname = displayname
		self.type = attribute_type
		self.metadata = metadata
	
	@property
	def fieldname(self):
		return self._fieldname
	
	def equals_json(self, resource):
		"""Checks the object for data equivalence to a JSON PartAttribute resource."""
		
		if isinstance(resource, DictType) and resource.get('__class__') == 'PartAttribute': 
			if self.fieldname != resource.get('fieldname'):
				return False
			if self.displayname != resource.get('displayname'):
				return False
			if self.type != resource.get('type'):
				return False
			if self.metadata != resource.get('metadata', {}):
				return False
		else:
			return False
		return True
	
	def __eq__(self, pa):
		if isinstance(pa, OctopartPartAttribute):
			try:
				if self.fieldname != pa.fieldname:
					return False
				if self.displayname != pa.displayname:
					return False
				if self.type != pa.type:
					return False
				if self.metadata != pa.metadata:
					return False
			except AttributeError:
				return False
		else:
			return False
		return True
	
	def __ne__(self, pa):
		return not self.__eq__(pa)
	
	def __hash__(self):
		return (hash(self.__class__), hash(self.fieldname))
	
	def __str__(self):
		if self.type == 'number':
			return ''.join((self.displayname, 'attribute: ', self.metadata['datatype'], ' (', self.metadata['unit']['name'], ')'))
		elif self.type == 'text':
			return ''.join((self.displayname, 'attribute: ', self.type))
		else:	# Note: 'else' is not a valid state in the API resource definition
			return self.displayname

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
	
	def _validate_args(self, args, arg_types, arg_ranges):
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
				if arg_types[key] in (IntType, LongType, FloatType):
					if args[key] < arg_ranges[key][0] or args[key] > arg_ranges[key][1]:
						raise OctopartException(args, arg_types, arg_ranges, 4)
				elif len(args[key]) < arg_ranges[key][0] or len(args[key]) > arg_ranges[key][1]:
					if arg_types[key] is StringType:
						raise OctopartException(args, arg_types, arg_ranges, 5)
					elif arg_types[key] is ListType:
						raise OctopartException(args, arg_types, arg_ranges, 11)
		if len(args_set) != len(args.keys()):
			raise OctopartException(args, arg_types, arg_ranges, 3)
	
	def _make_url(self, method, args):
		"""Constructs the URL to pass to _get().
		
		@param method: String containing the method path, such as "parts/search".
		@param args: Dictionary of arguments to pass to the API method.
		@return: Complete request URL string.
		"""
		
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
				v = str(v).replace(' ', '+')
				v = urllib2.quote(v,'[]{}":+,') #replace all others, leave structure untouched
				arg_strings.append('='.join((arg, v)))
			
			req_url = '?'.join((req_url, '&'.join(arg_strings)))
				
		return req_url
	
	def _get(self, req_url):
		"""Makes a GET request with the given API method and arguments.
		
		@param req_url: Complete API request URL. 
		@return: JSON response from server.
		"""
		
		response = urllib2.urlopen(req_url).read()
		json_obj = json.loads(unicode(response))
		return json_obj
	
	def _translate_periods(self, args):
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
				args[key] = self._translate_periods(args[key])
			elif type(args[key]) is ListType:
				for a in args[key]:
					if type(a) is DictType:
						a = self._translate_periods(a)
						
			if key in translation:
				args[translation[key]] = args.pop(key)
			
		return args
	
	def _categories_get_args(self, id):
		"""Validate and format arguments passed to categories_get().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'id': (IntType, LongType)}
		arg_ranges = {}
		args = {'id' : id}
		self._validate_args(args, arg_types, arg_ranges)
		
		return args

	def categories_get(self, id):
		"""Fetch a category object by its id. 
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-An OctopartCategory object.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'categories/get'
		args = self._categories_get_args(id)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, OctopartCategory.new_from_dict(json_obj)
		else:
			return None
	
	def _categories_get_multi_args(self, ids):
		"""Validate and format arguments passed to categories_get_multi().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'ids': ListType}
		arg_ranges = {}
		args = {'ids' : ids}
		self._validate_args(args, arg_types, arg_ranges)
		for id in args['ids']:
			if type(id) not in (IntType, LongType):
				raise OctopartException(args, arg_types, arg_ranges, 2)
		
		return args
	
	def categories_get_multi(self, ids):
		"""Fetch multiple category objects by their ids. 
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of OctopartCategory objects.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'categories/get_multi'
		args = self._categories_get_multi_args(ids)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, [OctopartCategory.new_from_dict(category) for category in json_obj]
		else:
			return None
	
	def _categories_search_args(self, args):
		"""Validate and format arguments passed to categories_search().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'q': StringType, 'start' : IntType, 'limit' : IntType, 'ancestor_id' : IntType}
		arg_ranges = {}
		self._validate_args(args, arg_types, arg_ranges)
		
		return args	
	
	def categories_search(self, **kwargs):
		"""Execute search over all result objects. 
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of (OctopartCategory, highlight_text) pairs for each result.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'categories/search'
		args = self._categories_search_args(kwargs)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			results = [(OctopartCategory.new_from_dict(result['item']), result['highlight']) for result in json_obj['results']]
			return json_obj, results
		else:
			return None
	
	def _parts_get_args(self, uid, args):
		"""Validate and format arguments passed to parts_get().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'uid': (IntType, LongType), \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		args = self._translate_periods(args)
		args['uid'] = uid
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
	
	def parts_get(self, uid, **kwargs):
		"""Fetch a part object by its id.
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-An OctopartPart object.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'parts/get'
		args = self._parts_get_args(uid, kwargs)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, OctopartPart.new_from_dict(json_obj)
		else:
			return None
	
	def _parts_get_multi_args(self, uids, args):
		"""Validate and format arguments passed to parts_get_multi().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'uids': ListType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {'uids': (0, 100)}
		args = self._translate_periods(args)
		args['uids'] = uids
		for id in args['uids']:
			if type(id) not in (IntType, LongType):
				raise OctopartException(args, arg_types, arg_ranges, 2)
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
	
	def parts_get_multi(self, uids, **kwargs):
		"""Fetch multiple part objects by their ids.
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of OctopartPart objects.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'parts/get_multi'
		args = self._parts_get_multi_args(uids, kwargs)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, [OctopartPart.new_from_dict(part) for part in json_obj]
		else:
			return None
	
	def _parts_search_args(self, args):
		"""Validate and format arguments passed to parts_search().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
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
		
		args = self._translate_periods(args)
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
		
				
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
		
	
	def parts_search(self, **kwargs):
		"""Execute a search over all result objects.
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of (OctopartPart, highlight_text) pairs for each result.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'parts/search'
		args = self._parts_search_args(kwargs)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			results = [tuple((OctopartPart.new_from_dict(result['item']), result['highlight'])) for result in json_obj['results']]
			return json_obj, results
		else:
			return None
	
	def _parts_suggest_args(self, q, args):
		"""Validate and format arguments passed to parts_suggest().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'q': StringType, 'limit' : IntType}
		arg_ranges = {'q': (2, float("inf")), 'limit' : (0, 10)}
		args['q'] = q
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
		
	
	def parts_suggest(self, q, **kwargs):
		"""Suggest a part search query string.
		
		Optimized for speed (useful for auto-complete features).
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of manufacturer part number strings.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'parts/suggest'
		args = self._parts_suggest_args(q, kwargs)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, json_obj['results']
		else:
			return None
	
	def _parts_match_args(self, manufacturer_name, mpn):
		"""Validate and format arguments passed to parts_match().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'manufacturer_name': StringType, 'mpn' : StringType}
		arg_ranges = {}
		args = {'manufacturer_name': manufacturer_name, 'mpn' : mpn}
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
	
	def parts_match(self, manufacturer_name, mpn):
		"""Match (manufacturer name, mpn) to part uid. 
		
		@return: a list of (part uid, manufacturer displayname, mpn) tuples.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'parts/match'
		args = self._parts_match_args(manufacturer_name, mpn)
		try:
			json_obj = self._get(self._make_url(method, args))
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
	
	def _partattributes_get_args(self, fieldname):
		"""Validate and format arguments passed to partattributes_get().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'fieldname': StringType}
		arg_ranges = {}
		args = {'fieldname': fieldname}
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
	
	def partattributes_get(self, fieldname):
		"""Fetch a PartAttribute object by its fieldname.
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-An OctopartPartAttribute object.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'partattributes/get'
		args = self._partattributes_get_args(fieldname)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				return None
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, OctopartPartAttribute.new_from_dict(json_obj)
		else:
			return None
	
	def _partattributes_get_multi_args(self, fieldnames):
		"""Validate and format arguments passed to partattributes_get_multi().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'fieldnames': ListType}
		arg_ranges = {}
		args = {'fieldnames': fieldnames}
		for name in args['fieldnames']:
			if isinstance(name, basestring) is False:
				raise OctopartException(args, arg_types, arg_ranges, 2)
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
	
	def partattributes_get_multi(self, fieldnames):
		"""Fetch multiple PartAttribute objects by their fieldnames.
		
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of OctopartPartAttribute objects.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'partattributes/get_multi'
		args = self._partattributes_get_multi_args(fieldnames)
		try:
			json_obj = self._get(self._make_url(method, args))
		except urllib2.HTTPError as e:
			if e.code == 404:
				raise OctopartException(args, arg_types, arg_ranges, 7)
			elif e.code == 503:
				raise OctopartException(args, arg_types, arg_ranges, 8)
			else:
				raise e
		if json_obj:
			return json_obj, [OctopartPartAttribute.new_from_dict(attrib) for attrib in json_obj]
		else:
			return None
	
	def _bom_match_args(self, lines, args):
		"""Validate and format arguments passed to bom_match().
		
		@return: Dictionary of valid arguments to pass to _make_url().
		@raise OctopartException: Raised if invalid argument syntax is passed in.
		"""
		
		arg_types = {'lines': ListType, \
					'optimize.return_stubs' : BooleanType, \
					'optimize.hide_datasheets' : BooleanType, \
					'optimize.hide_descriptions' : BooleanType, \
					'optimize.hide_images' : BooleanType, \
					'optimize.hide_hide_offers' : BooleanType, \
					'optimize.hide_hide_unauthorized_offers' : BooleanType, \
					'optimize.hide_specs' : BooleanType}
		arg_ranges = {}
		args = self._translate_periods(args)
		args['lines'] = lines
		# DictType arguments need to be validated just like the normal args dict
		lines_required_args = frozenset()
		lines_arg_types = {'q': StringType, \
					'mpn' : StringType, \
					'manufacturer' : StringType, \
					'sku' : StringType, \
					'supplier' : StringType, \
					'mpn_or_sku' : StringType, \
					'start' : IntType, \
					'limit' : IntType, \
					'reference' : StringType}
		lines_arg_ranges = {'limit' : (0, 20)}
		for line in lines:
			self._validate_args(line, lines_arg_types, lines_arg_ranges)
			# Method-specific checks not covered by validate_args:
			if lines_required_args.issubset(set(line.keys())) is False:
				raise OctopartException(line, lines_arg_types, lines_arg_ranges, 0)
			if (line.get('start', 0) + line.get('match', 0)) > 100:
				raise OctopartException(line, lines_arg_types, lines_arg_ranges, 6)

		# Now check the primary args dict as normal
		self._validate_args(args, arg_types, arg_ranges)
		
		return args
	
	def bom_match(self, lines, **kwargs):
		"""Match a list of part numbers to Octopart part objects.
		 
		@return: A pair containing:
			-The raw JSON result dictionary. 
			-A list of dicts containing:
				-A list of OctopartParts.
				-A reference string.
				-A status string.
				-Optionally, the number of search hits.
		If no JSON object is found without an Exception being raised, returns None.
		"""
		
		method = 'bom/match'
		args = self._bom_match_args(lines, kwargs)
		try:
			json_obj = self._get(self._make_url(method, args))
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
				items = [OctopartPart.new_from_dict(item) for item in result['items']]
				new_result = {'items' : items, 'reference' : result.get('reference', ''), 'status' : result['status']}
				if result.get('hits') is not None:
					new_result['hits'] = result.get('hits')
				results.append(new_result)
		
			return json_obj, results
		else:
			return None

