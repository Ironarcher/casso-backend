import os
import random
import MySQLdb
# Import the Flask Framework
from flask import Flask, jsonify
app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

db = getDB()
cursor = db.cursor()

@app.route('/')
def hello():
	"""Return a friendly HTTP greeting."""
	return "Hello again!"

@app.route('/api/v1.0/registerWebsite', methods=['POST'])
def webRegisterWebsite():
	#Arguments are 

@app.route('/api/v1.0/registerUser', methods=['POST'])
def webRegisterUser():
	#Arguments are optional username, email address, api key, phone number, ip address
	if not request.json or not 'emailaddress' in request.json or not 'apikey' in request.json or not 'phonenumber' in request.json or not 'ipaddress' in request.json:
        abort(400, "Missing information")
    #Get the website's id or reject if incorrect
    websiteID = getWebsiteID()
    if websiteID is null:
    	abort(400, "Incorrect API Key")

    #Verify that the emailaddress does not exist again on that website
    if not checkUserAllowed(request.json['emailaddress'], websiteID):
    	abort(400, "User already with that email already exists")

    #Create a new user entry
    if 'username' in request.json:
    	sql = "INSERT INTO users (username, emailaddress, phonenumber, secretphonekey, ipaddress, website_id) VALUES (%s,%s,%s,%s,%s,%s)" % (
    		request.json['username'], request.json['emailaddress'], request.json['phonenumber'], randKey(40),
    		request.json['ipaddress'], wesiteID)
	else:
		sql = "INSERT INTO users (emailaddress, phonenumber, secretphonekey, ipaddress, website_id) VALUES (%s,%s,%s,%s,%s)" % (
    		request.json['emailaddress'], request.json['phonenumber'], randKey(40),
    		request.json['ipaddress'], wesiteID)
	try:
		cursor.execute(sql)
		db.commit()
		return jsonify({'status' : 'success'})
	except:
		abort(400, "User creation has failed")

def getWebsiteID(apikey):
	try:
		cursor.execute('SELECT id from websites WHERE secretkey=%s'  % (request.json['apikey']))
	    result = cursor.fetchone()
	    if result.rowcount > 0:
	    	return result[0]
		else:
			return null
	except:
		return null

def checkUserExists(emailaddress, websiteid):
	try:
		cursor.execute('SELECT id from users WHERE emailaddress=%s AND websiteid=%s' % (emailaddress, websiteid))
		result = cursor.fetchone()
		if result.rowcount > 0:
			return True
		else:
			return False
	except:
		print("Check user error")
		abort(400, "Check user has failed")

def randKey(digits):
	return ''.join(random.choice(
		'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(digits))
  
def webAuthenticateUser():
	pass

def webRemoveUser():
	pass

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

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
