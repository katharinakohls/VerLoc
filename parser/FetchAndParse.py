import os
import json
import requests
import pandas as pd
import geopandas as gpd
import multiprocessing as mp

from os import listdir
from datetime import date
from vincenty import vincenty
from numpy.core.numeric import full

EU_LIST = ['Germany', 'United Kingdom', 'France', 'Italy', 'Ukraine', 'Poland', 'Netherlands', 'Belgium', 'Spain', 'Romania', 'Austria', 'Hungary', 'Slovakia', 'Czech Republic', 'Switzerland']    

def get_locations(mixnode_data, cities):
        location_lookup = {'location': [], 'lat': [], 'lon': [], 'country': [], 'iso3': []}

        for node in mixnode_data:
            loc = node['mix_node']['location']
            try:
                cty = cities[cities['city'] == loc].iloc[0]

                location_lookup['location'].append(loc)

                location_lookup['lat'].append(float(cty['lat']))
                location_lookup['lon'].append(float(cty['lng']))
                location_lookup['country'].append(cty['country'])
                location_lookup['iso3'].append(cty['iso3'])
            except Exception as e:
                pass
        
        return pd.DataFrame.from_dict(location_lookup)

def read_city_coordinates():
    cities = gpd.read_file('worldcities.csv')

    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')
    json_file = open('mixnodes/mixnodes_{}.json'.format(timestamp))
    mixnode_data = json.load(json_file) 

    location_lookup = get_locations(mixnode_data, cities)
    location_lookup.to_csv('city_coordinates.csv', sep=',')

    return location_lookup

def get_raw_mixnodes():
    finney_node_url = 'https://testnet-finney-explorer.nymtech.net/data/mixnodes.json'
    r = requests.get(finney_node_url, timeout=10)
    data = r.json()
    
    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')
    node_file = 'mixnodes/mixnodes_{}.json'.format(timestamp)

    with open(node_file, 'w') as outfile:
        json.dump(data, outfile)

    print ('File written:', node_file)
    return node_file

def prepare_node_identities(node_file, city_coordinates):

    node_id = 1
    mix_nodes = {'id': [], 'identity_key': [], 'ip': [], 'location': [], 'lat': [], 'lon': [], 'country': [], 'iso3': [], 'version': []}

    failed_entries = []
    with open(node_file) as json_file:
        data = json.load(json_file)
        for node in data:
            vers = node['mix_node']['version'].split('.')
            if int(vers[1]) >= 10:
                loc = node['mix_node']['location']

                try:
                    cty = city_coordinates[city_coordinates['location'] == loc].values[0]
                    
                    mix_nodes['id'].append(node_id)
                    mix_nodes['identity_key'].append(node['mix_node']['identity_key'])
                    mix_nodes['ip'].append(node['mix_node']['host'])
                    mix_nodes['version'].append(node['mix_node']['version'])

                    mix_nodes['location'].append(loc)    
                    mix_nodes['lat'].append(cty[1])
                    mix_nodes['lon'].append(cty[2])
                    mix_nodes['country'].append(cty[3])
                    mix_nodes['iso3'].append(cty[4])

                    node_id = node_id + 1
                except Exception as e:
                    failed_entries.append(loc)
                    pass

    mix_df = pd.DataFrame.from_dict(mix_nodes)

    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')

    out_file_full = 'mixnodes/node_identities_{}.csv'.format(timestamp)
    out_file_eu = 'mixnodes/eu_node_identities_{}.csv'.format(timestamp)

    eu_subset = mix_df[mix_df['country'].isin(EU_LIST)]

    mix_df.to_csv(out_file_full, sep=',', index=False)
    eu_subset.to_csv(out_file_eu, sep=',', index=False)

    with open('mixnodes/dbg_failed_nodes.txt', "w") as output:
        output.write(str(failed_entries))


    print ('Failed nodes: ', len(failed_entries), 'Successful nodes: ', len(mix_df['id']))

    # returns the full data set and the eu subset
    # right now we only use the eu subset
    return mix_df, eu_subset, out_file_full, out_file_eu

def parse_ip_addresses():
    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')
    node_identities = pd.read_csv('mixnodes/node_identities_{}.csv'.format(timestamp))

    ip_list = {}
    for index, row in node_identities.iterrows():
        ip_string = row['ip']
        ip_stripped = ''

        if '[' in ip_string :
            # IPv6
            ip_stripped = ip_string[:-5]
        else:
            # IPv4
            if 'h' in ip_stripped:
                print (ip_stripped)
                ip_stripped = ip_stripped.split('//')[1]
            
            ip_stripped = ip_string.split(':')[0]
            
        if len(ip_stripped) > 0:
            ip_list[row['id']] = ip_stripped

    return ip_list

