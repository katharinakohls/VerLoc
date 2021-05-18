import pytest

from blockchain.blockchain import Blockchain
from blockchain.network import Network, Node

@pytest.fixture
def node_object():
    node = Node(33)
    return node

@pytest.fixture
def network_object():
    network = Network(10)
    return network

@pytest.fixture
def blockchain_object():
    blockchain = Blockchain()
    return blockchain

@pytest.fixture
def epoch_beacon():
    network = Network(0)
    epoch_beacon = network.generate_epoch_beacon()
    return epoch_beacon
