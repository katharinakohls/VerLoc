#!/usr/bin/env python

import pytest

from blockchain.blockchain import Blockchain

@pytest.mark.parametrize('previous_hash,proof', [
    (None, 99),
    (b'\x11\x893\xe9-a;[\xb4T', 100)])
def test_new_block(blockchain_object, previous_hash, proof):
    epoch_index = 22
    previuos_chain_length = len(blockchain_object.chain)

    initial_pending_transactions = len(blockchain_object.pending_transactions)

    transaction_index = blockchain_object.new_transaction('random_output',{33: [b'\xa4\x12\x81v\x9fQB\x0e5\xbd', b'\x10\x04=\xab\x94a\xa79~\xd1']}, epoch_index)

    block = blockchain_object.new_block(proof, previous_hash)

    assert len(blockchain_object.pending_transactions) == 0
    assert previuos_chain_length < len(blockchain_object.chain)
    assert block['proof'] == proof
    assert block['previous_hash'] != None
    assert len(block['transactions']) == 1


@pytest.mark.parametrize('transaction_type,transaction_content', [
    ('random_output',{33: [b'\xa4\x12\x81v\x9fQB\x0e5\xbd', b'\x10\x04=\xab\x94a\xa79~\xd1']}),
    ('schedule',{44: [1,5,4,7,8,2]})])
def test_new_transaction(transaction_type, transaction_content, blockchain_object):
    epoch_index = 19

    transaction_index = blockchain_object.new_transaction(transaction_type,transaction_content,epoch_index)

    assert blockchain_object.last_block['index'] + 1 == transaction_index
    assert blockchain_object.pending_transactions[0]['type'] == transaction_type
    assert blockchain_object.pending_transactions[0]['epoch_index'] == epoch_index