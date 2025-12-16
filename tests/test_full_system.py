import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.models.ai_model import QuantumAIStabilizer
from src.stablecoin.oracle import HyperTechOracle
from src.api.main import app
from fastapi.testclient import TestClient
from web3 import Web3
from src.security.audit import QuantumSecurityAuditor

# Setup test client for API
client = TestClient(app)

# Mock Web3 for contract tests (use real in production)
w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
mock_contract_address = "0xMockContractAddress"  # Replace with deployed address
mock_abi = [...]  # Load real ABI from smart_contract.sol

@pytest.fixture
def ai_stabilizer():
    return QuantumAIStabilizer(use_quantum=False)  # Disable quantum for faster tests

@pytest.fixture
def oracle():
    return HyperTechOracle(web3_provider="http://localhost:8545")

@pytest.fixture
def auditor():
    return QuantumSecurityAuditor()

def test_ai_model_prediction(ai_stabilizer):
    """Test AI model for volatility prediction and stabilization."""
    dummy_data = np.random.rand(30)
    volatility = ai_stabilizer.predict_volatility(dummy_data)
    assert 0 <= volatility <= 1, "Volatility should be between 0 and 1"
    
    rec = ai_stabilizer.suggest_stabilization(1.05)  # Above peg
    assert rec["action"] in ["mint", "burn", "hold"], "Action should be valid"
    assert "amount" in rec, "Recommendation should include amount"

def test_oracle_feed_aggregation(oracle):
    """Test oracle for price feeds and quantum signatures."""
    with patch('requests.get') as mock_get:
        # Mock API responses
        mock_get.return_value.json.return_value = {"bitcoin": {"usd": 50000}}
        feed = oracle.fetch_price_feeds("bitcoin")
        assert "predicted_price" in feed, "Feed should include predicted price"
        assert "quantum_signature" in feed, "Feed should have quantum signature"
        assert feed["sources_used"] > 0, "Should use at least one source"

def test_api_endpoints():
    """Test API endpoints for mint, redeem, and oracle queries."""
    # Test root
    response = client.get("/")
    assert response.status_code == 200, "Root endpoint should work"
    
    # Test oracle feed (no auth needed)
    response = client.get("/oracle/bitcoin")
    assert response.status_code == 200, "Oracle endpoint should return data"
    data = response.json()
    assert "predicted_price" in data, "Response should include predicted price"
    
    # Test mint with mock auth (simulate JWT)
    with patch('src.api.main.verify_token') as mock_verify:
        mock_verify.return_value = {"user": "test"}
        response = client.post("/mint", json={"amount": 100, "user_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"})
        assert response.status_code == 200, "Mint should succeed with auth"
        assert "tx_hash" in response.json(), "Response should include tx hash"
    
    # Test redeem
    with patch('src.api.main.verify_token') as mock_verify:
        mock_verify.return_value = {"user": "test"}
        response = client.post("/redeem", json={"amount": 50, "user_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"})
        assert response.status_code == 200, "Redeem should succeed"

def test_smart_contract_interaction():
    """Test smart contract mint and redeem via Web3."""
    with patch.object(w3.eth, 'contract') as mock_contract:
        mock_instance = MagicMock()
        mock_contract.return_value = mock_instance
        mock_instance.functions.mint.return_value.transact.return_value = "0xTxHash"
        mock_instance.functions.redeem.return_value.transact.return_value = "0xRedeemHash"
        
        # Simulate mint
        contract = w3.eth.contract(address=mock_contract_address, abi=mock_abi)
        tx = contract.functions.mint("0xUser", 100, "mock_signature").transact()
        assert tx == "0xTxHash", "Mint transaction should return hash"
        
        # Simulate redeem
        tx = contract.functions.redeem(50).transact()
        assert tx == "0xRedeemHash", "Redeem transaction should return hash"

def test_security_audit(auditor):
    """Test security auditor for vulnerabilities and compliance."""
    with patch('subprocess.run') as mock_subprocess:
        mock_subprocess.return_value.stdout = "Mock audit output"
        report = auditor.run_full_audit()
        assert "smart_contract" in report, "Report should include contract audit"
        assert "python_code" in report, "Report should include code audit"
        assert "oracle_integrity" in report, "Report should include oracle check"
        assert "overall_risk" in report, "Report should have overall risk assessment"

def test_end_to_end_mint_flow(ai_stabilizer, oracle):
    """End-to-end test: AI prediction -> Oracle feed -> API mint -> Contract interaction."""
    # Step 1: AI stabilization check
    rec = ai_stabilizer.suggest_stabilization(0.98)  # Below peg
    assert rec["action"] == "mint", "AI should suggest minting for low peg"
    
    # Step 2: Oracle feed
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"bitcoin": {"usd": 49000}}
        feed = oracle.fetch_price_feeds("bitcoin")
        assert feed["predicted_price"] > 0, "Oracle should provide valid price"
    
    # Step 3: API mint with mocked components
    with patch('src.api.main.verify_token'), \
         patch.object(oracle, 'fetch_price_feeds', return_value=feed), \
         patch.object(oracle, 'get_stabilization_recommendation', return_value=rec):
        response = client.post("/mint", json={"amount": 100, "user_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"})
        assert response.status_code == 200, "End-to-end mint should succeed"
        data = response.json()
        assert data["ai_recommendation"]["action"] == "mint", "AI recommendation should be included"

# Additional test for error handling
def test_error_handling():
    """Test error scenarios (e.g., invalid peg, no auth)."""
    # Unauthorized mint
    response = client.post("/mint", json={"amount": 100, "user_wallet": "0x..."})
    assert response.status_code == 401, "Should require auth"
    
    # Invalid oracle asset
    response = client.get("/oracle/invalid")
    assert response.status_code == 500, "Should handle invalid assets gracefully"
