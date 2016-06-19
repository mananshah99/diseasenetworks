'''
toolbox.py

Description: includes functionality used to expedite Twitter API usage

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''

from twitter import *
from datetime import datetime
#from geocoder import Geocoder
# from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
import sys
import csv
import tweepy
import time
from random import randint

class TwitterCrawler():
    consumer_key="ODG4g793wWHmo1n5xObNZM1pD"
    consumer_secret="MZ6UyXZL2QJDCm69sjnFnsjZItcXgGAw65B5wkdFCHZDPOaB7s"
    access_key="904711148-4PCLSbR4x7fPdtpYfLpbbsf2VLgipsGP3Hw8W2jp"
    access_secret="1D388pjK9ljKT3bfJlPpyLSHE4ArcWU0gQeNf40jx7bmt"

    def __init__(self):
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_key, self.access_secret)
        self.api = tweepy.API(self.auth)
        self.api_raw = tweepy.API(self.auth, parser=tweepy.parsers.JSONParser())

    def print_search_rate_limit_status(self):
        print self.api.rate_limit_status()['resources']['search']

    def search_tweets(self, query, count=100):
        try:
            tweets = self.api_raw.search(query, count=count, result_type="recent", include_entities=True, lang="en") # only top 100 results will be shown
            # self.print_search_rate_limit_status()
            return tweets
        except Exception as error_message:
            if error_message.message[0]['code'] == 88:
                while(self.api.rate_limit_status()['resources']['search']['/search/tweets']['remaining'] == 0):
                    print "Sleeping for %d seconds." %(sleep_time)
                    time.sleep(int(sleep_time))
                    self.print_search_rate_limit_status()
            else:
                raise

# Utility function to obtain the configuration for API verification
def getconfig():
    config = {}
    execfile("setup.py", config)
    return config

# Performs a twitter search on a certain query, and returns
# user details as defined by (for user in results)
# user["screen_name"], user["name"], user["location"]
def user_search(query, config, verbose=False):
    # Create Twitter API object
    twitter = Twitter(auth = OAuth("904711148-4PCLSbR4x7fPdtpYfLpbbsf2VLgipsGP3Hw8W2jp",
                    "1D388pjK9ljKT3bfJlPpyLSHE4ArcWU0gQeNf40jx7bmt",
                    "ODG4g793wWHmo1n5xObNZM1pD",
                    "MZ6UyXZL2QJDCm69sjnFnsjZItcXgGAw65B5wkdFCHZDPOaB7s")
                  )

    # Perform a User Search
    results = twitter.users.search(q = '')

    # Print user details in results
    if verbose == True:
        for user in results:
            print "@%s (%s): %s" % (user["screen_name"], user["name"], user["location"])

    return results

# Returns the average tweeting rate for tweets associated with certain terms
def tweet_rate(terms, config, verbose=False):
    created_at_format = '%a %b %d %H:%M:%S +0000 %Y'
    # Create Twitter API object
    twitter = Twitter(auth = OAuth("904711148-4PCLSbR4x7fPdtpYfLpbbsf2VLgipsGP3Hw8W2jp",
                    "1D388pjK9ljKT3bfJlPpyLSHE4ArcWU0gQeNf40jx7bmt",
                    "ODG4g793wWHmo1n5xObNZM1pD",
                    "MZ6UyXZL2QJDCm69sjnFnsjZItcXgGAw65B5wkdFCHZDPOaB7s")
                  )

    if verbose==True:
       print twitter.application.rate_limit_status()
    query = twitter.search.tweets(q = terms)
    results = query["statuses"]
    # calculate average time between tweets
    first_timestamp = datetime.strptime(results[0]["created_at"], created_at_format)
    last_timestamp = datetime.strptime(results[-1]["created_at"], created_at_format)
    total_dt = (first_timestamp - last_timestamp).total_seconds()
    mean_dt = total_dt / len(results)

    if verbose==True:
        print "Average tweeting rate for '%s' between %s and %s: %.3fs" % (terms, results[-1]["created_at"], results[0]["created_at"], mean_dt)

    return [mean_dt, results[-1]["created_at"], results[0]["created_at"]]

# Returns the screen names of the followers of a twitter user
def followers(username, config, verbose=False):
    twitter = Twitter(auth = OAuth("904711148-4PCLSbR4x7fPdtpYfLpbbsf2VLgipsGP3Hw8W2jp",
                    "1D388pjK9ljKT3bfJlPpyLSHE4ArcWU0gQeNf40jx7bmt",
                    "ODG4g793wWHmo1n5xObNZM1pD",
                    "MZ6UyXZL2QJDCm69sjnFnsjZItcXgGAw65B5wkdFCHZDPOaB7s")
                  )
    query = twitter.friends.ids(screen_name = username)

    # We only get the IDs of the followers, so we have to do more work
    print "Found %d followers" % (len(query["ids"]))

    screen_names = []

    # Loop through in blocks of 100
    for n in range(0, len(query["ids"]), 100):
        ids = query["ids"][n:n+100]
        subquery = twitter.users.lookup(user_id = ids)
        for user in subquery:
            # Print the followers, star if verified
            if verbose==True:
                print " [%s] %s" % ("*" if user["verified"] else " ", user["screen_name"])
            screen_names.append(user["screen_name"])
    return screen_names

# Performs a twitter search for tweets close to the defined latitude and longitude, and
# saves the tweets to a CSV file
def geosearch(latitude, longitude, range, outfile, config, nresults, verbose=False):
    twitter = Twitter(auth = OAuth("904711148-4PCLSbR4x7fPdtpYfLpbbsf2VLgipsGP3Hw8W2jp",
                    "1D388pjK9ljKT3bfJlPpyLSHE4ArcWU0gQeNf40jx7bmt",
                    "ODG4g793wWHmo1n5xObNZM1pD",
                    "MZ6UyXZL2QJDCm69sjnFnsjZItcXgGAw65B5wkdFCHZDPOaB7s")
                  )
    cf = file(outfile, "w")
    cw = csv.writer(cf)
    row = ["user", "text", "latitude", "longitude"]
    cw.writerow(row)

    # break up twitter search due to throttling
    result_count = 0
    last_id = None
    while result_count <  nresults:
        query = twitter.search.tweets(q = "", geocode = "%f,%f,%dkm" % (latitude, longitude, range),
                                      count = 100, max_id = last_id)
        for result in query["statuses"]:
            if result["geo"]:
                user = result["user"]["screen_name"]
                text = result["text"]
                text = text.encode('ascii', 'replace')
                latitude = result["geo"]["coordinates"][0]
                longitude = result["geo"]["coordinates"][1]

                # write to CSV
                row = [user, text, latitude, longitude]
                cw.writerow(row)
                result_count += 1
            last_id = result["id"]
        print "got %d tweets" % result_count
    cf.close()

# Function to decode the verbal (e.g. Boston, MA) string in user
# location text and output latitude and longitude for twitter processing
#
#def latlong(location_text):
#    state_abbr_fp = "data/state_abbr_file"
#    city_fp = "data/city_file"
#    gc = Geocoder(state_abbr_fp, city_fp)
#    location_text = location_text.rstrip()
#    point = gc.geocode(location_text)
#    return [point[0], point[1]]

def geoplot(latitudes, longitudes):
    map = Basemap(projection='robin', lat_0=0, lon_0=-100,
                  resolution='l', area_thresh=1000.0)

    map.drawcoastlines()
    map.drawcountries()
    map.fillcontinents(color = 'gray')
    map.drawmapboundary()

    map.drawmeridians(np.arange(0, 360, 30))
    map.drawparallels(np.arange(-90, 90, 30))
    x, y = map(longitudes, latitudes)

    map.plot(x, y, 'bo', markersize = 8)
    plt.title("Locations of Streamed Tweets")
    plt.show()

def users_tweeting(topic, nresults):
	# Create Twitter API object
	twitter = Twitter(auth = OAuth("904711148-4PCLSbR4x7fPdtpYfLpbbsf2VLgipsGP3Hw8W2jp",
                    "1D388pjK9ljKT3bfJlPpyLSHE4ArcWU0gQeNf40jx7bmt",
                    "ODG4g793wWHmo1n5xObNZM1pD",
                    "MZ6UyXZL2QJDCm69sjnFnsjZItcXgGAw65B5wkdFCHZDPOaB7s")
           	       )

	result_count = 0
	last_id = None

	uq_users = set()
	tweets = []

	while result_count < nresults:
            temp = 100
            # if result_count + 100 < nresults:
            # 	temp = 100
            # else:
            #	temp = nresults - result_count

            query = twitter.search.tweets(q = topic, count = temp, max_id = last_id)

            for result in query["statuses"]:
                uq_users.update([result["user"]["screen_name"]])
                # if not result["retweeted"]:
                tweets.append(result["text"])
                # print result["text"], "  =>  ", result["user"]["screen_name"]
                # print "-----------------------------------------------------\n"
                result_count += 1
                last_id = result["id"]
        # print len(uq_users)
        # print uq_users
        return [len(uq_users), tweets]

def save_unprocessed(outfile, hashtag, N=200):
    f = open(outfile, 'w')
    ob = users_tweeting(hashtag, N)
    tweets = ob[1]
    for tweet in tweets:
        try:
            tweet = tweet + "\n"
            f.write(tweet)
        except:
            pass
    f.close()
