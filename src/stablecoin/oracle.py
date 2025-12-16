import logging
import requests
import numpy as np
import pandas as pd
from web3 import Web3
from cryptography.hazmat.primitives.asymmetric import dilithium  # Quantum-resistant signing
from src.models.ai_model import QuantumAIStabilizer  # Import the upgraded AI model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HyperTechOracle:
    def __init__(self, web3_provider: str, ai_model_path: str = "models/hybrid_stabilizer.pkl", sources: list = None):
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.ai_stabilizer = QuantumAIStabilizer(model_path=ai_model_path)
        self.sources = sources or [
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"  # Multi-source for decentralization
        ]
        self.quantum_key = dilithium.generate_private_key()  # For signing oracle data

    def fetch_price_feeds(self, asset: str = "bitcoin") -> dict:
        """Aggregate prices from multiple sources with AI prediction."""
        prices = []
        for url in self.sources:
            try:
                response = requests.get(url.replace("bitcoin", asset.lower()), timeout=5)
                data = response.json()
                if "coingecko" in url:
                    price = data.get(asset.lower(), {}).get('usd', 0)
                elif "binance" in url:
                    price = float(data.get('price', 0))
                elif "kraken" in url:
                    price = float(data.get('result', {}).get('XXBTZUSD', {}).get('c', [0])[0])
                prices.append(price)
            except Exception as e:
                logging.warning(f"Failed to fetch from {url}: {e}")
        
        if not prices:
            raise ValueError("No valid price feeds available")
        
        # Aggregate with median for outlier resistance
        median_price = np.median(prices)
        
        # AI prediction for next price (predictive stabilization)
        historical_data = np.array(prices[-30:])  # Last 30 feeds as dummy history
        if len(historical_data) < 30:
            historical_data = np.pad(historical_data, (30 - len(historical_data), 0), 'edge')
        predicted_volatility = self.ai_stabilizer.predict_volatility(historical_data)
        predicted_price = median_price * (1 + predicted_volatility * 0.01)  # Adjust for volatility
        
        # Quantum-sign the data for tamper-proofing
        data_to_sign = f"{asset}:{predicted_price}:{predicted_volatility}".encode()
        signature = self.quantum_key.sign(data_to_sign)
        
        return {
            "asset": asset,
            "median_price": median_price,
            "predicted_price": predicted_price,
            "volatility_score": predicted_volatility,
            "sources_used": len(prices),
            "quantum_signature": signature.hex(),
            "timestamp": pd.Timestamp.now().isoformat()
        }

    def submit_to_blockchain(self, contract_address: str, feed_data: dict):
        """Submit oracle data to a smart contract for on-chain use."""
        contract = self.w3.eth.contract(address=contract_address, abi=[...])  # Load ABI from smart_contract.sol
        tx = contract.functions.updatePrice(
            feed_data["asset"],
            int(feed_data["predicted_price"] * 10**18),  # Convert to wei-like units
            feed_data["quantum_signature"]
        ).transact({'from': self.w3.eth.accounts[0]})  # Use a funded account
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        logging.info(f"Oracle data submitted: {receipt.transactionHash.hex()}")
        return receipt

    def get_stabilization_recommendation(self, current_price: float, target_peg: float = 1.0) -> dict:
        """Use AI to recommend stabilization actions based on oracle data."""
        return self.ai_stabilizer.suggest_stabilization(current_price, target_peg)

# Example usage (for testing)
if __name__ == "__main__":
    oracle = HyperTechOracle(web3_provider="https://mainnet.infura.io/v3/YOUR_KEY")
    feed = oracle.fetch_price_feeds("bitcoin")
    print(feed)
    recommendation = oracle.get_stabilization_recommendation(feed["predicted_price"])
    print(recommendation)
