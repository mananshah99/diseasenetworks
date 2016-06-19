'''
ngrams.py

Description: ngrams.py is a experimental file used to analyze individual hashtags
for salience in contributing to the disease distribution curve. Multiple functions
are involved in this process, includig nltk's corpora stopwords and n-gram utiities
as well as tweet searching procedures and simple popularty determination.

Usage: ngrams.py may be imported and used for general functionality within a
main file (it is not class-based).

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''

import sys
sys.path.append("../util/")
sys.path.append("../classification/")

from toolbox import *
from nltk.corpus import stopwords
from collections import Counter
from nltk.util import ngrams

import csv
import time
import nltk
import pprint
import re
import string

pp = pprint.PrettyPrinter(indent = 4)

# NLTK's tokenization tooks help determine ngrams (without articles/unneessary
# stopwords)
def ngram(string, n):
	tokenize = nltk.word_tokenize(string)
	ng = ngrams(tokenize, n)
	return ng

# Determines key statistics for search_terms (an input file of terms) including
# the popularity score, start date, and end date. These statistics, along with
# additional features regarding the length of certain n-grams, are used to
# determine the popularity statistic
def getstats(search_terms, fname):
	outfile = open(fname, 'w')
	writer = csv.writer(outfile)

	with open(search_terms) as f:
		tags = f.readlines()
	f.close()

	writer.writerow(["Hashtag", "Tweet rate (seconds/tweet)", "Initial Date", "End Date"])

	for tag in tags:
		try:
			tag = tag.lstrip()
			tag = tag.rstrip()
			stats = tweet_rate(tag, []) # score, start date, end date
			writer.writerow([tag, stats[0], stats[1], stats[2]])

		except IndexError:
			writer.writerow([tag, 0, "none", "none"])
		except:
	                print "Unexpected error:", sys.exc_info()
		        print "[!] Rate limited. Waiting for 15 minutes"
			time.sleep(60 * 15)
			print "[!] Sleep complete. Continuing..."

        	        stats = tweet_rate(tag, []) #score, start date, end date

			try:
               			writer.writerow([tag, stats[0], stats[1], stats[2]])
			except:
				writer.writerow([tag, 0, "none", "none"])

	outfile.close()

# Analyzes a list of hashtags
def process_salient(file):
	with open(file) as f:
		lines = f.readlines()
	f.close()

	hashtags = []
	for line in lines:
		first_tok = line.split()[0]
		hashtags.append(first_tok)
	for hashtag in hashtags:
		print "===== HASHTAG: " + hashtag + " ====="
		analyze_hashtag(hashtag)
		print "===================================="


# Utility for analyze_hashtag
def multiple_replace(dict, text):
	regex = re.compile("|".join(map(re.escape, dict.keys())))
  	return regex.sub(lambda mo: dict[mo.group(0)], text)

# Provides a comprehensive overview of the n-grams in a given hashtag
def analyze_hashtag(hashtag):
	try:
		useless_words = ['&amp;', '==&gt;', '-', '--', 'RT', '&', 'http', ':', '#']
		punctuation_marks = re.compile(r'[.?!,":;#]')

		# STEP 1: how many users are tweeting about it?
		ob = users_tweeting(hashtag, 200)
		unique_users = ob[0]
       		print "Number of unique users: ", unique_users

		tweets = ob[1]

		# STEP 2: list of unigrams from the tweets
		words = []
		for tweet in tweets:
			ls = tweet.split()
			ls = [w for w in ls if not w in (stopwords.words('english') + useless_words)] # get only the relevant information
			words = words + ls

		words = [''.join(c for c in s if c not in string.punctuation) for s in words]
		words = [punctuation_marks.sub("", w) for w in words]
		words = filter(None, words)

		c = Counter(words)
		print "Unigrams: "
		pp.pprint(c.most_common(15))
		print "\n"

		# STEP 3: list of bigrams from the tweets
		bigrams = []
		for tweet in tweets:
			tweet = multiple_replace({
				"#": "",
				"@": "",
				"&amp": "",
				"http": "",
				"https":"",
				":":"",
				"RT":"",
				"?http":""
			}, tweet)

			ls = ngram(tweet, 2)
			bigrams = bigrams + ls

		for a, b in bigrams:
			a = punctuation_marks.sub("", a)
			b = punctuation_marks.sub("", b)

		c = Counter(bigrams)
		print "Bigrams: "
		pp.pprint(c.most_common(15))
		print "\n"

		trigrams = []
		for tweet in tweets:
			tweet = multiple_replace({
				"#": "",
				"@": "",
				"&amp": "",
				"http": "",
				"https":"",
				":":"",
				"RT":"",
				"?http":""
		}, tweet)

		ls = ngram(tweet, 3)
		trigrams = trigrams + ls

		for a, b, d in trigrams:
			a = punctuation_marks.sub("", a)
			b = punctuation_marks.sub("", b)
		d = punctuation_marks.sub("", d)

		c = Counter(trigrams)
		print "Trigrams: "
		pp.pprint(c.most_common(15))
	except:
		print sys.exc_info()
