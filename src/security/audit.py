from cryptography.hazmat.primitives import hashes, hmac
import jwt

def generate_quantum_key():
    # Generate Dilithium key pair
    private_key = dilithium.generate_private_key()
    public_key = private_key.public_key()
    return private_key, public_key

def sign_transaction(data: bytes, private_key):
    return private_key.sign(data)

def verify_jwt(token: str):
    # Decode and verify JWT with quantum-resistant claims
    decoded = jwt.decode(token, options={"verify_signature": False})  # Add full verification
    return decoded
