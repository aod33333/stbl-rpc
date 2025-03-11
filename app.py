from flask import Flask, request, jsonify
import requests
import os
from web3 import Web3

app = Flask(__name__)

STBL_ADDRESS = "0x6ba2344F60C999D0ea102C59Ab8BE6872796C08c".lower()  # Ethereum STBL
ETH_RPC = "https://eth.llamarpc.com"  # Ethereum RPC for STBL balance
BASE_RPC = "https://mainnet.base.org"  # Base RPC for proxying
w3_eth = Web3(Web3.HTTPProvider(ETH_RPC))

BALANCE_OF_ABI = {
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function"
}

@app.route('/rpc', methods=['POST'])
def handle_rpc():
    data = request.get_json()
    method = data.get("method")

    if method == "eth_chainId":
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": "0x2105"})  # Base
    if method == "wallet_addEthereumChain":
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": True})
    if method == "eth_call" and data["params"][0]["to"].lower() == "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2".lower():
        caller = "0x" + data["params"][0]["data"][34:74]  # Extract address
        contract = w3_eth.eth.contract(address=Web3.to_checksum_address(STBL_ADDRESS), abi=[BALANCE_OF_ABI])
        balance = contract.functions.balanceOf(caller).call()  # Real STBL balance from Ethereum
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": "0x" + hex(balance)[2:].zfill(64)})

    response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
    return jsonify(response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
