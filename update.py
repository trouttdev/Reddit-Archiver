#!/usr/bin/python

import RedditUtils
import time

username = 'USERNAME'
password = 'PASS'

start = time.time()

r = RedditUtils.RedditUtils(username, password)
r.getThreads()
r.updateSubscriberCount()

print("Exec time: " + str(time.time()-start))