#!/usr/bin/env python

import hashlib
import json
import base64
import sys
import pickle

from time import time
from random import randint

# https://github.com/mchrupcala/blockchain-walkthrough/blob/master/walkthrough.py

class Blockchain():
    """
    Central blockchain of the network

    ...

    Attributes
    ----------
    chain : list
        List of all blocks
    pending_transactions : list
        List of current pending transactions
   
    Methods
    -------
    get_chain_length()
        Returns the current length of the chain.
    new_block(self, proof, previous_hash=None)
        Creates a new block for all pending transactions and appends it to the chain.
    hash(block)
        Converts block contents into strings where needed and hashes the entire block.
    """
    def __init__(self):
        """
        Constructs all the necessary attributes for the blockchain object.

        Parameters
        ----------
        chain : list
            List of all blocks
        pending_transactions : list
            List of current pending transactions
        """
        self.chain = []
        self.pending_transactions = []

        self.new_block(previous_hash="genesis block", proof=100)

    @property
    def last_block(self):
        return self.chain[-1]

    def get_chain_length(self):
        return len(self.chain)

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new block and inserts all pending transactions, then adds it to the chain.

        Parameters
        ----------
        proof : int
            In theory this would be the proof needed for a new block. We don't use this as a security feature.
        previous_hash=None : bytes
            Hash of the previous block. We don't use this as a security feature.

        Returns
        -------
        block : dict
            New block that was appended to the chain.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_transactions = []
        self.chain.append(block)

        return block

    def new_transaction(self, transaction_type, transaction_content, epoch_index):
        """
        Creates a new transaction and appends it to the list of pending transactions.

        Parameters
        ----------
        transaction_type : str
            We have different transaction types and use this string to distinguish them in the blockchain.add()
            # TODO use a class for transactions
        transaction_content : dict
            Content of the transaction in the form node_id: content. The content can be a single item or a list, depending on the transaction type.
        epoch_index : int
            Index of the current epoch.

        Returns
        -------
        block_index : int
            Index of the new block
        """
        transaction = {
            'type': transaction_type,
            'content': transaction_content,
            'epoch_index': epoch_index, 
        }
        self.pending_transactions.append(transaction)
        block_index = self.last_block['index'] + 1
        return block_index

    def hash(self, block):
        """
        Hashes a full block.

        Parameters
        ----------
        block : dict
            Dict of the block that we want to hash

        Returns
        -------
        hex_hash : bytes
            Hash of the block
        """
        block_string = ''
        for key in block:
            try:
                block_string = block_string + str(block[key])
            except Exception as e:
                print ('Could not convert to string:', e)
        
        byte_string = block_string.encode()
        raw_hash = hashlib.sha256(byte_string)
        hex_hash = raw_hash.hexdigest()

        return hex_hash