def manage_processes(ip_list):
    num_processes = 64
    ip_addresses = list(ip_list.keys())

    portion_size = int(len(ip_addresses) / num_processes)

    index_start = 0
    index_end = portion_size
    processes = []
    for i in range(0, num_processes):
        ips = ip_addresses[index_start:index_end]
        ip_subset = {x: ip_list[x] for x in ips}

        processes.append(mp.Process(target=fetch_subset_measurements, args=(ip_subset, )))
        # print ('Process {} added with {} ips in total'.format(i, len(ip_subset)))

        index_start = index_end
        index_end = index_end + portion_size

    for p in processes:
        p.start()
    
    for p in processes:
        p.join()

    timing_files = [f for f in listdir('measurements/')]
    node_ids = [int(x.split('_')[0]) for x in timing_files]

def fetch_subset_measurements(ip_subset):
    for node in ip_subset:
        ip = ip_subset[node]
        try:
            r = requests.get('http://{}:8000/verloc'.format(ip), timeout=5)
            data = r.json()

            with open('measurements/{}_timings.json'.format(node), 'w') as outfile:
                json.dump(data, outfile)
        except:
            pass

def filter_node_identities(mixnodes, out_file):
    timing_files = [f for f in listdir('measurements/')]
    node_ids = [int(x.split('_')[0]) for x in timing_files]

    # only makes sense if we consider worldwide measurements
    # atm we focus on eu nodes
    mixnodes = mixnodes[mixnodes['id'].isin(node_ids)]
    mixnodes.to_csv(out_file, sep=',', index=False)

    return mixnodes

def manage_measurement_parser(node_identities):
    files = []
    for file in os.listdir('measurements/'):
        filename = os.fsdecode(file)
        if filename.endswith('.json'):
            files.append(filename)

    num_processes = 64

    portion_size = int(len(files) / num_processes)

    index_start = 0
    index_end = portion_size
    processes = []
    for i in range(0, num_processes):
        file_subset = files[index_start:index_end]

        processes.append(mp.Process(target=read_measurements, args=(file_subset, node_identities, i)))
        print ('Process {} added with {} nodes in total'.format(i, len(file_subset)))

        index_start = index_end
        index_end = index_end + portion_size

    for p in processes:
        p.start()
    
    for p in processes:
        p.join()
            
def read_measurements(measurement_subset, node_identities, process_id):

    propagation = {'FromIndex': [], 'ToIndex': [], 'TimeFromTo': []}

    for file in measurement_subset:
        from_id = file.split('_')[0]
        
        full_path = 'measurements/{}'.format(file)
        timings = pd.read_json(full_path)

        try:
            from_indices, to_indices, time_from_to = format_timings(timings, from_id, node_identities)

            propagation['FromIndex'].extend(from_indices)
            propagation['ToIndex'].extend(to_indices)
            propagation['TimeFromTo'].extend(time_from_to)
        except:
            pass

    if len(propagation['FromIndex']) > 1:
        prop_dict = pd.DataFrame.from_dict(propagation)
        prop_dict.to_csv('mp/{}_propagation.csv'.format(process_id), index=False, sep=',')

def format_timings(timings, from_index, node_identities):
    timings = pd.concat([timings.drop(['latest_measurement'], axis=1), timings['latest_measurement'].apply(pd.Series)], axis=1)
    timings = timings.dropna()

    timings.reset_index(drop=True, inplace=True)

    id_key_dict = node_identities[['identity_key', 'id']].set_index('identity_key').T.to_dict('list')
    s = timings['identity'].map(id_key_dict)

    timings['id'] = s.explode()
    timings.dropna()

    timings['minimum'] = timings['minimum'].apply(time_formatter)

    to_indices = list(timings['id'])
    time_from_to = list(timings['minimum'])
    from_indices = [from_index] * len(to_indices)
    
    return from_indices, to_indices, time_from_to

def time_formatter(time_string):
    timing = time_string.split(' ')
    seconds = 0
    for t in timing:
        if t.endswith('ms'):
            ms = t.split('ms')[0]
            seconds = seconds + int(ms) / 1000
        elif t.endswith('us'):
            us = t.split('us')[0]
            seconds = seconds + int(us) / 1e+6
        elif t.endswith('ns'):
            ns = t.split('ns')[0]
            seconds = seconds + int(ns) / 1e+9

    return seconds

