@app.route('/')
def add_token():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Token</title>
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                background-color: #f5f5f5;
                color: #333;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
                text-align: center;
            }
            h1 {
                font-size: 24px;
                margin-bottom: 10px;
            }
            p {
                font-size: 16px;
                margin-bottom: 20px;
            }
            .token-info {
                background: #f9f9f9;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: left;
            }
            .token-info img {
                width: 32px;
                vertical-align: middle;
                margin-right: 10px;
            }
            .status {
                margin-top: 10px;
                font-size: 14px;
                color: #666;
            }
            button {
                background: #0066cc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }
            @media (max-width: 480px) {
                .container {
                    margin: 10px;
                }
            }
        </style>
        <script>
            function waitForEthereum() {
                return new Promise((resolve, reject) => {
                    if (window.ethereum) {
                        return resolve(window.ethereum);
                    }
                    
                    let attempts = 0;
                    const maxAttempts = 20; // 10 seconds total
                    
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
                    
                    // Request account access first
                    status.textContent = 'Requesting account access...';
                    const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
                    
                    // Switch to our chain
                    status.textContent = 'Switching to Base Spoofed...';
                    await ethereum.request({
                        method: 'wallet_switchEthereumChain',
                        params: [{ chainId: '0x2105' }]
                    });
                    
                    // Check balance first to ensure the token is visible
                    status.textContent = 'Checking token balance...';
                    const account = accounts[0];
                    const tokenAddress = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
                    
                    // Call balanceOf function (function signature + padded address)
                    const functionSelector = '0x70a08231';
                    const paddedAddress = account.slice(2).padStart(64, '0');
                    const data = functionSelector + paddedAddress;
                    
                    await ethereum.request({
                        method: 'eth_call',
                        params: [
                            {
                                to: tokenAddress,
                                data: data
                            },
                            'latest'
                        ]
                    });
                    
                    // Now add the token
                    status.textContent = 'Requesting token addition...';
                    await ethereum.request({
                        method: 'wallet_watchAsset',
                        params: {
                            type: 'ERC20',
                            options: {
                                address: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                                symbol: 'USDT',
                                decimals: 6,
                                image: 'https://assets.coingecko.com/coins/images/325/large/Tether.png'
                            }
                        }
                    });
                    
                    status.textContent = 'Token added! If balance is not visible, try the refresh button.';
                    document.getElementById('refresh-button').style.display = 'block';
                } catch (error) {
                    status.textContent = 'Failed: ' + error.message;
                    if (error.code === 4902) {
                        status.textContent += ' (Network not found - please add the network first)';
                    }
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Add USDT Token</h1>
            <p>Add the spoofed USDT token to your wallet</p>
            <div class="token-info">
                <img src="https://assets.coingecko.com/coins/images/325/large/Tether.png" alt="USDT">
                <span>Tether USD (USDT)</span>
            </div>
            <button onclick="addToken()">Add Token to Wallet</button>
            <div id="status" class="status"></div>
            <button id="refresh-button" style="display: none; background: #666;" onclick="location.reload()">Refresh</button>
        </div>
    </body>
    </html>
    """)
