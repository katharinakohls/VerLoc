import pytest
import pandas as pd

from verloc.inputs import Measurement
from verloc.inputs import Node
from verloc.inputs import Network
from verloc.inputs import Schedule
from verloc.inputs import TimingData

def test_measurement_get_min_rtt():
    new_measurement = Measurement(10, 12, [1,2,3,4,5,6,7,8,9,10])

    assert new_measurement.get_min_rtt() == 1

def test_node_get_location():
    # node_id, node_key, ip_address, lat, lon, country_code, country
    new_node = Node(1, 'abc', '1.2.3', 10, 20, 'de', 'Germany')

    assert new_node.get_location() == (10,20)

def test_create_nodes():
    n = Network('now', 1000)

    assert len(n.network) == 1000
    assert n.network[0].get_location() == (48.3200536664685,17.3730031429023)
    assert n.network[0].get_country() == 105

@pytest.mark.parametrize('network_size', [100])
def test_schedule(net_object):
    network_size = 100
    num_refs = 15

    s = Schedule(num_refs, net_object)
    schedule = s.get_schedule()

    all_correct = True
    all_unique = True
    for elem in schedule:
        if not len(schedule[elem]) == num_refs:
            all_correct = len(schedule[elem])

        duplicates = set([x for x in schedule[elem] if schedule[elem].count(x) > 1])
        if len(duplicates) > 0:
            all_unique = False

    assert all_correct == True
    assert all_unique == True

@pytest.mark.parametrize('network_size', [100])
def test_assign_timings_to_network(net_object):
    network_size = 100
    num_refs = 15
    timing = TimingData()

    assert len(net_object) == network_size

    s = Schedule(num_refs, net_object)
    schedule = s.get_schedule()

    timing.assign_timings_to_network(schedule, net_object)

    node_0_my_measurements = net_object[0].get_my_measurements()

    assert len(node_0_my_measurements) == num_refs
