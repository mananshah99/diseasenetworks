# Conducts file I/O for PART-R-XXXX files provided by the HADOOP cluster
#
# An example file provided will look something like the following examples
#
# ======= Pretty standard
#
# I       2008081803_00000010_T
# V       A
# S       en      0.857141
# S       no      0.142859
# G       false   1.0
# U       http://twitter.com/Kacey3/statuses/869538531
# D       2008-08-18 03:41:14
# T       twitter / kacey close: #potd: potd2 #186 http://ti...
# C       twitter memes - global tags for twitter
#
# ======= No 'C' tag
#
# I       2008091015_00000066_T
# V       A
# S       en      0.999997
# G       false   1.0
# U       http://twitter.com/davidmaybury/statuses/916478787
# D       2008-09-10 15:34:43
# T       twitter / davidmaybury: @fluffylink waves like a ro...
#
# ======= Multiple links
#
# I       2009011417_00000133_T
# V       A
# S       en      0.714283
# S       fr      0.142859
# S       it      0.142858
# G       false   1.0
# U       http://twitter.com/complexd/statuses/1118674271
# D       2009-01-14 17:14:49
# T       complexd: email archiving provider liveoffice reports record-setting q4 sales - http://tinyurl.com/86bxjs
# C        email archiving provider liveoffice reports record-setting q4 sales -
# L       71              http://tinyurl.com/86bxjs
# L       71              http://tinyurl.com/86bxjs
#
#
# ======= A 'Q' (quotation) field
#
# I       2009030615_00000028_T
# V       A
# S       en      0.999998
# G       false   1.0
# U       http://twitter.com/mayormiller/
# D       2009-03-06 15:24:11
# T       toronto mayor david miller is twittering the city's 175th birthday (but so far it's pretty dull) | @mayormiller #followfriday (via friendfeed)
# C        hey there! mayormiller is using twitter. twitter is a free service that lets you ke... (redacted)
# Q       658     65      i'm going to play this tape on bill carrolls birthday. every year
#
# The methodology behind processing these large files (~2.8 GB, containing thousands of the above examples)
# involves both a quick method (for obtaining only the tweets) and a more involved method that returns and
# makes use of many of the attributes.
#
import os
import sys
import re
from progress.bar import Bar
import pprint
import itertools
import mmap
import subprocess
pp = pprint.PrettyPrinter(indent=4)

sys.path.append("../tagger/")
sys.path.append("../util/")

class Spinn3rParser():
    def __init__(self, filepath):
        self.FPATH = filepath

    def grep_tweets(self, N=200, hashtag_list=[], date=True, clear=False):
        # only search for lines that start with a 'T'
        # hashtag_list is a regex list (this allows for the next line to be possible)
        combined = "(" + ")|(".join(hashtag_list) + ")"
        list = []

        if clear==True:
            os.system('cls' if os.name == 'nt' else 'clear')

        bar = Bar('Finding Hashtags', max=N)

        date_str = ""
        df = False
        with open(self.FPATH, 'r') as f:
            for line in f:
                if date == False:
                    if line[0] == 'F':
                        line = line[1:]
                        line = line.lstrip()
                        line = line.rstrip()

                        if re.match(combined, line):
                            list.append(line)
                            bar.next()
                else:
                    if line[0] == 'D':
                        df = True
                        line = line[1:]
                        line = line.lstrip()
                        line = line.rstrip()
                        date_str = line

                    elif line[0] == 'F':
                        if df == True:
                            line = line[1:]
                            line = line.lstrip()
                            line = line.rstrip()

                            if re.match(combined, line):
                                tup = (line, date_str)
                                list.append(tup)
                                bar.next()
                                df = False

                if(len(list) >= N):
                    bar.finish()
                    return list

    def grep_tweets_all(self,
                        N=200,
                        hashtag_list=[],
                        ):

        twls = []
        def process_group(group):
            # process a json file that represents the group
            dict = {}
            ag = group.split('\n')
            #pp.pprint(ag)
            for i in ag:
                if not i:
                    continue
                elements = i.split('\t')
                dict[elements[0]] = elements[1]
            return dict

        block_expr = re.compile(r"((?:.+\n)+)", re.MULTILINE)
        fp = open(self.FPATH)
        contents = mmap.mmap(fp.fileno(), os.stat(self.FPATH).st_size, access=mmap.ACCESS_READ)

        # every block starts with I
        i = 0
        for block_match in block_expr.finditer(contents):
            group =  block_match.group()
            #print type(group)
            dict = process_group(group)
            if i == N:
                return twls
            i = i + 1
            twls.append(dict)

        return twls