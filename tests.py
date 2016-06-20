import unittest
import urllib, urllib2
import requests
import json

baseurl = "http://localhost:8080"

def getStatusCode(url):
	response = urllib.urlopen(baseurl + url)
	return response.getcode()

def getResponseMessage(url):
	response = urllib.urlopen(baseurl + url)
	return response.read()

def post(url, queryargs):
	#Example queryargs: { 'hello': 'no', 'foo': 'bar'}
	res = requests.post(baseurl + url, data=json.dumps(queryargs))
	return res.text

class CassoTesting(unittest.TestCase):

	def testHelloWorld_statuscode(self):
		self.assertEqual(getStatusCode('/'), 200)

	def testHelloWorld_message(self):
		self.assertEqual(getResponseMessage('/'), "Hello again!")


	def testRegisterWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/api/v1.0/registerUser', query))

	def testRegisterNoEmail(self):
		query = {"test":"test"}
		self.assertIn("Email address missing", post('/api/v1.0/registerUser', query))

	def testRegisterNoApiKey(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com"}
		self.assertIn("Api key missing", post('/api/v1.0/registerUser', query))

	def testRegisterNoPhoneNumber(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","apikey":"000"}
		self.assertIn("Phone number missing", post('/api/v1.0/registerUser', query))

	def testRegisterIncorrectWebsiteID(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","apikey":"000","ipaddress":"random"}
		self.assertIn("Incorrect API Key", post('/api/v1.0/registerUser', query))

	def testRegisterUserAlreadyExists1(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"3","apikey":"1421512","ipaddress":"random"}
		self.assertIn("User already with that email or phone number already exists", post('/api/v1.0/registerUser', query))

	def testRegisterUserAlreadyExists2(self):
		query = {"emailaddress":"arpad","phonenumber":"10991112222","apikey":"1421512","ipaddress":"random"}
		self.assertIn("User already with that email or phone number already exists", post('/api/v1.0/registerUser', query))

	def testRegisterUserAlreadyExists3(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","apikey":"1421512","ipaddress":"random"}
		self.assertIn("User already with that email or phone number already exists", post('/api/v1.0/registerUser', query))

	def testRegisterUserCreationWithUsername(self):
		query = {"username":"testuser2","emailaddress":"koolmammal5@gmail.com","phonenumber":"10239108940","apikey":"1421512","ipaddress":"random"}
		self.assertIn("success", post('/api/v1.0/registerUser', query))

	def testRegisterUserCreationWithoutUsername(self):
		query = {"emailaddress":"koolmamma@gmail.com","phonenumber":"102108940","apikey":"1421512","ipaddress":"random"}
		self.assertIn("success", post('/api/v1.0/registerUser', query))


	def testRemoveUserWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/api/v1.0/removeUser', query))

	def testRemoveUserNoEmailAddress(self):
		query = {"test":"test"}
		self.assertIn("Email address missing", post('/api/v1.0/removeUser', query))

	def testRemoveUserNoApiKey(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com"}
		self.assertIn("Api key missing", post('/api/v1.0/removeUser', query))

	def testRemoveUserNoPhoneNumber(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","apikey":"000"}
		self.assertIn("Phone number missing", post('/api/v1.0/removeUser', query))

	def testRemoveUserIncorrectWebsiteID(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","apikey":"000"}
		self.assertIn("Incorrect API Key", post('/api/v1.0/removeUser', query))

	def testRemoveUserDoesNotExistError1(self):
		query = {"emailaddress":"randomemail", "phonenumber":"10991112222","apikey":"1421512"}
		self.assertIn("User that you are trying to delete does not exist", post('/api/v1.0/removeUser', query))

	def testRemoveUserDoesNotExistError2(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com", "phonenumber":"125125125151517676","apikey":"1421512"}
		self.assertIn("User that you are trying to delete does not exist", post('/api/v1.0/removeUser', query))

	def testRemoveUser1(self):
		query = {"emailaddress":"koolmammal5@gmail.com", "phonenumber":"10239108940","apikey":"1421512"}
		self.assertIn("success", post('/api/v1.0/removeUser', query))

	def testRemoveUser2(self):
		query = {"emailaddress":"koolmamma@gmail.com", "phonenumber":"102108940","apikey":"1421512"}
		self.assertIn("success", post('/api/v1.0/removeUser', query))

	def testAuthenticateUserWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateNoApiKey(self):
		query = {"test":"test"}
		self.assertIn("Api key missing", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateNoApiKey(self):
		query = {"test":"test"}
		self.assertIn("Api key missing", post('/api/v1.0/authenticateUser', query))

if __name__ == '__main__':
	unittest.main()