import urllib
import requests
import json
import os
import thread
import time

baseurl = "https://casso-1339.appspot.com"
#baseurl = "http://localhost:8080"

def main():
	start_stress(100, 10)
	time.sleep(100000)

def start_stress(qps_get, qps_post):
	try:
		for i in range(qps_get):
			thread.start_new_thread(stress_get_req, ("checkthread"+str(i), 1))
			time.sleep(0.1)
		for j in range(qps_post):
			thread.start_new_thread(stress_verify, ("postthread"+str(j), 20))
			time.sleep(1)
	except:
		print 'thread error'

def stress_verify(threadname, delay):
	while(True):
		verify()
		print(threadname + ": " + str(time.time()))
		time.sleep(delay)
 
def stress_get_req(threadname, delay):
	while(True):
		print(threadname + ": " + phone_check())
		time.sleep(delay)

def phone_check():
	return get('/app/v1.0/checkAuth/34')

def verify():
	data = {
		"username" : "akovesdy17",
		"apikey" : "",
		"ipaddress" : "00.00"
	}
	response = post('/api/v1.0/authenticateUser', data)

def get(url):
	response = urllib.urlopen(baseurl + url)
	return response.read()

def post(url, queryargs):
	res = requests.post(baseurl + url, data=json.dumps(queryargs))
	return res.text

if __name__ == '__main__':
	main()