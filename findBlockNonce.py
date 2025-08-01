#!/bin/python
import hashlib
import os
import random


def mine_block(k, prev_hash, transactions):
    """
        k - Number of trailing zeros in the binary representation (integer)
        prev_hash - the hash of the previous block (bytes)
        rand_lines - a set of "transactions," i.e., data to be included in this block (list of strings)

        Complete this function to find a nonce such that 
        sha256( prev_hash + rand_lines + nonce )
        has k trailing zeros in its *binary* representation
    """
    if not isinstance(k, int) or k < 0:
        print("mine_block expects positive integer")
        return b'\x00'

    base_data = prev_hash
    for transaction in transactions:
        base_data += transaction.encode('utf-8')
    
    nonce_counter = 0
    while True:
        nonce = str(nonce_counter).encode('utf-8')
        hash_input = base_data + nonce
        hash_result = hashlib.sha256(hash_input).hexdigest()
        hash_binary = bin(int(hash_result, 16))[2:]
        hash_binary = hash_binary.zfill(256)
        trailing_zeros = 0
        for i in range(len(hash_binary) - 1, -1, -1):
            if hash_binary[i] == '0':
                trailing_zeros += 1
            else:
                break
        if trailing_zeros >= k:
            assert isinstance(nonce, bytes), 'nonce should be of type bytes'
            return nonce
        
        nonce_counter += 1

    assert isinstance(nonce, bytes), 'nonce should be of type bytes'
    return nonce


def get_random_lines(filename, quantity):
    """
    This is a helper function to get the quantity of lines ("transactions")
    as a list from the filename given. 
    Do not modify this function
    """
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line.strip())

    random_lines = []
    for x in range(quantity):
        random_lines.append(lines[random.randint(0, quantity - 1)])
    return random_lines


if __name__ == '__main__':
    # This code will be helpful for your testing
    filename = "bitcoin_text.txt"
    num_lines = 10  # The number of "transactions" included in the block

    # The "difficulty" level. For our blocks this is the number of Least Significant Bits
    # that are 0s. For example, if diff = 5 then the last 5 bits of a valid block hash would be zeros
    # The grader will not exceed 20 bits of "difficulty" because larger values take to long
    diff = 20

    transactions = get_random_lines(filename, num_lines)
    nonce = mine_block(diff, transactions)
    print(nonce)
