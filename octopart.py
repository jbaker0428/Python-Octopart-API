import urllib2
import json
import types

class Octopart:
	''' A simple client frontend to tho Octopart public REST API. '''
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

