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

def calculate_weights(input_network):
    G = input_network.copy()
    for node in G.nodes():
        successors = G.successors(node)
        weights = dict()
        total_degree = 0

        for successor in successors:
            try:
                total_degree += G.out_degree(successor)
            except TypeError:
                pass

        for successor in successors:
            successor_degree = G.out_degree(successor)
            try:
                int(successor_degree)
            except TypeError:
                successor_degree = 0
            if total_degree > 0:
                probability_of_infection = successor_degree / total_degree
            else:
                probability_of_infection = 0

            weights[successor] = probability_of_infection

        largest_weight = 0
        smallest_weight = 2
        for successor, weight in weights.items():
            if weight > largest_weight:
                largest_weight = weight
            elif weight < smallest_weight:
                smallest_weight = weight
        for successor in successors:
            if largest_weight != smallest_weight:
                relative_weight = (weights[successor] - smallest_weight) /\
                                  (largest_weight - smallest_weight)
            else:
                relative_weight = 0
            G[node][successor]['weight'] = relative_weight

    return G
