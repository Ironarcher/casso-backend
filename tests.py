import unittest
import urllib, urllib2
import requests
import json

baseurl = "https://casso-1339.appspot.com"
#baseurl = "http://localhost:8080"

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


	def testRegisterUserWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/api/v1.0/registerUser', query))

	def testRegisterUserNoEmail(self):
		query = {"test":"test"}
		self.assertIn("Email address missing", post('/api/v1.0/registerUser', query))

	def testRegisterUserNoApiKey(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com"}
		self.assertIn("Api key missing", post('/api/v1.0/registerUser', query))

	def testRegisterUserNoPhoneNumber(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","apikey":"000"}
		self.assertIn("Phone number missing", post('/api/v1.0/registerUser', query))

	def testRegisterUserNoPhoneID(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","apikey":"000", "phonenumber":"000"}
		self.assertIn("Phone ID missing", post('/api/v1.0/registerUser', query))

	def testRegisterUserIncorrectWebsiteID(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","apikey":"000","phone-id":"Arpad's stupid phone"}
		self.assertIn("Incorrect API Key", post('/api/v1.0/registerUser', query))

	def testRegisterUserAlreadyExists1(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"3","apikey":"1421512","phone-id":"Arpad's stupid phone"}
		self.assertIn("User already with that email or phone number already exists", post('/api/v1.0/registerUser', query))

	def testRegisterUserAlreadyExists2(self):
		query = {"emailaddress":"arpad","phonenumber":"10991112222","apikey":"1421512","phone-id":"Arpad's stupid phone"}
		self.assertIn("User already with that email or phone number already exists", post('/api/v1.0/registerUser', query))

	def testRegisterUserAlreadyExists3(self):
		query = {"emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","apikey":"1421512","phone-id":"Arpad's stupid phone"}
		self.assertIn("User already with that email or phone number already exists", post('/api/v1.0/registerUser', query))

	def testRegisterUserCreationWithUsername(self):
		query = {"username":"testuser2","emailaddress":"koolmammal5@gmail.com","phonenumber":"10239108940","apikey":"1421512","phone-id":"testphoneid"}
		self.assertIn("success", post('/api/v1.0/registerUser', query))

	def testRegisterUserCreationWithoutUsername(self):
		query = {"emailaddress":"koolmamma@gmail.com","phonenumber":"102108940","apikey":"1421512","phone-id":"testphoneid"}
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

	def testAuthenticateUserNoApiKey(self):
		query = {"test":"test"}
		self.assertIn("Api key missing", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserNoIPAddress(self):
		query = {"apikey":"0000"}
		self.assertIn("IP address of client missing", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserIncorrectApiKey(self):
		query = {"apikey":"0000","ipaddress":"158.123.131.1"}
		self.assertIn("Incorrect API Key", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserNoEmailAddressOrUsername(self):
		query = {"apikey":"1421512","ipaddress":"158.123.131.1"}
		self.assertIn("No username or email address provided to authenticate", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserIncorrectEmailAddress(self):
		query = {"apikey":"1421512","ipaddress":"158.123.131.1","emailaddress":"nonexistantemail@nothing.com"}
		self.assertIn("Incorrect Email address (does not exist in database)", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserIncorrectEmailAddressWithWebsite(self):
		query = {"apikey":"121512","ipaddress":"158.123.131.1","emailaddress":"arpad.kovesdy@gmail.com"}
		self.assertIn("Incorrect Email address (does not exist in database)", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserIncorrectEmailAddress(self):
		query = {"apikey":"121512","ipaddress":"158.123.131.1","emailaddress":"arpad.kovesdy@gmail.com"}
		self.assertIn("Incorrect Email address (does not exist in database)", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUserIncorrectUsername(self):
		query = {"apikey":"1421512","ipaddress":"158.123.131.1","username":"nonexistantusername"}
		self.assertIn("Incorrect Username (does not exist in database)", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUser(self):
		query = {"apikey":"1421512","ipaddress":"000.000.000.0","emailaddress":"arpad.kovesdy@gmail.com"}
		self.assertIn("success", post('/api/v1.0/authenticateUser', query))

	def testAuthenticateUser2(self):
		query = {"apikey":"1421512","ipaddress":"000.000.000.0","username":"akovesdy"}
		self.assertIn("Already authenticating another account", post('/api/v1.0/authenticateUser', query))


	#Mobile functions

	def testRegisterDeviceWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceMissingPhoneID(self):
		query = {"test":"test"}
		self.assertIn("Phone ID missing", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceMissingEmailAddress(self):
		query = {"phone-id":"0"}
		self.assertIn("Email Address missing", post('/app/v1.0/registerDevice', query))

	def testRegisterDevicePhoneNumberMissing(self):
		query = {"phone-id":"0", "emailaddress":"testemail@email.com"}
		self.assertIn("Phone number missing", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceSecurityQuestions1(self):
		query = {"phone-id":"0", "emailaddress":"testemail@email.com", "phonenumber":"000"}
		self.assertIn("Security questions incomplete or missing", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceSecurityQuestions2(self):
		query = {"phone-id":"0", "emailaddress":"testemail@email.com","phonenumber":"000","secq1":"Mother's maiden name?"}
		self.assertIn("Security questions incomplete or missing", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceUserIdIncorrect(self):
		query = {"phone-id":"0", "emailaddress":"testemail@email.com","phonenumber":"000","secq1":"Mother's maiden name?",
		"secq2":"1","secq3":"2","secq4":"3","seca1":"1","seca2":"2","seca3":"3","seca4":"4,"}
		self.assertIn("Incorrect secret phone number or email address", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceCompletely(self):
		query = {"phone-id":"Arpad's nonexistant iphone", "emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","secq1":"Mother's maiden name?",
		"secq2":"1","secq3":"2","secq4":"3","seca1":"1","seca2":"2","seca3":"3","seca4":"4,"}
		self.assertIn("success", post('/app/v1.0/registerDevice', query))

	def testRegisterDeviceCompletely2(self):
		query = {"phone-id":"Arpad's nonexistant iphone", "emailaddress":"arpad.kovesdy@gmail.com","phonenumber":"10991112222","secq1":"Mother's maiden name?",
		"secq2":"1","secq3":"2","secq4":"3","seca1":"1","seca2":"2","seca3":"3","seca4":"4,"}
		self.assertIn("1", post('/app/v1.0/registerDevice', query))


	def testCheckAuthReqUserDoesNotExist(self):
		self.assertIn("User ID does not exist", getResponseMessage('/app/v1.0/checkAuth/909090'))

	def testCheckAuthReqCompletely(self):
		self.assertIn("0", getResponseMessage('/app/v1.0/checkAuth/1'))


	def testAuthenticatePhoneWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneMissingPhoneNumber(self):
		query = {"test":"test"}
		self.assertIn("Phone number missing", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneMissingSecretPhoneKey(self):
		query = {"phonenumber":"000"}
		self.assertIn("Secret phone key missing", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneMissingUserID(self):
		query = {"phonenumber":"000", "secretphonekey":"ghfhfh"}
		self.assertIn("User ID missing", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneMissingPhoneID(self):
		query = {"phonenumber":"000", "secretphonekey":"ghfhfh", "user_id":"Arpad's fake iphone"}
		self.assertIn("Phone ID missing", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneWrongPhoneID(self):
		query = {"phonenumber":"000", "secretphonekey":"s2BH3C7thmSX9j0K6ag6eqqqJhUTB9gOgu62QfZf", "user_id":"0",
		"phone-id":"Wrong phoneid"}
		self.assertIn("Incorrect device information provided", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneWrongSecretKey(self):
		query = {"phonenumber":"000", "secretphonekey":"aaa", "user_id":"0",
		"phone-id":"Arpad's nonexistant iphone"}
		self.assertIn("Incorrect device information provided", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneWrongPhoneNumber(self):
		query = {"phonenumber":"000", "secretphonekey":"s2BH3C7thmSX9j0K6ag6eqqqJhUTB9gOgu62QfZf", "user_id":"0",
		"phone-id":"Arpad's nonexistant iphone"}
		self.assertIn("Incorrect phone number provided", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneWrongUserID(self):
		query = {"phonenumber":"10991112222", "secretphonekey":"s2BH3C7thmSX9j0K6ag6eqqqJhUTB9gOgu62QfZf", "user_id":"0",
		"phone-id":"Arpad's nonexistant iphone"}
		self.assertIn("Not allowed for authentication", post('/app/v1.0/authenticate', query))

	def testAuthenticatePhoneCompletely(self):
		query = {"phonenumber":"10991112222", "secretphonekey":"s2BH3C7thmSX9j0K6ag6eqqqJhUTB9gOgu62QfZf", "user_id":"1",
		"phone-id":"Arpad's nonexistant iphone"}
		self.assertIn("success", post('/app/v1.0/authenticate', query))


	def testDeactivatePhoneWrongFormat(self):
		query = {}
		self.assertIn("Request in the wrong format", post('/app/v1.0/deactivate', query))

	def testDeactivatePhoneMissingSecretPhoneKey(self):
		query = {"test":"test"}
		self.assertIn("Secret phone key missing", post('/app/v1.0/deactivate', query))

	def testDeactivatePhoneMissingUserID(self):
		query = {"secretphonekey":"ZjvFevrw9g1XhEeT5uQmoeWe1AItxMwbGj6e0OOH"}
		self.assertIn("User ID missing", post('/app/v1.0/deactivate', query))

	def testDeactivatePhoneMissingPhoneID(self):
		query = {"secretphonekey":"ZjvFevrw9g1XhEeT5uQmoeWe1AItxMwbGj6e0OOH", "user_id":"1"}
		self.assertIn("Phone ID missing", post('/app/v1.0/deactivate', query))

	def testDeactivatePhoneCompletely(self):
		query = {"secretphonekey":"ZjvFevrw9g1XhEeT5uQmoeWe1AItxMwbGj6e0OOH", "user_id":"1", "phone-id":"Arpad's nonexistant iphone"}
		self.assertIn("success", post('/app/v1.0/deactivate', query))


	def testCheckIfDeviceAuthDoneFromWebsite_useriddoesnotexist(self):
		self.assertIn("User does not exist", getResponseMessage('/api/v1.0/checkIfDeviceAuthed/909090'))

	def ZtestCheckIfDeviceAuthDoneFromWebsite(self):
		self.assertIn("success", getResponseMessage('/api/v1.0/checkIfDeviceAuthed/1'))


if __name__ == '__main__':
	unittest.main()