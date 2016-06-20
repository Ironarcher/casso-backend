import os
import random
import MySQLdb
# Import the Flask Framework
from flask import Flask, jsonify, request, abort
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
cursor = db.cursor()

#Website handling functions
#Start here

@app.route('/')
def hello():
	"""Return a friendly HTTP greeting."""
	return "Hello again!"

@app.route('/api/v1.0/registerWebsite', methods=['POST'])
def webRegisterWebsite():
	#Arguments are website url
	#Must be done manually currently
	if not request.json or not 'emailaddress' in request.get_json(force=True, silent=True):
		abort(400, 'ohno')
	return jsonify({'status' : 'success'})

@app.route('/api/v1.0/registerUser', methods=['POST'])
def webRegisterUser():
	#Arguments are optional username, email address, api key, phone number, ip address
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

    #Verify that the emailaddress does not exist again on that website
	if checkUserExists(req['emailaddress'], req['phonenumber'], websiteID) is True:
		abort(400, "User already with that email or phone number already exists")

	#Create a new user entry
	try:
		if 'username' in req:
			sql = "INSERT INTO users (username, emailaddress, phonenumber, secretphonekey, website_id) VALUES (%s,%s,%s,%s,%s)"
			cursor.execute(sql, (req['username'], req['emailaddress'], req['phonenumber'], randKey(40), websiteID))
			db.commit()
		else:
			sql = "INSERT INTO users (emailaddress, phonenumber, secretphonekey, website_id) VALUES (%s,%s,%s,%s)"
			cursor.execute(sql, (req['emailaddress'], req['phonenumber'], randKey(40), websiteID))
			db.commit()
	except:
		abort(400, "database error during user creation")

	return jsonify({'status' : 'success'})

def getWebsiteID(apikey):
	try:
		cursor.execute('SELECT pid from websites WHERE secretkey=%s', (apikey,))
		if cursor.rowcount > 0:
			result = cursor.fetchone()
			return int(result[0])
		else:
			return None
	except:
		print("get website id error")
		abort(400, "get website id error")

def checkUserExists(emailaddress, phonenumber, websiteid):
	try:
		sql1 = "SELECT pid from users WHERE emailaddress=%s AND website_id=%s"
		cursor.execute(sql1, (emailaddress, websiteid))
		if cursor.rowcount > 0:
			return True
		else:
			sql2 = "SELECT pid from users WHERE website_id=%s AND phonenumber=%s"
			cursor.execute(sql2, (websiteid, phonenumber))
			if cursor.rowcount  > 0:
				return True
			else:
				return False
	except:
		print("check user error")
		abort(400, "check user error")

def randKey(digits):
	return ''.join(random.choice(
		'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(digits))

@app.route('/api/v1.0/authenticateUser', methods=['POST'])
def webAuthenticateUser():
	#Arguments are optional either username or email, apikey, ipaddress of request to authenticate
	if not request.get_json(force=True, silent=True):
		abort(400, "Request in the wrong format")
	req = request.get_json(force=True)
	if 'apikey' not in req:
		abort(400, "Api key missing")
	if 'ipaddress' not in req:
		abort(400, "IP address of client missing")

	#Check the website's secret key
	websiteID = getWebsiteID(req['apikey'])
	if websiteID is None:
		abort(400, "Incorrect API Key")

	#Verify username/email and mark user down for authentication (update timestamp)
	user_id = 0
	if 'emailaddress' in req:
		sql = "SELECT pid from users WHERE emailaddress=%s AND website_id=%s"
		cursor.execute(sql, (req['emailaddress'], websiteID))
		if cursor.rowcount > 0:
			user_id = int(cursor.fetchone()[0])
		else:
			abort(400, "Incorrect Email address (does not exist in database)")
	elif 'username' in req:
		sql = "SELECT pid from users WHERE username=%s AND website_id=%s"
		cursor.execute(sql, (req['username'], websiteID))
		if cursor.rowcount > 0:
			user_id = int(cursor.fetchone()[0])
		else:
			abort(400, "Incorrect Username (does not exist in database)")
	else:
		abort(400, "No username or email address provided to authenticate")

	#Save record of authentication
	saveInteraction(req['ipaddress'], user_id)

	try:
		sql = "UPDATE users SET last_auth_request=NOW() WHERE pid=%s"
		cursor.execute(sql, (user_id,))
		db.commit()
	except:
		abort(400, "Failed to update user account")

	return jsonify({'status':'success'})

def saveInteraction(ipaddress, user_id):
	try:
		sql = "INSERT INTO comms (ipaddress, user_id) VALUES (%s, %s)"
		cursor.execute(sql, (ipaddress, user_id))
		db.commit()
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
	sql = "SELECT pid from users WHERE website_id=%s AND phonenumber=%s AND emailaddress=%s"
	cursor.execute(sql, (websiteID, req['phonenumber'], req['emailaddress']))
	if cursor.rowcount < 1:
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
		abort(400, "Failed to access database to delete user")

	return jsonify({'status':'success'})

#Functions for mobile support
#Start here





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
