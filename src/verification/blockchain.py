import json
import time
import hashlib
import os

class BlockchainRegistry:
    def __init__(self, registry_path='data/results/blockchain_registry.json'):
        self.registry_path = registry_path
        self.chain = []
        self.load()

    def load(self):
        if os.path.exists(self.registry_path):
            with open(self.registry_path) as f:
                self.chain = json.load(f)

    def save(self):
        os.makedirs('data/results', exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.chain, f, indent=2)

    def _compute_block_hash(self, block):
        block_str = json.dumps(block, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()

    def register(self, content_hash, public_key_hex, device_id, org_id):
        prev_hash = self.chain[-1]['block_hash'] if self.chain else '0' * 64
        block = {
            'block_id': len(self.chain),
            'timestamp': time.time(),
            'content_hash': content_hash,
            'public_key': public_key_hex,
            'device_id': device_id,
            'org_id': org_id,
            'prev_hash': prev_hash,
            'status': 'active'
        }
        block['block_hash'] = self._compute_block_hash(block)
        self.chain.append(block)
        self.save()
        return block['block_hash']

    def verify(self, content_hash):
        for block in self.chain:
            if block['content_hash'] == content_hash:
                if block['status'] == 'revoked':
                    return False, 'revoked'
                return True, 'verified'
        return False, 'not_found'

    def revoke(self, content_hash):
        for block in self.chain:
            if block['content_hash'] == content_hash:
                block['status'] = 'revoked'
                self.save()
                return True
        return False

    def get_chain_integrity(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            curr = self.chain[i]
            if curr['prev_hash'] != prev['block_hash']:
                return False
        return True
