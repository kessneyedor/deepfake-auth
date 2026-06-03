import cv2
import os
import json
import time
import hashlib
from PIL import Image, ExifTags

def extract_provenance(image_path):
    with open(image_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()

    img = Image.open(image_path)
    exif_data = img._getexif() or {}
    tags = {}
    for k, v in exif_data.items():
        tag_name = ExifTags.TAGS.get(k, k)
        if isinstance(v, (str, int, float)):
            tags[tag_name] = v

    return {
        'content_hash': content_hash,
        'timestamp': tags.get('DateTime', str(time.time())),
        'device': tags.get('Model', 'unknown'),
        'width': img.width,
        'height': img.height,
        'source_id': 'KDUniv_deepfake_auth_v1',
        'image_path': os.path.basename(image_path),
    }
