from flask import Flask, request
import json
import base64
import os

app = Flask(__name__)

@app.route('/add')
def add_to_wallet():
    encoded_data = request.args.get('data')
    data = json.loads(base64.b64decode(encoded_data).decode('utf-8'))
    script = f"""
    <script>
    if (window.ethereum) {{
      window.ethereum.request({json.dumps({"method": "wallet_addEthereumChain", "params": [data["chain"]]})})
        .then(() => window.ethereum.request({json.dumps({"method": "wallet_watchAsset", "params": data["token"]})}))
        .catch(err => alert('Error: ' + err.message));
    }} else {{
      alert('Please install MetaMask!');
    }}
    </script>
    """
    return f"<html><body>{script}</body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
