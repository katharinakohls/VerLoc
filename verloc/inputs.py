import pandas as pd

from random import shuffle

class Node():
    def __init__(self, node_id, ip_address, lat, lon, country_code):
        self.node_id = node_id
        self.ip_address = ip_address

        # TODO: lat and lon can only be within specific ranges
        self.location = (lat, lon)
        self.country_code = country_code

        self.my_measurements = [] # my_rtt is the time i measure
        self.their_measurements = [] # their_rtt is the time the other node measures at the same time with me
        self.reference_locations = []
        self.schedule = []

    def add_measurements(self, my_rtt, their_rtt):
        self.my_measurements.append(my_rtt)
        self.their_measurements.append(their_rtt)
    def add_ref_locations(self, ref_locations):
        self.reference_locations = ref_locations
    def add_schedule(self, schedule):
        self.schedule = schedule
    def assign_location_estimate(self, loc_estimate):
        self.location_estimate = loc_estimate

    def get_ref_locations(self):
        return self.reference_locations
    def get_location(self):
        return self.location
    def get_country(self):
        return self.country_code
    def get_node_id(self):
        return self.node_id
    def get_my_measurements(self):
        return self.my_measurements
    def get_their_measurements(self):
        return self.their_measurements
    def get_location_estimate(self):
        return self.location_estimate
    def get_schedule(self):
        return self.schedule

class Measurement():
    def __init__(self, from_node, to_node, timings):
        self.from_node = from_node
        self.to_node = to_node
        self.raw_timings = timings

    def get_min_rtt(self):
        return min(self.raw_timings)

class Schedule():
    def __init__(self, num_references, network):

        # initialize empty reference dict once
        # otherwise we'd overwrite references with empty lists later
        references = {}
        for node in network:
            tmp_id = node.get_node_id()
            references[tmp_id] = []


        base_refs = list(range(1, len(network)+1))
        for node_id in references:
            # check how many more references we need, can vary between nodes
            missing_references = num_references - len(references[node_id])

            while missing_references > 0:
                missing_references = num_references - len(references[node_id])
                
                # make sure we cannot receive references we already have or ourself
                filtered_refs = [x for x in base_refs if (x not in references[node_id] and x != node_id)]
                shuffle(filtered_refs)

                references[node_id].extend(filtered_refs[:missing_references])

            """
            We do symmetric measurements, so we can assume that if a measures b, then b measures a.
            This happens because nodes always do symmetric measurements. Consequently, we can update
            all nodes with these pairs.

            Example:
            - 1 has references 2,5,10
            - We add 1 to the reference sets of 2, 5, 10
            """
            for r in references[node_id]:
                if num_references - len(references[r]) > 0 and node_id not in references[r]:
                    references[r].append(node_id)

        self.schedule = references

    def get_schedule(self):
        return self.schedule

    def add_reference_data_to_nodes(self, network):
        # ! this is not safe, it depends on the correct ordering of the network list
        for node_idx, node in enumerate(self.schedule):
            # print ('Node {} has Schedule {}'.format(node, self.schedule[node]))

            ref_locs = []
            for ref in self.schedule[node]:
                ref_node = network[ref-1]
                ref_locs.append(ref_node.get_location())

            # print ('Added {} references'.format(len(ref_locs)))
            network[node_idx].add_schedule(self.schedule[node])
            network[node_idx].add_ref_locations(ref_locs)

class TimingData():
    def __init__(self):
        # TODO will be replaced by a parsing function
        self.propagation = pd.read_csv('/home/kk/Documents/Repos/2021-verloc-prototype/input_simulation/propagation.csv')

    def assign_timings_to_network(self, schedule, network):
        # ! this is not safe, it depends on the correct ordering of the network list

        for node_idx, node in enumerate(schedule):
            # ? how do we handle directions in the real-world data?
            for ref in schedule[node]:

                my_rtt = None
                their_rtt = None
                try:
                    my_rtt = self.propagation[(self.propagation['FromIndex'] == node) & (self.propagation['ToIndex'] == ref)]['TimeFromTo'].iloc[0]
                except:
                    my_rtt = self.propagation[(self.propagation['ToIndex'] == node) & (self.propagation['FromIndex'] == ref)]['TimeToFrom'].iloc[0]
                    
                try:
                    their_rtt = self.propagation[(self.propagation['FromIndex'] == node) & (self.propagation['ToIndex'] == ref)]['TimeToFrom'].iloc[0]
                except:
                    their_rtt = self.propagation[(self.propagation['ToIndex'] == node) & (self.propagation['FromIndex'] == ref)]['TimeFromTo'].iloc[0]
                    
                if my_rtt is not None and their_rtt is not None:
                    network[node_idx].add_measurements(my_rtt, their_rtt)

class Network():
    def __init__(self, network_size):
        # TODO will be replaced by a parsing function
        node_locations = pd.read_csv('/home/kk/Documents/Repos/2021-verloc-prototype/input_simulation/node_locations.csv')

        lats = list(node_locations['PhysLat'])
        lons = list(node_locations['PhysLon'])
        ccs  = list(node_locations['PhysCC'])

        network = []
        # ! this is not safe, it ids are only in the nodes and list must be ordered
        for i in range(0, node_locations.shape[0]):
            n = Node(i+1, '', lats[i], lons[i], ccs[i])
            network.append(n)

        self.network = network[:network_size]

    def get_network(self):
        return self.network

    def get_node_with_id(self, id):
        # ! this is not safe, it ids are only in the nodes and list must be ordered
        return network[id]
