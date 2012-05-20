import urllib2
import json
from types import *

class OctopartException(Exception):
	errors = {0: 'Required argument missing from method call.', \
			  1: 'Passed an invalid argument for this method.', \
			  2: 'Malformed argument.', \
			  3: 'An argument was passed more than once.'}
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
				if first_arg is True:
					first_arg = False
					req_url = req_url + '?' + arg + '=' + val
				else:
					req_url = req_url + '&' + arg + '=' + val
		
		response = urllib2.urlopen(req_url).read() 
		json_obj = json.loads(response)
		return json_obj
	
	# TODO: JSON list arguments will be passed as a python list, need to convert to string?
	#if type(arg val) in arg_types[arg]
	def categories_get(self, args):
		''' Fetch a category object by its id. '''
		method = 'categories/get'
		required_args = frozenset('id',)
		arg_types = {'id': StringType}
		valid_args = frozenset(arg_types.keys())
		args_set = set(args.keys())
		
		if required_args.issubset(args_set) is False:
			raise OctopartException(self.categories_get.__name__, args, 0)
		if args_set.issuperset(valid_args):
			raise OctopartException(self.categories_get.__name__, args, 1)
		for key in args_set:
			if arg_types[key] is StringType:
				if isinstance(args[key], basestring) is False:
					raise OctopartException(self.categories_get.__name__, args, 2)
			else:
				if type(args[key]) is not arg_types[key]:
					raise OctopartException(self.categories_get.__name__, args, 2)
		if len(args_set) != len(args.keys()):
			raise OctopartException(self.categories_get.__name__, args, 3)
		
		return self.__get(method, args)
	
	def categories_get_multi(self, args):
		''' Fetch multiple category objects by their ids. '''
		method = 'categories/get_multi'
		required_args = frozenset('ids',)
		arg_types = {'ids': ListType}
		valid_args = frozenset(arg_types.keys())
		args_set = set(args.keys())
		
		if required_args.issubset(args_set) is False:
			raise OctopartException(self.categories_get_multi.__name__, args, 0)
		if args_set.issuperset(valid_args):
			raise OctopartException(self.categories_get_multi.__name__, args, 1)
		for key in args_set:
			if arg_types[key] is StringType:
				if isinstance(args[key], basestring) is False:
					raise OctopartException(self.categories_get_multi.__name__, args, 2)
			else:
				if type(args[key]) is not arg_types[key]:
					raise OctopartException(self.categories_get_multi.__name__, args, 2)
		if len(args_set) != len(args.keys()):
			raise OctopartException(self.categories_get_multi.__name__, args, 3)
		
		return self.__get(method, args)
	
	def categories_search(self, args):
		''' Execute search over all category objects. '''
		method = 'categories/search'
		required_args = frozenset()
		arg_types = {'q': StringType, 'start' : IntType, 'limit' : IntType, 'ancestor_id' : IntType}
		valid_args = frozenset(arg_types.keys())
		args_set = set(args.keys())
		
		if required_args.issubset(args_set) is False:
			raise OctopartException(self.categories_search.__name__, args, 0)
		if args_set.issuperset(valid_args):
			raise OctopartException(self.categories_search.__name__, args, 1)
		for key in args_set:
			if arg_types[key] is StringType:
				if isinstance(args[key], basestring) is False:
					raise OctopartException(self.categories_search.__name__, args, 2)
			else:
				if type(args[key]) is not arg_types[key]:
					raise OctopartException(self.categories_search.__name__, args, 2)
		if len(args_set) != len(args.keys()):
			raise OctopartException(self.categories_search.__name__, args, 3)
		
		return self.__get(method, args)

