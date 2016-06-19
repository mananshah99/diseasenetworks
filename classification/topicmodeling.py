'''
topicmodeling.py

Description: topicmodeling.py is a experimental file used to determine features
relevant to similarity between tweets. Currently, this file contains methods to
stem tokens, tokenize text, and use sklearn's TF-IDF vectorizer and Kmeans to
cluster relevant tweets (with detailed output for further processing). The main
clustering file (clustering.py) implements these methods in a reusable manner.

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''
from __future__ import print_function

import nltk
import string
import os
import re
import sys
import numpy as np
import lda
import textmining
import pylab as pl

sys.path.append("../util/")

from matplotlib import pyplot
import matplotlib.pyplot as plt
from matplotlib.pylab import *

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import RandomizedPCA
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn import metrics

from nltk.stem.porter import PorterStemmer
from scipy.sparse import coo_matrix
from mpl_toolkits.mplot3d import Axes3D

#from time import time
from toolbox import *
from pylab import *

punctuation_marks = re.compile(r'[.?!,":;@#&$()]')
token_dict = {}
stemmer = PorterStemmer()

def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed

def tokenize(text):
    tokens = nltk.word_tokenize(text)
    stems = stem_tokens(tokens, stemmer)
    return stems

# Use a TF-IDF Vectorizer in order to compute the feature words
# (and also similarities) between multiple different hashtags. This
# is useful for feature selection (what term best predicts the class/hashtag
# of the document?) and is also useful for document classification according
# to groups (see http://scikit-learn.org/stable/auto_examples/text/document_classification_20newsgroups.html)
def keywords(hashtags):
    for hashtag in hashtags:
        ob = users_tweeting(hashtag, 20)
        tweets = ob[1]
        overall = ""
        for tweet in tweets:
            tweet = tweet.lstrip()
            tweet = tweet.rstrip()
            tweet = re.sub(r'[^\x00-\x7F]+',' ', tweet)
            tweet = re.sub(r'\s+', ' ', tweet)
            overall += " "
            overall += tweet

        lower = overall.lower()
        nopunct = punctuation_marks.sub("", lower)
        nopunct = re.sub("http//tco/[A-Za-z0-9]+ ", "", nopunct)

        token_dict[hashtag] = nopunct

    tfidf = TfidfVectorizer(tokenizer=tokenize, ngram_range = (1, 5))
    tfs = tfidf.fit_transform(token_dict.values())
    X = tfs
    print("n_samples: %d, n_features: %d" % X.shape)
    print("Performing dimensionality reduction using LSA")
    #t0 = time()
    # Vectorizer results are normalized, which makes KMeans behave as
    # spherical k-means for better results. Since LSA/SVD results are
    # not normalized, we have to redo the normalization.
    # svd = TruncatedSVD(20)
    # lsa = make_pipeline(svd, Normalizer(copy=False))

    # X = lsa.fit_transform(X)
    # print X

    # print("done in %fs" % (time() - t0))

    # explained_variance = svd.explained_variance_ratio_.sum()
    # print("Explained variance of the SVD step: {}%".format(
    #    int(explained_variance * 100)))

    km = KMeans(n_clusters=3, init='k-means++', max_iter=100, n_init=10, tol = 1e-8, verbose=True)
    print("Clustering sparse data with %s" % km)
    #t0 = time()
    km.fit(X)
    #print("done in %0.3fs" % (time() - t0))

    labels = km.labels_
    centroids = km.cluster_centers_
    figure = pl.figure(1)
    ax = Axes3D(figure)
    X = X.A
    # ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2])
    ax.scatter(X[:, 0], X[:, 1], X[:, 2])
    pl.show()

    # print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(X, km.labels_, sample_size=1000))

    print("Top terms per cluster:")
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    terms = tfidf.get_feature_names()
    for i in range(3):
        print("Cluster %d:" % i)
        for ind in order_centroids[i, :20]:
            print(' %s' % terms[ind])

    array = tfs.toarray()
    with open('tfidf.csv', 'wb') as csvfile:
        csvw = csv.writer(csvfile, delimiter=',')
        row1 = tfidf.get_feature_names()
        csvw.writerow(row1)
        for row in array:
            csvw.writerow(row)

    return [tfidf, X, km, tfs]

# Document/Term Matrix
def tdm(tweets):
    tdmatrix = textmining.TermDocumentMatrix()
    for tweet in tweets:
        tdmatrix.add_doc(tweet)
    return tdmatrix

# Plots a sparse matrix with pyplot
def plot_coo_matrix(m):
    if not isinstance(m, coo_matrix):
        m = coo_matrix(m)
    fig = plt.figure()
    ax = fig.add_subplot(111, axisbg='black')
    ax.plot(m.col, m.row, 's', color='white', ms=1)
    ax.set_xlim(0, m.shape[1])
    ax.set_ylim(0, m.shape[0])
    ax.set_aspect('equal')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.show()
    return ax

# Let's cluster into 3 groups because one group will be full of junk (not polar)
# ob = keywords(['#happy', '#sad', '#feelingsick'])
# plot(ob[2], reduced)

# ob2 = keywords(["#allergies", "#feelingsick", "#fever"])
# tfidf = ob2[0]

# str = 'Happy birthday to my bestie love you ugly face #birthday #happy #love'
# response = tfidf.transform([str])
# feature_names = tfidf.get_feature_names()
# for col in response.nonzero()[1]:
#    print feature_names[col], ' ==> ', response[0, col]
