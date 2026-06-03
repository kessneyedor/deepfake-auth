from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import hashlib, time, statistics, csv, os

def generate_keypair():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key

def sign(private_key, message: bytes) -> bytes:
    digest = hashlib.sha256(message).digest()
    return private_key.sign(digest)

def verify(public_key, message: bytes, signature: bytes) -> bool:
    try:
        digest = hashlib.sha256(message).digest()
        public_key.verify(signature, digest)
        return True
    except Exception:
        return False

def benchmark(n=1000):
    priv, pub = generate_keypair()
    msg = b'sample_media_hash_content'
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        sig = sign(priv, msg)
        times.append((time.perf_counter() - t0) * 1000)

    mean = statistics.mean(times)
    std = statistics.stdev(times)
    print(f"Ed25519 signing: mean={mean:.3f}ms  std={std:.3f}ms")

    os.makedirs('data/results', exist_ok=True)
    with open('data/results/signing_latency.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['algorithm', 'mean_ms', 'std_ms', 'iterations'])
        writer.writerow(['Ed25519', round(mean, 3), round(std, 3), n])

    print("Results saved to data/results/signing_latency.csv")
    return times

if __name__ == '__main__':
    benchmark()