import os
import json
import time
import hashlib
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class KeyManager:
    def __init__(self):
        self.root_secret = os.urandom(32)
        self.key_events = []
        self.revocation_list = []

    def derive_secret(self, parent_secret, info):
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32,
                    salt=None, info=info.encode())
        return hkdf.derive(parent_secret)

    def generate_device_key(self, org_id, device_id):
        inter_secret = self.derive_secret(self.root_secret, f'org:{org_id}')
        device_secret = self.derive_secret(inter_secret, f'device:{device_id}')
        priv_key = Ed25519PrivateKey.from_private_bytes(device_secret)
        pub_key = priv_key.public_key()
        meta = {
            'device_id': device_id,
            'org_id': org_id,
            'created_at': time.time(),
            'expires_at': time.time() + 30 * 86400,
            'status': 'active'
        }
        self.key_events.append({'event': 'keygen', 'device_id': device_id,
                                 'org_id': org_id, 'timestamp': time.time()})
        return priv_key, pub_key, meta

    def revoke(self, device_id):
        self.revocation_list.append({'device_id': device_id,
                                      'revoked_at': time.time()})
        self.key_events.append({'event': 'revocation', 'device_id': device_id,
                                 'timestamp': time.time()})

    def is_revoked(self, device_id):
        return any(r['device_id'] == device_id for r in self.revocation_list)

    def save_logs(self):
        os.makedirs('data/results', exist_ok=True)
        with open('data/results/key_events.json', 'w') as f:
            json.dump(self.key_events, f, indent=2)
        with open('data/results/revocation_list.json', 'w') as f:
            json.dump(self.revocation_list, f, indent=2)
