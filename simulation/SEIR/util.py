import copy
import getopt
import math
import networkx as nx
import matplotlib.pyplot as plt
import operator
import os
import random
import sys
from scipy import stats
import time
import random

def randomize_weights(weights):
    number = random.random() * sum(weights.values())
    for k, v in weights.items():
        if number <= v:
            break
        number -= v
    return k

def pad_string(integer, n):
    string = str(integer)
    while len(string) < n:
        string = "0" + string
    return string
