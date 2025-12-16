import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from src.stablecoin.oracle import HyperTechOracle
from src.models.ai_model import QuantumAIStabilizer
from cryptography.hazmat.primitives.asymmetric import dilithium
import jwt
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Bazinga-Core Stablecoin Hyper-Tech API", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS for dApp integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-quantum-secure-secret"  # Use env var in production
oracle = HyperTechOracle(web3_provider="https://mainnet.infura.io/v3/YOUR_KEY")
ai_stabilizer = QuantumAIStabilizer()

# Pydantic models for request/response
class MintRequest(BaseModel):
    amount: float
    user_wallet: str

class RedeemRequest(BaseModel):
    amount: float
    user_wallet: str

class OracleResponse(BaseModel):
    asset: str
    median_price: float
    predicted_price: float
    volatility_score: float
    quantum_signature: str

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if payload.get("exp") < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def root():
    return {"message": "Welcome to Bazinga-Core Hyper-Tech Stablecoin API"}

@app.post("/mint", dependencies=[Depends(verify_token)])
@limiter.limit("10/minute")  # Rate limit for security
async def mint_stablecoin(request: MintRequest, req: Request):
    try:
        # Fetch oracle data for peg check
        feed = oracle.fetch_price_feeds("usd")  # Assuming USD-pegged
        if feed["predicted_price"] > 1.01:  # Hyper-precise peg threshold
            raise HTTPException(status_code=400, detail="Peg unstable - minting paused")
        
        # AI recommendation for stabilization
        rec = oracle.get_stabilization_recommendation(feed["predicted_price"])
        if rec["action"] != "mint":
            raise HTTPException(status_code=400, detail="AI suggests no minting")
        
        # Simulate minting (integrate with smart contract)
        # tx_hash = oracle.submit_to_blockchain("0xContractAddress", feed)  # Real implementation
        tx_hash = "0xSimulatedTxHash"  # Placeholder
        logging.info(f"Minted {request.amount} for {request.user_wallet}")
        return {"status": "Minted", "tx_hash": tx_hash, "ai_recommendation": rec}
    except Exception as e:
        logging.error(f"Mint error: {e}")
        raise HTTPException(status_code=500, detail="Minting failed")

@app.post("/redeem", dependencies=[Depends(verify_token)])
@limiter.limit("10/minute")
async def redeem_stablecoin(request: RedeemRequest, req: Request):
    try:
        feed = oracle.fetch_price_feeds("usd")
        rec = oracle.get_stabilization_recommendation(feed["predicted_price"])
        if rec["action"] != "burn":  # Redemption as burn
            raise HTTPException(status_code=400, detail="AI suggests no redemption")
        
        # Simulate redemption
        tx_hash = "0xSimulatedRedeemHash"
        logging.info(f"Redeemed {request.amount} for {request.user_wallet}")
        return {"status": "Redeemed", "tx_hash": tx_hash, "ai_recommendation": rec}
    except Exception as e:
        logging.error(f"Redeem error: {e}")
        raise HTTPException(status_code=500, detail="Redemption failed")

@app.get("/oracle/{asset}", response_model=OracleResponse)
@limiter.limit("100/minute")
async def get_oracle_feed(asset: str, req: Request):
    try:
        feed = oracle.fetch_price_feeds(asset)
        return OracleResponse(**feed)
    except Exception as e:
        logging.error(f"Oracle fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch oracle data")

@app.get("/stabilize")
async def get_stabilization_advice(current_price: float, target_peg: float = 1.0):
    rec = ai_stabilizer.suggest_stabilization(current_price, target_peg)
    return {"advice": rec}

# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
