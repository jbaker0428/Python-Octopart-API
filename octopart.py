
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

class OctopartException(Exception):
	errors = {0: 'Required argument missing from method call.', \
			  1: 'Passed an invalid argument for this method.', \
			  2: 'Malformed argument.', \
			  3: 'An argument was passed more than once.', \
			  4: 'Argument value out of valid range.'}
	def __init__(self, source, args, error_number):
		self.source = source
		self.arguments = args
		self.error = error_number
		
	def __str__(self):
		str = errors[self.error] + ' Source: ' + self.source + ' Passed arguments: ' + self.arguments
		return repr(str)

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
	@staticmethod
	def new_from_dict(part_dict):
		# Convert everything to class instances
		part_dict['manufacturer'] = OctopartBrand.new_from_dict(part_dict['manufacturer'])
		for offer in part_dict['offers']:
			offer['supplier'] = OctopartBrand.new_from_dict(offer['supplier'])
		for spec in part_dict['specs']:
			spec['attribute'] = OctopartPartAttribute.new_from_dict(spec['attribute'])
		
		new = OctopartPart(part_dict['uid'], part_dict['mpn'], part_dict['manufacturer'], \
						part_dict['detail_url'], part_dict['avg_price'], part_dict['avg_avail'], \
						part_dict['market_status'], part_dict['num_suppliers'], \
						part_dict['num_authsupplier'], part_dict['short_description'], \
						part_dict['category_ids'], part_dict['images'], part_dict['datasheets'], part_dict['descriptions'], part_dict['hyperlinks'], part_dict['offers'], part_dict['specs'])
		return new
	
	def __init__(self, uid, mpn, manufacturer, detail_url, avg_price, avg_avail, \
				market_status, num_suppliers, num_authsuppliers, short_description, \
				category_ids, images, datasheets, descriptions, hyperlinks, offers, specs):
		self.uid = uid
		self.mpn = mpn
		self.manufacturer = manufacturer
		self.detail_url = detail_url
		self.avg_price = avg_price
		self.avg_avail = avg_avail
		self.market_status = market_status
		self.num_suppliers = num_suppliers
		self.num_authsuppliers = num_authsuppliers
		self.short_description = short_description
		self.category_ids = category_ids
		self.images = images
		self.datasheets = datasheets
		self.descriptions = descriptions
		self.hyperlinks = hyperlinks
		self.offers = offers
		self.specs = specs

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
		@param arg_ranges: Dictionary which contains range() calls for any numeric arguments with a limited range
		@raise OctopartException: If any syntax errors are found.'''
		valid_args = frozenset(arg_types.keys())
		args_set = set(args.keys())
		
		if required_args.issubset(args_set) is False:
			raise OctopartException(Octopart.validate_args.__name__, args, 0)
		if args_set.issuperset(valid_args):
			raise OctopartException(Octopart.validate_args.__name__, args, 1)
		for key in args_set:
			if arg_types[key] is StringType:
				if isinstance(args[key], basestring) is False:
					raise OctopartException(Octopart.validate_args.__name__, args, 2)
			else:
				if type(args[key]) is not arg_types[key]:
					raise OctopartException(Octopart.validate_args.__name__, args, 2)
			if key in arg_ranges.keys():
				if args[key] not in arg_ranges[key]:
					raise OctopartException(Octopart.validate_args.__name__, args, 4)
		if len(args_set) != len(args.keys()):
			raise OctopartException(Octopart.validate_args.__name__, args, 3)
	
	def __init__(self, api_key=None):
		self.api_key = api_key
	
	def __get(self, method, args):
		''' Makes a GET request with the given method and arguments. 
		@param method: String containing the method path, such as "parts/search" 
		@param args: Dictionary of arguments to pass to the API method 
		@return: JSON response from server'''
		
		# Construct the request URL
		req_url = Octopart.api_url + method
		if self.api_key is not None:
			args['apikey'] = self.api_key
		if len(args) > 0:
			first_arg = True
			for arg, val in args.items():
				if type(val) is BooleanType:
					v = int(val)
				elif type(val) is ListType:
					v = json.dumps(val, separators=(',',':'))
				else:
					v = val
				if first_arg is True:
					first_arg = False
					req_url = req_url + '?' + arg + '=' + v
				else:
					req_url = req_url + '&' + arg + '=' + v
		
		response = urllib2.urlopen(req_url).read() 
		json_obj = json.loads(response)
		return json_obj

	def categories_get(self, args):
		''' Fetch a category object by its id. 
		@return: An OctopartCategory object. '''
		method = 'categories/get'
		required_args = frozenset('id',)
		arg_types = {'id': IntType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_get.__name__, args, e.error_number)
		
		json_obj = self.__get(method, args)
		return OctopartCategory.new_from_dict(json_obj)
	
	def categories_get_multi(self, args):
		''' Fetch multiple category objects by their ids. 
		@return: A list of OctopartCategory objects. '''
		method = 'categories/get_multi'
		required_args = frozenset('ids',)
		arg_types = {'ids': ListType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_get_muti.__name__, args, e.error_number)
		
		json_obj = self.__get(method, args)
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
			raise OctopartException(self.categories_search.__name__, args, e.error_number)
		
		json_obj = self.__get(method, args)
		categories = []
		for result in json_obj['results']:
			new_category = OctopartCategory.new_from_dict(result['item'])
			categories.append([new_category, result['highlight']])
		return categories
	
	def parts_get(self, args):
		''' Fetch a part object by its id. 
		@return: An OctopartPart object. '''
		method = 'parts/get'
		required_args = frozenset('uid',)
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
			raise OctopartException(self.parts_get.__name__, args, e.error_number)
		
		json_obj = self.__get(method, args)
		return OctopartPart.new_from_dict(json_obj)
	
	def parts_get_multi(self, args):
		''' Fetch multiple part objects by their ids. 
		@return: A list of OctopartPart objects. '''
		method = 'parts/get_multi'
		required_args = frozenset('uids',)
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
			raise OctopartException(self.parts_get_multi.__name__, args, e.error_number)
		
		json_obj = self.__get(method, args)
		parts = []
		for part in json_obj:
			parts.append(OctopartPart.new_from_dict(part))
		return parts
	
	def parts_search(self, args):
		''' Execute a search over all result objects. 
		@return: A list of [OctopartPart, highlight_text] pairs. '''
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
		arg_ranges = {'start' : range(1000), \
					'limit' : range(100), \
					'drilldown.facets.start' : range(1000), \
					'drilldown.facets.limit' : range(100)}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.parts_search.__name__, args, e.error_number)
		
		json_obj = self.__get(method, args)
		parts = []
		for result in json_obj['results']:
			new_part = OctopartPart.new_from_dict(result['item'])
			parts.append([new_part, result['highlight']])
		return parts