def two_directional_prop(melted):
    for node_id in list(melted.FromIndex.unique()):
        subset_to = melted[melted['ToIndex'] == node_id]
        subset_from = melted[melted['FromIndex'] == node_id]
        time_dict = subset_to[['TimeFromTo', 'FromIndex']].set_index('FromIndex').T.to_dict('list')

        s = subset_from['ToIndex'].map(time_dict)
        subset_from['TimeToFrom'] = s.explode()

        melted.loc[list(subset_from.index), 'TimeToFrom'] = subset_from['TimeToFrom']

    propagation = melted.dropna()

    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')

    propagation.to_csv('static_data/melted_propagation_{}.csv'.format(timestamp), index=False, sep=',')
    return propagation

def melt_propagation(process_id):
    propagation = pd.read_csv('mp/{}_propagation.csv'.format(process_id))

    try:
        propagation = propagation.dropna()
        propagation = propagation.astype({'FromIndex': 'int'})
        propagation = propagation.astype({'ToIndex': 'int'})
  
        propagation.to_csv('mp/{}_melted.csv'.format(process_id), index=False, sep=',')
    except Exception as e:
        print (e)
        pass

def append_melted():
    for i in range(0, 64):
        tmp = pd.read_csv('mp/{}_propagation.csv'.format(i))
        tmp = tmp.dropna()
        tmp = tmp.astype({'FromIndex': 'int'})
        tmp = tmp.astype({'ToIndex': 'int'})
        if i == 0:
            melted = tmp
        else:
            melted = melted.append(tmp, ignore_index=True)

    melted = melted.dropna()

    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')

    melted.to_csv('static_data/melted_propagation_{}.csv'.format(timestamp), index=False, sep=',')
    return melted

def update_node_identities_and_melted(melted, node_identities):
    from_nodes = list(melted['FromIndex'].unique())
    to_nodes = list(melted['ToIndex'].unique())

    all_melted_nodes = list(set(from_nodes+to_nodes))

    print ('BEFORE:', len(node_identities.index), 'nodes')
    node_identities = node_identities[node_identities['id'].isin(all_melted_nodes)]
    print ('AFTER:', len(node_identities.index), 'nodes')

    lat_dict = node_identities[['id', 'lat']].set_index('id').T.to_dict('list')
    lon_dict = node_identities[['id', 'lon']].set_index('id').T.to_dict('list')

    s_from_lat = melted['FromIndex'].map(lat_dict)
    s_from_lon = melted['FromIndex'].map(lon_dict)
    s_to_lat = melted['ToIndex'].map(lat_dict)
    s_to_lon = melted['ToIndex'].map(lon_dict)

    melted['from_lat'] = s_from_lat.explode()
    melted['from_lon'] = s_from_lon.explode()
    melted['to_lat'] = s_to_lat.explode()
    melted['to_lon'] = s_to_lon.explode()

    melted = melted.dropna()

    melted['distances'] = melted.apply(lambda x: vincenty((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)) * 1000, axis=1)

    melted['speeds'] = melted.apply(lambda x: abs(x.distances / x.TimeFromTo), axis=1)

    today = date.today()
    timestamp = today.strftime('%d-%m-%Y')

    node_file = 'static_data/eu_node_identities_{}.csv'.format(timestamp)
    melted_file = 'static_data/melted_propagation_{}.csv'.format(timestamp)

    node_identities.to_csv(node_file, sep=',', index=False)
    melted.to_csv(melted_file, sep=',', index=False)

def main():
    # STEP 1: Get identities of current nodes with sufficient version
    node_file = get_raw_mixnodes()
    city_coordinates = read_city_coordinates()
    mixnodes, eu_mixnodes, out_file_full, out_file_eu = prepare_node_identities(node_file, city_coordinates)
    
    # STEP 2: Get measurements for all relevant nodes
    full_ip_list = parse_ip_addresses()
    manage_processes(full_ip_list)

    # STEP 2.5 remove nodes from list where we didn't get a response
    node_identities = filter_node_identities(eu_mixnodes, out_file_eu)

    # STEP 3: Create propagation table from measurements
    manage_measurement_parser(node_identities)

    # STEP 4: Assemble melted data
    melted = append_melted()
    final_propagation = two_directional_prop(melted)

    # STEP 5: remove nodes from the list that are not covered in the melted data
    update_node_identities_and_melted(final_propagation, node_identities)
    
if __name__ == '__main__':
    main()