import os
import sys
import pickle
import requests
from httplib2 import ServerNotFoundError
from requests.exceptions import ConnectionError, Timeout, HTTPError

from Account import *
import Settings

class InstagramAccount(Account):

	percF4F = 1/2
	percNotF4F = 1/2

	MAX_RETRIEVED_MEDIA = 10
	MAX_RETRIEVED_LIKE = 10
	MAX_RETRIEVED_COMMENTS = 10

	FSTATS_TRASH_TIME = 60*60*24*20		# 20 days

	MIN_TIME_BETWEEN_ACTIONS = 30		# seconds
	MAX_TIME_BETWEEN_ACTIONS = 40		# seconds 

	DUMP_DIRECTORY = "dump"

	f4fs = ["follow4follow","follow","followback"] 
	l4ls = ["like4like","likeback"]


	def __init__(self, accounts, account, tags, blogs):
		super(InstagramAccount, self).__init__(accounts, account['ID'], account['Mail'], account['Type'])
		self.username = account['Username']
		self.password = account['Password']
		self.tags = tags2list(tags)
		self.blogs = blogs2list(blogs)
		self.data = self.initData()
		self.num_post_xd = int(account['PostXD'])
		self.num_follow_xd = int(account['FollowXD'])
		self.num_like_xd = int(account['LikeXD'])
		self.num_post_xt = int(account['PostXT'])
		self.num_follow_xt = int(account['FollowXT'])
		self.num_like_xt = int(account['LikeXT'])
		self.status = self.STATUS_STOP
		self.loadStatistics()


	def getAccountName(self):
		return self.data['name']


	def getSocialName(self):
		return "instagram"


	def initStatistics(self):
		self.statistics = { 'timer_follow_match': {	'f+rl': 1, 'f': 1, 'f4f': 1, 'f4f+rl': 1 },
							'timer_follow_tot':   { 'f+rl': 1, 'f': 1, 'f4f': 1, 'f4f+rl': 1 },
							'timer_follow_succ':  {	'f+rl': float(1), 'f': float(1), 'f4f': float(1), 'f4f+rl': float(1) },
							'timer_follow_prob':  {	'f+rl': 1/float(4), 'f': 1/float(4), 'f4f': 1/float(4), 'f4f+rl': 1/float(4) },
							'timer_like_match':   { 'l4l': 1, 'l4l+f': 1, 'l4l+rl': 1, 'l4l+f+rl': 1, 'l+f+rl': 1,
													'l+f': 1, 'l+rl': 1, 'l': 1, 'rl': 1 },
							'timer_like_tot': 	  { 'l4l': 1, 'l4l+f': 1, 'l4l+rl': 1, 'l4l+f+rl': 1, 'l+f+rl': 1,
													'l+f': 1, 'l+rl': 1, 'l': 1, 'rl': 1 },
							'timer_like_succ': 	  { 'l4l': float(1), 'l4l+f': float(1), 'l4l+rl': float(1), 'l4l+f+rl': float(1), 
													'l+f+rl': float(1), 'l+f': float(1), 'l+rl': float(1), 'l': float(1), 'rl': float(1) },
							'timer_like_prob': 	  { 'l4l': 1/float(9), 'l4l+f': 1/float(9), 'l4l+rl': 1/float(9), 'l4l+f+rl': 1/float(9), 
													'l+f+rl': 1/float(9), 'l+f': 1/float(9), 'l+rl': 1/float(9), 'l': 1/float(9), 
													'rl': 1/float(9) }
							}
		self.dumpStatistics()


	def dumpStatistics(self):
		pickle.dump(self.statistics,open(self.DUMP_DIRECTORY + "/" + self.username + ".p","wb"))


	def loadStatistics(self):
		if os.path.exists(self.DUMP_DIRECTORY):
			if os.path.exists(self.DUMP_DIRECTORY + "/" + self.username + ".p"):
				try:
					self.statistics = pickle.load(open(self.DUMP_DIRECTORY + "/" + self.username + ".p","rb"))
				except Exception, msg:
					self.write("Error: " + str(msg))
			else:
				self.initStatistics()
		else:
			os.mkdir(self.DUMP_DIRECTORY)
			self.initStatistics()


	def updateMatchStatistics(self, group, action):
		self.statistics[group + "_match"][action] += 1
		self.updateSuccProbStatistics(group, action)


	def updateMatchesStatistics(self):
		bn = self.getAccountName()
		for follow in self.followersList:
			fstats = self.dbManager.getFstats(bn,follow)
			if fstats != []:
				for fstat in fstats:
					if fstat['action'][0] == 'f':
						self.updateMatchStatistics('timer_follow', fstat['action'])
					else:
						self.updateMatchStatistics('timer_follow', fstat['action'])
				args = (bn,follow)
				self.dbManager.delete('Fstats',args)
		# Delete old ones:
		timeLimit = int((time.time() - self.FSTATS_TRASH_TIME) * self.TIME_FACTOR)
		self.dbManager.deleteFstatsTrash(bn,timeLimit)


	def updateTotStatistics(self, group, action):
		self.statistics[group + "_tot"][action] += 1
		self.updateSuccProbStatistics(group, action)


	def updateSuccProbStatistics(self, group, action):
		match = float(self.statistics[group + "_match"][action])
		tot = float(self.statistics[group + "_tot"][action])
		self.statistics[group + "_succ"][action] = match / tot
		sum_succ = 0
		for key, item in self.statistics[group + "_succ"].iteritems():
			sum_succ += item
		for key in self.statistics[group + "_prob"]:
			self.statistics[group + "_prob"][key] = self.statistics[group + "_succ"][key] / sum_succ
		self.dumpStatistics()


	def addStatistics(self, followedBlog, action):
		if action[0] == 'f':
			group = 'timer_follow'
		else:
			group = 'timer_like'
		self.updateTotStatistics(group, action)
		args = (self.getAccountName(), followedBlog, action, int(time.time() * self.TIME_FACTOR))
		self.dbManager.add("Fstats",args)


	def initData(self):
		return {'private': "not available",
				'following': "not available",
				'followers': "not available",
				'messages': "not available",
				'name': "not available",
				'posts': "not available",
				'usertags': "not available"
				}


	def checkResponse(self, res):
		"Check if there is an error in response"
		if res != None:
			return True
		else:
			return False


	def updateBlog(self, firstTime=False):
		if self.getAccountName() != "not available":
			if firstTime:
				sys.stdout.write("\tUpdate " + self.getAccountName() + ".. ")
			else:
				self.write("\tUpdate " + self.getAccountName() + ".. ")
		else:
			if firstTime:
				sys.stdout.write("\tUpdate " + self.mail + ".. ")
			else:
				self.write("\tUpdate " + self.mail + ".. ")
		try:
			ibi = self.post_insta_request({'action': 'get_insta_blog_info'}, firstTime=True)
			if self.checkResponse(ibi):
				self.data['private'] = ibi['private']
				self.data['following'] = ibi['following']
				self.data['followers'] = ibi['follower']
				self.data['messages'] = ibi['message']
				self.data['name'] = ibi['name']
				self.data['posts'] = ibi['post']
				self.data['usertags'] = ibi['usertags']
				self.accounts.matches[ibi['name']] = self.strID
				if firstTime:
					print "ok."
				else:
					self.write("ok.\n")
			else:
				if firstTime:
					print "Error: cannot update."
				else:
					self.write("Error: cannot update.\n")
		except Exception, msg:
			if firstTime:
				print "Error Exception:\n" + str(msg)
			else:
				self.write("Error Exception:\n" + str(msg) + "\n")
						

	def updateBlogData(self):
		self.write("\tUpdate " + self.data['name'] + ".. ")
		post_data_up = {"action": "update_blog_data_insta", 
			"ID": self.account_id,
			"Following": self.data['following'],
			"Followers": self.data['followers'],
			"Posts": self.data['posts'],
			"Messages": self.data['messages'],
			"Name": self.data['name'],
			"Private": self.data['private'],
			"Usertags": self.data['usertags']
			}
		if (self.strID + "-post") in self.timersTime:
			post_data_up["Deadline_Post"] = self.timersTime[self.strID + "-post"]
		if (self.strID + "-follow") in self.timersTime:
			post_data_up["Deadline_Follow"] = self.timersTime[self.strID + "-follow"]
		if (self.strID + "-like") in self.timersTime:
			post_data_up["Deadline_Like"] = self.timersTime[self.strID + "-like"]
		up_res = self.post_request(post_data_up)
		if up_res != None:
			self.write("update status.. ")
			self.updateStatus()
			self.write("end of update.\n")


	def updateUpOp(self, newAccount):
		if self.username != newAccount['Username']:
			self.write("\t\t    Username: " + self.username + " -> " + newAccount['Username'] + "\n")
			self.username = newAccount['Username']
		if self.password != newAccount['Password']:
			self.write("\t\t    Password: " + self.password + " -> " + newAccount['Password'] + "\n")
			self.password = newAccount['Password']
		super(InstagramAccount, self).updateUpOp(newAccount)


	def copyBlog(self, blog_to_copy, limitMax, counter):
		self.write("Method 'copyBlog' not implemented for Instagram account!\n")


	def waitInsta(self, little=False):
		if little:
			secs = random.randint(1, 4)
		else:
			secs = random.randint(self.MIN_TIME_BETWEEN_ACTIONS, self.MAX_TIME_BETWEEN_ACTIONS)
		time.sleep(secs)


	def calc_time_post_follow(self):
		f_tf, l_tf = self.calc_expected_FL_TF()
		f_tl, l_tl = self.calc_expected_FL_TL()

		nl = ((self.num_like_xd * f_tf) - (self.num_follow_xd * l_tf)) / float(self.num_like_xt * ((l_tl * f_tf) - (f_tl * l_tf)))
		nf = (self.num_like_xd - (nl * self.num_like_xt * l_tl)) / float(self.num_follow_xt * l_tf)

		self.write("\tCalcule timers for " + self.getAccountName() + ":\n")
		if self.num_post_xd == 0:
			self.timer_post = 0
			self.write("\t\tnever post\n")
		else:
			self.timer_post = int((24*60*60/(self.num_post_xd/self.num_post_xt))+0.5)
			self.write("\t\tpost every " + seconds2timeStr(self.timer_post) + "\n")	
		self.timer_follow = int((24*60*60/nf)+0.5)
		self.write("\t\tfollow every " + seconds2timeStr(self.timer_follow) + "\n")
		self.timer_like = int((24*60*60/nl)+0.5)
		self.write("\t\tlike every " + seconds2timeStr(self.timer_like) + "\n")


	def calc_expected_FL_TF(self):
		return 1, (self.statistics['timer_follow_prob']['f+rl'] + self.statistics['timer_follow_prob']['f4f+rl'])


	def calc_expected_FL_TL(self):
		tlp = self.statistics['timer_like_prob']
		expected_f = tlp['l4l+f'] + tlp['l4l+f+rl'] + tlp['l+f+rl'] + tlp['l+f']
		expected_l = tlp['l4l'] + tlp['l4l+f'] + (2 * tlp['l4l+rl']) + (2 * tlp['l4l+f+rl']) 
		expected_l += (2 * tlp['l+f+rl']) + tlp['l+f'] + (2 * tlp['l+rl']) + tlp['l'] + tlp['rl'] 
		return expected_f, expected_l


	def checkNeedNewFollows(self):
		bn = self.getAccountName()
		# Check num Follows
		follows = self.dbManager.countFollow(bn)
		self.write("\t   check #follow.. ")
		if follows >= self.num_follow_xt:
			self.write("found " + str(follows) + ", ok\n")
		else:
			self.write("found " + str(follows) + ", needed at least " + str(self.num_follow_xt) + "\n")
			self.searchNewFollows(self.num_follow_xt-follows)


	def searchNewFollows(self, num_follows):
		num_following_blogs = len(self.blogs)
		if num_following_blogs >= num_follows:
			followXblog = 1
		elif num_following_blogs > 0:
			followXblog = int(num_follows/num_following_blogs)+1
		else:
			followXblog = 0
		self.write("\t      Getting follows..\n")
		for blog in self.blogs:
			counter = 0
			blog_id = self.getIdByUsernameInsta(blog)
			if blog_id == None:
				self.write("\t         Error (None response) for '" + blog + "' -> skip!\n")
				continue
			followers = self.getFollowersSocial(user=blog_id, maxNum=followXblog)
			for follow in followers:
				if (not follow in self.followersList) and (not follow in self.followingList):
					self.addFollowToDB(follow)
					counter += 1
					self.write("\r\t         from " + blog + ".. " + str(counter))
			self.write("\n")
			self.waitInsta(little=True)
		if len(self.tags) > 0:
			tag = self.randomTag()
			if self.MAX_RETRIEVED_COMMENTS + self.MAX_RETRIEVED_LIKE >= num_follows:
				popularPosts = 1
			else:
				popularPosts = int(num_follows/(self.MAX_RETRIEVED_COMMENTS + self.MAX_RETRIEVED_LIKE))+1
			counterMedia = 0
			counterLikers = 0
			counterComments = 0
			media = self.getTaggedPopularInsta(tag, popularPosts)
			for post in media:
				if (not post['userID'] in self.followingList) and (not post['userID'] in self.followersList):
					self.addFollowToDB(post['userID'])
					counterMedia += 1
					self.write("\r\t         from posts: " + str(counterMedia) + ", from likes: " + str(counterLikers) + ", from comments: " + str(counterComments))
				self.waitInsta(little=True)
				likers = self.getMediaLikersInsta(post['mediaID'], self.MAX_RETRIEVED_LIKE)
				for liker in likers: 
					if (not liker in self.followingList) and (not liker in self.followersList):
						self.addFollowToDB(liker)
						counterLikers += 1
						self.write("\r\t         from posts: " + str(counterMedia) + ", from likes: " + str(counterLikers) + ", from comments: " + str(counterComments))
				self.waitInsta(little=True)
				comments = self.getMediaCommentsInsta(post['mediaID'], self.MAX_RETRIEVED_COMMENTS)
				for comment in comments: 
					if (not comment in self.followingList) and (not comment in self.followersList):
						self.addFollowToDB(comment)
						counterComments += 1
						self.write("\r\t         from posts: " + str(counterMedia) + ", from likes: " + str(counterLikers) + ", from comments: " + str(counterComments))
				self.waitInsta(little=True)
			self.write("\n")
		else:
			self.write("\t         No Tags inserted.. cannot get new follows!\n")


	def postSocial(self, post):
		self.write("Method 'post' not implemented for Instagram account!\n")


	def followSocial(self, num_follows, isDump):
		blogname = self.getAccountName()
		alreadyFollowed = []
		num_f = 0
		num_f4f = 0
		num_frl = 0
		num_f4frl = 0
		errors = 0
		for counter in range(0,num_follows):
			seed = random.random()
			tfp = self.statistics['timer_follow_prob']
			if seed <= (tfp['f+rl'] + tfp['f']):
				could_get, follow = self.getNewFollowFromDB(alreadyFollowed)
				if not could_get:
					errors += 1
					self.write("\r\t" + str(counter + 1) + " of " + str(num_follows) + ": " + str(num_f) + " f, " + str(num_frl) + " f+rl, " + str(num_f4f) + " f4f, " + str(num_f4frl) + " f4f+rl" + " ( " + str(errors) + " errors )")
					continue
				alreadyFollowed.append(follow)
				if seed <= tfp['f+rl']:
					self.followAndRandomLike(follow, isDump)
					num_frl += 1
				else:
					self.justFollow(follow, isDump)
					num_f += 1
			else:
				could_get, follow = self.getNewFollowFromSearch(alreadyFollowed)
				if not could_get:
					errors += 1
					self.write("\r\t" + str(counter + 1) + " of " + str(num_follows) + ": " + str(num_f) + " f, " + str(num_frl) + " f+rl, " + str(num_f4f) + " f4f, " + str(num_f4frl) + " f4f+rl" + " ( " + str(errors) + " errors )")
					continue
				alreadyFollowed.append(follow)
				if seed <= (tfp['f+rl'] + tfp['f'] + tfp['f4f']):
					self.justFollow(follow, isDump, isF4F = True)
					num_f4f += 1
				else:
					self.followAndRandomLike(follow, isDump, isF4F = True)
					num_f4frl += 1
			self.write("\r\t" + str(counter + 1) + " of " + str(num_follows) + ": " + str(num_f) + " f, " + str(num_frl) + " f+rl, " + str(num_f4f) + " f4f, " + str(num_f4frl) + " f4f+rl" + " ( " + str(errors) + " errors )")
		self.write("\n")


	def getNewFollowFromDB(self, alreadyFollowed):
		blogname = self.getAccountName()
		while True:
			follow = self.dbManager.getFollows(blogname,1)
			if follow == []:
				self.write("Error: no follow in DB!\n")
				return False, None
			if not follow[0] in alreadyFollowed:
				return True, follow[0]
			else:
				self.deleteFollowFromDB(follow[0])


	def deleteFollowFromDB(self, follow):
		blogname = self.getAccountName()
		args = (follow,blogname)
		self.dbManager.delete("Follow",args)


	def addFollowToDB(self, follow):
		blogname = self.getAccountName()
		args = (follow,blogname,int(time.time()))
		self.dbManager.add("Follow",args)


	def getNewFollowFromSearch(self, alreadyFollowed):
		max_errors = 10
		num_errors = 0
		blogname = self.getAccountName()
		while True:
			tag = self.randomF4F()
			follow = self.getTaggedRecentInsta(tag, 1)
			if follow == None:
				self.write("Error: 'None' response for find recent media tagged '" + tag + "'\n")
				num_errors += 1
				if num_errors >= max_errors:
					self.write("Error: max num errors reached for getNewFollowFromSearch!\n")
					return False, None
				else:
					self.waitInsta(little=True)
			elif follow == []:
				self.write("Error: cannot find recent media tagged '" + tag + "'\n")
				return False, None
			elif not follow[0]['userID'] in alreadyFollowed:
				return True, follow[0]['userID']
			else:
				num_errors += 1
				if num_errors >= max_errors:
					self.write("Error: max num errors reached for getNewFollowFromSearch!\n")
					return False, None
				else:
					self.waitInsta(little=True)



	def followAndRandomLike(self, follow, isDump, isF4F = False):
		if isDump:
			if isF4F:
				self.write("f4f and random like:\n")
			else:
				self.write("follow and random like:\n")
			self.write(str(follow) + "\n") 
		self.followInsta(follow)
		self.randomMediaLikeInsta(follow)
		if isF4F:
			self.addStatistics(follow, 'f4f+rl')
		else:
			self.deleteFollowFromDB(follow)
			self.addStatistics(follow, 'f+rl')


	def justFollow(self, follow, isDump, isF4F = False):
		if isDump:
			if isF4F:
				self.write("just f4f:\n")
			else:
				self.write("just follow:\n")
			self.write(str(follow) + "\n")
		self.followInsta(follow)
		if isF4F:
			self.addStatistics(follow, 'f4f')
		else:
			self.deleteFollowFromDB(follow)
			self.addStatistics(follow, 'f')


	def followInsta(self, blog2follow):
		self.post_insta_request({'action': 'follow_insta', 'user': str(blog2follow)})
		self.followingList.append(blog2follow)
		self.waitInsta()


	def unfollowSocial(self, blog2unfollow):
		self.post_insta_request({'action': 'unfollow_insta', 'user': str(blog2unfollow)})
		self.waitInsta()


	def likeSocial(self, num_likes, isDump):
		blogname = self.getAccountName()
		num_l4l = 0
		num_l4lf = 0
		num_l4lrl = 0
		num_l4lfrl = 0
		num_lfrl = 0
		num_lf = 0
		num_lrl = 0
		num_l = 0
		num_rl = 0
		errors = 0
		for counter in range(0,num_likes):
			seed = random.random()
			tfl = self.statistics['timer_like_prob']
			if seed <= (tfl['l4l'] + tfl['l4l+f'] + tfl['l4l+rl'] + tfl['l4l+f+rl']):
				tag = self.randomL4L()
				self.write("\tGet recent media with tag '" + tag + "'.. ")
				media = self.getTaggedRecentInsta(tag,1)
				if media == None:
					errors += 1
					self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
					continue
				elif media == []:
					self.write("no recent tag for '" + tag + "'!\n")
					errors += 1
					self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
					continue
				else:
					self.write("ok\n")
				media = media[0]
				if seed <= tfl['l4l']:
					self.justLike(media, isDump, isL4L = True)
					num_l4l += 1
				elif seed <= tfl['l4l'] + tfl['l4l+f']:
					self.likeAndFollow(media, isDump, isL4L = True)
					num_l4lf += 1
				elif seed <= tfl['l4l'] + tfl['l4l+f'] + tfl['l4l+rl']:
					self.likeAndRandomLike(media, isDump, isL4L = True)
					num_l4lrl += 1
				else:
					self.likeFollowAndRandomLike(media, isDump, isL4L = True)
					num_l4lfrl += 1
			elif seed <= (1 - tfl['rl']):
				seed -= (tfl['l4l'] + tfl['l4l+f'] + tfl['l4l+rl'] + tfl['l4l+f+rl'])
				tag = self.randomTag()
				if tag == "":
					self.write("cannot get random tag!\n")
					errors += 1
					self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
					continue
				self.write("\tGet recent media with tag '" + tag + "'.. ")
				media = self.getTaggedRecentInsta(tag,1)
				if media == None:
					errors += 1
					self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
					continue
				elif media == []:
					self.write("no recent tag for '" + tag + "'!\n")
					errors += 1
					self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
					continue
				else:
					self.write("ok\n")
				media = media[0]
				if seed <= tfl['l+f+rl']:
					self.likeFollowAndRandomLike(media, isDump)
					num_lfrl += 1
				elif seed <= tfl['l+f+rl'] + tfl['l+f']:
					self.likeAndFollow(media, isDump)
					num_lf += 1
				elif seed <= tfl['l+f+rl'] + tfl['l+f'] + tfl['l+rl']:
					self.likeAndRandomLike(media, isDump)
					num_lrl += 1
				else:
					self.justLike(media, isDump)
					num_l += 1
			else:
				could_get, user = self.getNewFollowFromDB([])
				if not could_get:
					self.write("no follow in DB!\n")
					errors += 1
					self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
					continue
				self.randomLike(user, isDump)
				num_rl += 1
			self.write("\t" + str(counter + 1) + " of " + str(num_likes) + ": " + str(num_l4l) + " l4l, " + str(num_l4lf) + " l4l+f, " + str(num_l4lrl) + " l4l+rl, " + str(num_l4lfrl) + " l4l+f+rl, " + str(num_lfrl) + " l+f+rl, " + str(num_lf) + " l+f, " + str(num_lrl) + " l+rl, " + str(num_l) + " l, " + str(num_rl) + " rl ( " + str(errors) + " errors )\n")
		self.write("\n")


	def justLike(self, media, isDump, isL4L = False):
		self.likeInsta(media['mediaID'])
		if isL4L:
			self.addStatistics(media['userID'], 'l4l')
			if isDump:
				self.write("l4l\n")
		else:
			self.addStatistics(media['userID'], 'l')
			if isDump:
				self.write("l\n")


	def likeAndFollow(self, media, isDump, isL4L = False):
		self.likeInsta(media['mediaID'])
		self.followInsta(media['userID'])
		if isL4L:
			self.addStatistics(media['userID'], 'l4l+f')
			if isDump:
				self.write("l4l+f\n")
		else:
			self.addStatistics(media['userID'], 'l+f')
			if isDump:
				self.write("l+f\n")


	def likeAndRandomLike(self, media, isDump, isL4L = False):
		self.likeInsta(media['mediaID'])
		self.randomMediaLikeInsta(media['userID'])
		if isL4L:
			self.addStatistics(media['userID'], 'l4l+rl')
			if isDump:
				self.write("l4l+rl\n")
		else:
			self.addStatistics(media['userID'], 'l+rl')
			if isDump:
				self.write("l+rl\n")


	def likeFollowAndRandomLike(self, media, isDump, isL4L = False):
		self.likeInsta(media['mediaID'])
		self.followInsta(media['userID'])
		self.randomMediaLikeInsta(media['userID'])
		if isL4L:
			self.addStatistics(media['userID'], 'l4l+f+rl')
			if isDump:
				self.write("l4l+f+rl\n")
		else:
			self.addStatistics(media['userID'], 'l+f+rl')
			if isDump:
				self.write("l+f+rl\n")


	def randomLike(self, userID, isDump):
		self.randomMediaLikeInsta(userID)
		self.deleteFollowFromDB(userID)
		self.addStatistics(userID, 'rl')
		if isDump:
			self.write("rl\n")


	def likeInsta(self, postID):
		self.post_insta_request({'action': 'like_insta', 'postID': str(postID)})
		self.waitInsta()


	def getFollowersSocial(self, user=None, maxNum=None):
		""" must return dict with users (dict with name for each user) e total_users (total number of Followers of the blog) """
		params = {'action': 'get_followers_insta'}
		if user != None:
			params['userID'] = str(user)
		if maxNum != None:
			params['maxNum'] = maxNum
		followers = self.post_insta_request(params)
		if user == None:
			self.write("\r\t\tGet Followers List.. " + str(len(followers)) + "/" + str(self.data['followers']) + "\n")
		return followers


	def getFollowingsSocial(self, user=None):
		""" must return a list with ID for each user """
		if user == None:
			following = self.post_insta_request({'action': 'get_followings_insta'})
		else:
			following = self.post_insta_request({'action': 'get_followings_insta', 'userID': str(user)})
		self.write("\r\t\tGet Following List.. " + str(len(following)) + "/" + str(self.data['following']) + "\n")
		return following


	def getTaggedPopularInsta(self, tag, maxNum):
		return self.post_insta_request({'action': 'getHashtagFeed_insta', 'tag': tag, 'isPopular': True, 'maxNum': maxNum})


	def getTaggedRecentInsta(self, tag, maxNum):
		return self.post_insta_request({'action': 'getHashtagFeed_insta', 'tag': tag, 'isPopular': False, 'maxNum': maxNum})


	def getMediaLikersInsta(self, postID, maxNum):
		return self.post_insta_request({'action': 'get_likers_insta', 'postID': str(postID), 'maxNum': maxNum})


	def getMediaCommentsInsta(self, postID, maxNum):
		return self.post_insta_request({'action': 'get_comments_insta', 'postID': str(postID), 'maxNum': maxNum})


	def getMediaInsta(self, user, maxNum):
		return self.post_insta_request({'action': 'get_insta_media', 'user': str(user), 'maxNum': maxNum})


	def randomMediaLikeInsta(self, user, howMany=1):
		media = self.getMediaInsta(user, self.MAX_RETRIEVED_MEDIA)
		if media == None:
			self.write("\n\tError: randomMediaLikeInsta media=None for user '" + str(user) + "'\n")
		elif media == []:
			self.write("\n\tError: randomMediaLikeInsta media=[] for user '" + str(user) + "'\n")
		else:
			self.waitInsta(little=True)
			for count in range(0,howMany):
				key = random.randint(0, len(media)-1)
				self.likeInsta(media.pop(key))


	def getIdByUsernameInsta(self, user):
		resp = self.post_insta_request({'action': 'get_id_by_username', 'user': str(user)})
		if resp == None:
			return None
		else:
			return resp[0] 


	def post_insta_request(self, post_data, firstTime=False):
		post_data['username'] = self.username
		post_data['password'] = self.password
		try:
			return self.send_and_check_request_insta(post_data, firstTime)
		except HTTPError as e:
			if firstTime:
				print e
			else:
				self.write(str(e) + "\n")
			return None


	def send_and_check_request_insta(self, post_data, firstTime=False):
		try:
			resp = requests.post(Settings.PATH_TO_SERVER_INSTA + Settings.RECEIVER_INSTA, data = post_data)
			if resp.status_code == 200:
				try:
					parsed = resp.json()
					if 'Error' in parsed:
						if firstTime:
							print "Error: " + str(parsed['Error'])
						else:
							self.write("Error: " + str(parsed['Error']) + "\n")
						return None
					else:
						return parsed['Result']
				except ValueError as e:
					if firstTime:
						print "ValueError:\n" + str(resp.content)
					else:
						self.write("ValueError:\n")
						self.write(str(resp.content) + "\n")
					return None
			else:
				resp.raise_for_status()
		except ConnectionError as e:
			if firstTime:
				print "ConnectionError:\n" + str(e)
			else:
				self.write("ConnectionError:\n")
				self.write(str(e) + "\n")
			return None 
		except Timeout as e:
			if firstTime:
				print "Timeout Error:\n" + str(e)
			else:
				self.write("Timeout Error:\n")
				self.write(str(e) + "\n")
			return None


	def logAccount(self):
		self.write("\nLog information for " + self.getAccountName() + ":\n")
		self.write("ID: " + str(self.account_id) + "\n")
		self.write("strID: " + self.strID + "\n")
		self.write("mail: " + self.mail + "\n")
		self.write("type: " + str(self.account_type) + "\n")
		self.write("username: " + self.username + "\n")
		self.write("password: " + self.password + "\n")
		self.write("tags:\n")
		for tag in self.tags:
			self.write("\t" + tag + "\n")
		self.write("blogs:\n")
		for blog in self.blogs:
			self.write("\t" + blog + "\n")
		self.write("private: " + str(self.data['private']) + "\n")
		self.write("following: " + str(self.data['following']) + "\n")
		self.write("followers: " + str(self.data['followers']) + "\n")
		self.write("messages: " + str(self.data['messages']) + "\n")
		self.write("name: " + self.data['name'] + "\n")
		self.write("posts: " + str(self.data['posts']) + "\n")
		self.write("usertags: " + str(self.data['usertags']) + "\n")
		# self.write("url: " + self.data['url'] + "\n")
		self.write("num_post_xd: " + str(self.num_post_xd) + "\n")
		self.write("num_follow_xd: " + str(self.num_follow_xd) + "\n")
		self.write("num_like_xd: " + str(self.num_like_xd) + "\n")
		self.write("num_post_xt: " + str(self.num_post_xt) + "\n")
		self.write("num_follow_xt: " + str(self.num_follow_xt) + "\n")
		self.write("num_like_xt: " + str(self.num_like_xt) + "\n")
		self.write("status: " + str(self.status) + "\n")
		pprint(self.statistics)







