#!/usr/bin/env python

import json
import click
import base64

from random import randint
from tqdm import tqdm

from blockchain import Blockchain
from network import Network

__author__ = "Katharina Kohls"
__email__ = "kkohls@cs.ru.nl"
__status__ = "Prototype"

def write_blockchain(blockchain):
    with open('blockchain.json', 'w') as fp:
        json.dump(blockchain.chain, fp)

@click.command()
@click.option('-n', '--network_size', help='Number of nodes in the network', default=20)
@click.option('-e', '--num_epochs', help='Number of epochs to run the network', default=3)
@click.option('-r', '--num_references', help='Number of references for each node', default=5)
def main(network_size, num_epochs, num_references):
    click.secho('----------------------------------------\nInitializing a new network\n----------------------------------------', fg="blue", bold=True)
    click.secho('Network Size\t {}\nEpochs\t\t {}\nReferences\t {}\nBlockchain written to blockchain.json\n----------------------------------------'.format(network_size, num_epochs, num_references), fg="blue")

    blockchain = Blockchain()
    network_object = Network(network_size)
    network = network_object.network

    init_transaction = blockchain.new_transaction('initialization', network_object.pk_network, 0)
    epoch_beacon = network_object.generate_epoch_beacon()
    blockchain.new_block(randint(0,1000))

    for epoch in tqdm(range(1,num_epochs)):
        epoch_beacon = network_object.generate_epoch_beacon()
        chain_length = blockchain.get_chain_length()

        for node_id in network:
            node = network[node_id]
            # ? put all in one transaction or split transactions

            # compute y, pi and upload to blockchain
            t_random   = node.compute_random_output(epoch_beacon, blockchain, epoch, chain_length)
            t_schedule = node.generate_schedule(num_references, epoch, network_size, blockchain)

            # measurements + measurement results in another transaction

        # one block per epoch
        blockchain.new_block(randint(0,1000))

    write_blockchain(blockchain)

if __name__ == '__main__':
    main()
