#!/usr/bin/env python

import secrets
import hashlib
import base64
import ecvrf_edwards25519_sha512_elligator2

from random import randint

from blockchain import Blockchain

class Node():
    """
    Represents a node in the network infrastructure

    ...

    Attributes
    ----------
    node_id : int
        unique ID
    secret_key : bytes
        unique secret key
    public_key : bytes
        corresponding public key
    last_update_epoch : int
        keeps track of the epoch in which node had the last update (of schedules and measurements)
    epoch_blocks : dict
        keeps track of the block that was added in an epoch
    p_status : str
        status string for ecvrf_edwards25519_sha512_elligator2.ecvrf_prove
    pi_string : bytes
        proof for ecvrf_edwards25519_sha512_elligator2.ecvrf_prove
    b_status : str
        status string for ecvrf_edwards25519_sha512_elligator2.ecvrf_proof_to_hash
    beta_string : bytes
        hash output for ecvrf_edwards25519_sha512_elligator2.ecvrf_proof_to_hash
    schedule : list
        schedule of random references to be measured

    Methods
    -------
    compute_random_output(epoch_beacon, blockchain, epoch, block_id)
        Creates a transaction with the VRF random output and proof for the current epoch beacon.
    prove_random_output(schedule_data, epoch_beacon)
        Checks the current schedule and verifies its correctness using the VRF.
    generate_schedule(t, epoch, network_size, blockchain)
        Creates a transaction with t random references derived from the VRF input and a hash function.
    """
    def __init__(self, node_id):
        """
        Constructs all the necessary attributes for the node object.

        Parameters
        ----------
            node_id : int
                unique ID
            secret_key : bytes
                unique secret key
            public_key : bytes
                corresponding public key
            last_update_epoch : int
                keeps track of the epoch in which node had the last update (of schedules and measurements)
            epoch_blocks : dict
                keeps track of the block that was added in an epoch
            p_status : str
                status string for ecvrf_edwards25519_sha512_elligator2.ecvrf_prove
            pi_string : bytes
                proof for ecvrf_edwards25519_sha512_elligator2.ecvrf_prove
            b_status : str
                status string for ecvrf_edwards25519_sha512_elligator2.ecvrf_proof_to_hash
            beta_string : bytes
                hash output for ecvrf_edwards25519_sha512_elligator2.ecvrf_proof_to_hash
            schedule : list
                schedule of random references to be measured
        """

        # node credentials
        self.node_id = node_id
        self.secret_key = secrets.token_bytes(nbytes=32)
        self.public_key = ecvrf_edwards25519_sha512_elligator2.get_public_key(self.secret_key)

        # keep track of blocks and epochs
        self.last_update_epoch = -1
        self.epoch_blocks = {}

        # VRF
        self.p_status = None 
        self.pi_string = None
        self.b_status = None
        self.beta_string = None

        # references
        self.schedule = None 

    def compute_random_output(self, epoch_beacon, blockchain, epoch, block_id):
        """
        Creates a transaction with the VRF random output and proof for the current epoch beacon.

        Parameters
        ----------
        epoch_beacon : bytes
            Random beacon for the current epoch
        blockchain : Blockchain
            Global blockchain of a deployed system
        epoch : int
            Index of the current epoch
        block_id : int
            Index of the current block in the blockchain

        Returns
        -------
        transaction : dict
            New transaction including the random output of this node
        """

        self.p_status, self.pi_string = ecvrf_edwards25519_sha512_elligator2.ecvrf_prove(self.secret_key, epoch_beacon)
        self.b_status, self.beta_string = ecvrf_edwards25519_sha512_elligator2.ecvrf_proof_to_hash(self.pi_string)

        pi_string_enc = base64.b64encode(self.pi_string).decode('ascii')
        beta_string_enc = base64.b64encode(self.beta_string).decode('ascii')
        
        transaction = blockchain.new_transaction('random_output', {self.node_id: [pi_string_enc, beta_string_enc]}, epoch)

        self.last_update_epoch = epoch

        # ? obsolete
        self.epoch_blocks[epoch] = block_id
        
        return transaction

    # ! NOT USED
    # def prove_random_output(self, schedule_data, epoch_beacon):
    #     """
    #     Checks the current schedule and verifies its correctness using the VRF.

    #     Parameters
    #     ----------
    #     schedule_data : dict
    #         All scheduled measurements and the pk and proof, respectively
    #     epoch_beacon : bytes
    #         Random beacon for the current epoch

    #     Returns
    #     -------
    #     # TODO
    #     """
    #     for elem in schedule_data:
    #         public_key = schedule_data[elem]['pk']
    #         pi_string = schedule_data[elem]['pi']

    #         result, beta_string2 = ecvrf_edwards25519_sha512_elligator2.ecvrf_verify(public_key, pi_string, epoch_beacon)
    #         # ? can I skip the status fields and only focus on the result?
    #         if self.p_status == "VALID" and self.b_status == "VALID" and result == "VALID" and self.beta_string == beta_string2:
    #             print("Commitment verified")
    #             # TODO notify that results are not valid

    def generate_schedule(self, t, epoch, network_size, blockchain):
        """
        Creates a transaction with t random references derived from the VRF input and a hash function.

        Parameters
        ----------
        t : int
            Number of references to be generated
        epoch : int
            Index of the current epoch
        network_size : int
            Number of nodes in the network
        blockchain : Blockchain
            Global blockchain of a deployed system

        Returns
        -------
        transaction : dict
            New transaction including the schedule of random references
        """
        
        schedule = [] # list of random references
        hash_input = self.beta_string # hash the new result over and over again

        if self.last_update_epoch == epoch: 
            # we only generate a schedule if there is up-to-date information
            while len(schedule) < t: # ! we don't have a fallback break condition
                ''' we will hash hash_input over and over again to generate new references '''
                raw_hash = hashlib.sha256(hash_input)
                hex_hash = raw_hash.hexdigest()

                ref_hash = int(hashlib.sha256(hex_hash.encode('utf-8')).hexdigest(), 16)
                new_ref = ref_hash % network_size

                hash_input = str(ref_hash).encode('utf-8')

                if new_ref not in schedule:
                    schedule.append(new_ref)

            transaction = blockchain.new_transaction('schedule', {self.node_id: schedule}, epoch)

        self.schedule = schedule
        return transaction

    def upload_measurements(self):
        # TODO
        pass

class Network():
    """
    Represents the network

    ...

    Attributes
    ----------
    network_size : int
        How many nodes should be initialized
    network : dict
        Network representation in the form node_id: node
    pk_network : dict
        Network representation in the form node_id: pk(node)
   
    Methods
    -------
    generate_epoch_beacon()
        Generates a random beacon. This can be replaced by any source of randomness or a blockchain function.
    """
    def __init__(self, network_size):
        """
        Constructs all the necessary attributes for the network object.

        Parameters
        ----------
        network_size : int
            How many nodes should be initialized
        """
        network = {}
        pk_network = {}
        for node_id in range(0, network_size):
            ''' Create a new node  '''
            node = Node(node_id)
            network[node_id] = node
        
            pk_enc = base64.b64encode(node.public_key).decode('ascii')
            pk_network[node_id] = pk_enc

        self.network = network
        self.pk_network = pk_network

    def generate_epoch_beacon(self):
        ''' Generate a new random beacon  '''
        return open("/dev/urandom","rb").read(10)
