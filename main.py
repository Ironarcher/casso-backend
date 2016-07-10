import os
import random
import MySQLdb
import datetime
import time
import json
#import requests
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# Import the Flask Framework
from flask import Flask, jsonify, request, abort, render_template
app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

def getDB():
	if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
		db = MySQLdb.connect(
			unix_socket='/cloudsql/{}'.format(
				os.environ['CLOUDSQL_INSTANCE']),
				user=os.environ['CLOUDSQL_USERNAME'],
				passwd=os.environ['CLOUDSQL_PASSWORD'],
				db=os.environ['CLOUDSQL_DATABASE'])
	else:
		#REMOVE FOR DEPLOYMENT
		db = MySQLdb.connect("104.154.38.165", "root", os.environ['CLOUDSQL_PASSWORD'], "casso1")
	return db

db = getDB()
db.ping(True)

#Website handling functions
#Start here

@app.route('/')
def homePage():
	"""updated to return a homepage html"""
	return render_template('main.html')

@app.route('/api/v1.0/registerWebsite', methods=['POST'])
def webRegisterWebsite():
	#Arguments are website url
	#Must be done manually currently
	if not request.json or not 'emailaddress' in request.get_json(force=True, silent=True):
		abort(400, 'ohno')
	return jsonify({'status' : 'success'})

@app.route('/api/v1.0/registerUser', methods=['POST'])
def webRegisterUser():
	#Arguments are optional username, email address, api key, phone number, ip address, phone-id
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	req = request.get_json(force=True)
	if not 'emailaddress' in req:
		abort(400, "Email address missing")
	if not 'apikey' in req:
		abort(400, "Api key missing")
	if not 'phonenumber' in req:
		abort(400, "Phone number missing")
	if not 'phone-id' in req:
		abort(400, "Phone ID missing")

	#Get the website's id or reject if incorrect
	websiteID = getWebsiteID(req['apikey'])
	if websiteID is None:
		abort(400, "Incorrect API Key")

    #Verify that the emailaddress does not exist again on that website
	if checkUserExists(req['emailaddress'], req['phonenumber'], websiteID) is True:
		abort(400, "User already with that email or phone number already exists")

	#Create a new user entry
	cursor = db.cursor()
	if 'username' in req:
		sql = "INSERT INTO users (username, emailaddress, phonenumber, website_id) VALUES (%s,%s,%s,%s)"
		cursor.execute(sql, (req['username'], req['emailaddress'], req['phonenumber'], websiteID))
		db.commit()
	else:
		sql = "INSERT INTO users (emailaddress, phonenumber, website_id) VALUES (%s,%s,%s)"
		cursor.execute(sql, (req['emailaddress'], req['phonenumber'], websiteID))
		db.commit()

	sql = "UPDATE users SET phone_id=%s WHERE emailaddress=%s"
	cursor.execute(sql, (req['phone-id'], req['emailaddress']))
	db.commit()
	cursor.close()

	return jsonify({'status' : 'success'})

def getWebsiteID(apikey):
	try:
		cursor = db.cursor()
		sql = 'SELECT pid from websites WHERE secretkey=%s'
		cursor.execute(sql, (apikey,))
		if cursor.rowcount > 0:
			result = cursor.fetchone()
			cursor.close()
			return int(result[0])
		else:
			cursor.close()
			return None
	except:
		print("get website id error")
		abort(400, "get website id error")

def checkUserExists(emailaddress, phonenumber, websiteid):
	try:
		cursor = db.cursor()
		sql1 = "SELECT pid from users WHERE emailaddress=%s AND website_id=%s"
		cursor.execute(sql1, (emailaddress, websiteid))
		if cursor.rowcount > 0:
			cursor.close()
			return True
		else:
			sql2 = "SELECT pid from users WHERE website_id=%s AND phonenumber=%s"
			cursor.execute(sql2, (websiteid, phonenumber))
			if cursor.rowcount  > 0:
				cursor.close()
				return True
			else:
				cursor.close()
				return False
	except:
		print("check user error")
		abort(400, "check user error")

