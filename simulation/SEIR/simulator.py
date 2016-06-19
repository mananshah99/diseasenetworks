#!/usr/bin/python3
"""
simulator.py is a simulator for an internation infection spreading between
airports across air-travel routes; here, the airports are the nodes and the
flight travels are the edges.
"""
from util import *
from update import *
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

global VISUALIZE

def write_network(network, time, targets, seed, filename="network.dat"):
    print("\tDetermining network type.")
    if isinstance(network,nx.DiGraph):
        network_type = "Directed"
    else:
        network_type = "Undirected"

    print("\tCalculaing edges and vertices.")
    edges = network.number_of_edges()
    vertices = network.number_of_nodes()
    undirected = network.to_undirected()

    print("\tFinding subgraphs.")
    subgraphs = nx.connected_component_subgraphs(undirected)

    print("\tFinding network diameter.")
    diameter = nx.diameter(subgraphs[0])

    print("\tStoring network parameters")

    out = open(filename, "w")
    out.write("Simulation name: {0}\n\n".format(time))
    out.write("Network properties\n===============\n")
    out.write("Network type: {0}\n".format(network_type))
    out.write("Number of vertices: {0}\n".format(vertices))
    out.write("Number of edges: {0}\n".format(edges))
    out.write("Diameter: {0}\n".format(diameter))

    out.close()

