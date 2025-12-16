from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_oracle_feed():
    response = client.get("/oracle/bitcoin")
    assert response.status_code == 200
    data = response.json()
    assert "predicted_price" in data

def test_mint_without_auth():
    response = client.post("/mint", json={"amount": 100, "user_wallet": "0x..."})
    assert response.status_code == 401  # Unauthorized
