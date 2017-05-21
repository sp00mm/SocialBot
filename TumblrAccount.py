import pytumblr

class TumblrAppAccount(Account):


	def __init__(self, accounts, account):
		super().__init__(accounts, account['ID'], account['Mail'], account['Type'])
		self.token = account['Token']
		self.token_secret = account['Token_Secret']



class TumbrlAccount(Account):


	client = None
	clientInfo = None
    percF4F = 1/2
    percNotF4F = 1/2


	def __init__(self, accounts, account, tags, blogs):
		super().__init__(accounts, account['ID'], account['Mail'], account['Type'])
		self.token = account['Token']
		self.token_secret = account['Token_Secret']
		self.app_account = accounts.app_accounts[str(account['App_Account'])]
		self.tags = tags2list(tags)
		self.blogs = blogs2list(blogs)
		self.data = self.initData()
		self.num_post_xd = int(account['PostXD'])
		self.num_follow_xd = int(account['FollowXD'])
		self.num_like_xd = int(account['LikeXD'])
		self.num_post_xt = int(account['PostXT'])
		self.num_follow_xt = int(account['FollowXT'])
		self.num_like_xt = int(account['LikeXT'])
		self.setup_clients()	
		status = self.STATUS_STOP


	def getAccountName(self):
		return self.data['blogname']


	def getSocialName(self):
		return "tumblr"

	
	def setup_clients(self):
	    self.client = pytumblr.TumblrRestClient(
	        self.app_account.token,
	        self.app_account.token_secret,
	        self.token,
	        self.token_secret,
	    )
	    self.clientInfo = pytumblr.TumblrRestClient(
	        self.app_account.token,
	        self.app_account.token_secret,
	        self.token,
	        self.token_secret,
	    )


	def initData(self):
	    return { 'username': "not available",
	             'likes': "not available",
	             'following': "not available",
	             'followers': "not available",
	             'messages': "not available",
	             'blogname': "not available",
	             'posts': "not available",
	             'queue': "not available",
	             'url': "not available"
	             }


	def checkResponse(self, res):
	    "Check if there is an error in response"
	    if "meta" in res:
	        self.write("Error: " + res["meta"]["msg"] + " (status " + str(res["meta"]["status"]) + ")\n")
	        return False
	    else:
	        return True


	def updateBlog(self):
		try:
            response = self.clientInfo.info()
            if self.checkResponse(response):
                self.data['likes'] = response["user"]["likes"]
                self.data['following'] = response["user"]["following"]
                self.data['followers'] = response["user"]["blogs"][0]["followers"]
                self.data['messages'] = response["user"]["blogs"][0]["messages"]
                self.data['posts'] = response["user"]["blogs"][0]["posts"]
                self.data['queue'] = response["user"]["blogs"][0]["queue"] 
                if self.data['username'] == "not available":
                    self.data['username'] = response["user"]["name"]
                    self.data['blogname'] = response["user"]["blogs"][0]["name"]
                    self.data['url'] = response["user"]["blogs"][0]["url"]
                    self.accounts.matches[response["user"]["blogs"][0]["name"]] = self.account_id
            else:
            	self.write("Error: cannot update " + self.getAccountName() + ".\n")
        except ServerNotFoundError,msg:
            self.write("\tUpdate Error: " + str(msg) + "\n")
        except socket.error, msg:
            self.write("\tUpdate Error: " + str(msg) + "\n")
        except Exception, msg:
            self.write("\tUpdate Error on client.info(): " + str(msg) + "\n")


	def updateBlogData(self, timersTime):
	    self.write("\tUpdate " + self.data['blogname'] + ".. ")
	    post_data_up = {"action": "update_blog_data", 
	        "ID": self.account_id,
	        "Likes": self.data['likes'],
	        "Following": self.data['following'],
	        "Followers": self.data['followers'],
	        "Posts": self.data['posts'],
	        "Messages": self.data['messages'],
	        "Queue": self.data['queue'],
	        "Name": self.data['blogname'],
	        "Url": self.data['url']
	        }
	    if (self.strID + "-post") in self.timersTime:
	        post_data_up["Deadline_Post"] = self.timersTime[self.strID + "-post"]
	    if (self.strID + "-follow") in self.timersTime:
	        post_data_up["Deadline_Follow"] = self.timersTime[self.strID + "-follow"]
	    if (self.strID + "-like") in self.timersTime:
	        post_data_up["Deadline_Like"] = self.timersTime[self.strID + "-like"]
	    up_res = post_request(post_data_up)
	    if up_res != None:
	        self.updateStatus()
	        self.write("end of update.\n")


	def updateUpOp(self, newAccount):
		need_setup_clients = False 
		if self.app_account != self.app_accounts[str(newAccount['App_Account'])]:
			need_setup_clients = True 
        	self.app_account = self.app_accounts[str(newAccount['App_Account'])]
        if self.token != newAccount['Token']:
        	need_setup_clients = True
        	self.token = newAccount['Token']
        if self.token_secret != newAccount['Token_Secret']:
        	need_setup_clients = True
        	self.tokenSecret = newAccount['Token_Secret']
        if need_setup_clients:
            self.setup_clients()
        super().updateUpOp(newAccount)


    def copyBlog(self, blog_to_copy, limitMax, counter):
	    self.write("Done!\nLaunching procedure..\n",True)
	    self.writeln("Start to copy " + blog_to_copy + " in " + self.getAccountName() + "..\n",True)
	    my_account = matches[my_blog]
	    total_posts = (self.client.blog_info(blog_to_copy))['blog']['posts']
	    if total_posts > limitMax:
	        total_posts = limitMax
	    # counter = 0
	    howmany = 20
	    while counter < total_posts:
	        howmanythis = howmany
	        if (counter + howmany) > total_posts:
	            howmanythis = total_posts - counter
	        posts = (self.client.posts(blog_to_copy, limit = howmanythis, offset = counter))['posts']
	        for post in posts:
	            self.write("\tReblogging post " + str(counter+1) + "/" + str(total_posts) + ".. ",True)
	            if post['type'] != "photo":
	                self.write("Not reblogged: it's a " + post['type'] + " post!\n",True)
	                counter = counter + 1
	                continue
	            response = self.client.reblog(self.getAccountName(), id=post['id'], reblog_key=post['reblog_key'], tags = self.tags, type = "photo")
	            if self.checkResponse(response):
	                self.write("Done!\n",True)
	            counter = counter + 1


	def updateMatchesStatistics(self):
		pass


	def calc_time_post_follow(self):
	    self.write("\tCalcule timers for " + self.getAccountName() + ":\n")
	    self.timer_post = int((24*60*60/(self.num_post_xd/self.num_post_xt))+0.5)
	    self.write("\t\tpost every " + seconds2timeStr(self.timer_post) + "\n")
	    self.timer_follow = int((24*60*60/(self.num_follow_xd/self.num_follow_xt))+0.5)
	    self.write("\t\tfollow every " + seconds2timeStr(self.timer_follow) + "\n")
	    self.timer_like = int((24*60*60/(self.num_like_xd/self.num_like_xt))+0.5)
	    self.write("\t\tlike every " + seconds2timeStr(self.timer_like) + "\n")      


	def checkNeedNewFollows(self):
		bn = self.getAccountName()
		# Check num Follows
        follows = self.dbManager.countFollow(bn)
        self.write("\t   check #follow.. ")
        if follows >= (self.num_follow_xt * self.percNotF4F):
            self.write("found " + str(follows) + ", ok\n")
        else:
            self.write("found " + str(follows) + ", needed at least " + str(self.num_follow_xt * self.percNotF4F) + "\n")
            self.searchByTag((self.num_follow_xt * self.percNotF4F)-follows)
        # Check num F4F
        f4f = self.dbManager.countFollow("f4f-tumblr")
        self.write("\t   check #f4f-tumblr.. ")
        if f4f >= (self.num_follow_xt * self.percF4F):
            self.write("found " + str(f4f) + ", ok\n")
        else:
            self.write("found " + str(f4f) + ", needed at least " + str(self.num_follow_xt * self.percF4F) + "\n")
            tag = self.randomF4F()
            self.searchByTag((self.num_follow_xt * self.percF4F)-f4f, blogname="f4f-tumblr", tag=tag)


	def search_post(self, num_post=-1):
		blogname = self.getAccountName()
	    if num_post == -1:
	        num_post = self.num_post_xt
	    num_following_blogs = len(self.blogs)
	    postXblog = 0
	    if num_following_blogs >= num_post:
	        postXblog = 1
	    else:
	        postXblog = int(num_post/num_following_blogs)+1
	    self.write("\t      Getting posts..\n")
	    follows = self.dbManager.countFollow(blogname)
	    need_follow = False
	    if follows <= (self.num_follow_xt * self.percNotF4F):
	        need_follow = True
	    for following_blog in self.blogs:
	        counter = 0
	        offset_posts = 0
	        self.write("\t         post from " + following_blog + ".. ")
	        new_follows = []
	        id_posts = []
	        while counter < postXblog:
	            try:
	                response = self.clientInfo.posts(following_blog, type = "photo", notes_info = need_follow, offset = offset_posts)  # , limit = postXblog*5
	                if response['posts'] == []:
	                    break
	                for post in response['posts']:
	                    try:
	                        if (not post['liked']) and (not post['id'] in id_posts):
	                            id_post = post['id']
	                            id_posts.append(id_post)
	                            reblog_key = post['reblog_key']
	                            args = (id_post,reblog_key,following_blog,blogname,int(time.time()))
	                            self.client.like(id_post,reblog_key)
	                            self.dbManager.add("PostsLikes",args)
	                            counter_notes = 0
	                            if need_follow:
	                                for note in post['notes']:
	                                    if not note['followed']:
	                                        new_follows.append(note['blog_name'])
	                                        counter_notes += 1
	                                    if counter_notes >= (self.num_follow_xt * self.percNotF4F):
	                                        break
	                            counter += 1
	                    except KeyError,msg:
	                        self.write("\n\t         Error (keyerror) on searchpost: " + str(msg) + "\n")
	                        # pprint(post)
	                        counter += 1
	                    offset_posts += 1
	                    self.clearline()
	                    self.write("\t         post from " + following_blog + ".. " + str(counter) + "/" + str(postXblog) + "(scaled " + str(offset_posts) + "/" + str(response['blog']['posts']) + ")")
	                    if counter >= postXblog:
	                        break
	            except Exception,msg:
	                self.write("\n\t         Error Exception.. " + str(msg) + "\n") 
	                break
	        for new_follow in new_follows:
	            args = (new_follow,blogname,int(time.time()))
	            self.dbManager.add("Follow",args)
	        self.write("\r\t         post from " + following_blog + ".. Done! (" + str(counter))
	        if counter > 1:
	            self.write(" posts")
	        else:
	            self.write(" post")
	        if need_follow:
	            self.write(" and " + str(len(new_follows)) + " follow)\n")
	        else:
	            self.write(")\n")
	        self.updateStatistics()


	def searchByTag(self, num_tags,blogname=None,tag=None):
		if tag == None:
			tag = self.randomTag()
		if blogname == None:
			blogname = self.getAccountName
	    counter = 0
	    self.write("\t      Getting follows..\n")
	    new_follows = []
	    self.write("\t         posts tagged " + tag + ".. ")
	    timestamp = int(time.time())
	    try:
	        while counter < num_tags:
	            response = self.clientInfo.tagged(tag,before=timestamp)
	            for post in response:
	                try:
	                    if not post['followed']:
	                        new_follows.append(post['blog_name'])
	                        counter += 1
	                        self.write("\r\t         posts tagged " + tag + ".. " + str(counter) + "/" + str(num_tags))
	                    timestamp = post['timestamp']
	                except KeyError,msg:
	                    self.write("\n\t         Error (keyerror) on search_by_tag: " + str(msg) + "\n")
	                    counter += 1
	                if counter >= num_tags:
	                    break
	        for new_follow in new_follows:
	            args = (new_follow,blogname,int(time.time()))
	            self.dbManager.add("Follow",args)
	        self.write("\r\t         posts tagged " + tag + ".. Done! (" + str(counter) + " follow)\n")
	    except Exception,msg:
	        self.write("\n\t         Error Exception\n")
	    self.updateStatistics()


	def postSocial(self, post):
		self.client.reblog(self.getAccountName(), id=post['id'], reblog_key=post['reblogKey'], tags = self.tags, type = "photo", caption="")


	def followSocial(self, num_follows, isDump):
		counter = 0
		blogname = self.getAccountName()
		# Follow
	    follows = self.dbManager.getFollows(blogname,int(num_follows * self.percNotF4F))
	    counter = self.followSocialBlogs(follows, blogname, isDump, counter, num_follows)
	    # F4F
	    sn = self.getSocialName()
	    f4fs = self.dbManager.getFollows("f4f-" + sn,num_follows - int(num_follows * self.percNotF4F))
		self.followSocialBlogs(f4fs, "f4f-" + sn, isDump, counter, num_follows)


	def followSocialBlogs(self, toFollow, blogname, isDump, counter, num_follows):
		if isDump:
	        print toFollow
	    for follow in toFollow:
	        try:
	            if isDump:
	                print follow
	            self.followTumblr(follow)
	            args = (follow,blogname)
	            self.dbManager.delete("Follow",args)
	            counter += 1
	            self.write("\r\tfollowed " + str(counter) + "/" + str(num_follows))
	        except Exception,msg:
	            self.write("\n\tError: exception on " + blogname + " following\n")
	    return counter


	def followTumblr(self, blog2follow):
		self.client.follow(blog2follow)
		self.followingList.append(blog2follow)


	def unfollowSocial(self, blog2unfollow):
	    self.client.unfollow(blog2unfollow)


	def likeSocial(self, num_likes):
		tag = self.random_tag()
	    try:
	    	response = self.getTaggedTumblr(tag)
	        counter = 0
	        for post in response:
	            try:
	                if (not post['liked']) and (not post['followed']):
	                    self.likeTumblr(post['id'], post['reblog_key'])
	                    counter += 1
	                    self.write("\r\tliked " + str(counter) + "/" + str(num_likes))
	            except KeyError,msg:
	                self.write("\n\tError (keyerror) on like: " + str(msg) + "\n")
	                break
	            if counter >= num_likes:
	                break
	        self.write("\r\tliked " + str(counter) + " posts!\n")
	    except Exception,msg:
	        self.write("Error Exception\n")


	def likeTumblr(self, post_id, reblog_key):
		self.client.like(post_id, reblog_key)


	def getFollowersSocial(self, user=None):
		""" must return dict with users (list with ID for each user) """
		shouldGetNew = True
	    counterFollowers = 0
	    numErrors = 0
	    blogname = self.getAccountName()
	    followerNames = []
	    while shouldGetNew:
	        try:
	            followers = self.client.followers(blogname,offset=counterFollowers)
	            if followers['users'] == []:
	                break
	            for follower in followers['users']:
	                counterFollowers += 1
	                followerNames.append(follower['name'])
	            if counterFollowers >= followers['total_users']:
	                shouldGetNew = False
	            self.write("\r\tGet Followers List.. " + str(counterFollowers) + "/" + str(followers['total_users']) + " ")
	        except KeyError, msg:
	            numErrors += 1
	            if numErrors > 30:
	                shouldGetNew = False
	            else: 
	                time.sleep(2)
	    if numErrors > 30:
	        self.write("Error! (> 30 errors)\n")
	    else:
	        self.write("Done!\n")
	    return followerNames


	def getFollowingsSocial(self, user=None):
		""" must return a list with ID for each user """
	    shouldGetNew = True
	    counterFollowing = 0
	    numErrors = 0
	    blogname = self.getAccountName()
	    followingNames = []
	    while shouldGetNew:
	        try:
	        	following = self.client.following(offset=counterFollowing)
	            if following['blogs'] == []:
	                break
	            for follow in following['blogs']:
	                counterFollowing += 1
	                followingNames.append(follow['name'])
	            if counterFollowing >= following['total_blogs']:
	                shouldGetNew = False
	            self.write("\r\tGet Following List.. " + str(counterFollowing) + "/" + str(following['total_blogs']) + " ")
	        except KeyError, msg:
	            numErrors += 1
	            if numErrors > 30:
	                shouldGetNew = False
	            else: 
	                time.sleep(2)
	    if numErrors > 30:
	        self.write("Error! (> 30 errors)\n")
	    else:
	        self.write("Done!\n")
	    return followingNames


	def getTaggedTumblr(self, tag):
	    return self.clientInfo.tagged(tag)