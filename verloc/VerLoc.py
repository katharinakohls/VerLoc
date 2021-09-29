#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""VerLoc Prototype
   This is the multiprocessing implementation of the VerLoc prototype
   Please refer to the README.md for detailed instructions.
"""

# Data structure
import pandas as pd

# Handling files, multiprocessing
from tqdm import tqdm
from datetime import date
import multiprocessing as mp

# Data processing and plotting
import numpy as np
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import cm
from vincenty import vincenty
from statistics import median

# VerLoc Components
from localization import Localizer
from verification import Verifier
from confidence import ConfidenceScorer
from performance_eval import LocalizationPerformance, VerificationPerformance
from inputs import Measurement, Node, Network, Schedule, TimingData

# Localization Function
def run_localization(num_references, network, timing_measurements, process_id):

    # Random assignment of references for each node. 
    schedule = Schedule(num_references, network)
    timing_measurements.assign_timings_to_network(schedule.get_schedule(), network)
    schedule.add_reference_data_to_nodes(network)

    ground_truth = []

    loc_computations = []
    localization_results = []

    confidence_results = []
    confidence_details = {'node': [], 'score': [], 'fast': [], 'slow': [], 'identity_key': [], 'node_id': []}
    for i, node_id in enumerate(tqdm(network)):
        node = network[node_id]

        node_loc = Localizer(node.get_my_measurements(), node.get_their_measurements(), node.get_ref_locations())
        node_conf = ConfidenceScorer(node)

        # localize
        localization_decision, loc_duration = node_loc.estimate_location()
        node_confidence, fast_violations, slow_violations = node_conf.compute_confidence()

        confidence_details['node'].append(node_id)
        confidence_details['score'].append(node_confidence)
        confidence_details['fast'].append(fast_violations)
        confidence_details['slow'].append(slow_violations)

        confidence_details['identity_key'].append(node.get_identity_key())
        confidence_details['node_id'].append(node.get_node_id())

        # write results
        ground_truth.append(node.get_location())

        localization_results.append(tuple(localization_decision))
        confidence_results.append(node_confidence)
        loc_computations.append(loc_duration)
    
    confidence_df = pd.DataFrame.from_dict(confidence_details)
    loc_performance = LocalizationPerformance(ground_truth, localization_results, loc_computations, confidence_df, process_id)
    
    # loc_performance.prepare_summary()
    loc_performance.write_stats()

def main():
    num_references = 40 # Number of references used for the localization
    num_nodes = 512     # Number of nodes in the network, limits the original number of available nodes
    num_cores = 12      # TODO adjust according to target machine

    # use today's measurements to run the experiment
    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')

    print ('Initializing network with {} Nodes and {} References'.format(num_nodes, num_references))

    # read offline data
    net = Network(timestamp, num_nodes)
    network = net.get_network()

    timing_measurements = TimingData(timestamp)
    timing_measurements.define_available_references(network)

    processes = []
    for rep in range(0,num_cores):
        net = network
        mes = timing_measurements

        processes.append(mp.Process(target=run_localization, args=(num_references, net, mes, rep, )))

    for p in processes:
        p.start()
    
    for p in processes:
        p.join()

if __name__ == '__main__':
    main()
