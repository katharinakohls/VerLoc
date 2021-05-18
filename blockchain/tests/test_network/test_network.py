import pytest
from blockchain.network import Node

def test_compute_random_output(node_object, epoch_beacon, blockchain_object):
    epoch = 100
    block_id = 33

    try:
        transaction_index = node_object.compute_random_output(epoch_beacon, blockchain_object, epoch, block_id)
        test_compute_random_output_success = True
    except Exception as e:
        print ('Failed to test_compute_random_output:', e)
        test_compute_random_output_success = False

    assert test_compute_random_output_success == True

    assert blockchain_object.pending_transactions[0]['type'] == 'random_output'
    assert len( blockchain_object.pending_transactions[0]['content'][node_object.node_id]) == 2
    assert  blockchain_object.pending_transactions[0]['epoch_index'] == epoch
    
    assert node_object.last_update_epoch == epoch
    assert node_object.epoch_blocks[epoch] == block_id


def test_generate_schedule(node_object, blockchain_object, epoch_beacon):
    epoch = 99
    block_id = 123

    t = 5
    network_size = 100

    try:
        # we need a the beta string to compute a schedule
        transaction = node_object.compute_random_output(epoch_beacon, blockchain_object, epoch, block_id)
        compute_random_output_success = True
        try:
            node_object.generate_schedule(t, epoch, network_size, blockchain_object)
            in_time_schedule_attempt = True
        except Exception as e:
            print ('Failed to compute_random_output:', e)
            in_time_schedule_attempt = False
    except Exception as e:
        print ('Failed to generate_schedule:', e)
        compute_random_output_success = False

    assert compute_random_output_success == True
    assert in_time_schedule_attempt == True
    assert len(node_object.schedule) == t

def test_generate_epoch_beacon(network_object):
    beacon_a = network_object.generate_epoch_beacon()
    beacon_b = network_object.generate_epoch_beacon()

    assert beacon_a != beacon_b

def test_upload_measurements():
    pass