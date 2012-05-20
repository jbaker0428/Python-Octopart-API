
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
		''' Fetch a category object by its id. '''
		method = 'categories/get'
		required_args = frozenset('id',)
		arg_types = {'id': StringType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_get.__name__, args, e.error_number)
		
		return self.__get(method, args)
	
	def categories_get_multi(self, args):
		''' Fetch multiple category objects by their ids. '''
		method = 'categories/get_multi'
		required_args = frozenset('ids',)
		arg_types = {'ids': ListType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_get_muti.__name__, args, e.error_number)
		
		return self.__get(method, args)
	
	def categories_search(self, args):
		''' Execute search over all category objects. '''
		method = 'categories/search'
		required_args = frozenset()
		arg_types = {'q': StringType, 'start' : IntType, 'limit' : IntType, 'ancestor_id' : IntType}
		arg_ranges = {}
		
		try:
			Octopart.validate_args(args, required_args, arg_types, arg_ranges)
		except OctopartException as e:
			raise OctopartException(self.categories_search.__name__, args, e.error_number)
		
		return self.__get(method, args)
	
	def parts_get(self, args):
		''' Fetch a part object by its id. '''
		method = 'parts/get'
		required_args = frozenset('uid',)
		arg_types = {'uid': StringType, \
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
		
		return self.__get(method, args)
	
	def parts_get_multi(self, args):
		''' Fetch multiple part objects by their ids. '''
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
		
		return self.__get(method, args)

