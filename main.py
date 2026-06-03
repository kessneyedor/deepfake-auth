import sys
sys.path.append('.')
import cv2
import json
import time
import os
import csv
import glob
import hashlib
from src.metadata.extract import extract_provenance
from src.signing.key_manager import KeyManager
from src.signing.ecc_sign import sign
from src.watermark.dct_embed import embed
from src.verification.verifier import verify_media
from src.verification.blockchain import BlockchainRegistry
from src.verification.clip_fingerprint import extract_fingerprint, compare_fingerprints

PAYLOAD = [1, 0, 1, 1, 0, 0, 1, 0] * 6

def run_pipeline(image_path, priv_key, pub_key, km, bc):
    times = {}

    t0 = time.perf_counter()
    provenance = extract_provenance(image_path)
    times['metadata_ms'] = round((time.perf_counter() - t0) * 1000, 3)

    t0 = time.perf_counter()
    msg = json.dumps(provenance, sort_keys=True).encode()
    signature = sign(priv_key, msg)
    times['signing_ms'] = round((time.perf_counter() - t0) * 1000, 3)

    t0 = time.perf_counter()
    fp_original = extract_fingerprint(image_path)
    times['clip_ms'] = round((time.perf_counter() - t0) * 1000, 3)

    t0 = time.perf_counter()
    wm_img = embed(image_path, PAYLOAD)
    times['embedding_ms'] = round((time.perf_counter() - t0) * 1000, 3)

    wm_path = image_path.replace('images', 'images/watermarked').replace('.png', '_wm.png')
    os.makedirs(os.path.dirname(wm_path), exist_ok=True)
    cv2.imwrite(wm_path, wm_img)

    t0 = time.perf_counter()
    content_hash = provenance['content_hash']
    bc.register(content_hash, 'pub_key_placeholder',
                provenance.get('device', 'unknown'), 'KDUniv')
    times['blockchain_ms'] = round((time.perf_counter() - t0) * 1000, 3)

    t0 = time.perf_counter()
    result = verify_media(wm_path, PAYLOAD, pub_key, provenance,
                          signature, km.revocation_list)
    fp_watermarked = extract_fingerprint(wm_path)
    clip_similarity = compare_fingerprints(fp_original, fp_watermarked)
    bc_valid, bc_status = bc.verify(content_hash)
    result['blockchain_status'] = bc_status
    result['blockchain_valid'] = bc_valid
    result['clip_similarity'] = clip_similarity
    times['verification_ms'] = round((time.perf_counter() - t0) * 1000, 3)

    times['total_ms'] = round(sum(times.values()), 3)
    return result, times

if __name__ == '__main__':
    print("Loading CLIP model...")
    km = KeyManager()
    priv_key, pub_key, meta = km.generate_device_key('KDUniv', 'camera_001')
    bc = BlockchainRegistry()

    images = glob.glob('data/images/*.png')
    images = [i for i in images if 'watermarked' not in i and 'test_wm' not in i]

    print(f"Running full pipeline on {len(images)} images...\n")
    all_times = []
    results = []

    for img_path in images:
        result, times = run_pipeline(img_path, priv_key, pub_key, km, bc)
        all_times.append(times)
        results.append(result)
        print(f"{os.path.basename(img_path):20} | {result['verdict']:10} | "
              f"CLIP={result['clip_similarity']:.4f} | "
              f"blockchain={result['blockchain_status']:10} | "
              f"total={times['total_ms']}ms")

    print(f"\n=== Pipeline Latency Summary ===")
    for key in ['metadata_ms', 'signing_ms', 'clip_ms', 'embedding_ms',
                'blockchain_ms', 'verification_ms', 'total_ms']:
        avg = sum(t[key] for t in all_times) / len(all_times)
        print(f"  {key:20}: {avg:.3f} ms")

    authentic = sum(1 for r in results if r['is_authentic'])
    print(f"\nAuthentic: {authentic}/{len(results)} images")
    print(f"Chain integrity: {bc.get_chain_integrity()}")

    os.makedirs('data/results', exist_ok=True)
    with open('data/results/pipeline_latency.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_times[0].keys())
        writer.writeheader()
        writer.writerows(all_times)
    print("\nResults saved to data/results/pipeline_latency.csv")
