import pytest
from src.models.ai_model import QuantumAIStabilizer
import numpy as np

def test_predict_volatility():
    model = QuantumAIStabilizer(use_quantum=False)  # Test classical fallback
    data = np.random.rand(30)
    vol = model.predict_volatility(data)
    assert 0 <= vol <= 1

def test_suggest_stabilization():
    model = QuantumAIStabilizer()
    suggestion = model.suggest_stabilization(0.98)  # Below peg
    assert "action" in suggestion
    assert suggestion["action"] in ["mint", "burn", "hold"]
