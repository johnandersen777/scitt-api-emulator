import asyncio
import hashlib
import os
import subprocess
import time
from pathlib import Path
from pydantic import BaseModel, Field, validator
from web3 import Web3
from web3.auto import w3
import aiofiles
import pytest
import json
import psutil
import socket
from eth_account import Account


### Step 1: Utility to Get Random Available Port ###

def get_free_port() -> int:
    """Find an available random port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


### Step 2: Utility to Get Ethereum Credentials from Env or Generate ###

def get_ethereum_credentials(gas_wait_time: int) -> tuple[str, str]:
    """Get Ethereum credentials from environment variables or generate them dynamically."""
    private_key = os.getenv('ETH_PRIVATE_KEY')
    address = os.getenv('ETH_ADDRESS')

    if not private_key or not address:
        # Generate a new Ethereum account
        account = Account.create()
        private_key = account.privateKey.hex()
        address = account.address
        print(f"Generated new Ethereum account: {address}")

        # Simulate waiting for gas (configurable wait time)
        print(f"Waiting for {gas_wait_time} seconds to simulate gas wait...")
        time.sleep(gas_wait_time)
    
    return private_key, address


### Step 3: Define Pydantic Classes with Descriptions ###

class EthereumConfig(BaseModel):
    """Configuration for Ethereum connection and transaction details"""
    rpc_url: str = Field(..., description="RPC URL for the Ethereum network, e.g., Ganache")
    sender_private_key: str = Field(..., description="Sender's private key for signing transactions")
    sender_address: str = Field(..., description="Ethereum address of the sender for the transaction")
    chain_id: int = Field(1337, description="Chain ID of the Ethereum network (1337 for Ganache, 1 for Mainnet)")
    gas_wait_time: int = Field(5, description="Time to wait in seconds to simulate gas wait")

    @validator('rpc_url')
    def validate_rpc_url(cls, v):
        if not v.startswith('http'):
            raise ValueError('Invalid RPC URL')
        return v

    @validator('sender_private_key', 'sender_address')
    def validate_non_empty(cls, v, field):
        if not v:
            raise ValueError(f'{field.name} cannot be empty')
        return v


class ContractDetails(BaseModel):
    """Details of the deployed contract"""
    address: str = Field("", description="Deployed contract address on the Ethereum network")
    abi: list = Field([], description="ABI (Application Binary Interface) for interacting with the contract")

    @validator('address')
    def validate_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid contract address')
        return v


class FileContext(BaseModel):
    """Details for the file being hashed"""
    path: Path = Field(..., description="Path to the file whose hash will be computed")

    @validator('path')
    def validate_path(cls, v):
        if not v.exists():
            raise ValueError(f"File does not exist: {v}")
        return v


### Step 4: Web3 and Smart Contract Utilities ###

# Utility to deploy contract using web3.py
async def deploy_contract(w3: Web3, contract_source: str) -> ContractDetails:
    compiled_sol = compile_solidity(contract_source)
    contract_interface = compiled_sol['FileHashStorage']
    contract = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

    tx_hash = contract.constructor().transact({
        'from': w3.eth.accounts[0],
        'gas': 4000000,
        'gasPrice': w3.toWei('1', 'gwei'),
    })
    
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return ContractDetails(address=tx_receipt.contractAddress, abi=contract_interface['abi'])


# Utility to compile solidity contracts (using solcx)
def compile_solidity(source_code: str) -> dict:
    from solcx import compile_source
    return compile_source(source_code, output_values=["abi", "bin"])


# Compute file hash asynchronously
async def compute_file_hash(file_context: FileContext) -> str:
    hash_func = hashlib.sha256()
    
    async with aiofiles.open(file_context.path, 'rb') as file:
        while True:
            chunk = await file.read(1024)
            if not chunk:
                break
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


# Store file hash in deployed contract
async def store_hash_with_contract(w3: Web3, contract_details: ContractDetails, eth_config: EthereumConfig, file_hash: str):
    contract = w3.eth.contract(address=contract_details.address, abi=contract_details.abi)
    
    txn = contract.functions.storeFileHash(file_hash).buildTransaction({
        'from': eth_config.sender_address,
        'nonce': w3.eth.getTransactionCount(eth_config.sender_address),
        'gas': 3000000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'chainId': eth_config.chain_id
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, eth_config.sender_private_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
    return receipt.transactionHash.hex()


### Step 5: Ganache Setup ###

def start_ganache() -> tuple[subprocess.Popen, int]:
    """Starts Ganache on a random port and returns the subprocess object and port."""
    port = get_free_port()
    ganache_proc = subprocess.Popen([
        'npx', 'ganache-cli', '--port', str(port), '--accounts', '10'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait a moment to ensure Ganache is up
    time.sleep(5)
    
    return ganache_proc, port


def stop_ganache(ganache_proc: subprocess.Popen):
    """Stops the Ganache process."""
    ganache_proc.terminate()
    ganache_proc.wait()


### Step 6: Pytest Fixture ###

@pytest.fixture(scope="module")
def w3_and_contract():
    # Retrieve Ethereum credentials and configuration
    gas_wait_time = int(os.getenv('GAS_WAIT_TIME', 5))
    sender_private_key, sender_address = get_ethereum_credentials(gas_wait_time)

    # Set up EthereumConfig
    eth_config = EthereumConfig(
        rpc_url=f'http://127.0.0.1:{get_free_port()}',
        sender_private_key=sender_private_key,
        sender_address=sender_address,
    )

    ganache_proc, ganache_port = start_ganache()
    try:
        w3 = Web3(Web3.HTTPProvider(f'http://127.0.0.1:{ganache_port}'))
        
        # Deploy the contract
        contract_source = """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;

        contract FileHashStorage {
            mapping(string => bool) public storedHashes;

            function storeFileHash(string memory fileHash) public {
                storedHashes[fileHash] = true;
            }

            function isFileHashStored(string memory fileHash) public view returns (bool) {
                return storedHashes[fileHash];
            }
        }
        """
        contract_details = asyncio.run(deploy_contract(w3, contract_source))
        
        yield w3, contract_details
    finally:
        stop_ganache(ganache_proc)


### Step 7: Test File Hash Storage ###

@pytest.mark.asyncio
async def test_file_hash_storage(w3_and_contract):
    w3, contract_details = w3_and_contract
    
    # Define Ethereum configuration
    eth_config = EthereumConfig(
        rpc_url=w3.provider.endpoint_uri,
        sender_private_key=os.getenv('ETH_PRIVATE_KEY', 'your_private_key_here'),
        sender_address=w3.eth.accounts[0]
    )

    # Create a dummy file for testing
    test_file = Path("test_file.txt")
    test_file.write_text("This is a test file")

    # Create a FileContext object
    file_context = FileContext(path=test_file)

    # Compute the hash
    file_hash = await compute_file_hash(file_context)
    assert file_hash is not None

    # Store the hash in the contract
    txn_hash = await store_hash_with_contract(w3, contract_details, eth_config, file_hash)
    assert txn_hash is not None

    # Clean up the test file
    test_file.unlink()
