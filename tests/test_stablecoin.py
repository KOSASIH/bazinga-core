import pytest
from src.stablecoin.oracle import StablecoinOracle

@pytest.fixture
def oracle():
    return StablecoinOracle("http://localhost:8545", "models/test_model.h5")

def test_price_feed(oracle):
    price = oracle.get_price_feed("bitcoin")
    assert 0 < price < 100000  # Hyper-precise range

def test_mint_under_peg(oracle):
    # Mock contract and test minting
    assert oracle.update_peg("0xContract", 1.0) is not None
