from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
        #YOUR CODE HERE
    w3 = connect_to(chain)
    
    # Load contract information
    contract_data = get_contract_info(chain, contract_info)
    if not contract_data:
        print(f"Failed to load contract info for {chain}")
        return 0
    
    # Get contract details
    contract_address = contract_data['address']
    contract_abi = contract_data['abi']
    
    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    # Get current block number
    current_block = w3.eth.block_number
    
    # Scan last 5 blocks
    from_block = max(0, current_block - 4)
    to_block = current_block
    
    print(f"Scanning blocks {from_block} to {to_block} on {chain} chain")
    
    try:
        if chain == 'source':
            # Look for Deposit events on source chain
            deposit_filter = contract.events.Deposit.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            
            deposit_events = deposit_filter.get_all_entries()
            
            for event in deposit_events:
                print(f"Found Deposit event: {event}")
                handle_deposit_event(event, contract_info)
                
        elif chain == 'destination':
            # Look for Unwrap events on destination chain
            unwrap_filter = contract.events.Unwrap.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            
            unwrap_events = unwrap_filter.get_all_entries()
            
            for event in unwrap_events:
                print(f"Found Unwrap event: {event}")
                handle_unwrap_event(event, contract_info)
                
    except Exception as e:
        print(f"Error scanning blocks on {chain}: {e}")
        return 0
    
    return 1


def handle_deposit_event(deposit_event, contract_info="contract_info.json"):
    """
    Handle a Deposit event from the source chain by calling wrap() on the destination chain
    """
    print("Handling Deposit event - calling wrap() on destination chain")
    
    # Extract event data
    event_args = deposit_event['args']
    token = event_args['token']
    recipient = event_args['recipient']
    amount = event_args['amount']
    
    # Connect to destination chain
    dest_w3 = connect_to('destination')
    
    # Get destination contract info
    dest_contract_data = get_contract_info('destination', contract_info)
    dest_contract_address = dest_contract_data['address']
    dest_contract_abi = dest_contract_data['abi']
    
    # Add your warden private key here (the account that deployed the contracts)
    warden_private_key = "YOUR_WARDEN_PRIVATE_KEY_HERE"  # Replace with your actual private key
    
    # Create destination contract instance
    dest_contract = dest_w3.eth.contract(address=dest_contract_address, abi=dest_contract_abi)
    
    # Get warden account
    warden_account = dest_w3.eth.account.from_key(warden_private_key)
    
    try:
        # Build transaction for wrap function
        wrap_txn = dest_contract.functions.wrap(
            token,
            recipient,
            amount
        ).build_transaction({
            'from': warden_account.address,
            'nonce': dest_w3.eth.get_transaction_count(warden_account.address),
            'gas': 200000,
            'gasPrice': dest_w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = dest_w3.eth.account.sign_transaction(wrap_txn, warden_private_key)
        tx_hash = dest_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        print(f"Wrap transaction sent: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = dest_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Wrap transaction confirmed: {receipt['transactionHash'].hex()}")
        
    except Exception as e:
        print(f"Error calling wrap function: {e}")


def handle_unwrap_event(unwrap_event, contract_info="contract_info.json"):
    """
    Handle an Unwrap event from the destination chain by calling withdraw() on the source chain
    """
    print("Handling Unwrap event - calling withdraw() on source chain")
    
    # Extract event data
    event_args = unwrap_event['args']
    underlying_token = event_args['underlying_token']
    recipient = event_args['to']  # Note: the event uses 'to' field
    amount = event_args['amount']
    
    # Connect to source chain
    source_w3 = connect_to('source')
    
    # Get source contract info
    source_contract_data = get_contract_info('source', contract_info)
    source_contract_address = source_contract_data['address']
    source_contract_abi = source_contract_data['abi']
    warden_private_key = "501422b07d89c41904f20dc3380ecc2e51a7163554d8d4fc331122d20e62d42f"  
    
    # Create source contract instance
    source_contract = source_w3.eth.contract(address=source_contract_address, abi=source_contract_abi)
    
    # Get warden account
    warden_account = source_w3.eth.account.from_key(warden_private_key)
    
    try:
        # Build transaction for withdraw function
        withdraw_txn = source_contract.functions.withdraw(
            underlying_token,
            recipient,
            amount
        ).build_transaction({
            'from': warden_account.address,
            'nonce': source_w3.eth.get_transaction_count(warden_account.address),
            'gas': 200000,
            'gasPrice': source_w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = source_w3.eth.account.sign_transaction(withdraw_txn, warden_private_key)
        tx_hash = source_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        print(f"Withdraw transaction sent: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Withdraw transaction confirmed: {receipt['transactionHash'].hex()}")
        
    except Exception as e:
        print(f"Error calling withdraw function: {e}")


if __name__ == "__main__":
    # Test the bridge functionality
    print("Testing bridge functionality...")
    
    # Scan source chain for Deposit events
    print("Scanning source chain...")
    scan_blocks('source')
    
    # Scan destination chain for Unwrap events
    print("Scanning destination chain...")
    scan_blocks('destination')
