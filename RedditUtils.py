import sys
import urllib2
import urllib
import simplejson
import MySQLdb
import cookielib
import time
import httplib
import datetime

class RedditUtils:

    """
    A set of utilities for grabbing and using data from Reddit.com
    """
    conn = MySQLdb.connect (host = "localhost", user="root", passwd = "root", db = "reddits")
    c = conn.cursor()

    def __init__(self,username,password):
        """
        Get a login cookie using the Reddit API
        """
        print "Reddit Utils online!"
        self.cookie = self.__getCookie(username, password)

    def __getCookie(self, username, password):
        """
        Obtain the cookie and return it
        """
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        login_data = urllib.urlencode({'user' : username, 'passwd' : password})
        opener.open('http://www.reddit.com/api/login/'+username, login_data)
        print "Cookie obtained for user " + username
        return opener

    def __getStatusCode(self,subreddit):
        """
        Get the status code for a loaded page.
        Useful for finding 404's, 403's and 503's
        """
        url = "www.reddit.com"
        subreddit += ".json" #use json for quicker page pulls
        try:
            conn = httplib.HTTPConnection(url)
            conn.request("HEAD",subreddit)
            return conn.getresponse().status
        except Exception,e:
            print e
            try:
                #give it one more shot...
                conn = httplib.HTTPConnection(url)
                conn.request("HEAD",subreddit)
                return conn.getresponse().status
            except Exception,e:
                print e
                print "Error gettting response code. URL: " + subreddit
                return 0



    def getAllReddits(self):
        """
        Get all available subreddits with various information about them
        """
        print "Getting all reddits"
        try:
            data = self.cookie.open("http://www.reddit.com/reddits/.json")
            loadedPage = simplejson.load(data)
            loadedData = loadedPage['data']['children']
            after = loadedPage['data']['after']
            redditCount = 0
            while str(after) != 'null':
                if str(after) != 'null':
                    try:
                        self.c.execute("""INSERT INTO last VALUES (%s)""",after)
                    except Exception,e:
                        print e
                        print "Unable to insert reddit into last reddit table."
                for singleData in loadedData:
                    singleData = singleData['data']

                    url = singleData['url']
                    nsfw = str(int(singleData['over18']))
                    display_name = singleData['display_name']
                    subscribers = singleData['subscribers']


                    try:
                        row = self.c.execute("""SELECT * FROM reddits WHERE url = %s""",url)
                    except Exception,e:
                        row = 1
                        print e
                        print "Unable to execute select statement with given URL: " + url
                    if not row:
                        try:
                            self.c.execute("""INSERT INTO reddits (name,url,nsfw,subscribers) VALUES (%s,%s,%s,%s)""",(display_name,url,nsfw,subscribers))
                        except Exception,e:
                            print e
                            print "Unable to insert new reddit into reddits table"
                        redditCount += 1
                    else:
                        print "Reddit at url " + url + " already in DB"
                data = self.cookie.open("http://www.reddit.com/reddits/.json?after="+after)
                loadedPage = simplejson.load(data)
                loadedData = loadedPage['data']['children']
                after = loadedPage['data']['after']
                print redditCount
                if str(after) == 'null':
                    print "All done at " + redditCount + " reddits."
                time.sleep(.2)
        except Exception,e:
            print e
            print "Error getting reddits with given URL"

    def getNewReddits(self, days):
        """
        Grab any new subreddits made in the last x days and insert them into the database
        """
        print "Getting new reddits from the last " + str(days) + " days"
        seconds = days * 86400 #convert days to second to use UTC time stamps
        try:
            data = self.cookie.open("http://www.reddit.com/reddits/new/.json")
            loadedPage = simplejson.load(data)
            loadedData = loadedPage['data']['children']
            after = loadedPage['data']['after']
            count = 0
            time_flag = True
            while str(after) != 'null' and time_flag:
                for singleData in loadedData:

                    url = singleData['data']['url']
                    nsfw = str(int(singleData['data']['over18']))
                    displayName = singleData['data']['display_name']
                    subscribers = singleData['data']['subscribers']

                    time_flag = (time.time() - singleData['data']['created_utc']) <= seconds
                    row = self.c.execute("""SELECT * FROM reddits WHERE url = %s""",url)
                    if time_flag and row == 0:
                        try:
                            self.c.execute("""INSERT INTO reddits (name,url,nsfw,subscribers) VALUES (%s,%s,%s,%s)""",(displayName,url,nsfw,subscribers))
                        except:
                            raise
                        count += 1
                    else:
                        print "Reddit at url " + singleData['data']['url'] + " already in DB"
                data = self.cookie.open("http://www.reddit.com/reddits/new/.json?after="+after)
                loadedPage = simplejson.load(data)
                loadedData = loadedPage['data']['children']
                after = loadedPage['data']['after']
                print count
                time.sleep(.2)
            print "All done after " + str(count) + " new reddits added."
        except Exception,e:
            print e
            print "Unable to get new reddits. Likely a URL issue."

    def pruneDB(self):
        """"
        Remove reddits that no longer exist
        """
        print "Pruning database..."
        try:
            rows = self.c.execute("""SELECT name,url,nsfw, subreddit_id FROM reddits""")
            results = self.c.fetchall()
            prune_count = 0
            total_count = 0
            for result in results:
                total_count += 1
                percent = int(total_count*100/rows)
                name = result[0]
                url = result[1]
                nsfw = result[2]
                id = result[3]
                code = self.__getStatusCode(url)
                if code == 302:
                    #print str(url) + " is missing. Code " + str(code)
                    try:
                        row = self.c.execute("""SELECT * FROM missing WHERE url = %s""",url)
                    except Exception,e:
                        print e
                        print "Error finding row in missing table"
                        if row == 0:
                            try:
                               self.c.execute("""INSERT INTO missing VALUES(%s, %s, %s""",(name,url,nsfw))
                            except Exception,e:
                                print e
                                print "Error inserting missing row into missing table"
                            try:
                                self.c.execute("""DELETE FROM reddits WHERE subreddit_id = %s""",id)
                            except Exception,e:
                                print e
                                print "Error deleteing row from reddits"
                    prune_count += 1
                sys.stdout.write("\rPruning reddits... %(percent)2d%%" % {'percent':percent})
                sys.stdout.flush()
            print ""
            print "Pruning finished. Pruned " + str(prune_count) + " reddits"
        except:
            print "Unable to retrieve reddit URLs"
            raise


    def cleanDB(self):
        #Clean Db of any duplicated and reorder ID's
        print "Cleaning the dataabase"
        self.c.execute("""CREATE TABLE reddits_1 ( subreddit_id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT, name VARCHAR(256), url VARCHAR(256), nsfw TINYINT(1)""")
        self.c.execute("""INSERT INTO reddits_1 (name, url, nsfw) SELECT name, url, nsfw FROM reddits GROUP BY (url)""")
        self.c.execute("""DROP TABLE reddits""")
        self.c.execute("""RENAME TABLE reddits_1 TO reddits""")

    def getThreads(self,getComments = False):
        """
        Get 1the 100 least recently needed to be updated threads
        """
        self.c.execute("""SELECT subreddit_id, url FROM reddits WHERE next_update < %s LIMIT 100""",datetime.datetime.utcnow())
        results = self.c.fetchall()
        count = 0
        print "Getting thread data..."
        for result in results:
            
            subreddit_id = result[0]
            url = "http://www.reddit.com" + result[1] + ".json"

            now = datetime.datetime.utcnow()
            later = now + datetime.timedelta(hours= self.__updateDate(subreddit_id))
            try:
                self.c.execute("""INSERT INTO updates (subreddit_id,last_update) VALUES(%s,%s)""",(subreddit_id, now))
                update_id = self.c.lastrowid
                self.c.execute("""UPDATE reddits SET next_update = %s WHERE subreddit_id = %s""",(later, subreddit_id))
            except Exception,e:
                print e


            try:
                data = self.cookie.open(url)
                loadedPage = simplejson.load(data)
                loadedData = loadedPage['data']['children']

                for singleData in loadedData:
                    count += 1
                    #sys.stdout.write("\rArchiving thread " + str(count))
                    #sys.stdout.flush()
                    title = singleData['data']['title'].encode('utf-8')
                    author = singleData['data']['author'].encode('utf-8')
                    submit_time = time.time() - singleData['data']['created_utc']
                    votes = singleData['data']['ups'] - singleData['data']['downs']
                    comment_count = singleData['data']['num_comments']
                    thread_link = singleData['data']['url'].encode('utf-8')
                    comment_link = "http://www.reddit.com" + singleData['data']['permalink'].encode('utf-8')
                    domain = singleData['data']['domain'].encode('utf-8')
                    nsfw = str(int(singleData['data']['over_18']))

                    try:
                        text = singleData['data']['selftext_html'].encode('utf-8')
                    except Exception,e:
                        text = singleData['data']['selftext_html']
                    try:
                        self.c.execute("""INSERT INTO threads (subreddit_id,title,submit_time,votes,comment_count,thread_link,comment_link,author,domain,update_id,nsfw) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(subreddit_id,title,submit_time,votes,comment_count,thread_link,comment_link,author,domain,update_id,nsfw))
                    except Exception,e:
                        print e

                    thread = self.c.lastrowid
                    try:
                        self.c.execute("""INSERT INTO thread_main_text(thread_id, text) VALUES(%s,%s)""",(thread,text))
                    except Exception,e:
                        print e


                    data = self.cookie.open(comment_link + ".json")
                    loadedPage = simplejson.load(data)
                    loadedData = loadedPage[1]['data']['children']
                    if getComments:
                        self.__addComments(loadedData, 0, thread)
            except Exception,e:
                print e
                print("Error loading url " + str(result[1]))
                if self.__getStatusCode(result[1]) == '403':
                    next = now + datetime.timedelta(days=7)
                else:
                    next = now
                try:
                    self.c.execute("""UPDATE reddits SET next_update = %s WHERE subreddit_id = %s""",(now, subreddit_id))
                except Exception,e:
                    print e
                    print("Error inserting filed URL to updates")
        print("Archived " + str(count) + " threads")


    def __addComments(self, comments, parent, thread):
        for comment in comments:
            author = comment['data']['author'].encode('utf-8')
            votes = comment['data']['ups'] - comment['data']['downs']
            create_time = time.time() - comment['data']['created_utc']
            try:
                comment_text = comment['data']['selftext_html'].encode('utf-8')
            except Exception,e:
                print e
                comment_text = comment['data']['selftext_html']
            try:
                self.c.execute("""INSERT INTO comments(thread_id, parent_id, author, votes, create_time, comment_text) VALUES(%s,%s,%s,%s,%s,%s)""",(thread,parent,author,votes,create_time,comment_text))
            except Exception,e:
                print e


            parent = self.c.lastrowid #new parent id

            if comment['data']['replies'] != "":
                self.__addComments(comment['data']['replies']['data']['children'], parent, thread)

    def updateSubscriberCount(self):
        """
        Update the subscriber count of the 100 least recently updated subreddits
        """
        try:
            rows = self.c.execute("""SELECT subreddit_id,url FROM reddits ORDER BY last_update ASC LIMIT 100""")
            results = self.c.fetchall()
            total_count = 0
            for result in results:
                percent = int(total_count*100/rows)
                id = result[0]
                url = "http://www.reddit.com"+result[1]+"about.json"

                subscribers = self.__updateSubCount(url)

                self.c.execute("""UPDATE reddits SET subscribers = %s, last_update = %s WHERE subreddit_id = %s""",(subscribers, datetime.datetime.utcnow() , id))

                total_count += 1
                sys.stdout.write("\rUpdating Subscribers... %(percent)2d%%" % {'percent':percent})
                sys.stdout.flush()
        except Exception,e:
            print e

    def __updateSubCount(self,url):
        """
        Return the subscriber count for a given reddit
        """
        try:
            data = self.cookie.open(url)
            loadedPage = simplejson.load(data)
            loadedData = loadedPage['data']['subscribers']
            return loadedData
        except Exception,e:
            print "Error at url: " + url
            print e
            return 0

    def __updateDate(self, subreddit):
        """
        Return a number of hours based on the subscriber count of a given reddit
        """
        self.c.execute("""SELECT subscribers FROM reddits WHERE subreddit_id = %s""",subreddit)
        row = self.c.fetchone()
        if row[0] <= 10:
            return 168
        elif row[0] <= 100:
            return 72
        elif row[0] <= 50000:
            return 24
        else:
            return 6