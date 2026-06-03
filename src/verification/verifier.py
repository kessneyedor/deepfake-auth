import cv2
import sys
import json
sys.path.append('.')
from src.watermark.dct_decode import decode, ber
from src.signing.ecc_sign import verify as ecc_verify

def verify_media(image_path, original_payload, pub_key, provenance, signature, revocation_list):
    img = cv2.imread(image_path)
    recovered = decode(img, len(original_payload))
    wm_ber = ber(original_payload, recovered)

    msg = json.dumps(provenance, sort_keys=True).encode()
    sig_valid = ecc_verify(pub_key, msg, signature)

    revoked_ids = [r['device_id'] for r in revocation_list]
    key_ok = provenance.get('device') not in revoked_ids

    confidence = (
        (1 - wm_ber) * 0.5 +
        (0.3 if sig_valid else 0) +
        (0.2 if key_ok else 0)
    )

    return {
        'is_authentic': wm_ber < 0.1 and sig_valid and key_ok,
        'watermark_ber': round(wm_ber, 3),
        'signature_valid': sig_valid,
        'key_revoked': not key_ok,
        'confidence': round(confidence, 3),
        'verdict': 'AUTHENTIC' if wm_ber < 0.1 and sig_valid and key_ok else 'SUSPICIOUS'
    }
