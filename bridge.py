from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware
from datetime import datetime
import json

def connect_to(chain):
    if chain == 'source':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == 'destination':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError("Invalid chain name")
    
    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

def get_contract_info(chain, contract_info_path="contract_info.json"):
    try:
        with open(contract_info_path, 'r') as f:
            contracts = json.load(f)
        return contracts[chain]
    except Exception as e:
        print(f"Failed to read contract info: {e}")
        return None

with open("contract_info.json") as f:
    key_data = json.load(f)
    WARDEN_KEY = key_data['source']['warden_key']

def scan_blocks(chain, contract_info_path="contract_info.json"):
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return 0

    w3 = connect_to(chain)
    contract_data = get_contract_info(chain, contract_info_path)
    if not contract_data:
        return 0

    contract_address = Web3.to_checksum_address(contract_data['address'])
    contract_abi = contract_data['abi']
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    current_block = w3.eth.block_number
    from_block = max(0, current_block - 4)

    print(f"[{datetime.utcnow()}] Scanning blocks {from_block} to {current_block} on {chain} chain")

    try:
        if chain == 'source':
            events = contract.events.Deposit.create_filter(fromBlock=from_block, toBlock=current_block).get_all_entries()
            for event in events:
                print(f"[{datetime.utcnow()}] Found Deposit event: {event}")
                handle_deposit_event(event, contract_info_path)
        elif chain == 'destination':
            events = contract.events.Unwrap.create_filter(fromBlock=from_block, toBlock=current_block).get_all_entries()
            for event in events:
                print(f"[{datetime.utcnow()}] Found Unwrap event: {event}")
                handle_unwrap_event(event, contract_info_path)
    except Exception as e:
        print(f"Error scanning blocks on {chain}: {e}")
        return 0

    return 1

def handle_deposit_event(deposit_event, contract_info_path="contract_info.json"):
    print(f"[{datetime.utcnow()}] Handling Deposit event - calling wrap() on destination chain")

    args = deposit_event['args']
    token = Web3.to_checksum_address(args['token'])
    recipient = Web3.to_checksum_address(args['recipient'])
    amount = args['amount']

    dest_w3 = connect_to('destination')
    dest_contract_data = get_contract_info('destination', contract_info_path)
    dest_contract_address = Web3.to_checksum_address(dest_contract_data['address'])
    dest_contract_abi = dest_contract_data['abi']
    dest_contract = dest_w3.eth.contract(address=dest_contract_address, abi=dest_contract_abi)
    warden_account = dest_w3.eth.account.from_key(WARDEN_KEY)

    try:
        gas_estimate = dest_contract.functions.wrap(token, recipient, amount).estimate_gas({'from': warden_account.address})
        tx = dest_contract.functions.wrap(token, recipient, amount).build_transaction({
            'from': warden_account.address,
            'nonce': dest_w3.eth.get_transaction_count(warden_account.address),
            'gas': gas_estimate + 10000,
            'gasPrice': dest_w3.eth.gas_price
        })
        signed = dest_w3.eth.account.sign_transaction(tx, WARDEN_KEY)
        tx_hash = dest_w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = dest_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"[{datetime.utcnow()}] Wrap transaction confirmed: {receipt['transactionHash'].hex()}")
    except Exception as e:
        print(f"Error in wrap transaction: {e}")

def handle_unwrap_event(unwrap_event, contract_info_path="contract_info.json"):
    print(f"[{datetime.utcnow()}] Handling Unwrap event - calling withdraw() on source chain")

    args = unwrap_event['args']
    underlying_token = Web3.to_checksum_address(args['underlying_token'])
    recipient = Web3.to_checksum_address(args['to'])
    amount = args['amount']

    source_w3 = connect_to('source')
    source_contract_data = get_contract_info('source', contract_info_path)
    source_contract_address = Web3.to_checksum_address(source_contract_data['address'])
    source_contract_abi = source_contract_data['abi']
    source_contract = source_w3.eth.contract(address=source_contract_address, abi=source_contract_abi)
    warden_account = source_w3.eth.account.from_key(WARDEN_KEY)

    try:
        gas_estimate = source_contract.functions.withdraw(underlying_token, recipient, amount).estimate_gas({'from': warden_account.address})
        tx = source_contract.functions.withdraw(underlying_token, recipient, amount).build_transaction({
            'from': warden_account.address,
            'nonce': source_w3.eth.get_transaction_count(warden_account.address),
            'gas': gas_estimate + 10000,
            'gasPrice': source_w3.eth.gas_price
        })
        signed = source_w3.eth.account.sign_transaction(tx, WARDEN_KEY)
        tx_hash = source_w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"[{datetime.utcnow()}] Withdraw transaction confirmed: {receipt['transactionHash'].hex()}")
    except Exception as e:
        print(f"Error in withdraw transaction: {e}")

if __name__ == "__main__":
    print(f"[{datetime.utcnow()}] Starting bridge script...")
    scan_blocks('source')
    scan_blocks('destination')
