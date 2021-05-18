# https://testdriven.io/blog/modern-tdd/

import pandas as pd

from tqdm import tqdm

from localization import Localizer
from verification import Verifier
from performance_eval import LocalizationPerformance, VerificationPerformance
from inputs import Measurement, Node, Network, Schedule, TimingData



# TODO
"""
- exception handling
- results evaluation

- prototype components
  - VRF protocol to generate schedule
  - blockchain to store transparent information
"""

def main():
    network_size = 300
    num_references = 100

    print ('Initializing network with \n{} Nodes\n{} References'.format(network_size, num_references))

    # read offline data
    net = Network(network_size)
    network = net.get_network()
    schedule = Schedule(num_references, network)

    timing_measurements = TimingData()
    timing_measurements.assign_timings_to_network(schedule.get_schedule(), network)

    schedule.add_reference_data_to_nodes(network)

    ver_performance = VerificationPerformance(0, 0)

    print ('Finished Preparation')
    distances = []

    ground_truth = []
    localization_results = []
    verification_results = []
    for i, node in enumerate(tqdm(network)):
        node_ver = Verifier(node.get_my_measurements(), node.get_their_measurements(), node.get_schedule(), node.get_ref_locations())
        node_loc = Localizer(node.get_my_measurements(), node.get_their_measurements(), node.get_ref_locations())

        # localize and verify
        localization_decision = node_loc.estimate_location()
        verification_decicion = node_ver.verify_location()

        # node.assign_location_estimate(estimate)

        # ver_performance.plot_map(node_ver.get_cropped_grid(), node.get_location(), i)

        # write results
        ground_truth.append(node.get_location())
        localization_results.append(tuple(localization_decision))
        verification_results.append(verification_decicion)
    
    loc_performance = LocalizationPerformance(ground_truth, localization_results)
    ver_performance = VerificationPerformance(verification_results, ground_truth)
    loc_performance.prepare_summary()
    ver_performance.prepare_summary()

if __name__ == '__main__':
    main()