def create_network(nodes, edges):
    G = nx.DiGraph()
    print("\tLoading airports", end="")
    sys.stdout.flush()

    with open(nodes, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            entries = line.replace('"',"").rstrip().split(",")
            G.add_node(
                int(entries[0]),
                country = entries[3],
                name    = entries[1],
                lat     = entries[6],
                lon     = entries[7]
            )

    print("\t\t\t\t\t[Done]")

    print("\tLoading routes",end="")
    sys.stdout.flush()

    edge_count = 0
    error_count = 0
    duplicate_count = 0
    line_num = 1

    with open(edges, 'r', encoding="utf-8") as f:
        for line in f.readlines():
            entries = line.replace('"',"").rstrip().split(",")
            try:
                if G.has_edge(int(entries[3]), int(entries[5])):
                    duplicate_count += 1
                else:
                    if line_num > 1:
                        from_vertex = int(entries[3])
                        to_vertex = int(entries[5])
                        G.add_edge(from_vertex, to_vertex)
                        G.edge[from_vertex][to_vertex]['IATAFrom'] = entries[2]
                        G.edge[from_vertex][to_vertex]['IATATo'] = entries[4]
                        edge_count += 1
            except ValueError:
                error_count += 1
                pass
            line_num += 1

    print("\t\t\t\t\t\t[Done]")
    print("\t\t[Error Count]\t", error_count)
    print("\t\t[Dup Count]\t", duplicate_count)
    print("\t\t[Edge Count]\t", edge_count)

    # Limit to the first subgraph
    print("\tFinding largest subgraph",end="")
    sys.stdout.flush()
    undirected = G.to_undirected()
    subgraphs = nx.connected_component_subgraphs(undirected)
    subgraphs = list(subgraphs)
    subgraph_nodes = subgraphs[0].nodes()
    to_remove = list()
    for node in G.nodes():
        if node not in subgraph_nodes:
            to_remove.append(node)
    G.remove_nodes_from(to_remove)
    print("\t\t\t\t[Done]")
    print("\t\t[# Subgraphs]\t" + str(len(subgraphs)))

    print("\tRemoving isolated vertices",end="")
    # Remove nodes without inbound edges
    indeg = G.in_degree()
    outdeg = G.out_degree()
    to_remove = [n for n in indeg if (indeg[n] + outdeg[n] < 1)]
    G.remove_nodes_from(to_remove)
    print("\t\t\t\t[Done]")
    print("\t\t[# Removed]\t", str(len(to_remove)))

    # Calculate the edge weights
    print("\tCalculating edge weights",end="")
    G = calculate_weights(G)
    print("\t\t\t\t[Done]")

    # Add clustering data
    print("\tCalculating clustering coefficents",end="")
    cluster_network = nx.Graph(G)
    lcluster = nx.clustering(cluster_network)
    for i,j in G.edges():
        cluster_sum = lcluster[i] + lcluster[j]
        G[i][j]['cluster'] = cluster_sum
    print("\t\t\t[Done]")

    # Flag flights as domestic or international
    print("\tCategorizing international and domestic flights",end="")
    for i, j in G.edges():
        if G.node[i]["country"] == G.node[j]['country']:
            G[i][j]['international'] = False
        else:
            G[i][j]['international'] = True
    print("\t\t[Done]")

    return G

def infection(input_network, vaccination, starts, DELAY=0, vis = False,
              file_name = "sir.csv", title="",  RECALCULATE = True):

    print("Simulating infection")

    network = input_network.copy()

    # Open the data file
    f = open(file_name, "w")
    f.write("time, s, e, i, r\n")

    sys.stdout.flush()
    for node in network.nodes():
        network.node[node]["status"] =  "s"
        network.node[node]["color"] = "#A0C8F0"
        network.node[node]["age"] = 0

    # Assign the infected
    for start in starts:
        infected = start
        network.node[infected]["status"] = "i"
        network.node[infected]["color"]  = "red"#"green"

        if isinstance(network,nx.DiGraph):
            in_degree = network.in_degree()[infected]
            out_degree = network.out_degree()[infected]
            degree = in_degree + out_degree
        else:
            degree = network.degree()[infected]

        print("\t",network.node[infected]["name"],"[",degree,"]")


    if vaccination is not None:
        print("\tVaccinated: ", len(vaccination))
    else:
        print("\tVaccinated: None")

    if vis:
        pos = nx.spring_layout(network, scale=2)

    # Iterate through the evolution of the disease.
    for step in range(0,99):
        # If the delay is over, vaccinate.
        # Convert the STRING!
        if int(step) == int(DELAY):
            if vaccination is not None:
                print(DELAY,"on step",step)
                network.remove_edges_from(vaccination)
                # Recalculate the weights of the network as per necessary
                if RECALCULATE == True:
                    network = calculate_weights(network)


        # Create variables to hold the outcomes as they happen
        S,E,I,R = 0,0,0,0

        for node in network.nodes():
            status = network.node[node]["status"]
            age = network.node[node]["age"]
            color = network.node[node]["color"]

            if status is "i" and age >= 11:
                # The infected has reached its recovery time
                network.node[node]["status"] = "r"
                network.node[node]["color"] = "black"#"purple"

            if status is "e" and age >= 3 and age < 11:
                # The infected has reached its recovery time
                network.node[node]["status"] = "i"
                network.node[node]["color"] = "red"#"green"

            elif status is "e":
                network.node[node]["age"] += 1

            elif status is "i":
                # Propogate the infection.
                if age > 0:
                    victims = network.successors(node)
                    number_infections = 0
                    for victim in victims:
                        infect_status = network.node[victim]["status"]
                        infect = False
                        if random.uniform(0, 1) <= network[node][victim]['weight']:
                            infect = True
                            number_infections+=1
                        if infect_status == "s" and infect == True:
                            network.node[victim]["status"] = "e"
                            network.node[victim]["age"] = 0
                            network.node[victim]["color"] = "red"#"#FF6F00"
                network.node[node]["age"] += 1

        # Loop twice to prevent bias.
        for node in network.nodes():
            status = network.node[node]["status"]
            age = network.node[node]["age"]
            color = network.node[node]["color"]

            if status is "s":
                S += 1
            if status is "e":
                E += 1
            if status is "v":
                S += 1
            elif status is "r":
                R += 1
            elif status is "i":
                I += 1

        print("{0}, {1}, {2}, {3}, {4}".format(step, S, E, I, R))

        printline = "{0}, {1}, {2}, {3}, {4}".format(step, S, E, I, R)
        f.write(printline + "\n")

        if I is 0:
            break

        if vis:
            visualize(network, title, pos)

    print("\t----------\n\tS: {0}, I: {1}, R: {2}".format(S,I,R))

    return {"Susceptible":S,"Infected":I, "Recovered":R}

def main():
    VISUALIZE = False
    INTERNATIONAL = False
    DOMESTIC = False
    DELAY = 0
    NUM_SIMULATIONS = 10
    # Determine the parameters of the current simulation.
    opts, args = getopt.getopt(sys.argv[1:], "brcsidv", ["delay=",
                                                         "nsim="]
                                                            )
    AIRPORT_DATA = args[0]
    ROUTE_DATA = args[1]

    simulations = list()
    simulations.append('sir')

    for o, a in opts:
        if o == "-v":
            VISUALIZE = True
        elif o == "-i":
            INTERNATIONAL = True
        elif o == "-q":
            DOMESTIC = True
        elif o == "-y":
            RECALCULATE = False
        elif o == "--delay":
            DELAY = int(a)
        elif o == "--nsim":
            NUM_SIMULATIONS = int(a)

    seed = 100
    random.seed(seed)

    # Create the network using the command arguments.
    network = create_network(AIRPORT_DATA, ROUTE_DATA)

    # Generate target-selection weights, and choose target vertices to infect.
    degrees = network.degree()
    weights = dict()
    for airport, degree in degrees.items():
        weights[airport] = network.out_degree(airport) +\
                           network.in_degree(airport)
    targets = list()
    for ind in range(0,NUM_SIMULATIONS):
        target_round = list()
        while len(target_round) < 10:
             chosen_airport = randomize_weights(weights)
             if chosen_airport not in target_round:
                 target_round.append(chosen_airport)
        targets.append(target_round)


    # Make a directory for the data, and change into that directory.
    currenttime = time.strftime("%Y-%m-%dT%H%M%S", time.gmtime())
    os.makedirs(currenttime)
    os.chdir(currenttime)

    # Record relevent data about the simulation.
    # write_network(network, currenttime, targets, seed)

    edgepool = network.edges(data=True)
    if INTERNATIONAL:
        for i,j,data in edgepool:
            if data["international"] == False:
                edgepool.remove((i,j,data))
            index += 1
    elif DOMESTIC:
        for i,j,data in edgepool:
            if data["domestic"] == False:
                degrees.edgepool((i,j,data))
            index += 1


    for strategy in simulations:

        print("{0} mode".format(strategy) )

        index = 0
        
        os.makedirs(strategy)
        iteration = 0
        efforts = [0]
        efforts.extend(range(1,101,5))
        for target in targets:

            # Open a file for this targets dataset
            output_file = open("{0}/{0}_{1}.csv".format(strategy,
                                                        pad_string(iteration,4)
                                                        ),"w")
            output_file.write('"effort","total_infected, edges_closed"\n')

            for effort in efforts:
                if effort != 0:
                    max_index = int(len(cancellist) * (effort/100))-1
                    cancelled = cancellist[0:max_index]
                else:
                    cancelled = None

                title = "{0} - {1}%".format(strategy, effort/100)
                results = infection(network, cancelled, target, vis=VISUALIZE,
                                    title=title, DELAY=DELAY)
                total_infected = results["Infected"] + results["Recovered"]
                output_file.write("{0},{1}\n".format(effort/100,total_infected))

                if total_infected == 1:
                    for remaining_effort in range(effort+5,101,5):
                        output_file.write("{0},{1}\n".format(remaining_effort/100,
                                                              total_infected))
                    break

            iteration += 1
            output_file.close()


def visualize(network, title,pos):
    print("-- Starting to Visualize --")
    MAP = False

    if MAP:
        m = Basemap(
            projection='cea',
            llcrnrlat=-90, urcrnrlat=90,
            llcrnrlon=-180, urcrnrlon=180,
            resolution=None
            )

        pos = dict()

        for pos_node in network.nodes():
            # Normalize the lat and lon values
            x,y = m(float(network.node[pos_node]['lon']),
                    float(network.node[pos_node]['lat']))

            pos[pos_node] = [x,y]


    colors = []
    i_edge_colors = []
    d_edge_colors = []
    default = []
    infected = []
    for node in network.nodes():
        colors.append(network.node[node]["color"])
    for i,j in network.edges():
        color = network.node[i]["color"]
        alpha = 0.75
        if color == "#A0C8F0" or color == "#FF6F00" or color == "purple":
            color = "#A6A6A6"
            default.append((i,j))
            d_edge_colors.append(color)
        else:
            color = "red"#"#29A229"
            infected.append((i,j))
            i_edge_colors.append(color)

    plt.figure(figsize=(7,7))

    # Fist pass - Gray lines
    nx.draw_networkx_edges(network,pos,edgelist=default,
            width=0.5,
            edge_color=d_edge_colors,
            alpha=0.5,
            arrows=False)

    # Second Pass - Colored lines
    nx.draw_networkx_edges(network,pos,edgelist=infected,
            width=0.5,
            edge_color=i_edge_colors,
            alpha=0.75,
            arrows=False)

    nx.draw_networkx_nodes(network,
            pos,
            linewidths=0.5,
            node_size=10,
            with_labels=False,
            node_color = colors)

    # Adjust the plot limits
    cut = 0.5 #1.05
    xmax = cut * max(xx for xx,yy in pos.values())
    xmin = min(xx for xx,yy in pos.values())
    xmin = xmin - (cut * xmin)


    ymax = cut * max(yy for xx,yy in pos.values())
    ymin = (cut) * min(yy for xx,yy in pos.values())
    ymin = ymin - (cut * ymin)

    xmax += 1.2
    xmin -= 1.2
    ymax += 1.2
    ymin -= 1.5

    plt.xlim(xmin,xmax)
    plt.ylim(ymin,ymax)

    if MAP:
        m.bluemarble()
    plt.title=title

    plt.axis('off')

    number_files = str(len(os.listdir()))
    while len(number_files) < 3:
        number_files = "0" + number_files

    plt.savefig("infection-{0}.png".format(number_files),
                bbox_inches='tight', dpi=600
            )
    plt.close()

if __name__ == "__main__":
    main()
