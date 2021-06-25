# https://testdriven.io/blog/modern-tdd/

import pandas as pd

from tqdm import tqdm
from datetime import date

import multiprocessing as mp

from verification import Verifier
from confidence import ConfidenceScorer
from performance_eval import VerificationPerformance
from inputs import Measurement, Node, Network, Schedule, TimingData

def run_verification(num_references, network_subset, full_network, timing_measurements, process_id):
    schedule = Schedule(num_references, full_network)
    timing_measurements.assign_timings_to_network(schedule.get_schedule(), full_network)
    schedule.add_reference_data_to_nodes(full_network)

    ground_truth = []
    verification_results = []

    for node_id in network_subset:
        node = network_subset[node_id]
        
        node_ver = Verifier(node.get_my_measurements(), node.get_their_measurements(), node.get_schedule(), node.get_ref_locations(), node)

    #     # verify
        verification_decicion, final_grid = node_ver.verify_location()

        print (verification_decicion, node.country)

        if verification_decicion != -1 and len(final_grid) > 0:
            verification_results.append(verification_decicion)
            ground_truth.append(node.country)

    ver_performance = VerificationPerformance(verification_results, ground_truth, process_id)
    ver_performance.prepare_summary()

def main():
    num_references = 40
    num_nodes = 512
    num_cores = 64

    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')

    print ('Initializing network with {} Nodes and {} References'.format(num_nodes, num_references))

    # read offline data
    net = Network(timestamp, num_nodes)
    network = net.get_network()

    timing_measurements = TimingData(timestamp)
    timing_measurements.define_available_references(network)

    # verification
    # -------------------------
    processes = []

    node_ids = list(network.keys())
    network_subsets = int(len(node_ids) / num_cores)

    lower = 0
    upper = network_subsets
    for rep in range(0,num_cores):
        network_subset = {x: network[x] for x in node_ids[lower:upper]}
        mes = timing_measurements

        processes.append(mp.Process(target=run_verification, args=(num_references, network_subset, network, mes, rep, )))

        lower = upper
        upper = upper + network_subsets

    for p in processes:
        p.start()
    
    for p in processes:
        p.join()
    # -------------------------
    

if __name__ == '__main__':
    main()
