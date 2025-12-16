import pytest
from src.stablecoin.oracle import HyperTechOracle

@pytest.fixture
def oracle():
    return HyperTechOracle(web3_provider="http://localhost:8545", sources=["https://api.coingecko.com/..."])  # Mock URL

def test_fetch_price_feeds(oracle):
    feed = oracle.fetch_price_feeds("bitcoin")
    assert "predicted_price" in feed
    assert 0 < feed["predicted_price"] < 100000

def test_stabilization_recommendation(oracle):
    rec = oracle.get_stabilization_recommendation(1.02)
    assert rec["action"] in ["mint", "burn", "hold"]
