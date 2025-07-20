import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains


def merkle_assignment():
    """
        The only modifications you need to make to this method are to assign
        your "random_leaf_index" and uncomment the last line when you are
        ready to attempt to claim a prime. You will need to complete the
        methods called by this method to generate the proof.
    """
    # Generate the list of primes as integers
    num_of_primes = 8192
    primes = generate_primes(num_of_primes)

    # Create a version of the list of primes in bytes32 format
    leaves = convert_leaves(primes)

    # Build a Merkle tree using the bytes32 leaves as the Merkle tree's leaves
    tree = build_merkle(leaves)

    # Select a random leaf and create a proof for that leaf
    random_leaf_index = random.randint(1, len(primes) - 1)
    proof = prove_merkle(tree, random_leaf_index)

    # This is the same way the grader generates a challenge for sign_challenge()
    challenge = ''.join(random.choice(string.ascii_letters) for i in range(32))
    # Sign the challenge to prove to the grader you hold the account
    addr, sig = sign_challenge(challenge)

    if sign_challenge_verify(challenge, addr, sig):
        tx_hash = '0x'
        # TODO, when you are ready to attempt to claim a prime (and pay gas fees),
        #  complete this method and run your code with the following line un-commented
        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])


def generate_primes(num_primes):
    """
        Function to generate the first 'num_primes' prime numbers
        returns list (with length n) of primes (as ints) in ascending order
    """
    primes_list = []
    
    if num_primes < 6:
        limit = 30
    else:
        import math
        limit = int(num_primes * (math.log(num_primes) + math.log(math.log(num_primes))))
    
    prime = [True] * (limit + 1)
    p = 2
    
    while p * p <= limit:
        if prime[p]:
            for i in range(p * p, limit + 1, p):
                prime[i] = False
        p += 1
    
    for p in range(2, limit + 1):
        if prime[p]:
            primes_list.append(p)
            if len(primes_list) >= num_primes:
                break
    
    return primes_list[:num_primes]


def convert_leaves(primes_list):
    """
        Converts the leaves (primes_list) to bytes32 format
        returns list of primes where list entries are bytes32 encodings of primes_list entries
    """
    leaves = []
    
    for prime in primes_list:
        prime_bytes = prime.to_bytes(32, 'big')
        leaves.append(prime_bytes)
    
    return leaves


def build_merkle(leaves):
    """
        Function to build a Merkle Tree from the list of prime numbers in bytes32 format
        Returns the Merkle tree (tree) as a list where tree[0] is the list of leaves,
        tree[1] is the parent hashes, and so on until tree[n] which is the root hash
        the root hash produced by the "hash_pair" helper function
    """
    tree = []
    current_level = leaves[:]
    tree.append(current_level[:])
    
    while len(current_level) > 1:
        next_level = []
        
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                parent_hash = hash_pair(current_level[i], current_level[i + 1])
            else:
                parent_hash = current_level[i]
            
            next_level.append(parent_hash)
        
        current_level = next_level
        tree.append(current_level[:])
    
    return tree


def prove_merkle(merkle_tree, random_indx):
    """
        Takes a random_index to create a proof of inclusion for and a complete Merkle tree
        as a list of lists where index 0 is the list of leaves, index 1 is the list of
        parent hash values, up to index -1 which is the list of the root hash.
        returns a proof of inclusion as list of values
    """
    merkle_proof = []
    current_index = random_indx
    
    for level in range(len(merkle_tree) - 1):
        current_level = merkle_tree[level]
        
        if current_index % 2 == 0:
            sibling_index = current_index + 1
        else:
            sibling_index = current_index - 1
        
        if sibling_index < len(current_level):
            merkle_proof.append(current_level[sibling_index])
        
        current_index = current_index // 2
    
    return merkle_proof


def sign_challenge(challenge):
    """
        Takes a challenge (string)
        Returns address, sig
        where address is an ethereum address and sig is a signature (in hex)
        This method is to allow the auto-grader to verify that you have
        claimed a prime
    """
    acct = get_account()

    addr = acct.address
    eth_sk = acct.key

    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)
    
    eth_sig_obj = acct.sign_message(eth_encoded_msg)

    signature_hex = eth_sig_obj.signature.hex()
    
    if signature_hex.startswith('0x'):
        signature_hex = signature_hex[2:]

    return addr, signature_hex


def send_signed_msg(proof, random_leaf):
    """
        Takes a Merkle proof of a leaf, and that leaf (in bytes32 format)
        builds signs and sends a transaction claiming that leaf (prime)
        on the contract
    """
    chain = 'bsc'
    
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)
    
    contract = w3.eth.contract(address=address, abi=abi)
    
    nonce = w3.eth.get_transaction_count(acct.address)
    
    transaction = contract.functions.submit(proof, random_leaf).build_transaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.to_wei('5', 'gwei'),
    })
    
    signed_txn = acct.sign_transaction(transaction)
    
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_hash.hex()


# Helper functions that do not need to be modified
def connect_to(chain):
    """
        Takes a chain ('avax' or 'bsc') and returns a web3 instance
        connected to that chain.
    """
    if chain not in ['avax','bsc']:
        print(f"{chain} is not a valid option for 'connect_to()'")
        return None
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    else:
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    w3 = Web3(Web3.HTTPProvider(api_url))
    # inject the poa compatibility middleware to the innermost layer
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    return w3


def get_account():
    """
        Returns an account object recovered from the secret key
        in "sk.txt"
    """
    cur_dir = Path(__file__).parent.absolute()
    with open(cur_dir.joinpath('sk.txt'), 'r') as f:
        sk = f.readline().rstrip()
    if sk[0:2] == "0x":
        sk = sk[2:]
    return eth_account.Account.from_key(sk)


def get_contract_info(chain):
    """
        Returns a contract address and contract abi from "contract_info.json"
        for the given chain
    """
    contract_file = Path(__file__).parent.absolute() / "contract_info.json"
    if not contract_file.is_file():
        contract_file = Path(__file__).parent.parent.parent / "tests" / "contract_info.json"
    with open(contract_file, "r") as f:
        d = json.load(f)
        d = d[chain]
    return d['address'], d['abi']


def sign_challenge_verify(challenge, addr, sig):
    """
        Helper to verify signatures, verifies sign_challenge(challenge)
        the same way the grader will. No changes are needed for this method
    """
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)

    if eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == addr:
        print(f"Success: signed the challenge {challenge} using address {addr}!")
        return True
    else:
        print(f"Failure: The signature does not verify!")
        print(f"signature = {sig}\naddress = {addr}\nchallenge = {challenge}")
        return False


def hash_pair(a, b):
    """
        The OpenZeppelin Merkle Tree Validator we use sorts the leaves
        https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MerkleProof.sol#L217
        So you must sort the leaves as well

        Also, hash functions like keccak are very sensitive to input encoding, so the solidity_keccak function is the function to use

        Another potential gotcha, if you have a prime number (as an int) bytes(prime) will *not* give you the byte representation of the integer prime
        Instead, you must call int.to_bytes(prime,'big').
    """
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])


if __name__ == "__main__":
    merkle_assignment()
