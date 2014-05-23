import os

#For HTTP shit
import requests
import urllib
import json

#For Amazon uploading.
from awsauth import S3Auth

#For some encryption stuff
import hashlib
import random
import string
import StringIO
import gzip
import uuid
import random
import datetime



class Vine:
	def __init__(self):
	
		#Vine Client shit
		self.endpoint = "https://api.vineapp.com/"
		self.userAgent = "iphone/106 (iPhone; iOS 7.0.4; Scale/2.00)"
		self.proxy = None

		self.x_vine_client = "ios/1.4.7"

		#Amazon stuff
		self.awsUserAgent = "aws-sdk-iOS/1.4.4 iPhone-OS/6.1 en_US"
		self.aws_key = "AKIAJL2SSORTZ5AK6D4A"
		self.aws_secret = "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"
		self.acceptableAccessCodes = (200, 204)
	
		#User-specific shit
		self.loggedIn = False
		self.userId = ""
		self.username = ""
		self.session_id = ""
		self.following = 0
		self.followerCount = 0
		self.description = ""
		self.avatar = ""
		self.email = ""
		self.location = ""
		self.info = []
		self.avatarVersionId = ""
	
	def setProxy(self,proxy):
		self.proxy = proxy
	
	#Generates the ContentID for the Amazon S3 file in the "Vines" bucket
	def genCID(self):
		return "%s-%d-%016X_%s" % (uuid.uuid4(), random.randint(1024, 0xffff),random.randint(0x1000000000, 0xf0000000000), "1.1.2")
		
	#Gets the current date (y/m/d/) for the /videos/ path on the "Vines" bucket
	def genDatePath(self):
		return datetime.datetime.now().strftime("%Y/%m/%d/")
	
	#Simple setter for the sessionId so we don't have to make that login request again
	def setSessionId(self,sid):
		self.session_id =  sid
		self.loggedIn = True
	
	#Set the user ID just for the lulz
	def setUserId(self,uid):
		self.userId = uid
	
	#Uploads the avatar to Vine's S3 bucket and returns the full URI to where it's stored.
	#Parameters are: photo_file="/var/path/to/file.jpg" & photo_name="myPhoto.jpg"
	def uploadAvatar(self,photo,cid):
		avatar_url = "https://vines.s3.amazonaws.com/avatars/" + cid + ".jpg"
		f = open(photo,"rb")
		avatar_data = f.read()
		f.close()
		r = requests.put(avatar_url,data = avatar_data, auth=S3Auth(self.aws_key,self.aws_secret),headers={"Content-Type":"image/jpeg"})
		if r.status_code not in self.acceptableAccessCodes:
			return False
		else:
			self.avatarVersionId = r.headers.get("x-amz-version-id")
			return avatar_url + "?versionId=" + self.avatarVersionId


			
	def uploadVideo(self,video,cid):
		video_url = "https://vines.s3.amazonaws.com/videos/" + self.genDatePath() + cid + ".mp4"
		
		f = open(video,"rb")
		video_data = f.read()
		f.close()
		
		r = requests.put(video_url,data = video_data, auth=S3Auth(self.aws_key,self.aws_secret),headers={"Content-Type":"video/mp4"})#video/mp4
		if r.status_code not in self.acceptableAccessCodes:
			return False
		else:
			return video_url + "?versionId=" + r.headers.get("x-amz-version-id")
	
	def uploadVideoThumb(self,thumb,cid):
		thumb_url = "https://vines.s3.amazonaws.com/thumbs/" + self.genDatePath() + cid + ".mp4.jpg"
		f = open(thumb,"rb")
		thumb_data = f.read()
		f.close()
		
		r = requests.put(thumb_url,data = thumb_data, auth=S3Auth(self.aws_key,self.aws_secret),headers={"Content-Type":"image/jpeg"})
		if r.status_code not in self.acceptableAccessCodes:
			return False
		else:
			return thumb_url + "?versionId=" + r.headers.get("x-amz-version-id")

	def configureVine(self,payload):
		headers = {
			"Accept-Language" : "nb;q=1, en;q=0.9, fr;q=0.8, de;q=0.7, ja;q=0.6, nl;q=0.5",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"Content-Type" : "application/json; charset=utf-8",
			"User-Agent" : self.userAgent,
			"vine-session-id" : self.session_id,
			"X-Vine-Client" : self.x_vine_client,
			"Accept-Encoding" : "gzip, deflate"
		}
		pdata = json.dumps(payload)
		print "Data: " + str(pdata)
		r = requests.post(self.endpoint + "/posts",data = pdata, headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				print str(response)
				return True
			else:
				return False
		elif r.status_code == 400:
			return False
		else:
			return False

	def login(self,username,password):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"Content-Type" : "application/x-www-form-urlencoded; charset=utf-8",
			"Accept-Encoding" : "gzip"
		}
		payload = {
			"username" : username,
			"password" : password
		}
		if self.proxy == None:
			r = requests.post(self.endpoint + "users/authenticate",data=payload,headers=headers)
		else:
			r = requests.post(self.endpoint + "users/authenticate",data=payload,headers=headers,proxies=self.proxy)
		#print str(r.text)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			#print r.text
			if response['success'] == True:
				self.username = response['data']['username']
				self.userId = response['data']['userId']
				self.session_id = response['data']['key']
				self.loggedIn = True
				return True
			else:
				return False
		elif r.status_code == 400:
			#print "[Login]Error 400: " + str(r.text)
			return False
		else:
			#print "[Login]Unknown error: " + str(r.text)
			return False

	#Fetches the profile of a specific userId
	#users/profiles/%i
	def getUser(self,userid):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "users/profiles/" + str(userid),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response['data']
			else:
				return False
		else:
			return False
	
	#Get the feed for the userId specified
	def getTimeline(self,userid):
		#https://api.vineapp.com/timelines/users/
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "timelines/users/" + str(userid),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response['data']
			else:
				return False
		else:
			return False
	
	#Get global timeline - works, but doesn't update beyond January 2013
	def getGlobalTimeline(self,page):
		#https://api.vineapp.com/timelines/users/
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "timelines/global?page=" + str(page),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response['data']
			else:
				return False
		else:
			return False
		
	#Fetches the profile of the user currently logged in for this object
	def getMe(self):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "users/me",headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				self.info = response['data']
				return True
			else:
				return False
		else:
			return False

	#Creates a new Vine account
	def createAccount(self,payload):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Proxy-Connection":"keep-alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"Content-Type" : "application/x-www-form-urlencoded; charset=utf-8",
			"Accept-Encoding" : "gzip"
		}
		
		
		#proxy = {"http":"beej1990:OL7rpC6B@216.213.36.112:48120"}
		
		#
		#response should be: {"code": "", "data": {"userId": 945347559730343936, "key": "945347559730343936-833de214-cb13-4aec-b8f9-0fe90791e6dd"}, "success": true, "error": ""}
		if self.proxy == None:
			r = requests.post(self.endpoint + "users",data=payload,headers=headers,verify=True)
		else:
			r = requests.post(self.endpoint + "users",data=payload,headers=headers,proxies = self.proxy,verify=True)
		#print "Response headers: " + str(r.headers)
		#print "\n\nRequest Headers: " + str(r.request.headers)
		#print r.text
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				self.userId = response['data']['userId']
				self.session_id = response['data']['key']
				self.loggedIn = True
				return True
			else:
				return False
		elif r.status_code == 400:
			return False
		else:
			return False

	#Updates the users' profile for this account.
	#payload = object containing: description (string),username (or name - alphanumerics only :[ ), location (string), and valid avatarUrl (string - needs versionId appended)
	def editProfile(self,payload):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.put(self.endpoint + "users/" + str(self.userId),data=payload,headers=headers)
		print r.text
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return True
			else:
				return False
		else:
			return False
	
	#Like a specific vine (postId)
	def like(self,postId):
		#print "Beginning of like func. session is: " + self.session_id
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"Content-Length" : "0",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		like_url = self.endpoint + "posts/" + str(postId) + "/likes"
		#print like_url
		if self.proxy == None:
			r = requests.post(like_url,headers=headers)
		else:
			r = requests.post(like_url,headers=headers,proxies = self.proxy)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return True
			else:
				return False
		else:
			return False

	def revine(self,postId):
		#print "Beginning of revine func. session is: " + self.session_id
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"Content-Length" : "0",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		revine_url = self.endpoint + "posts/" + str(postId) + "/repost"
		#print revine_url
		if self.proxy == None:
			r = requests.post(revine_url,headers=headers)
		else:
			r = requests.post(revine_url,headers=headers,proxies = self.proxy)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return True
			else:
				return False
		else:
			return False
			
	#Like a specific vine (postId)
	def follow(self,user_id):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		#print "Following: " + str(user_id) + " from " + str(self.userId)
		if self.proxy == None:
			r = requests.post(self.endpoint + "users/" + str(user_id) + "/followers",headers=headers)
		else:
			r = requests.post(self.endpoint + "users/" + str(user_id) + "/followers",headers=headers, proxies = self.proxy)
			
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return True
			else:
				return False
		else:
			#print r.text
			return False
			
			
	#getpost
	def getPost(self,postId):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "posts/" + str(postId),headers=headers)
		if r.status_code == 200:
			#response['data']['likeId']
			print r.text
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return True
			else:
				return False
		else:
			return False
	
	def getFollowers(self,userId,page):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "users/" + str(userId) + "/followers?page=" + str(page),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response
			else:
				return False
		else:
			return False
	
	def getFollowing(self,userId,page):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "users/" + str(userId) + "/following?page=" + str(page),headers=headers)
		if r.status_code == 200:
			print r.text
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response
			else:
				return False
		else:
			return False
	
	#There are 5 pages of popular things. page=1
	def getPopular(self,page):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "timelines/popular?page=" + str(page),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response
			else:
				return False
		else:
			return False

	def searchUser(self,keyword):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "users/search/" + str(keyword),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response
			else:
				return False
		else:
			return False

	#Fetch Tag
	def searchTag(self,keyword):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		r = requests.get(self.endpoint + "timelines/tags/" + str(keyword),headers=headers)
		if r.status_code == 200:
			response = json.loads(r.text.decode('utf8'))
			if response['success'] == True:
				return response
			else:
				return False
		else:
			return False

	def comment(self, postid, comment):
		headers = {
			"Accept-Language" : "nb, en, fr, de, ja, nl, it, es, pt, pt-PT, da, fi, sv, ko, zh-Hans, zh-Hant, ru, pl, tr, uk, ar, hr, cs, el, he, ro, sk, th, id, ms, en-GB, ca, hu, vi, en-us;q=0.8",
			"Connection" : "Keep-Alive",
			"Accept" : "*/*",
			"User-Agent" : self.userAgent,
			"X-Vine-Client" : self.x_vine_client,
			"vine-session-id" : self.session_id,
			"Accept-Encoding" : "gzip"
		}
		comment_data = {
			"comment": comment,
			"entities": []
		}
		
		r = requests.post(self.endpoint + "posts/" + str(postid) + "/comments",data=comment_data,headers=headers)
		if r.status_code == 200:
			response = json.loads(r.content.decode('utf8'))
			if response['success'] == True:
				return response['data']['commentId']
			else:
				return False
		else:
			return False


