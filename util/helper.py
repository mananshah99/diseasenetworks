'''
helper.py

Description: Proveds helper functions for buildarff and clean python
files

Copyright (c) 2016, Manan Shah. All rights reserved. Redistribution and use in
source and binary forms, with or without modification, are not permitted without
retention of this notice.
'''
# adds "add" after "sym" occurs in "tweet"
# uses rfind()
def edit_line_r(tweet, sym, add):
  words = tweet.split(' ')
  processed = ''
  for i in range(len(words)):
    word = words[i]
    index = word.rfind(sym)
    if index != -1: #sym exists in word
      if index == len(word)-1: #last character in word
	if (word not in abbrev_english or word not in pn_abbrev_english): #ensure not in abbr list
	  processed += word + add + ' '
      else: #not the last character in word
	next_char = word[index+1]
	if not(next_char == '!' or next_char == '?' or next_char == '\n'): #case of "?!?!?!?!????!"

	  if (word not in abbrev_english or word not in pn_abbrev_english): #case of "e.g."
	    processed += word[:index+1] + add + word[index+1:] + ' '
	else:
	    processed += word + ' '
    else: #sym does not exist in word
      processed += word + ' '
  return processed.rstrip(' ')

# parse the text files containing popular abbreviations
def strip_new_line(words):
  L = []
  for word in words:
    index = word.find('\n')
    L.append(word[:index])
  return L

abbrev_english = strip_new_line(open('../word_rules/abbrev.english', 'r').readlines())
pn_abbrev_english = strip_new_line(open('../word_rules/pn_abbrev.english', 'r').readlines())
