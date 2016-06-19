'''
main.py

Description: Performs the entirety of the pipeline used to extract tweets
and plot distributions in real time. main.py makes use of multiple helper
files (such as toolbox, clean, geocoder, randomforest, cluster, and meddict)
and outputs a frequency distribution of tweets by time

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''
import sys
import pprint
import os
import random
import string
import matplotlib
import datetime as dt
import matplotlib.dates as mdates
import matplotlib.mlab as mlab
import matplotlib.cbook as cbook
import argparse
from progress.bar import Bar

sys.path.append("../util/")
sys.path.append("../prediction/")
sys.path.append("../tagger/")
sys.path.append("../word_rules/")
sys.path.append("../classification/clustering/")

from toolbox import *
from clean import *
from geocoder import *
from fio import *
from randomforest import *
from cluster import *
from subprocess import call
from meddict import *

pp = pprint.PrettyPrinter(indent=4)

# Clears (not recursively) the contents of a given folder
# [! Use with caution]
def rimraf(folder):
    for content in os.listdir(folder):
        if os.path.isfile(folder + '/' + content):
            os.unlink(folder + '/' + content)

def update_in_alist(alist, key, value):
    return [(k,v) if (k != key) else (key, value) for (k, v) in alist]

def update_in_alist_inplace(alist, key, value):
    alist[:] = update_in_alist(alist, key, value)

def timeseries(date_list, plot=False):
    TUPS = []
    for tup in date_list:
        date = tup[1]
        date = date[: date.find(' ')]
        dd = dt.datetime.strptime(date,'%Y-%m-%d').date()
        if dd not in [y[0] for y in TUPS]: # if the date is not already part of a tuple
            # add a tuple
            TUPS.append((dd, 1))
            #print "Appended"
        else:
            v = -1
            for y in TUPS:
                if y[0] == dd:
                    v = y[1]
            update_in_alist_inplace(TUPS, dd, v+1)
            #print "Updated"
    TUPS = sorted(TUPS, key=lambda v: v[1])
    x, y = map(list, zip(*TUPS))
    if plot:
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.scatter(x,y)
        #plt.gcf().autofmt_xdate()
        plt.show()
    else: # In the case you don't have a GUI option
        print x
        print "====="
        print y

# Step 0: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("VERBOSITY", help="Whether you want show progress updates", type=int)
parser.add_argument("NUM_TWEETS", help="Number of tweets to sample", type=int)
args = parser.parse_args()

NUM_SAMPLES = args.NUM_TWEETS
VERBOSITY = args.VERBOSITY

reload(sys)
sys.setdefaultencoding('utf8')

def printif(s):
    if VERBOSITY >= 1:
        print s

# Step 1: Get all of the tweets we want, with specific hashtags
# Remember that these are regex

printif("Loading hashtags, which are")
HASHTAGS = ['.*dayquil.*', '.*nyquil.*', '.*allergies.*','.*influenza.*']
# for full results, replace this with the complete list of 62+ hashtags

for ht in HASHTAGS:
    printif("\t" + ht)

printif("Loading Spinn3r parser on /dfs dataset, parsing tweets")
p = Spinn3rParser('dataset') # Include your particular dataset here, in Spinn3r format

tweets = p.grep_tweets(N = NUM_SAMPLES, hashtag_list = HASHTAGS)

# Step 2: Convert the tweets to a .twt file
# ==> Part 1: Save the tweets to a temporary file

printif("Reformatting, cleaning, and saving tweets to .twt file")
exclude = set(string.punctuation)
name = ''
i = 0
for s in HASHTAGS:
    s = ''.join(ch for ch in s if ch not in exclude)
    if i == 0:
        name = s
        i = i + 1
    else:
        name = name.lstrip()
        name = name.rstrip()
        name = name + '-' + s

name = name.rstrip()
name = '../tweets/' + name
RAW_NAME = name + '.raw'
PROCESSED_NAME = name + '.twt'
ARFF_NAME = name + '.arff'
CSV_NAME = name + '.csv'

with open(RAW_NAME, 'a+') as f:
    for tweet in tweets:
        f.write("%s\n" % tweet[0])

# ==> Part 2: Convert the raw file to a twt representation
twtt(RAW_NAME, PROCESSED_NAME)

printif("Generating an ARFF file for manual grading and WEKA from twt file")

# Step 3: Generate an ARFF file
call(["python", "../util/buildarff.py", PROCESSED_NAME, ARFF_NAME])
# invariant: tweets are still in the same order

# Step 4: Auto-label the ARFF file

printif("Generating CSV file from ARFF file for random forest")

# ==> Part 1: Convert to CSV
with open(CSV_NAME, 'a+') as cv:
    with open(ARFF_NAME, 'rw') as f:
        for line in f:
            if line[0] == "@":
                continue
            if line[0] == "":
                continue
            else:
                line = line.replace("," + PROCESSED_NAME, "")
                cv.write("%s\n" % line)

lines = [i for i in open(CSV_NAME, 'rw') if i[:-1]]

t = open(CSV_NAME, 'w+')
t.writelines(lines)
t.close()

# ==> Part 2: Attempt Clustering

printif("Attempting clustering with similarity defaulted to 0.1")
c = Corpus(similarity=0.1)

with open(RAW_NAME, 'rw') as f:
    for line in f:
        c.add(line)
groups = c.cluster()
printif('Number of Clusters: ' + str(len(groups)))
# printif('[main.py] Cluster Sampling:')
if VERBOSITY == 2:
    print "Cluster sampling:"
    for i in range(0, len(groups)):
        pp.pprint(groups[i].similars[0:10])
        print " ------------ "

# We need to tune extraneous groups here. need a methodolgy to eliminate clusters
# with certain attributes. This will help in the making predictions step
# The procedure is to select random samples from each cluster and test whether
# they are 1's or 0's as decided by the SPAM/NEWS v. NOT SPAM random forest classifier.
N_RANDOM = int((NUM_SAMPLES / len(groups) * 0.5))
print "Taking " + str(N_RANDOM) + " random samples from each cluster"
TEMP_RAW = name + '.traw'
TEMP_PROCESSED = name + '.ttwt'
TEMP_CSV = name + '.tcsv'
TEMP_ARFF =  name + '.tarff'

# Final list of tweets to analyze
TWEET_LIST = []

#bar = Bar('Clustering and classifying tweets', max=len(groups))
clusters_kept = 0
for j in range(0, len(groups)):
    N_RANDOM = int(0.5 * len(groups[j].similars))
    cluster = groups[j].similars
    tweets_ = [d['object'] for d in cluster]

    # take a random sample of the tweets
    NET_PREDICT = 0
    SAMPLES_TAKEN = 0
    for i in range(0, N_RANDOM):
        selection = random.choice(tweets_)
        SAMPLES_TAKEN = SAMPLES_TAKEN + 1

        #checks whether a body part is in the context of the sentence
        if not any(term in selection for term in total_terms):
            NET_PREDICT += 0.4 # this is most probably spam
        else:
            with open(TEMP_RAW, 'w') as f:
                f.write(selection)

            twtt(TEMP_RAW, TEMP_PROCESSED)

            call(["python", "../util/buildarff.py", TEMP_PROCESSED, TEMP_ARFF])

            # Step 4: Auto-label the ARFF file

            with open(TEMP_CSV, 'a+') as cv:
                with open(TEMP_ARFF, 'rw') as f:
                    for line in f:
                        if line[0] == "@":
                            continue
                        if line[0] == "":
                            continue
                        else:
                            line = line.replace("," + TEMP_PROCESSED, "")
                            cv.write("%s\n" % line)

            lines = [i for i in open(TEMP_CSV, 'rw') if i[:-1]]

            t = open(TEMP_CSV, 'w+')
            t.writelines(lines)
            t.close()

            # Make prediction for this one
            pred = make_predictions(TEMP_CSV, '../prediction/rf.cpickle')
            # printif("Prediction for " + selection + " is " + str(pred[0]))
            NET_PREDICT = NET_PREDICT + 0.3*pred[0]

            os.remove(TEMP_RAW)
            os.remove(TEMP_PROCESSED)
            os.remove(TEMP_CSV)
            os.remove(TEMP_ARFF)

    printif("NET_PREDICT for cluster " + str(j) + " is " + str(NET_PREDICT))
    printif("NUM_SAMPLES_TAKEN for cluster " + str(j) + " is " + str(SAMPLES_TAKEN))
    printif("NUM_RANDOM for cluster " + str(j) + " is " + str(N_RANDOM))
    printif("RATIO for cluster " + str(j) + " is " + str(float(NET_PREDICT) / N_RANDOM))
    printif("-------------------------------------")
    if NET_PREDICT > (0.35 * SAMPLES_TAKEN): # (we want if more than 35 percent are spam)
        # classified as spam, discard the entire cluster
        # printif("Skipping cluster " + str(j))
        continue
    else:
        clusters_kept += 1
        # printif("Added cluster " + str(j) + " to the final tweet list")
        # add it to the final tweet list
        for tweet in tweets_:
            TWEET_LIST.append(tweet)
    #bar.next()

#bar.finish()
printif("Kept " + str(clusters_kept) + " clusters (" + str(float(clusters_kept)/len(groups)) + ")")

TWEET_LIST_DATES = []
bar2 = Bar('Generating list of tuples to plot time series', max=len(TWEET_LIST))
for tweet in TWEET_LIST:
    for i in tweets:
        temp = i[0].lstrip().rstrip()
        tweet = tweet.lstrip().rstrip()
        if temp == tweet:
            # we have two matching strings, add the date
            tup = (tweet, i[1])
            TWEET_LIST_DATES.append(tup)
    bar2.next()

bar2.finish()
print "Generating time series for tweet list: T(N) ~ len(TWEET_LIST)"
timeseries(TWEET_LIST_DATES)