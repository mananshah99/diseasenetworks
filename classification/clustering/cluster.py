'''
cluster.py

Description: cluster.py is a class-based file that clusters documents using
cosine similarity with tf-idf vectorization. It further provides robust and
easily understandable function headings and descriptors.

Usage: cluster.py may not be called directly in a program--it consists of classes
    * Document
    * Corpus
    * Group
that may be called individually or in tandem within code. Individual documentation
for each class follows.

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''
import math
import csv
import os
import sys
from collections import defaultdict
from stemming.porter2 import stem
from stopwords import STOPWORDS

# Threshold for similarity in clustering procedures
SIM_THRESHOLD = .1

# Minimum document length
MIN_DOCUMENT_LENGTH = 3

class Document():

    # Tokenizes a document by removing unncesessary characters and stripping
    # stopwords (as defined in stopwords.py)
    def tokenize(self):
        strips = """\\.!?,(){}[]"'"""
        return [stem(c.strip(strips)) for c in self.document.lower().split()
                if self.stopwords.get(c.strip(strips)) is None]

    # Initializes key components of the Document() class
    def __init__(self, corpus, obj, str = None, stopwords = STOPWORDS):
        if not str:
            str = unicode(obj)
        self.stopwords = stopwords
        self.corpus = corpus
        self.object = obj
        self.document = str
        self.tf = {}
        self._tf_idf = None
        words = self.tokenize()
        for word in set(words):
            self.tf[word] = words.count(word) / float(len(words))

    # Representation of a Document
    def __repr__(self):
        return self.document

    # Calculates the inverse document frequency
    def idf(self, cached=True):
        num_docs = len(self.corpus.docs)
        idf = {}
        for word in self.tf.keys():
            num_occurences = self.corpus.words.get(word, 0)
            idf[word] = math.log(num_docs / (1.0 + num_occurences))
        return idf

    # Calculates the TF-IDF metric (thereby representing a document as a numeric
    # feature-based value)
    def tf_idf(self, cached = True):
        if self._tf_idf and cached:
            return self._tf_idf

        self._tf_idf = {}
        idf = self.idf()
        for word in self.tf.keys():
            self._tf_idf[word] = idf[word] * self.tf[word]

        return self._tf_idf

# A document corpus that uses TF-IDF to relate internal documents
class Corpus():
    def __init__(self, similarity = SIM_THRESHOLD, stopwords = STOPWORDS):
        self.stopwords = stopwords
        self.similarity = similarity
        self.docs = {}
        self.words = defaultdict(int)
        self.index = defaultdict(dict)

    # adds a document to the corpus, checking for minimum document length
    # and proper (unicode) format
    def add(self, document, key = None, str = None):
        if not key:
            try:
                key = document.id
            except AttributeError:
                key = document

        if not str:
            str = unicode(document)

        doc = Document(self, document, str = str, stopwords = self.stopwords)

        if len(doc.tf) < MIN_DOCUMENT_LENGTH:
           return

        # add each key in the document to the corpus (for overall TF-IDF)
        for k in doc.tf.keys():
            if k in self.words:
                self.words[k] += 1

        self.docs[key] = doc

    # indexes each word in the corpus
    def create_index(self):
        index = {}
        for id, doc in self.docs.iteritems():
            for word, weight in doc.tf_idf().iteritems():
                self.index[word][id] = weight

    # Performs clustering within an individual corpus. Here, we use TF-IDF
    # calculations in order to determine the relative 'score' of each documet,
    # subsequently clusterig them based on the minimum similarity threshold
    def cluster(self):
        seen = {}
        scores = {}
        self.create_index()
        for key, doc in self.docs.iteritems():
            if seen.get(key):
                continue

            seen[key] = 1
            scores[key] = defaultdict(int)

            for word, o_weight in doc.tf_idf().iteritems():
                if word in self.index:
                    matches = self.index[word]

                    for c_key, c_weight in matches.iteritems():
                        if c_key in seen:
                            continue
                        scores[key][c_key] += o_weight * c_weight

            scores[key] = dict(((k, v) for k, v in scores[key].iteritems() if v >= self.similarity))
            seen.update(scores[key])

        scores = sorted(scores.iteritems(), cmp = lambda x, y: cmp(len(x[1]), len(y[1])),
                        reverse = True)
        groups = []

        for key, similars in scores:
            if not similars:
                continue
            g = Group(self.docs[key].object)
            for id, similarity in similars.iteritems():
                g.add_similar(self.docs[id].object, similarity)
            mycmp = lambda x, y: cmp(x['similarity'], y['similarity'])
            g.similars.sort(cmp=mycmp)
            if g.length() > 10:
                groups.append(g)
        return groups

class Group:

    def __init__(self, primary=None):
        self.primary = primary
        self.similars = []

    def length(self):
        return len(self.similars)

    def add_similar(self, obj, similarity):
        self.similars.append(dict(object=obj, similarity=similarity))
