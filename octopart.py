import httplib
import json

class Octopart:
	''' A simple client frontend to tho Octopart public REST API. '''
	api_url = 'http://octopart.com/api/v2/'
	
	def __init__(self, api_key=None):
		self.api_key = api_key