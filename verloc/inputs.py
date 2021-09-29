import pandas as pd
from scipy import constants

from random import shuffle

class Node():
    def __init__(self, node_id, node_key, ip_address, lat, lon, country_code, country):
        self.node_id = node_id
        self.ip_address = ip_address
        self.node_key = node_key

        # TODO: lat and lon can only be within specific ranges
        self.location = (lat, lon)
        self.country_code = country_code
        self.country = country

        self.available_references = []

        self.my_measurements = [] # my_rtt is the time i measure
        self.their_measurements = [] # their_rtt is the time the other node measures at the same time with me
        self.reference_locations = []
        self.schedule = []

    def set_available_references(self, available_refs):
        self.available_references = available_refs
    def add_measurements(self, my_rtt, their_rtt):
        self.my_measurements.append(my_rtt)
        self.their_measurements.append(their_rtt)
    def add_ref_locations(self, ref_locations):
        self.reference_locations = ref_locations
    def add_schedule(self, schedule):
        self.schedule = schedule
    def assign_location_estimate(self, loc_estimate):
        self.location_estimate = loc_estimate

    def get_available_references(self):
        return self.available_references
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
            references[node] = []

        # use the list of ids in our network as search space for random references
        for node_id in network:
            node = network[node_id]
            
            # ---------------------------------------------------------------------------
            # check how many more references we need, can vary between nodes
            missing_references = num_references - len(references[node_id])

            iter_cnt = 0
            while missing_references > 0:
                missing_references = num_references - len(references[node_id])
                
                # make sure we cannot receive references we already have or ourself
                filtered_refs = []
                locations = []
                for candidate in node.get_available_references():
                    if candidate not in references[node_id] and candidate != node_id:
                        ref_loc = network[candidate].get_location()
                        if ref_loc not in locations and ref_loc != node.get_location():
                            filtered_refs.append(candidate)
                            locations.append(ref_loc)

                iter_cnt = iter_cnt + 1
                if iter_cnt > 10:
                    break

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
                try:
                    if num_references - len(references[r]) > 0 and node_id not in references[r]:
                        references[r].append(node_id)
                except Exception as e:
                    print (e)

        self.schedule = references


    def get_schedule(self):
        return self.schedule

    def add_reference_data_to_nodes(self, network):
        for node in self.schedule:
            # print ('Node {} has Schedule {}'.format(node, self.schedule[node]))

            ref_locs = []
            for ref in self.schedule[node]:
                ref_node = network[ref]
                ref_locs.append(ref_node.get_location())

            # print ('Added {} references'.format(len(ref_locs)))
            network[node].add_schedule(self.schedule[node])
            network[node].add_ref_locations(ref_locs)

class TimingData():
    def __init__(self, timestamp):
        # uses the parsed real-world measurements

        # uses today's measurements
        # self.propagation = pd.read_csv('../parser/static_data/melted_propagation_{}.csv'.format(timestamp))

        # used in the experimental eval of the USENIX'22 paper
        self.propagation = pd.read_csv('../parser/static_data/melted_propagation_25-06-2021.csv')
        
        self.propagation['distances'] = self.propagation['distances'] / 1000
        self.propagation['speeds'] = self.propagation['speeds'] / 1000

    def define_available_references(self, network):
        for node_id in network:
            node = network[node_id]

            prop_subset_from = list(self.propagation[self.propagation['FromIndex'] == node.get_node_id()]['ToIndex'])
            prop_subset_to = list(self.propagation[self.propagation['ToIndex'] == node.get_node_id()]['FromIndex'])

            available_references = prop_subset_from + list(set(prop_subset_from) - set(prop_subset_to))
            available_references = [x for x in available_references if x in network.keys()]

            node.set_available_references(list(set(available_references)))

    def assign_timings_to_network(self, schedule, network):
        for node in schedule:
            for ref in schedule[node]:

                my_rtt = None
                their_rtt = None
                try:
                    my_rtt = self.propagation[(self.propagation['FromIndex'] == node) & (self.propagation['ToIndex'] == ref)].iloc[0]['TimeFromTo']
                except:
                    my_rtt = self.propagation[(self.propagation['ToIndex'] == node) & (self.propagation['FromIndex'] == ref)].iloc[0]['TimeToFrom']
                    
                try:
                    their_rtt = self.propagation[(self.propagation['FromIndex'] == node) & (self.propagation['ToIndex'] == ref)].iloc[0]['TimeToFrom']
                except:
                    their_rtt = self.propagation[(self.propagation['ToIndex'] == node) & (self.propagation['FromIndex'] == ref)].iloc[0]['TimeFromTo']
                    
                if my_rtt is not None and their_rtt is not None:
                    network[node].add_measurements(my_rtt, their_rtt)

class Network():
    def __init__(self, timestamp, num_nodes):
        # uses the parsed real-world measurements

        # uses today's measurements
        # node_locations = pd.read_csv('../parser/static_data/eu_node_identities_{}.csv'.format(timestamp))

        # used in the experimental eval of the USENIX'22 paper
        node_locations = pd.read_csv('../parser/static_data/eu_node_identities_25-06-2021.csv')

        self.lats = list(node_locations['lat'])
        self.lons = list(node_locations['lon'])
        self.ccs  = list(node_locations['iso3'])
        self.ids = list(node_locations['id'])
        self.ips = list(node_locations['ip'])
        self.keys = list(node_locations['identity_key'])
        self.countries = list(node_locations['country'])

        network = {}
        for i in range(0, num_nodes):
            n = Node(self.ids[i], self.keys[i], self.ips[i], self.lats[i], self.lons[i], self.ccs[i], self.countries[i])
            network[self.ids[i]] = n

        self.network = network

    def get_network(self):
        return self.network
        