def randKey(digits):
	return ''.join(random.choice(
		'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(digits))

@app.route('/api/v1.0/authenticateUser', methods=['POST'])
def func_webAuthenticateUser():
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	response = webAuthenticateUser(request.get_json(force=True))
	if response['status'] == "failure":
		abort(response['code'], response['report'])
	elif response['status'] == "success":
		return jsonify(response)

def webAuthenticateUser(req):
	#Arguments are optional either username or email, apikey, ipaddress of request to authenticate
	if 'apikey' not in req:
		data = {
			"status":"failure",
			"report":"Api key missing",
			"code":400
		}
		return data
	if 'ipaddress' not in req:
		data = {
			"status":"failure",
			"report":"IP address of client missing",
			"code":400
		}
		return data

	#Check the website's secret key
	websiteID = getWebsiteID(req['apikey'])
	if websiteID is None:
		data = {
			"status":"failure",
			"report":"Incorrect API Key",
			"code":400
		}
		return data

	#Verify username/email and mark user down for authentication (update timestamp)
	cursor = db.cursor()
	user_id = 0
	if 'emailaddress' in req:
		sql = "SELECT pid from users WHERE emailaddress=%s AND website_id=%s"
		cursor.execute(sql, (req['emailaddress'], websiteID))
		if cursor.rowcount > 0:
			user_id = int(cursor.fetchone()[0])
		else:
			data = {
			"status":"failure",
			"report":"Incorrect Email address (does not exist in database)",
			"code":400
			}
			cursor.close()
			return data
	elif 'username' in req:
		sql = "SELECT pid from users WHERE username=%s AND website_id=%s"
		cursor.execute(sql, (req['username'], websiteID))
		if cursor.rowcount > 0:
			user_id = int(cursor.fetchone()[0])
		else:
			data = {
			"status":"failure",
			"report":"Incorrect Username (does not exist in database)",
			"code":400
			}
			cursor.close()
			return data
	else:
		data = {
			"status":"failure",
			"report":"No username or email address provided to authenticate",
			"code":400
			}
		cursor.close()
		return data
	#Check most that there is not a more recent user authentication attempt
	sql = "SELECT pid, creation_time, authed from comms WHERE user_id=%s AND creation_time=(SELECT max(creation_time) from comms WHERE user_id=%s)"
	cursor.execute(sql, (user_id, user_id))
	if cursor.rowcount > 0:
		#Success
		row = cursor.fetchone()
		comm_id = int(row[0])
		creation_time = row[1]
		authed = int(row[2])
		if authed == 0 and (datetime.datetime.utcnow() - creation_time).total_seconds() < 15.0:
			data = {
			"status":"failure",
			"report":"Already authenticating another account",
			"code":400
			}
			cursor.close()
			return data

	#Save record of authentication
	saveInteraction(req['ipaddress'], user_id)

	try:
		sql = "UPDATE users SET current_auth_comm_id=(SELECT pid from comms WHERE user_id=%s AND creation_time=(SELECT max(creation_time) from comms where user_id=%s)) WHERE pid=%s"
		cursor.execute(sql, (user_id, user_id, user_id))
		db.commit()
	except:
		data = {
			"status":"failure",
			"report":"Failed to update user account",
			"code":400
			}
		cursor.close()
		return data

	cursor.close()
	cache_result = mem_set_userauthcheck(user_id, 1)
	return {'status':'success', 'user_id':str(user_id)}

def saveInteraction(ipaddress, user_id):
	try:
		cursor = db.cursor()
		sql = "INSERT INTO comms (ipaddress, user_id) VALUES (%s, %s)"
		cursor.execute(sql, (ipaddress, user_id))
		db.commit()
		cursor.close()
	except:
		abort(400, "Failed to add interaction to database")

@app.route('/api/v1.0/removeUser', methods=['POST'])
def webRemoveUser():
	#Arguments are email address, api key, and phone number (all required)
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	req = request.get_json(force=True)
	if not 'emailaddress' in req:
		abort(400, "Email address missing")
	if not 'apikey' in req:
		abort(400, "Api key missing")
	if not 'phonenumber' in req:
		abort(400, "Phone number missing")

	#Get the website's id or reject if incorrect
	websiteID = getWebsiteID(req['apikey'])
	if websiteID is None:
		abort(400, "Incorrect API Key")

	#Check to make sure user exists
	#Unshielded code: Prone to erroring
	cursor = db.cursor()
	sql = "SELECT pid from users WHERE website_id=%s AND phonenumber=%s AND emailaddress=%s"
	cursor.execute(sql, (websiteID, req['phonenumber'], req['emailaddress']))
	if cursor.rowcount < 1:
		cursor.close()
		abort(400, "User that you are trying to delete does not exist")
	user_id = int(cursor.fetchone()[0])

	#TODO: Verify that the server has not deleted too many accounts recently
	#Remove user from the database
	try:
		sql = "DELETE from users where pid=%s"
		cursor.execute(sql, (user_id,))
		db.commit()
	except:
		print("user deletion failed")
		cursor.close()
		abort(400, "Failed to access database to delete user")

	cursor.close()
	return jsonify({'status':'success'})

@app.route('/api/v1.0/checkIfDeviceAuthed/<int:user_id>', methods=['GET'])
def func_checkIfDeviceAuthed(user_id):
	response = checkIfDeviceAuthed(user_id)
	if response['status'] == "failure":
		abort(400, "error in check auth")
	elif response['status'] == "success":
		return jsonify(response)

def checkIfDeviceAuthed(user_id):
	resp = mem_get_userauthcheck(user_id)
	if resp == -1 or resp == 0:
		return {"status":"failure"}
	elif resp == 1:
		return {"status":"success"}

'''
#Old function before memcache enable
def checkIfDeviceAuthed(user_id):
	cursor = db.cursor()
	sql = "SELECT current_auth_comm_id from users WHERE pid=%s"
	cursor.execute(sql, (user_id,))
	if cursor.rowcount > 0:
		#Success
		comm_id = int(cursor.fetchone()[0])
		sql = "SELECT creation_time, authed from comms WHERE pid=%s"
		cursor.execute(sql, (comm_id,))
		if cursor.rowcount > 0:
			#Success
			row = cursor.fetchone()
			creation_time = row[0]
			if int(row[1]) == 1:
				#Check to make sure that authentication is not greater than 15 seconds old
				if (datetime.datetime.utcnow() - creation_time).total_seconds() < 15.0:
					cursor.close()
					return {"status":"success"}
				else:
					data = {
						"status":"failure",
						"report":"Request invalidated: too old",
						"code":400
					}
					cursor.close()
					return data
			elif int(row[1]) == 0:
				cursor.close()
				data = {
					"status":"failure",
					"report":"not yet authenticated",
					"code":200
				}
				return data
			else:
				data = {
				"status":"failure",
				"report":"Database error",
				"code":400
			}
			cursor.close()
			return data
		else:
			data = {
				"status":"failure",
				"report":"Database error",
				"code":400
			}
			cursor.close()
			return data
	else:
		data = {
			"status":"failure",
			"report":"User does not exist",
			"code":400
		}
		cursor.close()
		return data
'''


#Functions for mobile support
#Start here

def getUserFromPhone(emailaddress, phonenumber):
	cursor = db.cursor()
	sql = "SELECT pid from users WHERE emailaddress=%s AND phonenumber=%s"
	cursor.execute(sql, (emailaddress, phonenumber))
	if cursor.rowcount > 0:
		#Success
		response = int(cursor.fetchone()[0])
		cursor.close()
		return response
	else:
		cursor.close()
		abort(400, "Incorrect secret phone number or email address")

@app.route('/app/v1.0/registerDevice', methods=['POST'])
def registerDevice():
	#Arguments are phone-id, email, phone number, security questions (4)
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	req = request.get_json(force=True)
	if not 'phone-id' in req:
		abort(400, "Phone ID missing")
	if not 'emailaddress' in req:
		abort(400, "Email Address missing")
	if not 'phonenumber' in req:
		abort(400, "Phone number missing")
	if not 'secq1' in req or not 'seca1' in req or not 'secq2' in req or not 'seca2' in req or not 'secq3' in req or not 'seca3' in req or not 'secq4' in req or not 'seca4' in req:
		abort(400, "Security questions incomplete or missing")

	#Get the user in question from the secret phone key
	user_id = getUserFromPhone(req['emailaddress'], req['phonenumber'])
	secretkey = randKey(40)

	#Add security questons and phone-id to user profile
	cursor = db.cursor()
	sql = "INSERT INTO devices (secq1, secq2, secq3, secq4, seca1, seca2, seca3, seca4, phone_id, secretphonekey, user_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
	cursor.execute(sql, (req['secq1'], req['secq2'], req['secq3'], req['secq4'], req['seca1'], req['seca2'], req['seca3'], req['seca4'], req['phone-id'],
		secretkey, user_id))
	db.commit()

	sql = "SELECT url from websites WHERE pid=(SELECT website_id from users WHERE pid=%s)"
	cursor.execute(sql, (user_id,))
	if cursor.rowcount > 0:
		url = cursor.fetchone()[0]
	else:
		url = "unknown"
	cursor.close()
	return jsonify({"status":"success", "user_id":user_id, "secretphonekey":secretkey, "url":url})

#Potential security flaw: consider switching to POST request
@app.route('/app/v1.0/checkAuth/<int:user_id>', methods=['GET'])
def checkIfAuthRequired(user_id):
	resp = mem_get_userauthcheck(user_id)
	if resp == -1:
		abort(400, "error in checkauth")
	else:
		#Return either 1 or 0
		return str(resp)

def manual_checkIfAuthRequired(user_id):
	return mem_get_userauthcheck(user_id)

#Mem-caching functions

def mem_get_userauthcheck(user_id):
	key = 'user_auth_' + str(user_id)
	data = memcache.get(key)
	if data is not None:
		return data
	else:
		response = checkauthquery(user_id)
		if response == 0:
			#User does not require authentication
			memcache.add(key=key, value=0, time=3600)
			return 0
		elif response == -1:
			#Error has occured
			return -1
		else:
			memcache.add(key=key, value=1, time=3600)
			return 1

def mem_set_userauthcheck(user_id, value):
	#Set: 1 is user requires authentication, 0 is user does not require authentication
	key = 'user_auth_' + str(user_id)
	if not memcache.set(key=key, value=value, time=3600):
		if not memcache.add(key=key, value=value, time=3600):
			return -1
		else:
			return 0
	else:
		return 0

def checkauthquery(user_id):
	cursor = db.cursor()
	sql = "SELECT current_auth_comm_id from users WHERE pid=%s"
	cursor.execute(sql, (user_id,))
	if cursor.rowcount > 0:
		#Success
		comm_id = int(cursor.fetchone()[0])
		sql = "SELECT authed from comms WHERE pid=%s"
		cursor.execute(sql, (comm_id,))
		if cursor.rowcount > 0:
			#Success
			result = int(cursor.fetchone()[0])
			cursor.close()
			if result == 1:
				return 0
			elif result == 0:
				return comm_id
			else:
				return -1
		else:
			cursor.close()
			return -1
	else:
		cursor.close()
		return -1

@app.route('/app/v1.0/authenticate', methods=['POST'])
def authenticateByPhone():
	#Arguments are phone number, secret phone key, user id, phone-id
	#Return IP Adress, other client device information
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	req = request.get_json(force=True)
	if not 'phonenumber' in req:
		abort(400, "Phone number missing")
	if not 'secretphonekey' in req:
		abort(400, "Secret phone key missing")
	if not 'user_id' in req:
		abort(400, "User ID missing")
	if not 'phone-id' in req:
		abort(400, "Phone ID missing")

	cursor = db.cursor()
	sql = "SELECT user_id from devices WHERE phone_id=%s AND secretphonekey=%s"
	cursor.execute(sql, (req['phone-id'], req['secretphonekey']))
	if cursor.rowcount > 0:
		#Success
		new_user_id = int(cursor.fetchone()[0])
		sql = "SELECT pid from users WHERE phonenumber=%s"
		cursor.execute(sql, (req['phonenumber'],))
		if cursor.rowcount > 0:
			#Phone number verified
			if int(cursor.fetchone()[0]) == new_user_id:		
				if new_user_id == int(req['user_id']):
					#Success, authenticated, set comm's authed to true
					sql = "UPDATE comms SET authed=true WHERE pid=(SELECT current_auth_comm_id FROM users WHERE pid=%s)"
					cursor.execute(sql, (new_user_id,))
					db.commit()
					cursor.close()
					update_cache_result = mem_set_userauthcheck(new_user_id, 0)
					if update_cache_result == 0:
						return jsonify({"status":"success"})
					else:
						return jsonify({"status":"issue updating memcache"})
				else:
					cursor.close()
					abort(400, "Not allowed for authentication")
			else:
				cursor.close()
				abort(400, "Phone number does not match other data")
		else:
			cursor.close()
			abort(400, "Incorrect phone number provided")
	else:
		cursor.close()
		abort(400, "Incorrect device information provided")

@app.route('/app/v1.0/deactivate', methods=['POST'])
def deactivatePhone():
	#Arguments are secret phone key, user id, phone-id
	#Return status
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	req = request.get_json(force=True)
	if not 'secretphonekey' in req:
		abort(400, "Secret phone key missing")
	if not 'user_id' in req:
		abort(400, "User ID missing")
	if not 'phone-id' in req:
		abort(400, "Phone ID missing")

	cursor = db.cursor()
	#Delete phone record from database
	sql = "DELETE FROM devices WHERE secretphonekey=%s AND user_id=%s AND phone_id=%s"
	cursor.execute(sql, (req['secretphonekey'], req['user_id'], req['phone-id']))
	db.commit()
	cursor.close()
	return jsonify({"status":"success"})

#Error handling functions
#Start here

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500

#Website begins here:

@app.route('/example', methods=['GET'])
def demo():
	return render_template('example.html')
	
@app.route('/contact', methods=['GET'])
def contact():
	return render_template('contact.html')
	
@app.route('/pricing', methods=['GET'])
def pricing():
	return render_template('pricing.html')

#Requires testing
#Requires error handling
@app.route('/demoauth', methods=['POST'])
def authenticateDemo():
	if 'username' in request.form:
		attempted_username = request.form['username']
		if attempted_username == "akovesdy17":
			#Correct username, continue
			query = {
				"username" : attempted_username,
				"apikey" : os.environ['CASSO_DEMO_API_KEY'],
				"ipaddress" : request.remote_addr
			}
			response = webAuthenticateUser(query)
			#return response
			if response['status'] == "success":
				user_id = response['user_id']
				timeup = time.time() + 15.0
				while(time.time() < timeup):
					response = manual_checkIfAuthRequired(user_id)
					if response == 0:
						#redirect('/success')
						return jsonify({"status":"success"})
					elif response == -1:
						return jsonify({"status":"error"})
					time.sleep(0.5)
				return jsonify({"status":"request timed out"})
			else:
				return jsonify({"status":response['report']})
		else:
			#Incorrect username
			return jsonify({"status":"username_missing"})

@app.route('/demoauth2', methods=['POST'])
def authenticateDemo2():
	if 'username' in request.form:
		attempted_username = request.form['username']
		if attempted_username == "akovesdy17":
			#Correct username, continue
			query = {
				"username" : attempted_username,
				"apikey" : os.environ['CASSO_DEMO_API_KEY'],
				"ipaddress" : request.remote_addr
			}
			response = webAuthenticateUser(query)
			#return response
			if response['status'] == "success":
				user_id = response['user_id']
				timeup = time.time() + 15.0
				while(time.time() < timeup):
					response = manual_checkIfAuthRequired(user_id)
					if response == 0:
						#redirect('/success')
						return jsonify({"status":"success"})
					elif response == -1:
						return jsonify({"status":"error"})
					time.sleep(0.5)
				return jsonify({"status":"request timed out"})
			else:
				return jsonify({"status":response['report']})
		else:
			#Incorrect username
			return jsonify({"status":"username_missing"})

@app.route('/success', methods=['GET'])
def demo_success():
	return render_template('success.html')

@app.route("/demo", methods=['GET'])
def demo2():
	return render_template('demo.html')


#API version 1.1

def initRequest(request):
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	return request.get_json(force=True)

def getWebsiteIDFromURL(url):
	cursor = db.cursor()
	sql = "SELECT pid from websites WHERE url=%s"
	cursor.execute(sql, (url,))
	if cursor.rowcount > 0:
		response = int(cursor.fetchone()[0])
		cursor.close()
		return response
	else:
		cursor.close()
		return -1

def incrementLogin(websiteID):
	cursor = db.cursor()
	sql = "UPDATE websites SET loginamt = loginamt + 1 WHERE pid = %s"
	cursor.execute(sql, (websiteID,))
	db.commit()
	cursor.close()

def api1_1saveInteraction(ipaddress, user_id):
	#Returns unique client_id key to return to client to allow token transmission
	try:
		cursor = db.cursor()
		client_id = randKey(40)
		sql = "INSERT INTO comms (ipaddress, user_id, token, client_id) VALUES (%s, %s, %s, %s)"
		cursor.execute(sql, (ipaddress, user_id, randKey(40), client_id))
		db.commit()
		cursor.close()
		return client_id
	except:
		abort(400, "Failed to add interaction to database")

#Requires testing
#From client browser to casso server to request authentication token
@app.route('/api/v1.1/clientAuth', methods=['POST'])
def api1_1clientAuth():
	#Arguments are either email or username or phonenumber, website base url (public, registered)
	req = request.form

	#Function logic
	if 'url' not in req:
		abort(400, "Base URL missing from request")

	websiteID = getWebsiteIDFromURL(req['url'])
	if websiteID == -1:
		abort(400, "Base URL does not exist in database")

	#Verify username/email and mark user down for authentication (update timestamp)
	cursor = db.cursor()
	user_id = 0
	if 'emailaddress' in req:
		sql = "SELECT pid from users WHERE emailaddress=%s AND website_id=%s"
		cursor.execute(sql, (req['emailaddress'], websiteID))
		if cursor.rowcount > 0:
			user_id = int(cursor.fetchone()[0])
		else:
			cursor.close()
			abort(400, "Incorrect Email address (does not exist in database)")
	elif 'username' in req:
		sql = "SELECT pid from users WHERE username=%s AND website_id=%s"
		cursor.execute(sql, (req['username'], websiteID))
		if cursor.rowcount > 0:
			user_id = int(cursor.fetchone()[0])
		else:
			cursor.close()
			abort(400, "Incorrect Username (does not exist in database)")
	else:
		cursor.close()
		abort(400, "No username or email address provided to authenticate")
	#Check most that there is not a more recent user authentication attempt
	sql = "SELECT pid, creation_time, authed from comms WHERE user_id=%s AND creation_time=(SELECT max(creation_time) from comms WHERE user_id=%s)"
	cursor.execute(sql, (user_id, user_id))
	if cursor.rowcount > 0:
		#Success
		row = cursor.fetchone()
		comm_id = int(row[0])
		creation_time = row[1]
		authed = int(row[2])
		if authed == 0 and (datetime.datetime.utcnow() - creation_time).total_seconds() < 15.0:
			cursor.close()
			abort(400, "Already authenticating another account")

	#Save record of authentication
	client_id = api1_1saveInteraction(request.remote_addr, user_id)

	try:
		sql = "UPDATE users SET current_auth_comm_id=(SELECT pid from comms WHERE user_id=%s AND creation_time=(SELECT max(creation_time) from comms where user_id=%s)) WHERE pid=%s"
		cursor.execute(sql, (user_id, user_id, user_id))
		db.commit()
	except:
		cursor.close()
		abort(400, "Failed to update user account")

	incrementLogin(websiteID)
	cursor.close()
	pushNotification()
	return jsonify({'status':'success', 'user_id':str(user_id), 'client_id':client_id})

def getToken(user_id, client_id):
	cursor = db.cursor()
	sql = "SELECT token from comms WHERE client_id=%s AND user_id=%s"
	cursor.execute(sql, (client_id, user_id))
	if cursor.rowcount > 0:
		#Success
		result = cursor.fetchone()[0]
		cursor.close()
		return result
	else:
		cursor.close()
		abort(400, "Wrong user ID or client ID provided")

#Requires testing
#From client's browser to casso servers, checking if the phone authenticated
#And sending back the token if it has (only if the client_id is correct)
@app.route('/api/v1.1/clientCheck', methods=['POST'])
def api1_1clientCheck():
	#Arguments are user_id and client_id
	req = request.form

	if 'user_id' not in req:
		abort(400, "User ID missing")

	if 'client_id' not in req:
		abort(400, "Client ID missing")

	cursor = db.cursor()
	sql = "SELECT authed FROM comms WHERE client_id=%s AND user_id=%s"
	cursor.execute(sql, (req['client_id'], req['user_id']))
	if cursor.rowcount > 0:
		authed = int(cursor.fetchone()[0])
		cursor.close()
		#If not authed, false, return failure, if true then return token
		if authed == 0:
			return jsonify({"status":"failure"})
		elif authed == 1:
			return jsonify({"status":"success", "token":getToken(req['user_id'], req['client_id'])})
	else:
		cursor.close()
		abort(400, "Wrong user ID or client ID")

#Send firebase message to alert phone to authenticate
#Arguments: Device ID (in the future)
def pushNotification():
	url = "https://fcm.googleapis.com/fcm/send"
	apikey = os.environ['FCM_API_KEY']
	#Temporary connection to one device
	device_id = "dJyQgsjQkyk:APA91bHYyMMQY8Ap33qkEMt2dFfSOzfG-wdwnAzbi7rzeul7Gured0vOiCs_dYu3Q1Rgf_tdR80b3dWcWc9BzbYAZ0bcyjcm275qa_T4fy69GEt1p5Bwdodi07QT098k9mnTqZuuF3mc"
	headers = {"Authorization":"key=%s" % (apikey,), "Content-Type":"application/json"}
	queryargs = json.dumps({"data":{"reqtype" : "auth"}, "to": device_id})

	res = urlfetch.fetch(
		url=url,
		payload=queryargs,
		method=urlfetch.POST,
		headers=headers
		)

	results = res.content

#Requires testing
#POST request sent by phone to Casso to authenticate
@app.route('/api/v1.1/deviceAuth', methods=['POST'])
def api1_1deviceAuth():
	#Use API version 1.0 function phoneAuthenticate for this
	pass

#Requires testing
#POST request sent by website to Casso to check auth based on token
@app.route('/api/v1.1/webAuth', methods=['POST'])
def api1_1webAuth():
	pass

#Requires testing
#POST request sent by phone to Casso to signal the device's FCM token
@app.route('/api/v1.1/FCMTokenUpdate', methods=['POST'])
def api1_1FMCTokenUpdate():
	#Arguments are secret phone key, phone-id, and new token
	req = initRequest(request)

	if not 'secretphonekey' in req:
		abort(400, "Missing secret phone key")
	if not 'phone-id' in req:
		abort(400, "Missing phone ID")
	if not 'fcmtoken' in req:
		abort(400, "Missing new FCM token")

	cursor = db.cursor()
	sql = "SELECT pid FROM devices WHERE secretphonekey=%s and phone_id=%s"
	cursor.execute(sql, (req['secretphonekey']), req['phone-id'])
	if cursor.rowcount > 0:
		pid = int(cursor.fetchone()[0])
		sql = "UPDATE devices SET fcmtoken=%s WHERE pid=%s"
		cursor.execute(sql, (req['fcmtoken']), pid)
		db.commit()
		cursor.close()
		return jsonify({"status":"success"})
	else:
		cursor.close()
		abort(400, "Incorrect secret phone key or phone ID provided")


